from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import date, datetime


class InterventionCreate(BaseModel):
    student_id: uuid.UUID
    prediction_id: Optional[uuid.UUID] = None
    type: str
    priority: Optional[str] = None
    title: str
    description: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    due_date: Optional[date] = None


class InterventionStatusUpdate(BaseModel):
    status: str  # PENDING | IN_PROGRESS | COMPLETED | DISMISSED
    notes: Optional[str] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None


class InterventionOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    prediction_id: Optional[uuid.UUID]
    type: str
    priority: Optional[str]
    title: str
    description: Optional[str]
    assigned_to: Optional[uuid.UUID]
    due_date: Optional[date]
    status: str
    notes: Optional[str]
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterventionListOut(BaseModel):
    items: List[InterventionOut]
    total: int

