"""Seed demo HOD account directly via database (bypasses API role restriction)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.auth.utils import hash_password


def seed_demo():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "hod@failsafe.edu").first()
        if existing:
            print(f"Demo user already exists: {existing.email} (role={existing.role})")
            return
        user = User(
            name="Demo HOD",
            email="hod@failsafe.edu",
            password_hash=hash_password("demo1234"),
            role="hod",
            department="Computer Science",
        )
        db.add(user)
        db.commit()
        print(f"Created demo user: {user.email} (role={user.role})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
