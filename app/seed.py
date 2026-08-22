"""Seed geofence zones and test coordinates for Himachal Pradesh tourist circuit."""

from sqlalchemy.orm import Session

from app.models.geofence import GeoFence
from app.models.safety_resource import SafetyResource
from app.models.target_zone import TargetZone
from app.schemas.geofence import CircleGeometry, GeoFenceCreateRequest
from app.schemas.location import LocationUpdateRequest
from app.schemas.safety_resource import SafetyResourceCreateRequest
from app.geofence.zone_types import GeometryType, Severity, ZoneType
from app.location.resource_types import SafetyResourceType
from app.services.geofence_service import GeofenceService
from app.services.location_service import LocationService
from app.services.safety_resource_service import SafetyResourceService

# Himachal Pradesh approximate reference coordinates
HIMACHAL_CENTER = (32.317, 77.157)  # Solang Valley Anchor

DEFAULT_ZONES: list[GeoFenceCreateRequest] = [
    GeoFenceCreateRequest(
        id="unsafe_avalanche_slope",
        name="Solang Riverbank & Avalanche Slope",
        zone_type=ZoneType.UNSAFE,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.HIGH,
        description="Active avalanche corridor and steep riverbank slope — tourists must turn back.",
        warning_message="DANGER: You are entering an active avalanche slope risk zone. Turn back immediately!",
        circle=CircleGeometry(center_lat=32.3250, center_lng=77.1520, radius_m=400),
        is_crowd_zone=False,
    ),
    GeoFenceCreateRequest(
        id="restricted_riverbank",
        name="Solang Riverbank Restricted Zone",
        zone_type=ZoneType.RESTRICTED,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.MEDIUM,
        description="Restricted buffer around steep river flow.",
        warning_message="You are entering a restricted riverbank zone. Proceed with caution.",
        circle=CircleGeometry(center_lat=32.3120, center_lng=77.1550, radius_m=300),
        is_crowd_zone=False,
    ),
    GeoFenceCreateRequest(
        id="warning_pine_forest",
        name="Hadimba Pine Forest Trek",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.MEDIUM,
        description="Pine forest trek route — caution for remote conditions.",
        warning_message="Caution: Entering Hadimba Pine Forest Trek. Keep on marked trails and check weather conditions.",
        circle=CircleGeometry(center_lat=32.2480, center_lng=77.1820, radius_m=400),
        is_crowd_zone=False,
    ),
    # Crowd-density zones (distinguished using is_crowd_zone=True)
    GeoFenceCreateRequest(
        id="crowd_ropeway_hub",
        name="Solang Valley Ropeway & Activity Hub",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.LOW,
        description="High-density tourist ropeway and adventure hub (busy but safe).",
        warning_message="You're entering a high-footfall area — stay alert to your surroundings.",
        circle=CircleGeometry(center_lat=32.3170, center_lng=77.1570, radius_m=200),
        is_crowd_zone=True,
    ),
    GeoFenceCreateRequest(
        id="crowd_hadimba_temple",
        name="Hadimba Devi Temple & Courtyard",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.LOW,
        description="Pagoda temple courtyard — high tourist concentration (busy but safe).",
        warning_message="You're entering a high-footfall area — stay alert to your surroundings.",
        circle=CircleGeometry(center_lat=32.2432, center_lng=77.1892, radius_m=200),
        is_crowd_zone=True,
    ),
    GeoFenceCreateRequest(
        id="crowd_mall_road",
        name="Manali Mall Road & Town Square",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.LOW,
        description="Safe walking corridor and shopping street — high density (busy but safe).",
        warning_message="You're entering a high-footfall area — stay alert to your surroundings.",
        circle=CircleGeometry(center_lat=32.2574, center_lng=77.1748, radius_m=300),
        is_crowd_zone=True,
    ),
    GeoFenceCreateRequest(
        id="crowd_kasol_market",
        name="Kasol Market & Parvati Riverfront",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.LOW,
        description="Popular riverfront stroll and market street — high density (busy but safe).",
        warning_message="You're entering a high-footfall area — stay alert to your surroundings.",
        circle=CircleGeometry(center_lat=32.0097, center_lng=77.3153, radius_m=250),
        is_crowd_zone=True,
    ),
    # Additional HP areas for circuit coverage
    GeoFenceCreateRequest(
        id="warning_rohtang_pass",
        name="Rohtang Pass Crest & Snow Ridge",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.HIGH,
        description="High-altitude alpine pass zone prone to sub-zero temperatures and high winds.",
        warning_message="Warning: Rohtang Pass Crest & Snow Ridge. Extreme high altitude. Watch for sudden weather changes and low oxygen.",
        circle=CircleGeometry(center_lat=32.3730, center_lng=77.3710, radius_m=1000),
        is_crowd_zone=False,
    ),
    GeoFenceCreateRequest(
        id="warning_tunnel_south",
        name="Atal Tunnel South Portal Corridor",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.LOW,
        description="Atal Tunnel entrance/exit corridor — controlled traffic entry.",
        warning_message="Caution: Entering tunnel corridor (South Portal). Stick to safety lanes and watch for traffic.",
        circle=CircleGeometry(center_lat=32.3150, center_lng=77.1550, radius_m=400),
        is_crowd_zone=False,
    ),
    GeoFenceCreateRequest(
        id="warning_tunnel_north",
        name="Atal Tunnel North Portal Corridor",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.LOW,
        description="Atal Tunnel entrance/exit corridor — controlled traffic entry.",
        warning_message="Caution: Entering tunnel corridor (North Portal). Stick to safety lanes and watch for traffic.",
        circle=CircleGeometry(center_lat=32.4010, center_lng=77.1480, radius_m=400),
        is_crowd_zone=False,
    ),
]

