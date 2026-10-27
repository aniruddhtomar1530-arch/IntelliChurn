from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from fastapi import HTTPException

from app.core.config import settings
from app.schemas import CustomerInput
from app.services.features import FEATURE_COLUMNS, risk_level


@lru_cache
def _load_bundle():
    model_path = Path(settings.model_path)
    if not model_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Trained model not found at {model_path}. Train it with backend/ml_pipeline/train_model.py.",
        )
    return joblib.load(model_path)


def predict(customer: CustomerInput) -> dict:
    bundle = _load_bundle()
    row = pd.DataFrame([{key: getattr(customer, key) for key in FEATURE_COLUMNS}])
    pipeline = bundle["pipeline"]
    probability = float(pipeline.predict_proba(row)[0][1])
    transformed = pipeline.named_steps["preprocessor"].transform(row)
    values = bundle["explainer"].shap_values(transformed)
    if isinstance(values, list):
        values = values[1]
    elif values.ndim == 3:
        values = values[:, :, 1]
    contributions = values[0]
    names = bundle["feature_names"]
    factors = sorted(
        [
            {"feature": str(name), "impact": float(impact)}
            for name, impact in zip(names, contributions, strict=True)
        ],
        key=lambda item: abs(item["impact"]),
        reverse=True,
    )[:8]
    return {
        "churn_probability": probability,
        "risk_level": risk_level(probability),
        "explanation": factors,
    }
