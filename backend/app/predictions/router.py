import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, Prediction, FeatureSnapshot
from app.auth.utils import get_current_user
from app.predictions.schemas import PredictionOut, RiskTrendOut, RiskTrendPoint, SimulateRequest, SimulateResponse
from ml.predict import run_simulation

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
    
    snap = db.query(FeatureSnapshot).filter(FeatureSnapshot.id == pred.snapshot_id).first()
    pred.raw_features = snap.raw_features if snap else None
    return pred


@router.post("/{student_id}/simulate", response_model=SimulateResponse)
def simulate_prediction(
    student_id: uuid.UUID,
    payload: SimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find latest feature snapshot for this student
    snap = (
        db.query(FeatureSnapshot)
        .filter(FeatureSnapshot.student_id == student_id)
        .order_by(FeatureSnapshot.uploaded_at.desc())
        .first()
    )
    if not snap or not snap.raw_features:
        raise HTTPException(status_code=404, detail="No feature snapshot found to simulate against")

    # Start with the raw features from the snapshot
    row = dict(snap.raw_features)

    # Apply overrides
    overrides = payload.model_dump(exclude_unset=True)
    for k, v in overrides.items():
        if v is not None:
            row[k] = v

    # Run simulation
    result = run_simulation(row)
    return SimulateResponse(**result)


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
