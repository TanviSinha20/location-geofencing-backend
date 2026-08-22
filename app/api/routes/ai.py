"""AI Safety Routing Module."""

import json
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import APIResponse
from app.schemas.safety_score import SafetyScoreResponse
from app.ai.scoring_engine import compute_safety_score

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get(
    "/safety-score/{tourist_id}",
    response_model=APIResponse[SafetyScoreResponse],
    status_code=status.HTTP_200_OK,
    summary="Compute and return AI safety score and active anomalies for a tourist",
)
def get_tourist_safety_score(
    tourist_id: str,
    db: Session = Depends(get_db)
) -> APIResponse[SafetyScoreResponse]:
    # Calculate safety score using real-time locations and zone mappings
    score_obj = compute_safety_score(tourist_id, db)

    # Parse anomalies JSON list stored in DB
    anomalies_list = []
    if score_obj.anomalies:
        try:
            anomalies_list = json.loads(score_obj.anomalies)
        except Exception:
            pass

    response_data = SafetyScoreResponse(
        tourist_id=score_obj.tourist_id,
        safety_score=score_obj.safety_score,
        risk_level=score_obj.risk_level,
        anomalies=anomalies_list,
        recorded_at=score_obj.recorded_at
    )
    return APIResponse(
        data=response_data,
        message="AI safety score generated successfully"
    )
