"""Geofence CRUD and event generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.geofence.engine import ZoneMatch, evaluate_point, split_transitions
from app.geofence.zone_types import (
    ZONE_TYPE_TO_ENTER_EVENT,
    ZONE_TYPE_TO_EXIT_EVENT,
    GeometryType,
    ZoneType,
)
from app.models.geofence import GeoFence
from app.models.geofence_event import GeofenceEvent
from app.models.tourist_zone_state import TouristZoneState
from app.schemas.geofence import (
    GeoFenceCreateRequest,
    GeoFenceResponse,
    GeoFenceUpdateRequest,
    GeofenceEventResponse,
)
from app.utils.exceptions import NotFoundError, ValidationError


class GeofenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_zones(self, active_only: bool = False) -> list[GeoFenceResponse]:
        stmt = select(GeoFence)
        if active_only:
            stmt = stmt.where(GeoFence.is_active.is_(True))
        zones = self.db.scalars(stmt.order_by(GeoFence.name)).all()
        return [self._to_response(zone) for zone in zones]

    def get_zone(self, zone_id: str) -> GeoFenceResponse:
        zone = self._get_zone_or_404(zone_id)
        return self._to_response(zone)

    def create_zone(self, payload: GeoFenceCreateRequest) -> GeoFenceResponse:
        if self.db.get(GeoFence, payload.id):
            raise ValidationError(f"Zone {payload.id} already exists")

        zone = GeoFence(
            id=payload.id,
            name=payload.name,
            zone_type=payload.zone_type.value,
            geometry_type=payload.geometry_type.value,
            severity=payload.severity.value,
            description=payload.description,
            warning_message=payload.warning_message,
            is_active=payload.is_active,
            is_crowd_zone=payload.is_crowd_zone,
        )
        self._apply_geometry(zone, payload.geometry_type, payload.circle, payload.polygon)
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)
        return self._to_response(zone)

    def update_zone(self, zone_id: str, payload: GeoFenceUpdateRequest) -> GeoFenceResponse:
        zone = self._get_zone_or_404(zone_id)
        if payload.name is not None:
            zone.name = payload.name
        if payload.zone_type is not None:
            zone.zone_type = payload.zone_type.value
        if payload.severity is not None:
            zone.severity = payload.severity.value
        if payload.description is not None:
            zone.description = payload.description
        if payload.warning_message is not None:
            zone.warning_message = payload.warning_message
        if payload.is_active is not None:
            zone.is_active = payload.is_active
        if payload.is_crowd_zone is not None:
            zone.is_crowd_zone = payload.is_crowd_zone
        if payload.circle is not None:
            zone.geometry_type = GeometryType.CIRCLE.value
            zone.center_lat = payload.circle.center_lat
            zone.center_lng = payload.circle.center_lng
            zone.radius_m = payload.circle.radius_m
            zone.polygon_coordinates = None
        if payload.polygon is not None:
            zone.geometry_type = GeometryType.POLYGON.value
            zone.polygon_coordinates = json.dumps(payload.polygon.coordinates)
            zone.center_lat = None
            zone.center_lng = None
            zone.radius_m = None

        self.db.commit()
        self.db.refresh(zone)
        return self._to_response(zone)

    def delete_zone(self, zone_id: str) -> None:
        zone = self._get_zone_or_404(zone_id)
        self.db.delete(zone)
        self.db.commit()

    def process_location(
        self,
        tourist_id: str,
        latitude: float,
        longitude: float,
    ) -> tuple[str, list[str], list[GeofenceEventResponse]]:
        zones = self.db.scalars(select(GeoFence).where(GeoFence.is_active.is_(True))).all()
        matches = evaluate_point(latitude, longitude, list(zones))

        previous_states = self.db.scalars(
            select(TouristZoneState).where(TouristZoneState.tourist_id == tourist_id)
        ).all()
        previous_ids = {state.zone_id for state in previous_states}
        entered, exited_ids = split_transitions(previous_ids, matches)

        events: list[GeofenceEventResponse] = []
        now = datetime.now(UTC)

        for match in entered:
            existing = self.db.scalar(
                select(TouristZoneState).where(
                    TouristZoneState.tourist_id == tourist_id,
                    TouristZoneState.zone_id == match.zone_id,
                )
            )
            if not existing:
                state = TouristZoneState(tourist_id=tourist_id, zone_id=match.zone_id, entered_at=now)
                self.db.add(state)
            event = self._persist_event(
                tourist_id=tourist_id,
                match=match,
                latitude=latitude,
                longitude=longitude,
                event_type=ZONE_TYPE_TO_ENTER_EVENT[match.zone_type],
            )
            events.append(event)

        for zone_id in exited_ids:
            state = self.db.scalar(
                select(TouristZoneState).where(
                    TouristZoneState.tourist_id == tourist_id,
                    TouristZoneState.zone_id == zone_id,
                )
            )
            if state:
                self.db.delete(state)
            zone = self._get_zone_or_404(zone_id)
            match = ZoneMatch(
                zone_id=zone.id,
                zone_name=zone.name,
                zone_type=ZoneType(zone.zone_type),
                severity=zone.severity,
                warning_message=zone.warning_message,
            )
            event = self._persist_event(
                tourist_id=tourist_id,
                match=match,
                latitude=latitude,
                longitude=longitude,
                event_type=ZONE_TYPE_TO_EXIT_EVENT[ZoneType(zone.zone_type)],
            )
            events.append(event)

        active_zone_ids = [match.zone_id for match in matches]
        if not previous_ids and not active_zone_ids:
            status = "OUTSIDE"
        elif not previous_ids and active_zone_ids:
            status = "ENTERING"
        elif previous_ids and active_zone_ids and not entered and not exited_ids:
            status = "INSIDE"
        elif exited_ids and not active_zone_ids:
            status = "LEAVING"
        elif entered or exited_ids:
            status = "TRANSITION"
        else:
            status = "INSIDE" if active_zone_ids else "OUTSIDE"

        self.db.commit()
        return status, active_zone_ids, events

    def get_events(
        self,
        tourist_id: str | None = None,
        limit: int = 50,
    ) -> list[GeofenceEventResponse]:
        stmt = select(GeofenceEvent).order_by(GeofenceEvent.created_at.desc()).limit(limit)
        if tourist_id:
            stmt = stmt.where(GeofenceEvent.tourist_id == tourist_id)
        rows = self.db.scalars(stmt).all()
        return [self._event_to_response(row) for row in rows]

    def reset_test_data(self) -> dict[str, int]:
        events = self.db.scalars(select(GeofenceEvent)).all()
        states = self.db.scalars(select(TouristZoneState)).all()
        for row in events:
            self.db.delete(row)
        for row in states:
            self.db.delete(row)
        self.db.commit()
        return {"events_deleted": len(events), "zone_states_deleted": len(states)}

    def _persist_event(
        self,
        tourist_id: str,
        match: ZoneMatch,
        latitude: float,
        longitude: float,
        event_type: str,
    ) -> GeofenceEventResponse:
        row = GeofenceEvent(
            event_type=event_type.value if hasattr(event_type, "value") else str(event_type),
            tourist_id=tourist_id,
            zone_id=match.zone_id,
            severity=match.severity,
            message=match.warning_message,
            latitude=latitude,
            longitude=longitude,
        )
        self.db.add(row)
        self.db.flush()

        if row.severity == "CRITICAL":
            from app.identity.audit_service import log_incident
            log_incident(row, self.db)

        return self._event_to_response(row)

    def _get_zone_or_404(self, zone_id: str) -> GeoFence:
        zone = self.db.get(GeoFence, zone_id)
        if not zone:
            raise NotFoundError(f"Geofence zone '{zone_id}' not found")
        return zone

    @staticmethod
    def _apply_geometry(zone: GeoFence, geometry_type: GeometryType, circle, polygon) -> None:
        if geometry_type == GeometryType.CIRCLE:
            assert circle is not None
            zone.center_lat = circle.center_lat
            zone.center_lng = circle.center_lng
            zone.radius_m = circle.radius_m
            zone.polygon_coordinates = None
        else:
            assert polygon is not None
            zone.polygon_coordinates = json.dumps(polygon.coordinates)
            zone.center_lat = None
            zone.center_lng = None
            zone.radius_m = None

    @staticmethod
    def _to_response(zone: GeoFence) -> GeoFenceResponse:
        polygon = json.loads(zone.polygon_coordinates) if zone.polygon_coordinates else None
        return GeoFenceResponse(
            id=zone.id,
            name=zone.name,
            zone_type=zone.zone_type,
            geometry_type=zone.geometry_type,
            severity=zone.severity,
            description=zone.description,
            warning_message=zone.warning_message,
            is_active=zone.is_active,
            is_crowd_zone=zone.is_crowd_zone,
            center_lat=zone.center_lat,
            center_lng=zone.center_lng,
            radius_m=zone.radius_m,
            polygon_coordinates=polygon,
        )

    @staticmethod
    def _event_to_response(row: GeofenceEvent) -> GeofenceEventResponse:
        return GeofenceEventResponse(
            type=row.event_type,
            userId=row.tourist_id,
            zoneId=row.zone_id,
            time=row.created_at,
            severity=row.severity,
            message=row.message,
            latitude=row.latitude,
            longitude=row.longitude,
        )
