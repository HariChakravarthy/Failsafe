from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Student, Prediction, Intervention, FeatureSnapshot
from app.auth.utils import get_current_user
from app.dashboard.schemas import (
    DashboardSummary, RiskDistribution, InterventionStats,
    DashboardTrends, WeekTrend,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_students = db.query(Student).count()

    # Latest prediction per student (subquery)
    latest_pred_subq = (
        db.query(
            Prediction.student_id,
            func.max(Prediction.predicted_at).label("max_at"),
        )
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

    high = sum(1 for p in latest_preds if p.risk_level == "HIGH")
    medium = sum(1 for p in latest_preds if p.risk_level == "MEDIUM")
    low = sum(1 for p in latest_preds if p.risk_level == "LOW")
    total_pred = len(latest_preds)

    iv_counts = (
        db.query(Intervention.status, func.count(Intervention.id))
        .group_by(Intervention.status)
        .all()
    )
    iv_map = {row[0]: row[1] for row in iv_counts}

    return DashboardSummary(
        total_students=total_students,
        risk_distribution=RiskDistribution(high=high, medium=medium, low=low, total=total_pred),
        intervention_stats=InterventionStats(
            pending=iv_map.get("PENDING", 0),
            in_progress=iv_map.get("IN_PROGRESS", 0),
            completed=iv_map.get("COMPLETED", 0),
            dismissed=iv_map.get("DISMISSED", 0),
        ),
        high_risk_percentage=round(high / total_pred * 100, 1) if total_pred else 0.0,
    )


@router.get("/trends", response_model=DashboardTrends)
def get_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Simpler approach — pull all and aggregate in Python
    all_pairs = (
        db.query(FeatureSnapshot.week_number, Prediction.risk_score, Prediction.risk_level)
        .join(Prediction, Prediction.snapshot_id == FeatureSnapshot.id)
        .order_by(FeatureSnapshot.week_number)
        .all()
    )

    week_data: dict = {}
    for week_num, risk_score, risk_level in all_pairs:
        if week_num not in week_data:
            week_data[week_num] = {"scores": [], "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        week_data[week_num]["scores"].append(risk_score)
        week_data[week_num][risk_level] = week_data[week_num].get(risk_level, 0) + 1

    weeks = [
        WeekTrend(
            week_number=wk,
            avg_risk_score=round(sum(d["scores"]) / len(d["scores"]), 3),
            high_risk_count=d["HIGH"],
            medium_risk_count=d["MEDIUM"],
            low_risk_count=d["LOW"],
        )
        for wk, d in sorted(week_data.items())
    ]
    return DashboardTrends(weeks=weeks)
