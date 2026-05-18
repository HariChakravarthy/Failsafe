import io
import uuid
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, FeatureSnapshot, Prediction
from app.auth.utils import get_current_user
from app.students.schemas import StudentCreate, StudentUpdate, StudentOut, StudentListOut, UploadSummary
from ml.predict import run_prediction_pipeline

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=StudentListOut)
def list_students(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Student)
    if search:
        query = query.filter(
            (Student.name.ilike(f"%{search}%")) | (Student.student_code.ilike(f"%{search}%"))
        )
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    for student in items:
        pred = db.query(Prediction).filter(Prediction.student_id == student.id).order_by(Prediction.predicted_at.desc()).first()
        student.latest_risk = pred.risk_level if pred else None
    return StudentListOut(items=items, total=total, page=page, size=size)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    pred = db.query(Prediction).filter(Prediction.student_id == student.id).order_by(Prediction.predicted_at.desc()).first()
    student.latest_risk = pred.risk_level if pred else None
    return student


@router.post("", response_model=StudentOut, status_code=201)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Student).filter(Student.student_code == payload.student_code).first():
        raise HTTPException(status_code=400, detail="Student code already exists")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models import FeatureSnapshot, Prediction, Intervention
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # Cascade delete manually
    snap_ids = [s.id for s in db.query(FeatureSnapshot).filter(FeatureSnapshot.student_id == student_id).all()]
    pred_ids = [p.id for p in db.query(Prediction).filter(Prediction.student_id == student_id).all()]
    db.query(Intervention).filter(Intervention.student_id == student_id).delete()
    db.query(Prediction).filter(Prediction.student_id == student_id).delete()
    db.query(FeatureSnapshot).filter(FeatureSnapshot.student_id == student_id).delete()
    db.delete(student)
    db.commit()


@router.post("/upload", response_model=UploadSummary)
async def upload_csv(
    file: UploadFile = File(...),
    week_number: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a CSV of student features; triggers batch prediction for each student."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    required_cols = {"student_code", "absences", "studytime", "failures"}
    missing = required_cols - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")

    summary = UploadSummary(total_uploaded=0, high_risk=0, medium_risk=0, low_risk=0)
    errors = []

    for _, row in df.iterrows():
        try:
            student = db.query(Student).filter(Student.student_code == str(row["student_code"])).first()
            if not student:
                student = Student(
                    student_code=str(row["student_code"]),
                    name=row.get("name"),
                    age=int(row["age"]) if "age" in row and pd.notna(row["age"]) else None,
                    gender=row.get("sex"),
                    faculty_id=current_user.id,
                )
                db.add(student)
                db.flush()

            snapshot = FeatureSnapshot(
                student_id=student.id,
                week_number=week_number,
                absences=int(row.get("absences", 0)),
                studytime=int(row.get("studytime", 1)),
                failures=int(row.get("failures", 0)),
                raw_features=row.dropna().to_dict(),
            )
            db.add(snapshot)
            db.flush()

            prediction = run_prediction_pipeline(row.to_dict(), student.id, snapshot.id, db)
            if prediction:
                student.latest_risk = prediction.risk_level
                if prediction.risk_level == "HIGH":
                    summary.high_risk += 1
                elif prediction.risk_level == "MEDIUM":
                    summary.medium_risk += 1
                else:
                    summary.low_risk += 1
                summary.total_uploaded += 1
        except Exception as e:
            errors.append(f"Row {row.get('student_code', '?')}: {e}")

    db.commit()
    summary.errors = errors
    return summary
