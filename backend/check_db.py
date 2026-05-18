from app.database import SessionLocal
from app.models import Student, FeatureSnapshot, Prediction

db = SessionLocal()
print("Students:", db.query(Student).count())
print("Snapshots:", db.query(FeatureSnapshot).count())
print("Predictions:", db.query(Prediction).count())

preds = db.query(Prediction).limit(5).all()
for p in preds:
    print(f"Pred: Student {p.student_id}, Risk: {p.risk_level}, Score: {p.risk_score}")
