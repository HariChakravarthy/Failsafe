from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


class StudentCreate(BaseModel):
    student_code: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    faculty_id: Optional[uuid.UUID] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    faculty_id: Optional[uuid.UUID] = None


class StudentOut(BaseModel):
    id: uuid.UUID
    student_code: str
    name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    department: Optional[str]
    semester: Optional[int]
    latest_risk: Optional[str] = None
    faculty_id: Optional[uuid.UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class StudentListOut(BaseModel):
    items: List[StudentOut]
    total: int
    page: int
    size: int


class UploadSummary(BaseModel):
    total_uploaded: int
    high_risk: int
    medium_risk: int
    low_risk: int
    errors: List[str] = []
