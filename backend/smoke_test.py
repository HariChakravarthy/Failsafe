import urllib.request, json, os

BASE = "http://127.0.0.1:8000"

def post(url, body):
    req = urllib.request.Request(BASE+url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def get(url, token=None):
    req = urllib.request.Request(BASE+url)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

print("=== FAILSAFE FULL SMOKE TEST ===")
print()

# 1. Auth
login = post("/auth/login", {"email": "hod@failsafe.edu", "password": "demo1234"})
token = login["access_token"]
print("1. Login            OK  JWT token received")

# 2. Profile
me = get("/auth/me", token)
print("2. /auth/me         OK  name=" + me["name"] + "  role=" + me["role"])

# 3. Students list
students = get("/students", token)
print("3. /students        OK  total=" + str(students["total"]) + " students in DB")

# 4. Dashboard
try:
    dash = get("/dashboard/summary", token)
    high   = str(dash.get("high_risk", 0))
    medium = str(dash.get("medium_risk", 0))
    low    = str(dash.get("low_risk", 0))
    print("4. /dashboard       OK  HIGH=" + high + "  MEDIUM=" + medium + "  LOW=" + low)
except Exception as e:
    print("4. /dashboard       ERR " + str(e))

# 5. Interventions
try:
    iv = get("/interventions", token)
    print("5. /interventions   OK  total=" + str(iv["total"]))
except Exception as e:
    print("5. /interventions   ERR " + str(e))

# 6. Phase model metrics check
print()
print("--- Phase Model Summary ---")
for phase in [0, 1, 2]:
    path = "ml/models/metrics_phase" + str(phase) + ".json"
    m = json.load(open(path))
    t  = m["test"]
    cv = m["cv"]
    label = m.get("phase_label", "Phase " + str(phase))
    print("  Phase " + str(phase) + ": CV_AUC=" + str(cv["auc"]["mean"])
          + " +/-" + str(cv["auc"]["std"])
          + "  Test_AUC=" + str(t["auc"])
          + "  Recall=" + str(cv["rec"]["mean"])
          + "  Threshold=" + str(t["threshold"]))

# 7. Admin reset is now protected
try:
    req = urllib.request.Request(BASE + "/admin/reset", method="DELETE")
    urllib.request.urlopen(req)
    print()
    print("7. /admin/reset     FAIL - should have been blocked!")
except urllib.error.HTTPError as e:
    print()
    if e.code == 403:
        print("7. /admin/reset     OK  correctly returns 403 for unauthenticated request")
    else:
        print("7. /admin/reset     returned " + str(e.code) + " (expected 403)")

print()
print("=== SMOKE TEST COMPLETE ===")
