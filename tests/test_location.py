"""Location API tests."""

from app.schemas.geofence import CircleGeometry, GeoFenceCreateRequest
from app.geofence.zone_types import GeometryType, Severity, ZoneType


def _create_unsafe_zone(client, zone_id: str, lat: float, lng: float, radius_m: float = 500) -> None:
    payload = GeoFenceCreateRequest(
        id=zone_id,
        name=f"Test Zone {zone_id}",
        zone_type=ZoneType.UNSAFE,
        geometry_type=GeometryType.CIRCLE,
        severity=Severity.HIGH,
        warning_message="Unsafe area entered.",
        circle=CircleGeometry(center_lat=lat, center_lng=lng, radius_m=radius_m),
    )
    response = client.post("/api/v1/geofences", json=payload.model_dump(mode="json"))
    assert response.status_code == 201


def test_update_and_get_current_location(client):
    tourist_id = "t1"
    body = {"latitude": 26.55, "longitude": 93.14, "accuracy": 8.5}
    update = client.post(f"/api/v1/locations/{tourist_id}", json=body)
    assert update.status_code == 200
    data = update.json()["data"]
    assert data["location"]["tourist_id"] == tourist_id
    assert data["geofence_status"] == "OUTSIDE"

    current = client.get(f"/api/v1/locations/{tourist_id}/current")
    assert current.status_code == 200
    assert current.json()["data"]["latitude"] == 26.55


def test_enter_unsafe_zone_generates_event(client):
    _create_unsafe_zone(client, "unsafe_test", 26.60, 93.20, 600)
    tourist_id = "t2"

    outside = client.post(
        f"/api/v1/locations/{tourist_id}",
        json={"latitude": 26.50, "longitude": 93.10},
    )
    assert outside.json()["data"]["events"] == []

    inside = client.post(
        f"/api/v1/locations/{tourist_id}",
        json={"latitude": 26.60, "longitude": 93.20},
    )
    events = inside.json()["data"]["events"]
    assert len(events) == 1
    assert events[0]["type"] == "ENTERED_UNSAFE_ZONE"
    assert events[0]["userId"] == tourist_id


def test_exit_unsafe_zone_generates_event(client):
    _create_unsafe_zone(client, "unsafe_exit", 26.61, 93.21, 600)
    tourist_id = "t3"

    client.post(f"/api/v1/locations/{tourist_id}", json={"latitude": 26.61, "longitude": 93.21})
    exit_resp = client.post(
        f"/api/v1/locations/{tourist_id}",
        json={"latitude": 26.50, "longitude": 93.10},
    )
    events = exit_resp.json()["data"]["events"]
    assert any(event["type"] == "EXITED_UNSAFE_ZONE" for event in events)


def test_simulate_movement(client):
    _create_unsafe_zone(client, "unsafe_sim", 26.62, 93.22, 700)
    payload = {
        "start_latitude": 26.50,
        "start_longitude": 93.10,
        "end_latitude": 26.62,
        "end_longitude": 93.22,
        "steps": 4,
    }
    response = client.post("/api/v1/locations/t4/simulate", json=payload)
    assert response.status_code == 200
    updates = response.json()["data"]["updates"]
    assert len(updates) == 4
    assert any(update["events"] for update in updates)


def test_list_all_tourists_and_reset(client):
    client.post("/api/v1/locations/t5", json={"latitude": 26.55, "longitude": 93.14})
    listed = client.get("/api/v1/locations")
    assert listed.status_code == 200
    assert any(item["tourist_id"] == "t5" for item in listed.json()["data"])

    reset = client.post("/api/v1/locations/test/reset")
    assert reset.status_code == 200
    assert reset.json()["data"]["locations_deleted"] >= 1


def test_get_last_known_location(client):
    tourist_id = "t6"
    client.post(f"/api/v1/locations/{tourist_id}", json={"latitude": 26.55, "longitude": 93.14})
    client.post(f"/api/v1/locations/{tourist_id}", json={"latitude": 26.56, "longitude": 93.15})
    last = client.get(f"/api/v1/locations/{tourist_id}/last")
    assert last.status_code == 200
    assert last.json()["data"]["latitude"] == 26.56
