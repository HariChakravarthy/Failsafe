"""
Rule-based intervention engine.
Reads SHAP values from a prediction and generates a catalogue of
personalised intervention plans for the student.
"""
from datetime import date, timedelta
from typing import List, Dict, Any
import uuid
from sqlalchemy.orm import Session
from app.models import Intervention, Prediction


# ── Catalogue ────────────────────────────────────────────────────────────────
CATALOGUE = [
    {
        "feature": "absences",
        "shap_threshold": 0.3,
        "type": "ATTENDANCE_REVIEW",
        "priority": "URGENT",
        "title": "Mandatory Attendance Review",
        "description": (
            "Student's absence rate is a primary risk factor. "
            "Schedule a one-on-one meeting immediately and notify parent/guardian."
        ),
        "due_within_days": 3,
    },
    {
        "feature": "failures",
        "shap_threshold": 0.25,
        "type": "ACADEMIC_COUNSELLING",
        "priority": "HIGH",
        "title": "Academic Counselling Referral",
        "description": (
            "History of past class failures is significantly increasing risk. "
            "Refer student to academic counsellor for structured support plan."
        ),
        "due_within_days": 5,
    },
    {
        "feature": "studytime",
        "shap_threshold": 0.2,
        "type": "STUDY_PLAN",
        "priority": "HIGH",
        "title": "Personalised Study Plan + Peer Mentoring",
        "description": (
            "Low study time is a key risk driver. "
            "Assign a peer mentor and provide a weekly structured study schedule."
        ),
        "due_within_days": 7,
    },
    {
        "feature": "Walc",
        "shap_threshold": 0.15,
        "type": "WELLNESS_REFERRAL",
        "priority": "MEDIUM",
        "title": "Wellness Counsellor Referral",
        "description": (
            "Weekend alcohol consumption is contributing to risk. "
            "Refer student to the wellness counsellor for a confidential session."
        ),
        "due_within_days": 10,
    },
    {
        "feature": "Dalc",
        "shap_threshold": 0.15,
        "type": "WELLNESS_REFERRAL",
        "priority": "MEDIUM",
        "title": "Wellness Counsellor Referral",
        "description": (
            "Workday alcohol consumption is contributing to risk. "
            "Refer student to the wellness counsellor for a confidential session."
        ),
        "due_within_days": 10,
    },
    {
        "feature": "famsup",
        "shap_threshold": 0.12,
        "type": "MENTOR_ASSIGNMENT",
        "priority": "MEDIUM",
        "title": "Faculty Mentor Assignment",
        "description": (
            "Lack of family educational support is a risk factor. "
            "Assign a faculty mentor to provide additional guidance and check-ins."
        ),
        "due_within_days": 7,
    },
    {
        "feature": "health",
        "shap_threshold": 0.12,
        "type": "HEALTH_REFERRAL",
        "priority": "MEDIUM",
        "title": "Medical / Wellness Check",
        "description": (
            "Health issues are impacting academic performance. "
            "Refer student to the campus health centre for a check-up."
        ),
        "due_within_days": 7,
    },
    {
        "feature": "goout",
        "shap_threshold": 0.1,
        "type": "TIME_MANAGEMENT",
        "priority": "LOW",
        "title": "Time Management Workshop",
        "description": (
            "Frequent social outings are contributing to lower study time. "
            "Recommend the next available time management workshop."
        ),
        "due_within_days": 14,
    },
    {
        "feature": "romantic",
        "shap_threshold": 0.08,
        "type": "PERSONAL_COUNSELLING",
        "priority": "LOW",
        "title": "Personal Counsellor Note",
        "description": (
            "Relationship status may be affecting focus. "
            "A personal counsellor note is suggested — student discretion applies."
        ),
        "due_within_days": 14,
    },
    {
        "feature": "internet",
        "shap_threshold": -0.05,  # negative SHAP = missing internet hurts
        "type": "RESOURCE_ACCESS",
        "priority": "LOW",
        "title": "Library / Computer Lab Access Guidance",
        "description": (
            "Student lacks home internet access, limiting study resources. "
            "Provide information about library and computer lab schedules."
        ),
        "due_within_days": 5,
    },
]


def generate_interventions(
    prediction: Prediction,
    assigned_to_id: uuid.UUID,
    db: Session,
) -> List[Intervention]:
    """
    Given a Prediction object (with shap_values as a dict), generate and
    persist Intervention records according to the catalogue rules.
    Returns the list of created Intervention ORM objects.
    """
    shap: Dict[str, float] = prediction.shap_values or {}
    created: List[Intervention] = []
    today = date.today()

    # Deduplicate by type (e.g. Walc + Dalc both trigger WELLNESS_REFERRAL)
    seen_types: set = set()

    for rule in CATALOGUE:
        feature = rule["feature"]
        value = shap.get(feature, 0.0)
        threshold = rule["shap_threshold"]

        triggered = (threshold >= 0 and value >= threshold) or \
                    (threshold < 0 and value <= threshold)

        if not triggered:
            continue

        if rule["type"] in seen_types:
            continue
        seen_types.add(rule["type"])

        intervention = Intervention(
            student_id=prediction.student_id,
            prediction_id=prediction.id,
            type=rule["type"],
            priority=rule["priority"],
            title=rule["title"],
            description=rule["description"],
            assigned_to=assigned_to_id,
            due_date=today + timedelta(days=rule["due_within_days"]),
            status="PENDING",
        )
        db.add(intervention)
        created.append(intervention)

    return created
