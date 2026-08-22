"""Safety resource and live location tests."""

from app.location.resource_types import SafetyResourceType
from app.schemas.safety_resource import SafetyResourceCreateRequest


def test_list_seeded_safety_resources(client):
    response = client.get("/api/v1/safety-resources")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 10
    types = {item["resource_type"] for item in data}
    assert SafetyResourceType.PATROL.value in types
    assert SafetyResourceType.POLICE.value in types
    assert SafetyResourceType.HOSPITAL.value in types


def test_find_nearby_safety_resources(client):
    # Solang Valley HP coordinates
    response = client.get(
        "/api/v1/safety-resources/nearby",
        params={"latitude": 32.317, "longitude": 77.157, "radius_km": 25},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["patrol_units"]) >= 1
    assert len(data["police"]) >= 1
    assert len(data["hospitals"]) >= 1
    assert data["patrol_units"][0]["distance_m"] >= 0


def test_location_update_includes_nearby_safety(client):
    response = client.post(
        "/api/v1/locations/tourist_live_1",
        json={"latitude": 32.317, "longitude": 77.157, "accuracy": 5.0},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nearby_safety"] is not None
    assert len(data["nearby_safety"]["police"]) >= 1


def test_live_location_endpoint(client):
    client.post(
        "/api/v1/locations/tourist_live_2",
        json={"latitude": 32.315, "longitude": 77.155},
    )
    response = client.get("/api/v1/locations/tourist_live_2/live", params={"radius_km": 25})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["location"]["tourist_id"] == "tourist_live_2"
    assert "geofence_status" in data
    assert len(data["nearby_safety"]["patrol_units"]) >= 1


def test_create_safety_resource(client):
    payload = SafetyResourceCreateRequest(
        id="patrol_test_1",
        name="Test Patrol Unit",
        resource_type=SafetyResourceType.PATROL,
        latitude=32.3000,
        longitude=77.1500,
        phone="+91-9999999999",
    )
    response = client.post("/api/v1/safety-resources", json=payload.model_dump(mode="json"))
    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Test Patrol Unit"
