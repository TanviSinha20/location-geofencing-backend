"""Safety resource CRUD and nearby lookup."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.location.resource_types import SafetyResourceType
from app.models.safety_resource import SafetyResource
from app.schemas.safety_resource import (
    NearbySafetyResource,
    NearbySafetyResponse,
    SafetyResourceCreateRequest,
    SafetyResourceResponse,
    SafetyResourceUpdateRequest,
)
from app.utils.exceptions import NotFoundError, ValidationError
from app.utils.geo import haversine_distance_m


class SafetyResourceService:
    DEFAULT_RADIUS_KM = 25.0
    DEFAULT_LIMIT_PER_TYPE = 5

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_resources(
        self,
        resource_type: SafetyResourceType | None = None,
        active_only: bool = True,
    ) -> list[SafetyResourceResponse]:
        stmt = select(SafetyResource)
        if active_only:
            stmt = stmt.where(SafetyResource.is_active.is_(True))
        if resource_type:
            stmt = stmt.where(SafetyResource.resource_type == resource_type.value)
        rows = self.db.scalars(stmt.order_by(SafetyResource.name)).all()
        return [self._to_response(row) for row in rows]

    def get_resource(self, resource_id: str) -> SafetyResourceResponse:
        return self._to_response(self._get_or_404(resource_id))

    def create_resource(self, payload: SafetyResourceCreateRequest) -> SafetyResourceResponse:
        if self.db.get(SafetyResource, payload.id):
            raise ValidationError(f"Safety resource '{payload.id}' already exists")
        row = SafetyResource(
            id=payload.id,
            name=payload.name,
            resource_type=payload.resource_type.value,
            latitude=payload.latitude,
            longitude=payload.longitude,
            address=payload.address,
            phone=payload.phone,
            description=payload.description,
            is_24x7=payload.is_24x7,
            is_active=payload.is_active,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def update_resource(self, resource_id: str, payload: SafetyResourceUpdateRequest) -> SafetyResourceResponse:
        row = self._get_or_404(resource_id)
        if payload.name is not None:
            row.name = payload.name
        if payload.resource_type is not None:
            row.resource_type = payload.resource_type.value
        if payload.latitude is not None:
            row.latitude = payload.latitude
        if payload.longitude is not None:
            row.longitude = payload.longitude
        if payload.address is not None:
            row.address = payload.address
        if payload.phone is not None:
            row.phone = payload.phone
        if payload.description is not None:
            row.description = payload.description
        if payload.is_24x7 is not None:
            row.is_24x7 = payload.is_24x7
        if payload.is_active is not None:
            row.is_active = payload.is_active
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def delete_resource(self, resource_id: str) -> None:
        row = self._get_or_404(resource_id)
        self.db.delete(row)
        self.db.commit()

    def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float | None = None,
        limit_per_type: int | None = None,
    ) -> NearbySafetyResponse:
        radius_km = radius_km or self.DEFAULT_RADIUS_KM
        limit_per_type = limit_per_type or self.DEFAULT_LIMIT_PER_TYPE
        radius_m = radius_km * 1000

        rows = self.db.scalars(
            select(SafetyResource).where(SafetyResource.is_active.is_(True))
        ).all()

        nearby: list[NearbySafetyResource] = []
        for row in rows:
            distance_m = haversine_distance_m(latitude, longitude, row.latitude, row.longitude)
            if distance_m <= radius_m:
                nearby.append(
                    NearbySafetyResource(
                        **self._to_response(row).model_dump(),
                        distance_m=round(distance_m, 1),
                    )
                )

        nearby.sort(key=lambda item: item.distance_m)

        patrol = [r for r in nearby if r.resource_type == SafetyResourceType.PATROL][:limit_per_type]
        police = [r for r in nearby if r.resource_type == SafetyResourceType.POLICE][:limit_per_type]
        hospitals = [r for r in nearby if r.resource_type == SafetyResourceType.HOSPITAL][:limit_per_type]

        return NearbySafetyResponse(
            search_radius_km=radius_km,
            patrol_units=patrol,
            police=police,
            hospitals=hospitals,
        )

    def _get_or_404(self, resource_id: str) -> SafetyResource:
        row = self.db.get(SafetyResource, resource_id)
        if not row:
            raise NotFoundError(f"Safety resource '{resource_id}' not found")
        return row

    @staticmethod
    def _to_response(row: SafetyResource) -> SafetyResourceResponse:
        return SafetyResourceResponse(
            id=row.id,
            name=row.name,
            resource_type=row.resource_type,
            latitude=row.latitude,
            longitude=row.longitude,
            address=row.address,
            phone=row.phone,
            description=row.description,
            is_24x7=row.is_24x7,
            is_active=row.is_active,
        )
