"""Tourist location ORM model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TouristLocation(Base):
    __tablename__ = "tourist_locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tourist_id: Mapped[str] = mapped_column(String(64), index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    __table_args__ = (Index("ix_tourist_current", "tourist_id", "is_current"),)
