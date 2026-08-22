"""Geofence request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.geofence.zone_types import GeometryType, Severity, ZoneType


class CircleGeometry(BaseModel):
    center_lat: float = Field(..., ge=-90, le=90)
    center_lng: float = Field(..., ge=-180, le=180)
    radius_m: float = Field(..., gt=0, le=100_000)


class PolygonGeometry(BaseModel):
    coordinates: list[list[list[float]]] = Field(
        ...,
        description="GeoJSON polygon coordinates: [[[lng, lat], ...]]",
    )

    @field_validator("coordinates")
    @classmethod
    def validate_ring(cls, value: list[list[list[float]]]) -> list[list[list[float]]]:
        if not value or not value[0] or len(value[0]) < 4:
            raise ValueError("Polygon must contain at least one ring with 4+ points")
        return value


class GeoFenceCreateRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    zone_type: ZoneType
    geometry_type: GeometryType
    severity: Severity
    description: str | None = None
    warning_message: str = Field(..., min_length=1)
    is_active: bool = True
    is_crowd_zone: bool = False
    circle: CircleGeometry | None = None
    polygon: PolygonGeometry | None = None

    @model_validator(mode="after")
    def validate_geometry(self) -> "GeoFenceCreateRequest":
        if self.geometry_type == GeometryType.CIRCLE and not self.circle:
            raise ValueError("circle geometry is required for CIRCLE zones")
        if self.geometry_type == GeometryType.POLYGON and not self.polygon:
            raise ValueError("polygon geometry is required for POLYGON zones")
        if self.geometry_type == GeometryType.CIRCLE and self.polygon:
            raise ValueError("provide only circle geometry for CIRCLE zones")
        if self.geometry_type == GeometryType.POLYGON and self.circle:
            raise ValueError("provide only polygon geometry for POLYGON zones")
        return self


class GeoFenceUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    zone_type: ZoneType | None = None
    severity: Severity | None = None
    description: str | None = None
    warning_message: str | None = None
    is_active: bool | None = None
    is_crowd_zone: bool | None = None
    circle: CircleGeometry | None = None
    polygon: PolygonGeometry | None = None


class GeoFenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    zone_type: ZoneType
    geometry_type: GeometryType
    severity: Severity
    description: str | None
    warning_message: str
    is_active: bool
    is_crowd_zone: bool = False
    center_lat: float | None = None
    center_lng: float | None = None
    radius_m: float | None = None
    polygon_coordinates: list[list[list[float]]] | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_polygon(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data
        import json

        polygon = getattr(data, "polygon_coordinates", None)
        if polygon and isinstance(polygon, str):
            return {
                "id": data.id,
                "name": data.name,
                "zone_type": data.zone_type,
                "geometry_type": data.geometry_type,
                "severity": data.severity,
                "description": data.description,
                "warning_message": data.warning_message,
                "is_active": data.is_active,
                "is_crowd_zone": getattr(data, "is_crowd_zone", False),
                "center_lat": data.center_lat,
                "center_lng": data.center_lng,
                "radius_m": data.radius_m,
                "polygon_coordinates": json.loads(polygon),
            }
        return data


class GeofenceEventResponse(BaseModel):
    type: str
    userId: str
    zoneId: str
    time: datetime
    severity: str
    message: str
    latitude: float
    longitude: float


class GeofenceCheckRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class GeofenceCheckResponse(BaseModel):
    status: str
    inside_zones: list[GeoFenceResponse]
    events: list[GeofenceEventResponse]
