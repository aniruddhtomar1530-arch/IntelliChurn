import csv
import io
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Customer, Prediction
from app.schemas import (
    CustomerInput,
    CustomerRead,
    DashboardSummary,
    PredictionRead,
    RetentionRequest,
)
from app.services.features import FEATURE_COLUMNS, risk_level
from app.services.llm_service import generate_retention_strategy
from app.services.ml_service import predict

router = APIRouter(prefix="/api")
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
CSV_FIELDS = set(FEATURE_COLUMNS) | {"customer_id", "churn"}
HEADER_ALIASES = {
    re.sub(r"[^a-z0-9]", "", field.lower()): field
    for field in CSV_FIELDS
}
HEADER_ALIASES["customerid"] = "customer_id"


def _as_bool(value: str, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise ValueError(f"{field} must be true/false, yes/no, or 1/0")


def _parse_customer(row: dict[str, str | None]) -> CustomerInput:
    values = {key: (value or "").strip() for key, value in row.items() if key}
    unknown_fields = set(values) - CSV_FIELDS
    if unknown_fields:
        raise ValueError(f"Unexpected CSV columns: {', '.join(sorted(unknown_fields))}")
    if not values.get("customer_id"):
        raise ValueError("customer_id is required")
    total_charges = values.get("total_charges", "")
    churn_value = values.get("churn", "")
    return CustomerInput(
        customer_id=values["customer_id"],
        gender=values["gender"],
        senior_citizen=int(values["senior_citizen"]),
        partner=_as_bool(values["partner"], "partner"),
        dependents=_as_bool(values["dependents"], "dependents"),
        tenure=int(values["tenure"]),
        phone_service=_as_bool(values["phone_service"], "phone_service"),
        multiple_lines=values["multiple_lines"],
        internet_service=values["internet_service"],
        online_security=values["online_security"],
        online_backup=values["online_backup"],
        device_protection=values["device_protection"],
        tech_support=values["tech_support"],
        streaming_tv=values["streaming_tv"],
        streaming_movies=values["streaming_movies"],
        contract=values["contract"],
        paperless_billing=_as_bool(values["paperless_billing"], "paperless_billing"),
        payment_method=values["payment_method"],
        monthly_charges=float(values["monthly_charges"]),
        total_charges=float(total_charges) if total_charges else 0.0,
        churn=_as_bool(churn_value, "churn") if churn_value else None,
    )


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db)):
    customer_count = db.scalar(select(func.count()).select_from(Customer)) or 0
    prediction_count = db.scalar(select(func.count()).select_from(Prediction)) or 0
    latest_prediction_ids = (
        select(func.max(Prediction.id).label("prediction_id"))
        .group_by(Prediction.customer_id)
        .subquery()
    )
    high_risk_count = db.scalar(
        select(func.count())
        .select_from(Prediction)
        .join(latest_prediction_ids, Prediction.id == latest_prediction_ids.c.prediction_id)
        .where(Prediction.risk_level == "High")
    ) or 0
    labeled_count = db.scalar(
        select(func.count()).select_from(Customer).where(Customer.churn.is_not(None))
    ) or 0
    churn_count = db.scalar(
        select(func.count()).select_from(Customer).where(Customer.churn.is_(True))
    ) or 0
    recent = db.scalars(
        select(Prediction)
        .join(latest_prediction_ids, Prediction.id == latest_prediction_ids.c.prediction_id)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .limit(8)
    ).all()
    return {
        "total_customers": customer_count,
        "high_risk_customers": high_risk_count,
        "predictions_made": prediction_count,
        "labeled_churn_rate": churn_count / labeled_count if labeled_count else None,
        "recent_predictions": recent,
    }


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
):
    if not 1 <= limit <= 500 or offset < 0:
        raise HTTPException(status_code=422, detail="limit must be 1-500 and offset cannot be negative")
    return db.scalars(
        select(Customer).order_by(Customer.customer_id).offset(offset).limit(limit)
    ).all()


@router.get("/customers/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/customers/import")
async def import_customers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a CSV file.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV file must be 20 MB or smaller.")
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        required_fields = CSV_FIELDS - {"churn"}
        if not reader.fieldnames:
            raise ValueError("CSV must include a header row.")
        raw_headers = reader.fieldnames
        normalized_headers = [
            HEADER_ALIASES.get(
                re.sub(r"[^a-z0-9]", "", header.lower()),
                header.strip(),
            )
            for header in raw_headers
        ]
        if len(normalized_headers) != len(set(normalized_headers)):
            raise ValueError("CSV has duplicate columns after header normalization.")
        missing = sorted(required_fields - set(normalized_headers))
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")
        rows = []
        customer_ids = set()
        for line_number, raw_row in enumerate(reader, start=2):
            try:
                if None in raw_row:
                    raise ValueError("row has more values than the header")
                normalized_row = dict(zip(normalized_headers, raw_row.values(), strict=True))
                customer = _parse_customer(normalized_row)
                if customer.customer_id in customer_ids:
                    raise ValueError(f"duplicate customer_id {customer.customer_id}")
                customer_ids.add(customer.customer_id)
                rows.append(customer.model_dump())
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"Row {line_number}: {exc}") from exc
        if not rows:
            raise ValueError("CSV contains no customer rows.")
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid CSV: {exc}") from exc

    try:
        for values in rows:
            customer_id = values.pop("customer_id")
            existing = db.get(Customer, customer_id)
            if existing is None:
                db.add(Customer(customer_id=customer_id, **values))
            else:
                for key, value in values.items():
                    setattr(existing, key, value)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"imported": len(rows)}


@router.post("/customers/{customer_id}/predict", response_model=PredictionRead)
def predict_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer_data = CustomerInput.model_validate(customer)
    result = predict(customer_data)
    prediction = Prediction(
        customer_id=customer_id,
        churn_probability=result["churn_probability"],
        risk_level=result["risk_level"] or risk_level(result["churn_probability"]),
        explanation=result["explanation"],
        created_at=datetime.now(timezone.utc),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.post("/retention-strategy")
def retention_strategy(request: RetentionRequest):
    return {"strategy": generate_retention_strategy(request)}


@router.get("/customers/{customer_id}/predictions", response_model=list[PredictionRead])
def customer_predictions(customer_id: str, db: Session = Depends(get_db)):
    if db.get(Customer, customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db.scalars(
        select(Prediction)
        .where(Prediction.customer_id == customer_id)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
    ).all()
