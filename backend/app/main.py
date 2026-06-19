from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.auth.router import router as auth_router
from app.students.router import router as students_router
from app.predictions.router import router as predictions_router
from app.interventions.router import router as interventions_router
from app.dashboard.router import router as dashboard_router

# Auto-create tables (use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FAILSAFE API",
    description="Early Student Failure Detection & Intervention System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(predictions_router)
app.include_router(interventions_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"message": "Welcome to FAILSAFE API"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "FAILSAFE API"}


@app.delete("/admin/reset")
def reset_data(
    db: "Session" = __import__("fastapi").Depends(__import__("app.database", fromlist=["get_db"]).get_db),
    current_user: "User" = __import__("fastapi").Depends(__import__("app.auth.utils", fromlist=["require_hod"]).require_hod),
):
    """Wipe all student data but keep users. HOD/Admin only."""
    from app.models import Intervention, Prediction, FeatureSnapshot, Student
    db.query(Intervention).delete(synchronize_session=False)
    db.query(Prediction).delete(synchronize_session=False)
    db.query(FeatureSnapshot).delete(synchronize_session=False)
    db.query(Student).delete(synchronize_session=False)
    db.commit()
    return {"message": "All student data cleared. Users retained."}
