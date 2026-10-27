from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    customer_id: str = Field(min_length=1, max_length=64)
    gender: str
    senior_citizen: int = Field(ge=0, le=1)
    partner: bool
    dependents: bool
    tenure: int = Field(ge=0, le=120)
    phone_service: bool
    multiple_lines: str
    internet_service: str
    online_security: str
    online_backup: str
    device_protection: str
    tech_support: str
    streaming_tv: str
    streaming_movies: str
    contract: str
    paperless_billing: bool
    payment_method: str
    monthly_charges: float = Field(ge=0)
    total_charges: float = Field(ge=0)
    churn: bool | None = None


class CustomerRead(CustomerInput):
    model_config = ConfigDict(from_attributes=True)


class Factor(BaseModel):
    feature: str
    impact: float


class PredictionRead(BaseModel):
    id: int
    customer_id: str
    churn_probability: float
    risk_level: str
    explanation: list[Factor]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    total_customers: int
    high_risk_customers: int
    predictions_made: int
    labeled_churn_rate: float | None
    recent_predictions: list[PredictionRead]


class RetentionRequest(BaseModel):
    customer: CustomerInput
    churn_probability: float = Field(ge=0, le=1)
    factors: list[Factor]
