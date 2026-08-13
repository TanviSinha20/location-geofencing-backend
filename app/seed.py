"""Seed geofence zones and test coordinates for Kaziranga demo."""

from sqlalchemy.orm import Session

from app.models.geofence import GeoFence
from app.models.safety_resource import SafetyResource
from app.models.target_zone import TargetZone
from app.schemas.geofence import CircleGeometry, GeoFenceCreateRequest, PolygonGeometry
from app.schemas.location import LocationUpdateRequest
from app.schemas.safety_resource import SafetyResourceCreateRequest
from app.geofence.zone_types import GeometryType, Severity, ZoneType
from app.location.resource_types import SafetyResourceType
from app.services.geofence_service import GeofenceService
from app.services.location_service import LocationService
from app.services.safety_resource_service import SafetyResourceService

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


# Patrol units, police outposts, and hospitals near Kaziranga National Park, Assam
DEFAULT_SAFETY_RESOURCES: list[SafetyResourceCreateRequest] = [
    # Forest patrolling units
    SafetyResourceCreateRequest(
        id="patrol_kohora_1",
        name="Kaziranga Kohora Forest Patrol Unit",
        resource_type=SafetyResourceType.PATROL,
        latitude=26.5835,
        longitude=93.1745,
        address="Kohora Range, Kaziranga National Park, Assam",
        phone="+91-3776-262001",
        description="Primary forest patrolling unit near Kohora entrance.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="patrol_bagori_1",
        name="Bagori Range Patrol Post",
        resource_type=SafetyResourceType.PATROL,
        latitude=26.6180,
        longitude=93.2480,
        address="Bagori Range, Kaziranga National Park, Assam",
        phone="+91-3776-262002",
        description="Western range forest patrol and wildlife monitoring.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="patrol_agoratoli_1",
        name="Agoratoli Range Patrol Unit",
        resource_type=SafetyResourceType.PATROL,
        latitude=26.5920,
        longitude=93.2050,
        address="Agoratoli Range, Kaziranga National Park, Assam",
        phone="+91-3776-262003",
        description="Eastern sector patrolling and tourist safety support.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="patrol_burapahar_1",
        name="Burapahar Patrol Checkpoint",
        resource_type=SafetyResourceType.PATROL,
        latitude=26.5960,
        longitude=93.1980,
        address="Burapahar Sector, Kaziranga National Park, Assam",
        phone="+91-3776-262004",
        description="Checkpoint patrol for restricted zone boundary.",
        is_24x7=True,
    ),
    # Police
    SafetyResourceCreateRequest(
        id="police_kohora_1",
        name="Kohora Police Outpost",
        resource_type=SafetyResourceType.POLICE,
        latitude=26.5825,
        longitude=93.1725,
        address="NH-715, Kohora, Kaziranga, Assam 785109",
        phone="+91-100",
        description="Nearest police outpost to Kaziranga tourist zone.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="police_traffic_1",
        name="Kaziranga Traffic Police Point",
        resource_type=SafetyResourceType.POLICE,
        latitude=26.5800,
        longitude=93.1690,
        address="Kohora Main Road, Kaziranga, Assam",
        phone="+91-3776-262010",
        description="Highway traffic and tourist convoy safety point.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="police_bokakhat_1",
        name="Bokakhat Police Station",
        resource_type=SafetyResourceType.POLICE,
        latitude=26.6385,
        longitude=93.3880,
        address="Bokakhat Town, Golaghat District, Assam",
        phone="+91-3776-242020",
        description="District police station covering Kaziranga area.",
        is_24x7=True,
    ),
    # Hospitals
    SafetyResourceCreateRequest(
        id="hospital_kohora_phc",
        name="Kohora Primary Health Centre",
        resource_type=SafetyResourceType.HOSPITAL,
        latitude=26.5815,
        longitude=93.1715,
        address="Kohora, Kaziranga, Assam 785109",
        phone="+91-3776-262100",
        description="Nearest primary health centre for tourists and locals.",
        is_24x7=False,
    ),
    SafetyResourceCreateRequest(
        id="hospital_bokakhat_civil",
        name="Bokakhat Civil Hospital",
        resource_type=SafetyResourceType.HOSPITAL,
        latitude=26.6395,
        longitude=93.3870,
        address="Bokakhat, Golaghat District, Assam",
        phone="+91-3776-242200",
        description="Civil hospital with emergency and trauma care.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="hospital_golaghat_district",
        name="Golaghat District Hospital",
        resource_type=SafetyResourceType.HOSPITAL,
        latitude=26.5110,
        longitude=93.9620,
        address="Golaghat Town, Assam 785702",
        phone="+91-3774-240300",
        description="District-level hospital for serious emergencies.",
        is_24x7=True,
    ),
]


# Authority broadcast target zones (matches frontend dropdown)
DEFAULT_TARGET_ZONES: list[dict] = [
    {
        "id": "hp_solang_rohtang",
        "name": "Himachal Pradesh (Solang / Rohtang)",
        "state": "Himachal Pradesh",
        "center_lat": 32.3167,
        "center_lng": 77.1333,
        "default_radius_km": 14.0,
        "description": "High-altitude zone prone to flash floods, cloudbursts, and landslides.",
    },
    {
        "id": "as_kaziranga",
        "name": "Assam (Kaziranga National Park)",
        "state": "Assam",
        "center_lat": 26.5775,
        "center_lng": 93.1711,
        "default_radius_km": 14.0,
        "description": "Wildlife sanctuary and ecologically sensitive tourist area.",
    },
]

# Demo tourists for Himachal broadcast testing
HIMACHAL_TEST_TOURISTS = [
    ("tourist_hp_1", 32.3200, 77.1400),   # inside 14 km
    ("tourist_hp_2", 32.3100, 77.1250),   # inside 14 km
    ("tourist_hp_3", 32.4500, 77.3000),   # outside 14 km
]


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
        *HIMACHAL_TEST_TOURISTS,
    ]
    for tourist_id, lat, lng in samples:
        try:
            location_service.get_current_location(tourist_id)
        except Exception:
            location_service.update_location(
                tourist_id,
                LocationUpdateRequest(latitude=lat, longitude=lng, accuracy=10.0),
            )


def seed_safety_resources(db: Session) -> None:
    service = SafetyResourceService(db)
    for resource in DEFAULT_SAFETY_RESOURCES:
        if db.get(SafetyResource, resource.id):
            continue
        service.create_resource(resource)


def seed_target_zones(db: Session) -> None:
    for zone_data in DEFAULT_TARGET_ZONES:
        if db.get(TargetZone, zone_data["id"]):
            continue
        db.add(TargetZone(**zone_data))
    db.commit()


def run_seed(db: Session) -> None:
    seed_zones(db)
    seed_target_zones(db)
    seed_safety_resources(db)
    seed_sample_locations(db)
