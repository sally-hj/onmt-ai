"""Référence naïve/saisonnière évaluée avec séparation chronologique stricte."""
import math
from datetime import date

from app.core.errors import AppError
from app.schemas.analysis import SeriesPoint


def next_month(value, offset=1):
    n = value.year*12+value.month-1+offset
    return date(n//12,n%12+1,1)


def forecast(series, horizon):
    if horizon > 12 or len(series) < 36 or any(p.value is None for p in series):
        raise AppError('missing_data','Prévision : 36 mois complets requis et horizon maximal de 12 mois.',422)
    if any(next_month(a.date) != b.date for a,b in zip(series,series[1:])):
        raise AppError('missing_data','Historique discontinu : prévision refusée.',422)
    train, test = series[:-12],series[-12:]
    naive_errors = [p.value-train[-1].value for p in test]
    seasonal_errors = [p.value-train[-12+i].value for i,p in enumerate(test)]
    mae_naive = sum(abs(x) for x in naive_errors)/12
    mae_seasonal = sum(abs(x) for x in seasonal_errors)/12
    seasonal = mae_seasonal <= mae_naive
    errors = seasonal_errors if seasonal else naive_errors
    rmse = math.sqrt(sum(x*x for x in errors)/12)
    points = []
    for step in range(horizon):
        value = series[-12+step].value if seasonal else series[-1].value
        # Bande empirique des erreurs hors entraînement ; aucune couverture probabiliste garantie.
        points.append(SeriesPoint(date=next_month(series[-1].date,step+1),value=value,kind='forecast',
                                  lower=max(0,value-1.96*rmse),upper=value+1.96*rmse))
    warnings = [f'forecast_method:{"seasonal_naive" if seasonal else "last_value"}',
                f'holdout_12_months_mae_naive:{mae_naive:.4f}',f'holdout_12_months_mae_seasonal:{mae_seasonal:.4f}',
                f'holdout_rmse:{rmse:.4f}','forecast_interval_empirical_no_guaranteed_coverage',
                'forecast_no_causal_explanation_or_exogenous_variables']
    return points,warnings
