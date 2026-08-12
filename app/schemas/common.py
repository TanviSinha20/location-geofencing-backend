"""Shared API response schemas."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int


class TimestampMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recorded_at: datetime = Field(..., description="ISO-8601 timestamp")
