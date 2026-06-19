import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Intervention, Prediction
from app.auth.utils import get_current_user, require_hod
from app.interventions.schemas import (
    InterventionCreate, InterventionStatusUpdate, InterventionOut, InterventionListOut
)

router = APIRouter(prefix="/interventions", tags=["interventions"])


@router.get("", response_model=InterventionListOut)
def list_interventions(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Intervention)
    if status:
        query = query.filter(Intervention.status == status.upper())
    if priority:
        query = query.filter(Intervention.priority == priority.upper())
    if risk_level:
        query = query.join(Prediction, Intervention.prediction_id == Prediction.id).filter(
            Prediction.risk_level == risk_level.upper()
        )
    total = query.count()
    items = query.order_by(Intervention.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return InterventionListOut(items=items, total=total)


@router.get("/{student_id}", response_model=InterventionListOut)
def get_student_interventions(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(Intervention)
        .filter(Intervention.student_id == student_id)
        .order_by(Intervention.created_at.desc())
        .all()
    )
    return InterventionListOut(items=items, total=len(items))


@router.patch("/{intervention_id}/status", response_model=InterventionOut)
def update_intervention_status(
    intervention_id: uuid.UUID,
    payload: InterventionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_statuses = {"PENDING", "IN_PROGRESS", "COMPLETED", "DISMISSED"}
    if payload.status.upper() not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from {valid_statuses}")

    iv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not iv:
        raise HTTPException(status_code=404, detail="Intervention not found")

    iv.status = payload.status.upper()
    if payload.notes is not None:
        iv.notes = payload.notes
    
    if iv.status == "COMPLETED":
        from datetime import datetime, timezone
        iv.completed_at = datetime.now(timezone.utc)
        if payload.outcome:
            iv.outcome = payload.outcome.upper()
        if payload.outcome_notes:
            iv.outcome_notes = payload.outcome_notes
    else:
        iv.completed_at = None
        iv.outcome = None
        iv.outcome_notes = None

    db.commit()
    db.refresh(iv)
    return iv


@router.post("", response_model=InterventionOut, status_code=201)
def create_intervention(
    payload: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hod),   # HOD / Admin only
):
    """Manually create an intervention. Auto-generated ones come from the prediction pipeline.
    Only HOD or Admin can manually create intervention records."""
    iv = Intervention(**payload.model_dump())
    db.add(iv)
    db.commit()
    db.refresh(iv)
    return iv
