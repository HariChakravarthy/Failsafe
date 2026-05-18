import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, Prediction, FeatureSnapshot
from app.auth.utils import get_current_user
from app.predictions.schemas import PredictionOut, RiskTrendOut, RiskTrendPoint

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{student_id}", response_model=PredictionOut)
def get_latest_prediction(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pred = (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )
    if not pred:
        raise HTTPException(status_code=404, detail="No prediction found for this student")
    return pred


@router.get("/{student_id}/history", response_model=RiskTrendOut)
def get_prediction_history(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preds = (
        db.query(Prediction, FeatureSnapshot)
        .join(FeatureSnapshot, Prediction.snapshot_id == FeatureSnapshot.id)
        .filter(Prediction.student_id == student_id)
        .order_by(FeatureSnapshot.week_number.asc())
        .all()
    )
    history = [
        RiskTrendPoint(
            week_number=snap.week_number,
            risk_score=pred.risk_score,
            risk_level=pred.risk_level,
            predicted_at=pred.predicted_at,
        )
        for pred, snap in preds
    ]
    return RiskTrendOut(student_id=student_id, history=history)
