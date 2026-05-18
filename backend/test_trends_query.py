from app.database import SessionLocal
from app.models import FeatureSnapshot, Prediction
import traceback

try:
    db = SessionLocal()
    res = (
        db.query(FeatureSnapshot.week_number, Prediction.risk_score, Prediction.risk_level)
        .join(Prediction, Prediction.snapshot_id == FeatureSnapshot.id)
        .order_by(FeatureSnapshot.week_number)
        .all()
    )
    print("Success:", len(res))
except Exception as e:
    traceback.print_exc()
