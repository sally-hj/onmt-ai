from app.core.timing import measured
"""Lecture native autorisée : les fichiers QVD restent les seules sources tabulaires."""
import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path
from threading import RLock

from pyqvd import QvdTable

from app.core.errors import AppError, forbidden


def source_version(path: Path):
    if not path.is_file():
        raise AppError('missing_data', 'Source QVD configurée absente ; régénérez les données ou vérifiez la configuration.', 503)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_month(value):
    """Dates ISO, dates Python et numéros de date Qlik (origine 1899-12-30)."""
    if isinstance(value, datetime):
        value = value.date()
    elif isinstance(value, (float, int)) and not isinstance(value, bool):
        value = date(1899, 12, 30) + timedelta(days=value)
    elif isinstance(value, str):
        value = date.fromisoformat(value)
    if not isinstance(value, date) or value.day != 1:
        raise ValueError('La période mensuelle doit commencer le premier jour du mois.')
    return value.isoformat()


class QvdReader:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.cache={}
        self.cache_lock=RLock()

    def path(self, source):
        path = (self.root/source['file']).resolve()
        if not path.is_relative_to(self.root) or path.suffix.casefold() != '.qvd':
            raise AppError('invalid_request','Chemin de source QVD non autorisé.',422)
        return path

    @measured('lecture_qvd')
    def read(self, source, access, filters=None):
        if source['module'] not in access.allowed_modules or not access.allowed_territories:
            raise forbidden()
        filters = filters or {}
        if set(filters)-{'destination','market'}:
            raise AppError('invalid_request','Filtre inconnu ; seuls destination et market sont autorisés.',422)
        if filters.get('destination') and filters['destination'] not in access.allowed_territories:
            raise forbidden()
        path = self.path(source)
        before = source_version(path)
        try:
            with self.cache_lock:
                cached=self.cache.get(str(path))
                if cached and cached[0]==before:
                    table=cached[1]
                else:
                    table=QvdTable.from_qvd(path).to_dict()
                    if len(self.cache)>=8: self.cache.clear()
                    self.cache[str(path)]=(before,table)
        except Exception as exc:
            raise AppError('tool_failed','QVD illisible ; vérifier format, compression et compatibilité PyQvd.',422) from exc
        if source_version(path) != before:
            raise AppError('source_changed','La source a changé pendant sa lecture ; relancez après son remplacement complet.',409)
        missing = set(source['fields'].values())-set(table['columns'])
        if missing:
            raise AppError('missing_data','Schéma QVD incomplet : ' + ', '.join(sorted(missing)),422)
        rows = []
        for values in table['data']:
            native = dict(zip(table['columns'],values))
            row = {logical:native[physical] for logical,physical in source['fields'].items()}
            # Le périmètre territorial est appliqué avant tout calcul, contrôle visible ou prompt.
            if row['destination'] not in access.allowed_territories:
                continue
            if any(row.get(k) != v for k,v in filters.items()):
                continue
            try:
                row['month'] = normalize_month(row['month'])
            except (ValueError,TypeError,OverflowError):
                row['_invalid_date'] = True
            rows.append(row)
        discovery = {name: sorted({type(row[i]).__name__ for row in table['data'] if row[i] is not None})
                     for i,name in enumerate(table['columns'])}
        return rows, before, discovery
