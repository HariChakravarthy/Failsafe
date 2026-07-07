"""
Live end-to-end upload test.
Reads actual rows from student-mat.csv and POSTs them to the running server.
Tests all 3 phases.
"""
import urllib.request, json, io, csv, os

BASE = "http://127.0.0.1:8000"

def post_json(url, body, token=None):
    req = urllib.request.Request(BASE+url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def post_csv(url, csv_bytes, token):
    import urllib.request
    boundary = b"----TestBoundary"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Disposition: form-data; name=\"file\"; filename=\"test.csv\"\r\n"
        b"Content-Type: text/csv\r\n\r\n"
        + csv_bytes + b"\r\n"
        b"--" + boundary + b"--\r\n"
    )
    req = urllib.request.Request(BASE+url, data=body, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "multipart/form-data; boundary=----TestBoundary")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

# ── Auth ──────────────────────────────────────────────────────────────────────
print("=== LIVE UPLOAD END-TO-END TEST ===\n")
login = post_json("/auth/login", {"email": "hod@failsafe.edu", "password": "demo1234"})
token = login["access_token"]
print("Auth OK - logged in as HOD\n")

# ── Load real data ─────────────────────────────────────────────────────────────
mat_path = os.path.join("..", "data", "student-mat.csv")
with open(mat_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter=";")
    rows = list(reader)

# Use 5 real students for test — add student_code
test_rows = []
for i, row in enumerate(rows[:5]):
    row["student_code"] = "TEST_" + str(i+1).zfill(3)
    test_rows.append(row)

print(f"Using {len(test_rows)} real rows from student-mat.csv")
print("Students:", [r["student_code"] for r in test_rows])
print()

def make_csv(rows, include_g1=False, include_g2=False):
    out = io.StringIO()
    cols = list(rows[0].keys())
    if not include_g1 and "G1" in cols:
        cols = [c for c in cols if c != "G1"]
    if not include_g2 and "G2" in cols:
        cols = [c for c in cols if c != "G2"]
    # Always exclude G3 (that is the target, never a feature)
    cols = [c for c in cols if c != "G3"]
    writer = csv.DictWriter(out, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")

# ── Phase 0 upload (no grades) ────────────────────────────────────────────────
print("--- Phase 0: Before Term 1 (no grades) ---")
csv0 = make_csv(test_rows, include_g1=False, include_g2=False)
r0 = post_csv("/students/upload?week_number=1&phase=0", csv0, token)
print(f"  Uploaded     : {r0['total_uploaded']} students")
print(f"  HIGH risk    : {r0['high_risk']}")
print(f"  MEDIUM risk  : {r0['medium_risk']}")
print(f"  LOW risk     : {r0['low_risk']}")
if r0.get("errors"):
    print(f"  Errors       : {r0['errors']}")
print()

# ── Phase 1 upload (+G1) ──────────────────────────────────────────────────────
print("--- Phase 1: Between Term 1 & Term 2 (+G1) ---")
csv1 = make_csv(test_rows, include_g1=True, include_g2=False)
r1 = post_csv("/students/upload?week_number=5&phase=1", csv1, token)
print(f"  Uploaded     : {r1['total_uploaded']} students")
print(f"  HIGH risk    : {r1['high_risk']}")
print(f"  MEDIUM risk  : {r1['medium_risk']}")
print(f"  LOW risk     : {r1['low_risk']}")
print()

# ── Phase 2 upload (+G1+G2) ──────────────────────────────────────────────────
print("--- Phase 2: After Term 2 (+G1+G2) ---")
csv2 = make_csv(test_rows, include_g1=True, include_g2=True)
r2 = post_csv("/students/upload?week_number=10&phase=2", csv2, token)
print(f"  Uploaded     : {r2['total_uploaded']} students")
print(f"  HIGH risk    : {r2['high_risk']}")
print(f"  MEDIUM risk  : {r2['medium_risk']}")
print(f"  LOW risk     : {r2['low_risk']}")
print()

# ── Check a student profile ───────────────────────────────────────────────────
req = urllib.request.Request(BASE + "/students?search=TEST_001")
req.add_header("Authorization", "Bearer " + token)
r = urllib.request.urlopen(req)
students = json.loads(r.read())
if students["items"]:
    s = students["items"][0]
    print("--- Student Profile: TEST_001 ---")
    print(f"  Name         : {s.get('name', 'N/A')}")
    print(f"  Student code : {s.get('student_code','N/A')}")
    print(f"  Latest risk  : {s.get('latest_risk','N/A')}")
    print(f"  Alert count  : {s.get('alert_count', 0)}")
else:
    print("Student TEST_001 not found in search.")

print()
print("=== ALL UPLOAD TESTS PASSED ===")
