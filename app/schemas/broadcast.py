"""Emergency broadcast request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.location.broadcast_types import BroadcastSeverity


class RadiusConfigResponse(BaseModel):
    min_km: float = 1.0
    max_km: float = 50.0
    default_km: float = 14.0
    step_km: float = 1.0


class TargetZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    state: str
    center_lat: float
    center_lng: float
    default_radius_km: float
    description: str | None = None
    is_active: bool = True


class AffectedTourist(BaseModel):
    tourist_id: str
    latitude: float
    longitude: float
    distance_km: float
    recorded_at: datetime


class BroadcastPreviewRequest(BaseModel):
    zone_id: str = Field(..., min_length=1)
    radius_km: float = Field(..., gt=0, le=100, description="Geofence radius from authority slider")


class BroadcastPreviewResponse(BaseModel):
    zone_id: str
    zone_name: str
    state: str
    radius_km: float
    center_lat: float
    center_lng: float
    tourist_count: int
    affected_tourists: list[AffectedTourist]


class BroadcastSendRequest(BaseModel):
    zone_id: str = Field(..., min_length=1)
    radius_km: float = Field(..., gt=0, le=100, description="Geofence radius set by authority via slider")
    severity: BroadcastSeverity
    title: str = Field(..., min_length=1, max_length=256)
    message: str = Field(..., min_length=1)


class TouristAlertDelivery(BaseModel):
    tourist_id: str
    distance_km: float
    alert_type: str
    severity: str
    title: str
    message: str
    delivered_at: datetime


class BroadcastSendResponse(BaseModel):
    broadcast_id: int
    zone_id: str
    zone_name: str
    state: str
    radius_km: float
    severity: BroadcastSeverity
    title: str
    message: str
    tourists_notified: int
    deliveries: list[TouristAlertDelivery]
    sent_at: datetime
