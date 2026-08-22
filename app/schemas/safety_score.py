"""Safety score response schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.ai.anomaly_types import RiskLevel


class SafetyScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tourist_id: str
    safety_score: float = Field(..., description="Calculated tourist safety score (0-100)")
    risk_level: RiskLevel = Field(..., description="Determined safety risk level")
    anomalies: list[str] = Field(default_factory=list, description="Active anomalies detected")
    recorded_at: datetime
