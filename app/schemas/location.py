"""Location request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LocationUpdateRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: float | None = Field(None, ge=0, description="Accuracy in meters")
    speed: float | None = Field(None, ge=0, description="Speed in m/s")
    heading: float | None = Field(None, ge=0, lt=360, description="Bearing in degrees")
    recorded_at: datetime | None = Field(None, description="Client timestamp; defaults to server time")
    safety_radius_km: float | None = Field(
        None,
        gt=0,
        le=100,
        description="User-configured radius (km) for nearby safety resource search",
    )

    @field_validator("latitude", "longitude")
    @classmethod
    def reject_null_island_edge_cases(cls, value: float) -> float:
        return round(value, 7)


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tourist_id: str
    latitude: float
    longitude: float
    accuracy: float | None = None
    speed: float | None = None
    heading: float | None = None
    recorded_at: datetime
    last_updated: datetime
    is_current: bool = True


class LocationUpdateResult(BaseModel):
    location: LocationResponse
    geofence_status: str
    active_zones: list[str]
    events: list["GeofenceEventResponse"]
    nearby_safety: "NearbySafetyResponse | None" = None


class TouristLocationSummary(BaseModel):
    tourist_id: str
    latitude: float
    longitude: float
    recorded_at: datetime
    last_updated: datetime


class SimulateMovementRequest(BaseModel):
    start_latitude: float = Field(..., ge=-90, le=90)
    start_longitude: float = Field(..., ge=-180, le=180)
    end_latitude: float = Field(..., ge=-90, le=90)
    end_longitude: float = Field(..., ge=-180, le=180)
    steps: int = Field(5, ge=2, le=50)
    interval_ms: int = Field(0, ge=0, le=5000, description="Delay between steps (testing only)")


class SimulateMovementResponse(BaseModel):
    tourist_id: str
    updates: list[LocationUpdateResult]


class MockLocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    label: str | None = Field(None, description="Optional test label e.g. safe, unsafe_entry")


# Forward reference resolved in geofence/safety schemas
from app.schemas.geofence import GeofenceEventResponse  # noqa: E402
from app.schemas.safety_resource import NearbySafetyResponse  # noqa: E402

LocationUpdateResult.model_rebuild()
