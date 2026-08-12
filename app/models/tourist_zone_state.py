"""Tracks which zones a tourist is currently inside."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TouristZoneState(Base):
    __tablename__ = "tourist_zone_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tourist_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    zone_id: Mapped[str] = mapped_column(String(64), ForeignKey("geofences.id"), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("tourist_id", "zone_id", name="uq_tourist_zone"),)
