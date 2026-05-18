import urllib.request
import json

data = json.dumps({
    "name": "Demo HOD",
    "email": "hod@failsafe.edu",
    "password": "demo1234",
    "role": "hod",
    "department": "Computer Science"
}).encode('utf-8')

req = urllib.request.Request("http://localhost:8000/auth/register", data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as response:
        print(response.getcode())
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode('utf-8'))
