import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # faculty | hod | admin
    department = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    students = relationship("Student", back_populates="faculty")
    assigned_interventions = relationship("Intervention", back_populates="assigned_user")


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_code = Column(String(30), unique=True, nullable=False)
    name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(10))
    department = Column(String(100))
    semester = Column(Integer)
    faculty_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    faculty = relationship("User", back_populates="students")
    feature_snapshots = relationship("FeatureSnapshot", back_populates="student")
    predictions = relationship("Prediction", back_populates="student")
    interventions = relationship("Intervention", back_populates="student")


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    week_number = Column(Integer)
    absences = Column(Integer)
    studytime = Column(Integer)
    failures = Column(Integer)
    raw_features = Column(JSON)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    student = relationship("Student", back_populates="feature_snapshots")
    predictions = relationship("Prediction", back_populates="snapshot")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("feature_snapshots.id"))
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False)  # HIGH | MEDIUM | LOW
    shap_values = Column(JSON, nullable=False)
    shap_summary = Column(Text)
    predicted_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    student = relationship("Student", back_populates="predictions")
    snapshot = relationship("FeatureSnapshot", back_populates="predictions")
    interventions = relationship("Intervention", back_populates="prediction")


class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"))
    type = Column(String(50), nullable=False)
    priority = Column(String(20))
    title = Column(String(200))
    description = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    due_date = Column(Date)
    status = Column(String(20), default="PENDING")  # PENDING | IN_PROGRESS | COMPLETED | DISMISSED
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="interventions")
    prediction = relationship("Prediction", back_populates="interventions")
    assigned_user = relationship("User", back_populates="assigned_interventions")
