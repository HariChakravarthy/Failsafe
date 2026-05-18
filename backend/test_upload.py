import urllib.request
import urllib.parse
import json

# 1. Login
data = json.dumps({"email": "hod@failsafe.edu", "password": "demo1234"}).encode("utf-8")
req = urllib.request.Request("http://localhost:8000/auth/login", data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    token = json.loads(response.read().decode())["access_token"]

# 2. Upload sample_upload.csv
import email.message
import mimetypes
import uuid

boundary = uuid.uuid4().hex
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": f"multipart/form-data; boundary={boundary}"
}

with open("data/sample_upload.csv", "rb") as f:
    csv_data = f.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="sample_upload.csv"\r\n'
    f"Content-Type: text/csv\r\n\r\n"
).encode('utf-8') + csv_data + f"\r\n--{boundary}\r\n".encode('utf-8') + (
    f'Content-Disposition: form-data; name="week_number"\r\n\r\n1\r\n'
    f"--{boundary}--\r\n"
).encode('utf-8')

req2 = urllib.request.Request("http://localhost:8000/students/upload", data=body, headers=headers)
try:
    with urllib.request.urlopen(req2) as res2:
        print("Upload success:", res2.read().decode())
except urllib.error.HTTPError as e:
    print("Upload failed:", e.code, e.read().decode())
