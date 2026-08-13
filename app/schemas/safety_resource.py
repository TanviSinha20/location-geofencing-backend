"""Safety resource request/response schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.location.resource_types import SafetyResourceType


class SafetyResourceCreateRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    resource_type: SafetyResourceType
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str | None = None
    phone: str | None = None
    description: str | None = None
    is_24x7: bool = False
    is_active: bool = True


class SafetyResourceUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    resource_type: SafetyResourceType | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    address: str | None = None
    phone: str | None = None
    description: str | None = None
    is_24x7: bool | None = None
    is_active: bool | None = None


class SafetyResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    resource_type: SafetyResourceType
    latitude: float
    longitude: float
    address: str | None = None
    phone: str | None = None
    description: str | None = None
    is_24x7: bool = False
    is_active: bool = True


class NearbySafetyResource(SafetyResourceResponse):
    distance_m: float = Field(..., description="Distance from tourist in meters")


class NearbySafetyResponse(BaseModel):
    search_radius_km: float
    patrol_units: list[NearbySafetyResource]
    police: list[NearbySafetyResource]
    hospitals: list[NearbySafetyResource]


class LiveLocationResponse(BaseModel):
    location: "LocationResponse"
    geofence_status: str
    active_zones: list[str]
    events: list["GeofenceEventResponse"]
    nearby_safety: NearbySafetyResponse


from app.schemas.geofence import GeofenceEventResponse  # noqa: E402
from app.schemas.location import LocationResponse  # noqa: E402

LiveLocationResponse.model_rebuild()
