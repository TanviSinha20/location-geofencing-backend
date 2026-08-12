"""Seed geofence zones and test coordinates for Kaziranga demo."""

from sqlalchemy.orm import Session

from app.models.geofence import GeoFence
from app.schemas.geofence import CircleGeometry, GeoFenceCreateRequest, PolygonGeometry
from app.schemas.location import LocationUpdateRequest
from app.geofence.zone_types import GeometryType, Severity, ZoneType
from app.services.geofence_service import GeofenceService
from app.services.location_service import LocationService

# Kaziranga National Park approximate reference coordinates
KAZIRANGA_CENTER = (26.5775, 93.1711)

DEFAULT_ZONES: list[GeoFenceCreateRequest] = [
    GeoFenceCreateRequest(
        id="unsafe_core_1",
        name="Kaziranga Core Restricted Habitat",
        zone_type=ZoneType.UNSAFE,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.HIGH,
        description="Core wildlife habitat — tourists must not enter.",
        warning_message="You have entered an unsafe area. Turn back immediately.",
        circle=CircleGeometry(center_lat=26.5775, center_lng=93.1711, radius_m=800),
    ),
    GeoFenceCreateRequest(
        id="restricted_buffer_1",
        name="Park Buffer Restricted Zone",
        zone_type=ZoneType.RESTRICTED,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.MEDIUM,
        description="Restricted buffer around sensitive habitat.",
        warning_message="You are entering a restricted zone. Proceed with caution.",
        circle=CircleGeometry(center_lat=26.5850, center_lng=93.1800, radius_m=1200),
    ),
    GeoFenceCreateRequest(
        id="warning_flood_plain",
        name="Flood Plain Warning Zone",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.POLYGON,
        severity=Severity.LOW,
        description="Seasonal flood plain — warning only.",
        warning_message="Warning: you are approaching a flood-prone area.",
        polygon=PolygonGeometry(
            coordinates=[
                [
                    [93.1600, 26.5700],
                    [93.1750, 26.5700],
                    [93.1750, 26.5600],
                    [93.1600, 26.5600],
                    [93.1600, 26.5700],
                ]
            ]
        ),
    ),
]

# Test coordinates for frontend/backend integration
TEST_COORDINATES = {
    "safe": (26.5500, 93.1400),
    "unsafe_inside": (26.5775, 93.1711),
    "restricted_inside": (26.5850, 93.1800),
    "warning_inside": (26.5650, 93.1650),
    "boundary_edge": (26.5846, 93.1711),
    "approach_unsafe": (26.5700, 93.1711),
}


def seed_zones(db: Session) -> None:
    service = GeofenceService(db)
    for zone in DEFAULT_ZONES:
        if db.get(GeoFence, zone.id):
            continue
        service.create_zone(zone)


def seed_sample_locations(db: Session) -> None:
    location_service = LocationService(db)
    samples = [
        ("tourist_safe_1", *TEST_COORDINATES["safe"]),
        ("tourist_test_2", *TEST_COORDINATES["approach_unsafe"]),
    ]
    for tourist_id, lat, lng in samples:
        try:
            location_service.get_current_location(tourist_id)
        except Exception:
            location_service.update_location(
                tourist_id,
                LocationUpdateRequest(latitude=lat, longitude=lng, accuracy=10.0),
            )


def run_seed(db: Session) -> None:
    seed_zones(db)
    seed_sample_locations(db)
