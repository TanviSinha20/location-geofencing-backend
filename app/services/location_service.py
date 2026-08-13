"""Tourist location business logic."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.models.location import TouristLocation
from app.schemas.location import (
    LocationResponse,
    LocationUpdateRequest,
    LocationUpdateResult,
    SimulateMovementRequest,
    SimulateMovementResponse,
    TouristLocationSummary,
)
from app.schemas.safety_resource import LiveLocationResponse, NearbySafetyResponse
from app.services.geofence_service import GeofenceService
from app.services.safety_resource_service import SafetyResourceService
from app.utils.exceptions import NotFoundError
from app.utils.geo import interpolate_path


class LocationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.geofence_service = GeofenceService(db)
        self.safety_service = SafetyResourceService(db)

    def update_location(
        self,
        tourist_id: str,
        payload: LocationUpdateRequest,
        include_nearby_safety: bool = True,
        safety_radius_km: float | None = None,
    ) -> LocationUpdateResult:
        recorded_at = payload.recorded_at or datetime.now(UTC)

        self.db.execute(
            update(TouristLocation)
            .where(TouristLocation.tourist_id == tourist_id, TouristLocation.is_current.is_(True))
            .values(is_current=False)
        )

        location = TouristLocation(
            tourist_id=tourist_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy=payload.accuracy,
            speed=payload.speed,
            heading=payload.heading,
            recorded_at=recorded_at,
            is_current=True,
        )
        self.db.add(location)
        self.db.flush()

        status, active_zones, events = self.geofence_service.process_location(
            tourist_id=tourist_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )

        self.db.commit()
        self.db.refresh(location)

        response = self._to_response(location)
        nearby = (
            self.safety_service.find_nearby(payload.latitude, payload.longitude, radius_km=safety_radius_km)
            if include_nearby_safety
            else None
        )
        return LocationUpdateResult(
            location=response,
            geofence_status=status,
            active_zones=active_zones,
            events=events,
            nearby_safety=nearby,
        )

    def get_live_location(
        self,
        tourist_id: str,
        safety_radius_km: float | None = None,
    ) -> LiveLocationResponse:
        location = self.db.scalar(
            select(TouristLocation)
            .where(TouristLocation.tourist_id == tourist_id, TouristLocation.is_current.is_(True))
            .order_by(desc(TouristLocation.recorded_at))
        )
        if not location:
            raise NotFoundError(f"No location found for tourist '{tourist_id}'")

        status, active_zones = self._evaluate_geofence_status(
            tourist_id, location.latitude, location.longitude
        )
        nearby = self.safety_service.find_nearby(
            location.latitude, location.longitude, radius_km=safety_radius_km
        )
        return LiveLocationResponse(
            location=self._to_response(location),
            geofence_status=status,
            active_zones=active_zones,
            events=[],
            nearby_safety=nearby,
        )

    def _evaluate_geofence_status(
        self, tourist_id: str, latitude: float, longitude: float
    ) -> tuple[str, list[str]]:
        """Read-only geofence status for live location without creating events."""
        from app.geofence.engine import evaluate_point, split_transitions
        from app.models.geofence import GeoFence
        from app.models.tourist_zone_state import TouristZoneState

        zones = self.db.scalars(select(GeoFence).where(GeoFence.is_active.is_(True))).all()
        matches = evaluate_point(latitude, longitude, list(zones))
        previous_states = self.db.scalars(
            select(TouristZoneState).where(TouristZoneState.tourist_id == tourist_id)
        ).all()
        previous_ids = {state.zone_id for state in previous_states}
        entered, exited_ids = split_transitions(previous_ids, matches)
        active_zone_ids = [match.zone_id for match in matches]

        if not previous_ids and not active_zone_ids:
            status = "OUTSIDE"
        elif entered:
            status = "ENTERING" if not exited_ids else "TRANSITION"
        elif exited_ids and not active_zone_ids:
            status = "LEAVING"
        elif active_zone_ids:
            status = "INSIDE"
        else:
            status = "OUTSIDE"
        return status, active_zone_ids

    def get_current_location(self, tourist_id: str) -> LocationResponse:
        location = self.db.scalar(
            select(TouristLocation)
            .where(TouristLocation.tourist_id == tourist_id, TouristLocation.is_current.is_(True))
            .order_by(desc(TouristLocation.recorded_at))
        )
        if not location:
            raise NotFoundError(f"No location found for tourist '{tourist_id}'")
        return self._to_response(location)

    def get_last_known_location(self, tourist_id: str) -> LocationResponse:
        location = self.db.scalar(
            select(TouristLocation)
            .where(TouristLocation.tourist_id == tourist_id)
            .order_by(desc(TouristLocation.recorded_at))
        )
        if not location:
            raise NotFoundError(f"No location history for tourist '{tourist_id}'")
        return self._to_response(location)

    def list_all_tourists(self) -> list[TouristLocationSummary]:
        subquery = (
            select(
                TouristLocation.tourist_id,
                func.max(TouristLocation.recorded_at).label("max_recorded"),
            )
            .where(TouristLocation.is_current.is_(True))
            .group_by(TouristLocation.tourist_id)
            .subquery()
        )
        rows = self.db.execute(
            select(TouristLocation).join(
                subquery,
                (TouristLocation.tourist_id == subquery.c.tourist_id)
                & (TouristLocation.recorded_at == subquery.c.max_recorded),
            )
        ).scalars().all()

        return [
            TouristLocationSummary(
                tourist_id=row.tourist_id,
                latitude=row.latitude,
                longitude=row.longitude,
                recorded_at=row.recorded_at,
                last_updated=row.recorded_at,
            )
            for row in rows
        ]

    def simulate_movement(
        self,
        tourist_id: str,
        payload: SimulateMovementRequest,
    ) -> SimulateMovementResponse:
        path = interpolate_path(
            payload.start_latitude,
            payload.start_longitude,
            payload.end_latitude,
            payload.end_longitude,
            payload.steps,
        )
        updates: list[LocationUpdateResult] = []
        for lat, lng in path:
            result = self.update_location(
                tourist_id,
                LocationUpdateRequest(latitude=lat, longitude=lng),
            )
            updates.append(result)
        return SimulateMovementResponse(tourist_id=tourist_id, updates=updates)

    def reset_test_data(self) -> dict[str, int]:
        locations = self.db.scalars(select(TouristLocation)).all()
        for row in locations:
            self.db.delete(row)
        geofence_stats = self.geofence_service.reset_test_data()
        self.db.commit()
        return {"locations_deleted": len(locations), **geofence_stats}

    @staticmethod
    def _to_response(location: TouristLocation) -> LocationResponse:
        return LocationResponse(
            tourist_id=location.tourist_id,
            latitude=location.latitude,
            longitude=location.longitude,
            accuracy=location.accuracy,
            speed=location.speed,
            heading=location.heading,
            recorded_at=location.recorded_at,
            last_updated=location.recorded_at,
            is_current=location.is_current,
        )
