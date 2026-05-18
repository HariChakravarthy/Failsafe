import urllib.request
import json

# Login
req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "hod@failsafe.edu", "password": "demo1234"}).encode(),
    headers={"Content-Type": "application/json"}
)
token = json.loads(urllib.request.urlopen(req).read().decode())["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get Summary
req_sum = urllib.request.Request("http://localhost:8000/dashboard/summary", headers=headers)
summary = urllib.request.urlopen(req_sum).read().decode()
print("Summary:", summary)

# Get Students
req_stu = urllib.request.Request("http://localhost:8000/students?size=5", headers=headers)
students = urllib.request.urlopen(req_stu).read().decode()
print("\nStudents:", students)
