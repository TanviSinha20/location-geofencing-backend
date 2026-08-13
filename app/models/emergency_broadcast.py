"""Emergency broadcast log."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EmergencyBroadcast(Base):
    __tablename__ = "emergency_broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    zone_name: Mapped[str] = mapped_column(String(128), nullable=False)
    radius_km: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    tourists_notified: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
