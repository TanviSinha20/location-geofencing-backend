"""Incident auditing and logging onto the simulated ledger."""

from datetime import UTC, datetime
from sqlalchemy.orm import Session

from app.models.geofence_event import GeofenceEvent
from app.identity.chain import append_block


def log_incident(event: GeofenceEvent, db: Session) -> None:
    """
    Serialize a critical safety event and append its cryptographic
    representation onto the blockchain ledger.
    """
    timestamp_str = (
        event.created_at.isoformat()
        if event.created_at
        else datetime.now(UTC).isoformat()
    )

    incident_data = {
        "event_type": "CRITICAL_GEOFENCE_VIOLATION",
        "event_id": event.id,
        "tourist_id": event.tourist_id,
        "zone_id": event.zone_id,
        "severity": event.severity,
        "message": event.message,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "timestamp": timestamp_str
    }

    append_block(incident_data, db)
