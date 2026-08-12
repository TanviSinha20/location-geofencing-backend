"""Geofence API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import APIResponse
from app.schemas.geofence import (
    GeoFenceCreateRequest,
    GeoFenceResponse,
    GeoFenceUpdateRequest,
    GeofenceCheckRequest,
    GeofenceCheckResponse,
    GeofenceEventResponse,
)
from app.services.geofence_service import GeofenceService

router = APIRouter(prefix="/geofences", tags=["geofences"])


@router.get("", response_model=APIResponse[list[GeoFenceResponse]], summary="List geofence zones")
def list_geofences(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> APIResponse[list[GeoFenceResponse]]:
    service = GeofenceService(db)
    return APIResponse(data=service.list_zones(active_only=active_only))


@router.post(
    "",
    response_model=APIResponse[GeoFenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create geofence zone",
)
def create_geofence(
    payload: GeoFenceCreateRequest,
    db: Session = Depends(get_db),
) -> APIResponse[GeoFenceResponse]:
    service = GeofenceService(db)
    zone = service.create_zone(payload)
    return APIResponse(data=zone, message="Geofence created")


@router.get(
    "/events/list",
    response_model=APIResponse[list[GeofenceEventResponse]],
    summary="List geofence events",
)
def list_events(
    tourist_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> APIResponse[list[GeofenceEventResponse]]:
    service = GeofenceService(db)
    return APIResponse(data=service.get_events(tourist_id=tourist_id, limit=limit))


@router.get("/{zone_id}", response_model=APIResponse[GeoFenceResponse], summary="Get geofence zone")
def get_geofence(zone_id: str, db: Session = Depends(get_db)) -> APIResponse[GeoFenceResponse]:
    service = GeofenceService(db)
    return APIResponse(data=service.get_zone(zone_id))


@router.patch("/{zone_id}", response_model=APIResponse[GeoFenceResponse], summary="Update geofence zone")
def update_geofence(
    zone_id: str,
    payload: GeoFenceUpdateRequest,
    db: Session = Depends(get_db),
) -> APIResponse[GeoFenceResponse]:
    service = GeofenceService(db)
    zone = service.update_zone(zone_id, payload)
    return APIResponse(data=zone, message="Geofence updated")


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete geofence zone")
def delete_geofence(zone_id: str, db: Session = Depends(get_db)) -> None:
    service = GeofenceService(db)
    service.delete_zone(zone_id)


@router.post(
    "/check/{tourist_id}",
    response_model=APIResponse[GeofenceCheckResponse],
    summary="Check point against geofences without persisting location",
)
def check_geofence(
    tourist_id: str,
    payload: GeofenceCheckRequest,
    db: Session = Depends(get_db),
) -> APIResponse[GeofenceCheckResponse]:
    service = GeofenceService(db)
    status_label, active_zone_ids, events = service.process_location(
        tourist_id=tourist_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    zones = [service.get_zone(zone_id) for zone_id in active_zone_ids]
    return APIResponse(
        data=GeofenceCheckResponse(status=status_label, inside_zones=zones, events=events),
        message="Geofence check complete",
    )
