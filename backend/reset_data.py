"""
reset_data.py — Wipe all student data from the FAILSAFE database.

Usage (from project root):
    python backend/reset_data.py

Requires a running backend OR direct DB access via DATABASE_URL in backend/.env
HOD/Admin credentials are required (JWT authentication).
"""
import os
import sys
import json
import urllib.request
import urllib.error

BACKEND_URL = os.getenv("FAILSAFE_URL", "http://localhost:8000")


def get_hod_token(email: str, password: str) -> str:
    """Login and return a JWT access token."""
    payload = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{BACKEND_URL}/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data["access_token"]
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Login failed ({e.code}): {e.read().decode()}")
        sys.exit(1)


def reset_data(token: str) -> None:
    """Call DELETE /admin/reset with HOD auth."""
    req = urllib.request.Request(
        f"{BACKEND_URL}/admin/reset",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"[OK] {data['message']}")
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Reset failed ({e.code}): {e.read().decode()}")
        sys.exit(1)


if __name__ == "__main__":
    print("=== FAILSAFE Data Reset ===")
    print(f"Target: {BACKEND_URL}")
    print()

    email    = input("HOD/Admin email   : ").strip()
    password = input("HOD/Admin password: ").strip()

    confirm = input("\nThis will DELETE all student data (predictions, interventions, snapshots).\nType YES to confirm: ").strip()
    if confirm != "YES":
        print("Aborted.")
        sys.exit(0)

    print("\nLogging in...")
    token = get_hod_token(email, password)
    print("Resetting data...")
    reset_data(token)
