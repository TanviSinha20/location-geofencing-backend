"""Geofence API and engine tests."""

from app.geofence.engine import evaluate_point, point_in_zone
from app.geofence.zone_types import GeometryType, Severity, ZoneType
from app.models.geofence import GeoFence
from app.schemas.geofence import CircleGeometry, GeoFenceCreateRequest, PolygonGeometry


def test_create_circle_and_polygon_zones(client):
    circle = GeoFenceCreateRequest(
        id="circle_1",
        name="Circle Zone",
        zone_type=ZoneType.RESTRICTED,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.MEDIUM,
        warning_message="Restricted",
        circle=CircleGeometry(center_lat=26.58, center_lng=93.17, radius_m=500),
    )
    response = client.post("/api/v1/geofences", json=circle.model_dump(mode="json"))
    assert response.status_code == 201

    polygon = GeoFenceCreateRequest(
        id="polygon_1",
        name="Polygon Zone",
        zone_type=ZoneType.WARNING,
        geometry_type=GeometryType.POLYGON,
        severity=Severity.LOW,
        warning_message="Warning zone",
        polygon=PolygonGeometry(
            coordinates=[
                [
                    [93.16, 26.57],
                    [93.17, 26.57],
                    [93.17, 26.56],
                    [93.16, 26.56],
                    [93.16, 26.57],
                ]
            ]
        ),
    )
    response = client.post("/api/v1/geofences", json=polygon.model_dump(mode="json"))
    assert response.status_code == 201

    listed = client.get("/api/v1/geofences")
    assert listed.status_code == 200
    assert len(listed.json()["data"]) >= 2


def test_point_in_circle_engine():
    zone = GeoFence(
        id="z1",
        name="Test",
        zone_type=ZoneType.UNSAFE.value,
        geometry_type=GeometryType.CIRCLE.value,
        center_lat=26.5775,
        center_lng=93.1711,
        radius_m=800,
        severity=Severity.HIGH.value,
        warning_message="Unsafe",
        is_active=True,
    )
    assert point_in_zone(26.5775, 93.1711, zone) is True
    assert point_in_zone(26.50, 93.10, zone) is False


def test_evaluate_point_returns_matches():
    zone = GeoFence(
        id="z2",
        name="Test",
        zone_type=ZoneType.UNSAFE.value,
        geometry_type=GeometryType.CIRCLE.value,
        center_lat=26.60,
        center_lng=93.20,
        radius_m=500,
        severity=Severity.HIGH.value,
        warning_message="Unsafe",
        is_active=True,
    )
    matches = evaluate_point(26.60, 93.20, [zone])
    assert len(matches) == 1
    assert matches[0].zone_id == "z2"


def test_inactive_zone_ignored():
    zone = GeoFence(
        id="z3",
        name="Inactive",
        zone_type=ZoneType.UNSAFE.value,
        geometry_type=GeometryType.CIRCLE.value,
        center_lat=26.60,
        center_lng=93.20,
        radius_m=500,
        severity=Severity.HIGH.value,
        warning_message="Unsafe",
        is_active=False,
    )
    matches = evaluate_point(26.60, 93.20, [zone])
    assert matches == []


def test_geofence_events_list(client):
    zone = GeoFenceCreateRequest(
        id="event_zone",
        name="Event Zone",
        zone_type=ZoneType.UNSAFE,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.HIGH,
        warning_message="Unsafe",
        circle=CircleGeometry(center_lat=26.63, center_lng=93.23, radius_m=500),
    )
    client.post("/api/v1/geofences", json=zone.model_dump(mode="json"))
    client.post("/api/v1/locations/t7", json={"latitude": 26.63, "longitude": 93.23})

    events = client.get("/api/v1/geofences/events/list?tourist_id=t7")
    assert events.status_code == 200
    assert len(events.json()["data"]) >= 1
