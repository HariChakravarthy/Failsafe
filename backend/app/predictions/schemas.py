from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


class SimulateRequest(BaseModel):
    absences: Optional[int] = None
    studytime: Optional[int] = None
    failures: Optional[int] = None
    Walc: Optional[int] = None
    goout: Optional[int] = None
    health: Optional[int] = None


class SimulateResponse(BaseModel):
    risk_score: float
    risk_level: str
    shap_values: Dict[str, float]
    shap_summary: Optional[str]



class PredictionOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    snapshot_id: uuid.UUID
    risk_score: float
    risk_level: str
    shap_values: Dict[str, float]
    shap_summary: Optional[str]
    raw_features: Optional[Dict[str, Any]] = None
    predicted_at: datetime

    class Config:
        from_attributes = True


class RiskTrendPoint(BaseModel):
    week_number: int
    risk_score: float
    risk_level: str
    predicted_at: datetime


class RiskTrendOut(BaseModel):
    student_id: uuid.UUID
    history: List[RiskTrendPoint]
