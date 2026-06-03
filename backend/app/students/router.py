import io
import uuid
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, FeatureSnapshot, Prediction
from app.auth.utils import get_current_user, require_hod
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
    from sqlalchemy import func

    query = db.query(Student)
    if search:
        query = query.filter(
            (Student.name.ilike(f"%{search}%")) | (Student.student_code.ilike(f"%{search}%"))
        )
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()

    # Single subquery to fetch latest prediction per student — avoids N+1
    student_ids = [s.id for s in items]
    if student_ids:
        latest_pred_subq = (
            db.query(
                Prediction.student_id,
                func.max(Prediction.predicted_at).label("max_at"),
            )
            .filter(Prediction.student_id.in_(student_ids))
            .group_by(Prediction.student_id)
            .subquery()
        )
        latest_preds = (
            db.query(Prediction)
            .join(
                latest_pred_subq,
                (Prediction.student_id == latest_pred_subq.c.student_id)
                & (Prediction.predicted_at == latest_pred_subq.c.max_at),
            )
            .all()
        )
        risk_map = {str(p.student_id): p.risk_level for p in latest_preds}
    else:
        risk_map = {}

    for student in items:
        student.latest_risk = risk_map.get(str(student.id))

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


@router.get("/{student_id}/report")
def download_student_report(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import Response
    from app.models import Prediction, Intervention
    from app.students.report import generate_student_report

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    prediction = db.query(Prediction).filter(Prediction.student_id == student_id).order_by(Prediction.predicted_at.desc()).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="No prediction snapshot available for this student")

    interventions = db.query(Intervention).filter(Intervention.student_id == student_id).order_by(Intervention.created_at.desc()).all()

    pdf_bytes = generate_student_report(student, prediction, interventions)

    filename = f"{student.student_code}_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


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
    current_user: User = Depends(require_hod),   # HOD / Admin only
):
    from app.models import FeatureSnapshot, Prediction, Intervention
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # Cascade delete manually
    db.query(Intervention).filter(Intervention.student_id == student_id).delete()
    db.query(Prediction).filter(Prediction.student_id == student_id).delete()
    db.query(FeatureSnapshot).filter(FeatureSnapshot.student_id == student_id).delete()
    db.delete(student)
    db.commit()


@router.post("/upload", response_model=UploadSummary)
async def upload_csv(
    file: UploadFile = File(...),
    week_number: int = Query(1, ge=1),
    phase: int = Query(0, ge=0, le=2, description="Prediction phase: 0=before G1, 1=after G1, 2=after G1+G2"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a CSV of student features; triggers batch prediction for each student.

    Phase controls which model is used:
      0 = Before Term 1 exams  — behavioural features only (30 features)
      1 = After  Term 1 exams  — adds G1 first period grade  (31 features)
      2 = After  Term 2 exams  — adds G1 + G2 period grades  (32 features)
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        # Auto-detect delimiter: UCI files use ';', most exports use ','
        sample = content[:2048].decode("utf-8", errors="ignore")
        import csv as _csv
        try:
            dialect = _csv.Sniffer().sniff(sample, delimiters=";,")
            sep = dialect.delimiter
        except Exception:
            sep = ","  # fallback
        df = pd.read_csv(io.BytesIO(content), sep=sep)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    # student_code is optional — auto-generate from row index if absent
    if "student_code" not in df.columns:
        df["student_code"] = [f"S{str(i+1).zfill(4)}" for i in range(len(df))]

    required_cols = {"absences", "studytime", "failures"}
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

            prediction = run_prediction_pipeline(row.to_dict(), student.id, snapshot.id, db, phase=phase)
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