# Test coordinates for frontend/backend integration
# Note: Coordinate values are approximate prototype placeholders representing tourist nodes.
TEST_COORDINATES = {
    "safe": (32.2620, 77.1620),             # Old Manali Craft & Cafe Street (safe stroll)
    "unsafe_inside": (32.3250, 77.1520),    # Inside Solang Riverbank & Avalanche Slope UNSAFE zone
    "restricted_inside": (32.3120, 77.1550), # Inside Solang Riverbank restricted zone
    "warning_inside": (32.2460, 77.1850),   # Inside Hadimba Pine Forest Trek warning zone
    "boundary_edge": (32.3235, 77.1520),    # Near boundary edge of Solang Avalanche Slope
    "approach_unsafe": (32.3210, 77.1520),  # Approach to Solang Avalanche Slope
}

# Patrol units, police stations, and hospitals in Kullu and Manali Valley
DEFAULT_SAFETY_RESOURCES: list[SafetyResourceCreateRequest] = [
    # Patrolling
    SafetyResourceCreateRequest(
        id="patrol_solang_1",
        name="Himachal PCR Unit 04",
        resource_type=SafetyResourceType.PATROL,
        latitude=32.3175,
        longitude=77.1575,
        address="Solang Valley Checkpost, Kullu Valley, HP",
        phone="+91-177-2620311",
        description="Highway patrolling unit monitoring Solang Valley and tunnel access.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="patrol_rohtang_rescue",
        name="Rohtang Pass Rescue Patrol",
        resource_type=SafetyResourceType.PATROL,
        latitude=32.3730,
        longitude=77.3710,
        address="Rohtang Pass Peak Checkpoint, HP",
        phone="+91-177-2620312",
        description="Search & rescue patrol covering the Rohtang Pass region.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="patrol_manikaran_post",
        name="Manikaran Hot Springs Patrol",
        resource_type=SafetyResourceType.PATROL,
        latitude=32.0333,
        longitude=77.4133,
        address="Manikaran Sahib Pilgrim Area, HP",
        phone="+91-177-2620313",
        description="Local patrol support for crowd safety and pilgrim assistance.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="patrol_vashisht_post",
        name="Vashisht Springs Patrol Post",
        resource_type=SafetyResourceType.PATROL,
        latitude=32.2650,
        longitude=77.1870,
        address="Vashisht Village, HP",
        phone="+91-177-2620314",
        description="Patrolling unit for safety around temple springs and treks.",
        is_24x7=True,
    ),
    # Police
    SafetyResourceCreateRequest(
        id="police_manali_central",
        name="Manali Central Tourist Police Station",
        resource_type=SafetyResourceType.POLICE,
        latitude=32.2570,
        longitude=77.1750,
        address="Mall Road, Manali Town, HP",
        phone="+91-177-2620100",
        description="Main tourist police support and incident dispatch unit.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="police_old_manali",
        name="Old Manali Tourist Police Outpost",
        resource_type=SafetyResourceType.POLICE,
        latitude=32.2620,
        longitude=77.1620,
        address="Old Manali Craft Street, HP",
        phone="+91-177-2620101",
        description="Local police outpost supporting the old town cafe circuit.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="police_kasol",
        name="Kasol Local Police Station",
        resource_type=SafetyResourceType.POLICE,
        latitude=32.0097,
        longitude=77.3153,
        address="Kasol Market, Parvati Valley, HP",
        phone="+91-177-2620102",
        description="Incident response and security post covering Parvati Valley.",
        is_24x7=True,
    ),
    # Hospitals
    SafetyResourceCreateRequest(
        id="hospital_manali_civil",
        name="Manali Civil District Hospital & Trauma Center",
        resource_type=SafetyResourceType.HOSPITAL,
        latitude=32.2580,
        longitude=77.1740,
        address="Near Mall Road, Manali, HP",
        phone="+91-177-2621100",
        description="District level trauma center and emergency care.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="hospital_kullu_emergency",
        name="Kullu Regional Emergency Care Center",
        resource_type=SafetyResourceType.HOSPITAL,
        latitude=31.9580,
        longitude=77.1090,
        address="Main Highway, Kullu Town, HP",
        phone="+91-177-2622200",
        description="Regional emergency care and specialty surgical services.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="hospital_kasol_clinic",
        name="Kasol Emergency Medical Clinic",
        resource_type=SafetyResourceType.HOSPITAL,
        latitude=32.0100,
        longitude=77.3160,
        address="Kasol Market, HP",
        phone="+91-177-2621102",
        description="24x7 medical clinic with ambulance service.",
        is_24x7=True,
    ),
    SafetyResourceCreateRequest(
        id="hospital_sissu_post",
        name="Sissu Valley Alpine Medical Post",
        resource_type=SafetyResourceType.HOSPITAL,
        latitude=32.4833,
        longitude=77.1167,
        address="Sissu Village, Lahaul, HP",
        phone="+91-177-2621103",
        description="Alpine medical post supporting tourists in Lahaul region.",
        is_24x7=True,
    ),
]

# Authority broadcast target zones (Himachal Pradesh circuits)
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
        "id": "hp_parvati_valley",
        "name": "Himachal Pradesh (Parvati Valley)",
        "state": "Himachal Pradesh",
        "center_lat": 32.0097,
        "center_lng": 77.3153,
        "default_radius_km": 14.0,
        "description": "Eco-sensitive Parvati Valley zone covering Kasol and Manikaran pilgrim routes.",
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
    # tourist_safe_1 is seeded on the Solang Valley North Trail (approx prototype coordinates)
    samples = [
        ("tourist_safe_1", 32.3210, 77.1580),
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
    # Delete old stale Kaziranga target zones/safety resources/geofences
    # to perform a clean relocation migration.
    db.query(GeoFence).delete()
    db.query(SafetyResource).delete()
    db.query(TargetZone).delete()
    db.commit()

    seed_zones(db)
    seed_target_zones(db)
    seed_safety_resources(db)
    seed_sample_locations(db)
