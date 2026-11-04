from pathlib import Path
from typing import Protocol

from app.core.errors import AppError, forbidden
from app.core.security import require_module
from app.schemas.analysis import AnalysisResult
from app.schemas.common import AccessContext


class AnalysisProvider(Protocol):
    def get_analysis(self, analysis_id: str, access_context: AccessContext) -> AnalysisResult:
        """Doha vérifie existence, droits métier et références avant de retourner le résultat."""
        ...


class UnconnectedAnalysisProvider:
    def get_analysis(self, analysis_id, access_context):
        require_module(access_context)
        raise AppError('missing_data', 'Le fournisseur des analyses de Doha n’est pas connecté.', 503)


class SyntheticAnalysisProvider:
    """Uniquement construit en mode démo explicite, jamais en secours d’une erreur réelle."""
    def __init__(self, fixture_dir: Path):
        self.results = {a.analysis_id: a for p in fixture_dir.glob('analysis_result*.json')
                        for a in [AnalysisResult.model_validate_json(p.read_text(encoding='utf-8'))]}
        if not self.results or any(not a.is_synthetic for a in self.results.values()):
            raise ValueError('Fixtures synthétiques obligatoires en démo')

    def get_analysis(self, analysis_id, access_context):
        require_module(access_context)
        if ('commercial' not in access_context.allowed_modules or 'Agadir' not in access_context.allowed_territories):
            raise forbidden()
        result = self.results.get(analysis_id)
        if result is None:
            raise AppError('missing_data', 'Analyse de démonstration absente.', 404)
        return result.model_copy(deep=True)
