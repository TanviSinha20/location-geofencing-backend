from app.schemas.common import APIResponse, ErrorResponse, PaginationMeta
from app.schemas.geofence import (
    GeoFenceCreateRequest,
    GeoFenceResponse,
    GeoFenceUpdateRequest,
    GeofenceCheckRequest,
    GeofenceCheckResponse,
    GeofenceEventResponse,
)
from app.schemas.location import (
    LocationResponse,
    LocationUpdateRequest,
    LocationUpdateResult,
    MockLocationRequest,
    SimulateMovementRequest,
    SimulateMovementResponse,
    TouristLocationSummary,
)

__all__ = [
    "APIResponse",
    "ErrorResponse",
    "PaginationMeta",
    "GeoFenceCreateRequest",
    "GeoFenceResponse",
    "GeoFenceUpdateRequest",
    "GeofenceCheckRequest",
    "GeofenceCheckResponse",
    "GeofenceEventResponse",
    "LocationResponse",
    "LocationUpdateRequest",
    "LocationUpdateResult",
    "MockLocationRequest",
    "SimulateMovementRequest",
    "SimulateMovementResponse",
    "TouristLocationSummary",
]
