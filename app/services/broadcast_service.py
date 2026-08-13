"""Emergency geofenced broadcast business logic."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.location.broadcast_types import BroadcastSeverity
from app.models.emergency_broadcast import EmergencyBroadcast
from app.models.location import TouristLocation
from app.models.target_zone import TargetZone
from app.schemas.broadcast import (
    AffectedTourist,
    BroadcastPreviewResponse,
    BroadcastSendRequest,
    BroadcastSendResponse,
    RadiusConfigResponse,
    TargetZoneResponse,
    TouristAlertDelivery,
)
from app.utils.exceptions import NotFoundError
from app.utils.geo import haversine_distance_m


class BroadcastService:
    RADIUS_MIN_KM = 1.0
    RADIUS_MAX_KM = 50.0
    RADIUS_DEFAULT_KM = 14.0
    RADIUS_STEP_KM = 1.0

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_radius_config(self, zone_id: str | None = None) -> RadiusConfigResponse:
        default = self.RADIUS_DEFAULT_KM
        if zone_id:
            zone = self._get_zone_or_404(zone_id)
            default = zone.default_radius_km
        return RadiusConfigResponse(
            min_km=self.RADIUS_MIN_KM,
            max_km=self.RADIUS_MAX_KM,
            default_km=default,
            step_km=self.RADIUS_STEP_KM,
        )

    def list_target_zones(self, active_only: bool = True) -> list[TargetZoneResponse]:
        stmt = select(TargetZone)
        if active_only:
            stmt = stmt.where(TargetZone.is_active.is_(True))
        rows = self.db.scalars(stmt.order_by(TargetZone.state, TargetZone.name)).all()
        return [TargetZoneResponse.model_validate(row) for row in rows]

    def get_target_zone(self, zone_id: str) -> TargetZoneResponse:
        return TargetZoneResponse.model_validate(self._get_zone_or_404(zone_id))

    def find_tourists_in_radius(self, zone_id: str, radius_km: float) -> list[AffectedTourist]:
        zone = self._get_zone_or_404(zone_id)
        radius_m = radius_km * 1000
        current_locations = self._get_current_locations()

        affected: list[AffectedTourist] = []
        for loc in current_locations:
            distance_m = haversine_distance_m(zone.center_lat, zone.center_lng, loc.latitude, loc.longitude)
            if distance_m <= radius_m:
                affected.append(
                    AffectedTourist(
                        tourist_id=loc.tourist_id,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        distance_km=round(distance_m / 1000, 2),
                        recorded_at=loc.recorded_at,
                    )
                )
        affected.sort(key=lambda t: t.distance_km)
        return affected

    def preview_broadcast(self, zone_id: str, radius_km: float) -> BroadcastPreviewResponse:
        zone = self._get_zone_or_404(zone_id)
        affected = self.find_tourists_in_radius(zone_id, radius_km)
        return BroadcastPreviewResponse(
            zone_id=zone.id,
            zone_name=zone.name,
            state=zone.state,
            radius_km=radius_km,
            center_lat=zone.center_lat,
            center_lng=zone.center_lng,
            tourist_count=len(affected),
            affected_tourists=affected,
        )

    def send_broadcast(self, payload: BroadcastSendRequest) -> BroadcastSendResponse:
        zone = self._get_zone_or_404(payload.zone_id)
        affected = self.find_tourists_in_radius(payload.zone_id, payload.radius_km)
        now = datetime.now(UTC)

        broadcast = EmergencyBroadcast(
            zone_id=zone.id,
            zone_name=zone.name,
            radius_km=payload.radius_km,
            severity=payload.severity.value,
            title=payload.title,
            message=payload.message,
            tourists_notified=len(affected),
        )
        self.db.add(broadcast)
        self.db.flush()

        deliveries: list[TouristAlertDelivery] = []
        for tourist in affected:
            deliveries.append(
                TouristAlertDelivery(
                    tourist_id=tourist.tourist_id,
                    distance_km=tourist.distance_km,
                    alert_type="EMERGENCY_BROADCAST",
                    severity=payload.severity.value,
                    title=payload.title,
                    message=payload.message,
                    delivered_at=now,
                )
            )

        self.db.commit()
        self.db.refresh(broadcast)

        return BroadcastSendResponse(
            broadcast_id=broadcast.id,
            zone_id=zone.id,
            zone_name=zone.name,
            state=zone.state,
            radius_km=payload.radius_km,
            severity=BroadcastSeverity(payload.severity),
            title=payload.title,
            message=payload.message,
            tourists_notified=len(deliveries),
            deliveries=deliveries,
            sent_at=broadcast.created_at,
        )

    def _get_current_locations(self) -> list[TouristLocation]:
        subquery = (
            select(
                TouristLocation.tourist_id,
                func.max(TouristLocation.recorded_at).label("max_recorded"),
            )
            .where(TouristLocation.is_current.is_(True))
            .group_by(TouristLocation.tourist_id)
            .subquery()
        )
        return list(
            self.db.execute(
                select(TouristLocation).join(
                    subquery,
                    (TouristLocation.tourist_id == subquery.c.tourist_id)
                    & (TouristLocation.recorded_at == subquery.c.max_recorded),
                )
            ).scalars().all()
        )

    def _get_zone_or_404(self, zone_id: str) -> TargetZone:
        zone = self.db.get(TargetZone, zone_id)
        if not zone or not zone.is_active:
            raise NotFoundError(f"Target zone '{zone_id}' not found")
        return zone
