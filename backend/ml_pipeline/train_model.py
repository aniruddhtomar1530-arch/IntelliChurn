import argparse
from pathlib import Path
import sys

import joblib
import pandas as pd
import shap
from catboost import CatBoostClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.features import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, FEATURE_COLUMNS  # noqa: E402


def train(dataset: Path, output: Path) -> None:
    data = pd.read_csv(dataset)
    source_columns = {
        "customerID": "customer_id",
        "SeniorCitizen": "senior_citizen",
        "Partner": "partner",
        "Dependents": "dependents",
        "PhoneService": "phone_service",
        "MultipleLines": "multiple_lines",
        "InternetService": "internet_service",
        "OnlineSecurity": "online_security",
        "OnlineBackup": "online_backup",
        "DeviceProtection": "device_protection",
        "TechSupport": "tech_support",
        "StreamingTV": "streaming_tv",
        "StreamingMovies": "streaming_movies",
        "Contract": "contract",
        "PaperlessBilling": "paperless_billing",
        "PaymentMethod": "payment_method",
        "MonthlyCharges": "monthly_charges",
        "TotalCharges": "total_charges",
        "Churn": "churn",
    }
    data = data.rename(columns=source_columns)
    required = set(FEATURE_COLUMNS) | {"churn"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")

    features = data[FEATURE_COLUMNS].copy()
    features["total_charges"] = pd.to_numeric(features["total_charges"], errors="coerce")
    for name in BOOLEAN_FEATURES:
        features[name] = features[name].map({"Yes": True, "No": False})
        if features[name].isna().any():
            raise ValueError(f"{name} must contain only 'Yes' and 'No'.")
    target = data["churn"].map({"Yes": 1, "No": 0})
    if target.isna().any():
        raise ValueError("Churn column must contain only 'Yes' and 'No'.")
    class_counts = target.value_counts()
    if len(class_counts) != 2:
        raise ValueError("Training data must contain both churn classes: 'Yes' and 'No'.")
    minority_count = int(class_counts.min())
    if minority_count < 2:
        raise ValueError("Each churn class needs at least two rows for SMOTE.")

    numeric_features = [name for name in FEATURE_COLUMNS if name not in CATEGORICAL_FEATURES]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
        ]
    )
    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("sampler", SMOTE(random_state=42, k_neighbors=min(5, minority_count - 1))),
            (
                "classifier",
                CatBoostClassifier(
                    iterations=500,
                    depth=6,
                    learning_rate=0.05,
                    verbose=False,
                    random_seed=42,
                    thread_count=4,
                    allow_writing_files=False,
                ),
            ),
        ]
    )
    pipeline.fit(features, target)
    explainer = shap.TreeExplainer(pipeline.named_steps["classifier"])
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "explainer": explainer,
            "feature_names": pipeline.named_steps["preprocessor"].get_feature_names_out().tolist(),
        },
        output,
    )
    print(
        f"Model saved to {output}. Trained on {len(features)} rows "
        f"({int(target.sum())} churn cases)."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train IntelliChurn's churn classifier.")
    parser.add_argument(
        "--data",
        type=Path,
        default=ROOT / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "backend" / "ml_pipeline" / "saved_models" / "churn_bundle.joblib",
    )
    args = parser.parse_args()
    if not args.data.is_file():
        parser.error(f"Dataset not found: {args.data}")
    train(args.data, args.output)
