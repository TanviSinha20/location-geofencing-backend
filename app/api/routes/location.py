"""Location API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import APIResponse
from app.schemas.location import (
    LocationResponse,
    LocationUpdateRequest,
    LocationUpdateResult,
    MockLocationRequest,
    SimulateMovementRequest,
    SimulateMovementResponse,
    TouristLocationSummary,
)
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post(
    "/{tourist_id}",
    response_model=APIResponse[LocationUpdateResult],
    status_code=status.HTTP_200_OK,
    summary="Update tourist location",
)
def update_location(
    tourist_id: str,
    payload: LocationUpdateRequest,
    db: Session = Depends(get_db),
) -> APIResponse[LocationUpdateResult]:
    service = LocationService(db)
    result = service.update_location(tourist_id, payload)
    return APIResponse(data=result, message="Location updated")


@router.get(
    "/{tourist_id}/current",
    response_model=APIResponse[LocationResponse],
    summary="Get tourist current location",
)
def get_current_location(tourist_id: str, db: Session = Depends(get_db)) -> APIResponse[LocationResponse]:
    service = LocationService(db)
    return APIResponse(data=service.get_current_location(tourist_id))


@router.get(
    "/{tourist_id}/last",
    response_model=APIResponse[LocationResponse],
    summary="Get tourist last known location",
)
def get_last_known_location(tourist_id: str, db: Session = Depends(get_db)) -> APIResponse[LocationResponse]:
    service = LocationService(db)
    return APIResponse(data=service.get_last_known_location(tourist_id))


@router.post(
    "/test/reset",
    response_model=APIResponse[dict[str, int]],
    summary="Reset location and geofence test data",
)
def reset_test_data(db: Session = Depends(get_db)) -> APIResponse[dict[str, int]]:
    service = LocationService(db)
    stats = service.reset_test_data()
    return APIResponse(data=stats, message="Test data reset")


@router.get(
    "",
    response_model=APIResponse[list[TouristLocationSummary]],
    summary="List all tourist locations (admin/testing)",
)
def list_all_locations(db: Session = Depends(get_db)) -> APIResponse[list[TouristLocationSummary]]:
    service = LocationService(db)
    return APIResponse(data=service.list_all_tourists())


@router.post(
    "/{tourist_id}/simulate",
    response_model=APIResponse[SimulateMovementResponse],
    summary="Simulate tourist movement along a path",
)
def simulate_movement(
    tourist_id: str,
    payload: SimulateMovementRequest,
    db: Session = Depends(get_db),
) -> APIResponse[SimulateMovementResponse]:
    service = LocationService(db)
    result = service.simulate_movement(tourist_id, payload)
    return APIResponse(data=result, message="Movement simulation complete")


@router.post(
    "/{tourist_id}/mock",
    response_model=APIResponse[LocationUpdateResult],
    summary="Post mock GPS coordinates",
)
def mock_location(
    tourist_id: str,
    payload: MockLocationRequest,
    db: Session = Depends(get_db),
) -> APIResponse[LocationUpdateResult]:
    service = LocationService(db)
    result = service.update_location(
        tourist_id,
        LocationUpdateRequest(latitude=payload.latitude, longitude=payload.longitude),
    )
    return APIResponse(data=result, message=f"Mock location applied{f': {payload.label}' if payload.label else ''}")
