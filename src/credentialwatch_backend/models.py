from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from .db import Base

class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    npi: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String)
    dept: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    primary_specialty: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    credentials: Mapped[List["Credential"]] = relationship("Credential", back_populates="provider")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="provider")


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("providers.id"))
    type: Mapped[str] = mapped_column(String)  # e.g. "state_license", "board_cert", "dea"
    issuer: Mapped[str] = mapped_column(String)
    number: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)  # "active", "expired", "pending"
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider: Mapped["Provider"] = relationship("Provider", back_populates="credentials")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="credential")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("providers.id"))
    credential_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("credentials.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String)  # "info", "warning", "critical"
    window_days: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String, default="ui")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    provider: Mapped["Provider"] = relationship("Provider", back_populates="alerts")
    credential: Mapped[Optional["Credential"]] = relationship("Credential", back_populates="alerts")
