"""Geofenced Emergency Broadcast Centre API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.broadcast import (
    BroadcastPreviewRequest,
    BroadcastPreviewResponse,
    BroadcastSendRequest,
    BroadcastSendResponse,
    RadiusConfigResponse,
    TargetZoneResponse,
)
from app.schemas.common import APIResponse
from app.services.broadcast_service import BroadcastService

router = APIRouter(prefix="/broadcast", tags=["emergency-broadcast"])


@router.get(
    "/radius-config",
    response_model=APIResponse[RadiusConfigResponse],
    summary="Get geofence radius slider config for frontend",
)
def get_radius_config(
    zone_id: str | None = Query(None, description="Optional zone to get zone-specific default radius"),
    db: Session = Depends(get_db),
) -> APIResponse[RadiusConfigResponse]:
    service = BroadcastService(db)
    return APIResponse(data=service.get_radius_config(zone_id=zone_id))


@router.get(
    "/target-zones",
    response_model=APIResponse[list[TargetZoneResponse]],
    summary="List target zones for authority dropdown",
)
def list_target_zones(db: Session = Depends(get_db)) -> APIResponse[list[TargetZoneResponse]]:
    service = BroadcastService(db)
    return APIResponse(data=service.list_target_zones())


@router.get(
    "/target-zones/{zone_id}",
    response_model=APIResponse[TargetZoneResponse],
    summary="Get target zone details",
)
def get_target_zone(zone_id: str, db: Session = Depends(get_db)) -> APIResponse[TargetZoneResponse]:
    service = BroadcastService(db)
    return APIResponse(data=service.get_target_zone(zone_id))


@router.post(
    "/preview",
    response_model=APIResponse[BroadcastPreviewResponse],
    summary="Preview tourists affected by geofence radius before sending alert",
)
def preview_broadcast(
    payload: BroadcastPreviewRequest,
    db: Session = Depends(get_db),
) -> APIResponse[BroadcastPreviewResponse]:
    service = BroadcastService(db)
    result = service.preview_broadcast(payload.zone_id, payload.radius_km)
    return APIResponse(data=result, message=f"{result.tourist_count} tourist(s) within {payload.radius_km} km")


@router.post(
    "/send",
    response_model=APIResponse[BroadcastSendResponse],
    summary="Send emergency SMS/app alert to all tourists within geofence radius",
)
def send_broadcast(
    payload: BroadcastSendRequest,
    db: Session = Depends(get_db),
) -> APIResponse[BroadcastSendResponse]:
    service = BroadcastService(db)
    result = service.send_broadcast(payload)
    return APIResponse(
        data=result,
        message=f"Emergency broadcast sent to {result.tourists_notified} tourist(s) within {payload.radius_km} km",
    )
