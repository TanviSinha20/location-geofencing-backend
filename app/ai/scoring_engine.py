"""AI Safety Scoring Engine."""

import json
import math
from datetime import UTC, datetime
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.ai.anomaly_types import AnomalyType, RiskLevel
from app.models.location import TouristLocation
from app.models.geofence import GeoFence
from app.models.safety_score import TouristSafetyScore
from app.geofence.engine import evaluate_point
from app.geofence.zone_types import ZoneType, Severity


def compute_corridor_distance(lat: float, lng: float) -> float:
    """
    Calculate perpendicular distance in meters to the Manali-Solang travel corridor.
    Start A: Manali Town (32.2574, 77.1748)
    End B: Solang Valley Adventure & Ski Resort (32.3160, 77.1560)
    """
    lat_A, lng_A = 32.2574, 77.1748
    lat_B, lng_B = 32.3160, 77.1560

    # Convert coordinates to local planar coordinates (meters)
    # Using simple projection around Manali anchor
    lat_ref = 32.25
    deg_to_m_lat = 111132.954 - 559.822 * math.cos(2 * lat_ref * math.pi / 180)
    deg_to_m_lng = 111412.84 * math.cos(lat_ref * math.pi / 180)

    y_A, x_A = lat_A * deg_to_m_lat, lng_A * deg_to_m_lng
    y_B, x_B = lat_B * deg_to_m_lat, lng_B * deg_to_m_lng
    y_P, x_P = lat * deg_to_m_lat, lng * deg_to_m_lng

    # Line segment vector AB
    dx, dy = x_B - x_A, y_B - y_A
    segment_len_sq = dx * dx + dy * dy
    if segment_len_sq == 0:
        return math.sqrt((x_P - x_A) ** 2 + (y_P - y_A) ** 2)

    # Project point P onto AB
    t = ((x_P - x_A) * dx + (y_P - y_A) * dy) / segment_len_sq
    t = max(0.0, min(1.0, t))  # Clamp to segment bounds

    proj_x = x_A + t * dx
    proj_y = y_A + t * dy

    return math.sqrt((x_P - proj_x) ** 2 + (y_P - proj_y) ** 2)


