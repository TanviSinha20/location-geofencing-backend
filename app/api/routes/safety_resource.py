"""Safety resource API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.location.resource_types import SafetyResourceType
from app.schemas.common import APIResponse
from app.schemas.safety_resource import (
    NearbySafetyResponse,
    SafetyResourceCreateRequest,
    SafetyResourceResponse,
    SafetyResourceUpdateRequest,
)
from app.services.safety_resource_service import SafetyResourceService

router = APIRouter(prefix="/safety-resources", tags=["safety-resources"])


@router.get("", response_model=APIResponse[list[SafetyResourceResponse]], summary="List safety resources")
def list_safety_resources(
    resource_type: SafetyResourceType | None = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> APIResponse[list[SafetyResourceResponse]]:
    service = SafetyResourceService(db)
    return APIResponse(data=service.list_resources(resource_type=resource_type, active_only=active_only))


@router.post(
    "",
    response_model=APIResponse[SafetyResourceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create safety resource",
)
def create_safety_resource(
    payload: SafetyResourceCreateRequest,
    db: Session = Depends(get_db),
) -> APIResponse[SafetyResourceResponse]:
    service = SafetyResourceService(db)
    return APIResponse(data=service.create_resource(payload), message="Safety resource created")


@router.get("/nearby", response_model=APIResponse[NearbySafetyResponse], summary="Find nearby safety resources")
def find_nearby_safety_resources(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(25.0, gt=0, le=100),
    limit_per_type: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> APIResponse[NearbySafetyResponse]:
    service = SafetyResourceService(db)
    data = service.find_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit_per_type=limit_per_type,
    )
    return APIResponse(data=data)


@router.get("/{resource_id}", response_model=APIResponse[SafetyResourceResponse], summary="Get safety resource")
def get_safety_resource(resource_id: str, db: Session = Depends(get_db)) -> APIResponse[SafetyResourceResponse]:
    service = SafetyResourceService(db)
    return APIResponse(data=service.get_resource(resource_id))


@router.patch("/{resource_id}", response_model=APIResponse[SafetyResourceResponse], summary="Update safety resource")
def update_safety_resource(
    resource_id: str,
    payload: SafetyResourceUpdateRequest,
    db: Session = Depends(get_db),
) -> APIResponse[SafetyResourceResponse]:
    service = SafetyResourceService(db)
    return APIResponse(data=service.update_resource(resource_id, payload), message="Safety resource updated")


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete safety resource")
def delete_safety_resource(resource_id: str, db: Session = Depends(get_db)) -> None:
    service = SafetyResourceService(db)
    service.delete_resource(resource_id)
