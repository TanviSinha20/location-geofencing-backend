"""Integration tests for AI Anomaly Detection and Blockchain Digital ID Modules."""

import json
from datetime import UTC, datetime, timedelta
from app.ai.anomaly_types import RiskLevel, AnomalyType


def test_ai_safety_scoring_and_hysteresis(client):
    # A. Initial location update in a completely safe area (Old Manali)
    resp = client.post(
        "/api/v1/locations/tourist_test_ai_1",
        json={"latitude": 32.2620, "longitude": 77.1620}
    )
    assert resp.status_code == 200

    # Retrieve safety score
    score_resp = client.get("/api/v1/ai/safety-score/tourist_test_ai_1")
    assert score_resp.status_code == 200
    data = score_resp.json()["data"]
    assert data["safety_score"] == 100.0
    assert data["risk_level"] == RiskLevel.LOW.value
    assert data["anomalies"] == []

    # B. Move to an UNSAFE restricted zone (Solang Avalanche Slope: 32.3250, 77.1520)
    # This is the 1st anomalous reading. Hysteresis should cap the risk level at MEDIUM.
    resp2 = client.post(
        "/api/v1/locations/tourist_test_ai_1",
        json={"latitude": 32.3250, "longitude": 77.1520}
    )
    assert resp2.status_code == 200

    score_resp2 = client.get("/api/v1/ai/safety-score/tourist_test_ai_1")
    assert score_resp2.status_code == 200
    data2 = score_resp2.json()["data"]
    # The raw deduction for unsafe is -60, score would be 40 (HIGH risk).
    # But because of hysteresis (1st reading), it should be capped at RiskLevel.MEDIUM and score >= 55.
    assert data2["risk_level"] == RiskLevel.MEDIUM.value
    assert data2["safety_score"] >= 55.0
    assert AnomalyType.RESTRICTED_ZONE_ENTRY.value in data2["anomalies"]

    # C. Post a 2nd consecutive anomalous reading in the same slope.
    # This should now escalate the risk level to CRITICAL or HIGH.
    resp3 = client.post(
        "/api/v1/locations/tourist_test_ai_1",
        json={"latitude": 32.3250, "longitude": 77.1520}
    )
    assert resp3.status_code == 200

    score_resp3 = client.get("/api/v1/ai/safety-score/tourist_test_ai_1")
    assert score_resp3.status_code == 200
    data3 = score_resp3.json()["data"]
    # Escalation allowed! Raw score is 40, risk level should be HIGH.
    assert data3["risk_level"] in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value)
    assert data3["safety_score"] < 50.0


def test_crowd_zone_exemption(client):
    # Post location update inside a busy crowd-density zone (Hadimba Devi Temple: 32.2432, 77.1892)
    resp = client.post(
        "/api/v1/locations/tourist_test_crowd",
        json={"latitude": 32.2432, "longitude": 77.1892}
    )
    assert resp.status_code == 200

    score_resp = client.get("/api/v1/ai/safety-score/tourist_test_crowd")
    assert score_resp.status_code == 200
    data = score_resp.json()["data"]
    # Since it is a crowd zone (busy but safe), it should NOT be flagged as a restricted zone anomaly,
    # keeping the risk level at LOW and score near 100.
    assert data["risk_level"] == RiskLevel.LOW.value, f"Data is: {data}"
    assert AnomalyType.RESTRICTED_ZONE_ENTRY.value not in data["anomalies"]


def test_did_issuance_verification_and_blockchain(client):
    # 1. Issue a Digital ID
    expiry = (datetime.now(UTC) + timedelta(days=365)).isoformat()
    kyc_hash = "a" * 64
    issue_payload = {
        "tourist_id": "tourist_blockchain_test",
        "kyc_hash": kyc_hash,
        "valid_until": expiry
    }
    resp = client.post("/api/v1/identity/issue", json=issue_payload)
    assert resp.status_code == 201
    did_data = resp.json()["data"]
    assert did_data["tourist_id"] == "tourist_blockchain_test"
    assert did_data["did"] == "did:sih:tourist:tourist_blockchain_test"
    assert did_data["is_active"] is True

    # 2. Verify Digital ID
    verify_resp = client.get("/api/v1/identity/verify/tourist_blockchain_test")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["data"]["did"] == "did:sih:tourist:tourist_blockchain_test"

    # 3. Check Blockchain Chain block creation
    chain_resp = client.get("/api/v1/identity/chain")
    assert chain_resp.status_code == 200
    blocks = chain_resp.json()["data"]
    # Must have at least Genesis block + DID issuance block
    assert len(blocks) >= 2
    assert any(b["data"].get("event_type") == "DID_ISSUED" for b in blocks)

    # 4. Check Blockchain Integrity Verification
    verify_chain_resp = client.get("/api/v1/identity/chain/verify")
    assert verify_chain_resp.status_code == 200
    assert verify_chain_resp.json()["data"]["is_valid"] is True


def test_critical_geofence_hook_audit(client):
    # Ensure there's a fresh database connection to check hook behavior.
    # Move tourist to Solang Avalanche Slope (UNSAFE zone, severity HIGH).
    # Wait, our seed data Solang Valley Avalanche Slope has severity = HIGH.
    # Wait, the hook checks for row.severity == "CRITICAL".
    # Let's post a location update inside a zone that is CRITICAL.
    # To test this, let's create a custom geofence with CRITICAL severity via API!
    zone_payload = {
        "id": "critical_danger_test_zone",
        "name": "Extreme Landslide Ravine",
        "zone_type": "UNSAFE",
        "geometry_type": "CIRCLE",
        "severity": "CRITICAL",
        "warning_message": "CRITICAL DANGER: Active landslide ravine!",
        "circle": {
            "center_lat": 32.3300,
            "center_lng": 77.1600,
            "radius_m": 200.0
        }
    }
    create_resp = client.post("/api/v1/geofences", json=zone_payload)
    assert create_resp.status_code == 201

    # Before location update, check block count
    chain_before = client.get("/api/v1/identity/chain")
    count_before = len(chain_before.json()["data"])

    # Update location inside this critical zone
    update_resp = client.post(
        "/api/v1/locations/tourist_critical_audit_test",
        json={"latitude": 32.3300, "longitude": 77.1600}
    )
    assert update_resp.status_code == 200

    # Hook should trigger! A new block containing the critical violation should be appended
    chain_after = client.get("/api/v1/identity/chain")
    assert chain_after.status_code == 200
    blocks = chain_after.json()["data"]
    expected_count = count_before + 2 if count_before == 0 else count_before + 1
    assert len(blocks) == expected_count

    last_block = blocks[-1]
    assert last_block["data"]["event_type"] == "CRITICAL_GEOFENCE_VIOLATION"
    assert last_block["data"]["tourist_id"] == "tourist_critical_audit_test"
    assert last_block["data"]["zone_id"] == "critical_danger_test_zone"