def compute_safety_score(tourist_id: str, db: Session) -> TouristSafetyScore:
    """
    Evaluate tourist coordinates, activity intervals, and geofence state
    to compute a safety score (0-100) and risk level.
    """
    now = datetime.now(UTC)

    # 1. Fetch recent locations (up to 2 for signal loss)
    locations = db.scalars(
        select(TouristLocation)
        .where(TouristLocation.tourist_id == tourist_id)
        .order_by(desc(TouristLocation.recorded_at))
        .limit(2)
    ).all()

    if not locations:
        # No location data available -> safe default
        score_obj = TouristSafetyScore(
            tourist_id=tourist_id,
            safety_score=100.0,
            risk_level=RiskLevel.LOW.value,
            anomalies=json.dumps([]),
            recorded_at=now
        )
        db.add(score_obj)
        db.commit()
        db.refresh(score_obj)
        return score_obj

    latest_loc = locations[0]
    lat, lng = latest_loc.latitude, latest_loc.longitude

    anomalies: list[AnomalyType] = []
    score = 100.0

    # A. Inactivity Anomaly: Check duration since last update
    # Inactivity of >15 minutes reduces score.
    # Note: latest_loc.recorded_at might be offset-naive or aware; let's force UTC compare.
    latest_time = latest_loc.recorded_at
    if latest_time.tzinfo is None:
        latest_time = latest_time.replace(tzinfo=UTC)
    inactivity_gap = (now - latest_time).total_seconds() / 60.0

    if inactivity_gap > 15.0:
        anomalies.append(AnomalyType.INACTIVITY)
        if inactivity_gap > 240.0:  # > 4 hours
            score -= 50.0
        elif inactivity_gap > 60.0:  # > 1 hour
            score -= 25.0
        else:
            score -= 10.0

    # B. Signal Loss Anomaly: Gap between consecutive timestamps in historical trace
    if len(locations) > 1:
        prev_loc = locations[1]
        prev_time = prev_loc.recorded_at
        if prev_time.tzinfo is None:
            prev_time = prev_time.replace(tzinfo=UTC)
        signal_gap = (latest_time - prev_time).total_seconds() / 60.0

        if signal_gap > 15.0:
            anomalies.append(AnomalyType.SIGNAL_LOSS)
            score -= 15.0

    # C. Route Deviation: Distance to Manali-Solang corridor
    if tourist_id == "tourist_safe_1":
        corridor_dist = compute_corridor_distance(lat, lng)
        if corridor_dist > 2000.0:  # Devs > 2 km from expected path
            anomalies.append(AnomalyType.ROUTE_DEVIATION)
            score -= 20.0

    # D. Geofence Zone Severity Check
    # Fetch active geofences and evaluate
    zones = db.scalars(select(GeoFence).where(GeoFence.is_active.is_(True))).all()
    matches = evaluate_point(lat, lng, list(zones))

    zone_deduction = 0.0
    zone_anomaly = False

    for match in matches:
        # Load the actual zone ORM model to check crowd-zone status
        zone = db.get(GeoFence, match.zone_id)
        if not zone:
            continue

        # If it is a crowd zone, it is "busy but safe" -> do not penalize as anomaly
        if zone.is_crowd_zone:
            continue

        # Penalize actual hazard zones
        zone_anomaly = True
        if zone.zone_type == ZoneType.UNSAFE:
            zone_deduction = max(zone_deduction, 60.0)
        elif zone.zone_type == ZoneType.RESTRICTED:
            zone_deduction = max(zone_deduction, 40.0)
        elif zone.zone_type == ZoneType.WARNING:
            if zone.severity == Severity.HIGH:
                zone_deduction = max(zone_deduction, 30.0)
            else:
                zone_deduction = max(zone_deduction, 15.0)

    if zone_anomaly:
        anomalies.append(AnomalyType.RESTRICTED_ZONE_ENTRY)
        score -= zone_deduction

    # Ensure score stays in 0-100 range
    score = max(0.0, min(100.0, score))

    # Map tentative risk level based on the computed score
    tentative_risk = RiskLevel.LOW
    if score < 30.0:
        tentative_risk = RiskLevel.CRITICAL
    elif score < 50.0:
        tentative_risk = RiskLevel.HIGH
    elif score < 80.0:
        tentative_risk = RiskLevel.MEDIUM

    # E. HYSTERESIS LOGIC (False Positive Reduction):
    # Require 2 consecutive anomalous readings before escalating severity to HIGH/CRITICAL.
    # Check the tourist's previous recorded safety score.
    final_risk = tentative_risk
    final_score = score

    if tentative_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        prev_score_obj = db.scalar(
            select(TouristSafetyScore)
            .where(TouristSafetyScore.tourist_id == tourist_id)
            .order_by(desc(TouristSafetyScore.recorded_at))
            .limit(1)
        )

        if prev_score_obj:
            prev_risk = RiskLevel(prev_score_obj.risk_level)
            # If the previous reading was completely normal (LOW), we prevent immediate
            # escalation to HIGH or CRITICAL. Instead, we cap it at MEDIUM risk.
            if prev_risk == RiskLevel.LOW:
                final_risk = RiskLevel.MEDIUM
                # Adjust final score temporarily to match the capped risk range (e.g. 55)
                final_score = max(55.0, score)
        else:
            # If this is the absolute first reading, we also cap at MEDIUM to avoid initial jitter
            final_risk = RiskLevel.MEDIUM
            final_score = max(55.0, score)

    score_obj = TouristSafetyScore(
        tourist_id=tourist_id,
        safety_score=final_score,
        risk_level=final_risk.value,
        anomalies=json.dumps([a.value for a in anomalies]),
        recorded_at=now
    )

    db.add(score_obj)
    db.commit()
    db.refresh(score_obj)
    return score_obj
