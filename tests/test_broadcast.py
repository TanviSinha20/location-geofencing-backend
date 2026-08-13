"""Emergency broadcast and configurable radius tests."""


def test_radius_config_endpoint(client):
    response = client.get("/api/v1/broadcast/radius-config")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["min_km"] == 1.0
    assert data["max_km"] == 50.0
    assert data["default_km"] == 14.0


def test_radius_config_per_zone(client):
    response = client.get(
        "/api/v1/broadcast/radius-config",
        params={"zone_id": "hp_solang_rohtang"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["default_km"] == 14.0


def test_list_target_zones(client):
    response = client.get("/api/v1/broadcast/target-zones")
    assert response.status_code == 200
    zones = response.json()["data"]
    assert any(z["id"] == "hp_solang_rohtang" for z in zones)
    assert any(z["name"] == "Himachal Pradesh (Solang / Rohtang)" for z in zones)


def test_broadcast_preview_respects_user_radius(client):
    # Seed Himachal tourists via location updates
    client.post("/api/v1/locations/tourist_hp_1", json={"latitude": 32.32, "longitude": 77.14})
    client.post("/api/v1/locations/tourist_hp_2", json={"latitude": 32.31, "longitude": 77.125})
    client.post("/api/v1/locations/tourist_hp_3", json={"latitude": 32.45, "longitude": 77.30})

    preview_14 = client.post(
        "/api/v1/broadcast/preview",
        json={"zone_id": "hp_solang_rohtang", "radius_km": 14},
    )
    assert preview_14.status_code == 200
    count_14 = preview_14.json()["data"]["tourist_count"]
    assert count_14 >= 2

    preview_5 = client.post(
        "/api/v1/broadcast/preview",
        json={"zone_id": "hp_solang_rohtang", "radius_km": 5},
    )
    count_5 = preview_5.json()["data"]["tourist_count"]
    assert count_5 <= count_14


def test_send_broadcast(client):
    client.post("/api/v1/locations/tourist_hp_1", json={"latitude": 32.32, "longitude": 77.14})

    response = client.post(
        "/api/v1/broadcast/send",
        json={
            "zone_id": "hp_solang_rohtang",
            "radius_km": 14,
            "severity": "CRITICAL",
            "title": "⚠️ Flash Flood & Sudden Cloudburst Warning",
            "message": "Heavy rainfall alert active in Solang Valley. Avoid unmapped riverbanks and move to higher ground immediately.",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["severity"] == "CRITICAL"
    assert data["radius_km"] == 14
    assert data["tourists_notified"] >= 1
    assert data["deliveries"][0]["alert_type"] == "EMERGENCY_BROADCAST"


def test_location_update_user_radius(client):
    client.post("/api/v1/locations/tourist_radius_1", json={"latitude": 26.5775, "longitude": 93.1711})

    narrow = client.post(
        "/api/v1/locations/tourist_radius_1",
        json={"latitude": 26.5775, "longitude": 93.1711, "safety_radius_km": 5},
    )
    wide = client.post(
        "/api/v1/locations/tourist_radius_1",
        json={"latitude": 26.5775, "longitude": 93.1711, "safety_radius_km": 50},
    )
    narrow_count = sum(
        len(narrow.json()["data"]["nearby_safety"][k])
        for k in ("patrol_units", "police", "hospitals")
    )
    wide_count = sum(
        len(wide.json()["data"]["nearby_safety"][k])
        for k in ("patrol_units", "police", "hospitals")
    )
    assert wide_count >= narrow_count
    assert narrow.json()["data"]["nearby_safety"]["search_radius_km"] == 5
    assert wide.json()["data"]["nearby_safety"]["search_radius_km"] == 50
