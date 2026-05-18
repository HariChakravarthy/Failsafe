import urllib.request
import json

req = urllib.request.Request(
    "http://localhost:8000/auth/login",
    data=json.dumps({"email": "hod@failsafe.edu", "password": "demo1234"}).encode(),
    headers={"Content-Type": "application/json"}
)
token = json.loads(urllib.request.urlopen(req).read().decode())["access_token"]
headers = {"Authorization": f"Bearer {token}"}

req_trends = urllib.request.Request("http://localhost:8000/dashboard/trends", headers=headers)
print("Trends:", urllib.request.urlopen(req_trends).read().decode())
