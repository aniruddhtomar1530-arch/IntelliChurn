from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gender: Mapped[str] = mapped_column(String(20))
    senior_citizen: Mapped[int] = mapped_column(Integer)
    partner: Mapped[bool] = mapped_column(Boolean)
    dependents: Mapped[bool] = mapped_column(Boolean)
    tenure: Mapped[int] = mapped_column(Integer)
    phone_service: Mapped[bool] = mapped_column(Boolean)
    multiple_lines: Mapped[str] = mapped_column(String(40))
    internet_service: Mapped[str] = mapped_column(String(40))
    online_security: Mapped[str] = mapped_column(String(40))
    online_backup: Mapped[str] = mapped_column(String(40))
    device_protection: Mapped[str] = mapped_column(String(40))
    tech_support: Mapped[str] = mapped_column(String(40))
    streaming_tv: Mapped[str] = mapped_column(String(40))
    streaming_movies: Mapped[str] = mapped_column(String(40))
    contract: Mapped[str] = mapped_column(String(40))
    paperless_billing: Mapped[bool] = mapped_column(Boolean)
    payment_method: Mapped[str] = mapped_column(String(60))
    monthly_charges: Mapped[float] = mapped_column(Float)
    total_charges: Mapped[float] = mapped_column(Float)
    churn: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    churn_probability: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20))
    explanation: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    customer: Mapped[Customer] = relationship(back_populates="predictions")
