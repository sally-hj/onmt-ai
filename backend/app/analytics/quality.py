"""Contrôles bloquants pour éviter sommes partielles silencieuses et double comptage."""
import math
from collections import Counter


def inspect_rows(rows, source):
    errors = []
    grains = Counter(tuple(row.get(k) for k in source['grain']) for row in rows)
    keys = Counter(row.get('key') for row in rows)
    if any(n > 1 for n in grains.values()) or any(n > 1 for n in keys.values()):
        errors.append('duplicate_grain_or_key')
    if any(row.get('_invalid_date') for row in rows):
        errors.append('invalid_month')
    for field in source['fields']:
        if field in {'key','month','destination','market'}:
            if any(row.get(field) in [None,''] for row in rows):
                errors.append('missing_dimension:' + field)
            continue
        values = [r.get(field) for r in rows]
        if any(v is None for v in values):
            errors.append('missing_value:' + field)
        if any(v is not None and (isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v < 0) for v in values):
            errors.append('invalid_nonnegative_number:' + field)
        if not source.get('units',{}).get(field):
            errors.append('missing_unit:' + field)
    for row in rows:
        if isinstance(row.get('rooms_sold'),(int,float)) and isinstance(row.get('rooms_available'),(int,float)):
            if row['rooms_sold'] > row['rooms_available']:
                errors.append('occupied_rooms_exceed_capacity')
    return sorted(set(errors))
