import sys
sys.path.insert(0, '.')
from ml.predict import run_simulation

base_row = {
    'absences': 17, 'studytime': 4, 'failures': 1,
    'goout': 4, 'health': 5, 'famrel': 3,
    'Dalc': 1, 'age': 17, 'Medu': 2, 'Fedu': 2,
    'traveltime': 1, 'freetime': 3,
    'school': 'GP', 'sex': 'M', 'address': 'U',
    'famsize': 'GT3', 'Pstatus': 'T',
    'Mjob': 'other', 'Fjob': 'other', 'reason': 'course',
    'guardian': 'mother', 'schoolsup': 'no', 'famsup': 'yes',
    'paid': 'no', 'activities': 'yes', 'nursery': 'yes',
    'higher': 'yes', 'internet': 'yes', 'romantic': 'no',
}

print("=== MONOTONE CONSTRAINT VERIFICATION ===\n")

# 1. Walc decreasing should NEVER increase risk
print("TEST 1: Walc decreasing -> risk must decrease or stay same")
prev = 1.0
passed = True
for walc_val, label in [(5, "Very High"), (4, "High"), (3, "Medium"), (2, "Low"), (1, "Very Low")]:
    row = dict(base_row); row['Walc'] = walc_val
    r = run_simulation(row, phase=0)
    score = r['risk_score']
    flag = "" if score <= prev + 0.001 else "  !! VIOLATION"
    if score > prev + 0.001:
        passed = False
    print("  Walc=" + str(walc_val) + " (" + label + "): " + str(round(score, 4)) + "  " + r['risk_level'] + flag)
    prev = score
print("  Result:", "PASS" if passed else "FAIL")

print()

# 2. Absences increasing should NEVER decrease risk
print("TEST 2: Absences increasing -> risk must increase or stay same")
prev = 0.0
passed = True
for abs_val in [0, 5, 10, 17, 25, 40, 60]:
    row = dict(base_row); row['absences'] = abs_val; row['Walc'] = 3
    r = run_simulation(row, phase=0)
    score = r['risk_score']
    flag = "" if score >= prev - 0.001 else "  !! VIOLATION"
    if score < prev - 0.001:
        passed = False
    print("  absences=" + str(abs_val) + ": " + str(round(score, 4)) + "  " + r['risk_level'] + flag)
    prev = score
print("  Result:", "PASS" if passed else "FAIL")

print()

# 3. Studytime increasing should NEVER increase risk
print("TEST 3: Studytime increasing -> risk must decrease or stay same")
prev = 1.0
passed = True
for st_val in [1, 2, 3, 4]:
    labels = {1: "<2hrs", 2: "2-5hrs", 3: "5-10hrs", 4: ">10hrs"}
    row = dict(base_row); row['studytime'] = st_val; row['Walc'] = 3
    r = run_simulation(row, phase=0)
    score = r['risk_score']
    flag = "" if score <= prev + 0.001 else "  !! VIOLATION"
    if score > prev + 0.001:
        passed = False
    print("  studytime=" + str(st_val) + " (" + labels[st_val] + "): " + str(round(score, 4)) + "  " + r['risk_level'] + flag)
    prev = score
print("  Result:", "PASS" if passed else "FAIL")

print()

# 4. G1 increasing should NEVER increase risk (Phase 2)
print("TEST 4: G1 increasing -> risk must decrease or stay same (Phase 2)")
prev = 1.0
passed = True
for g1_val in [2, 5, 8, 11, 14, 17, 20]:
    row = dict(base_row); row['Walc'] = 3; row['G1'] = g1_val; row['G2'] = 10
    r = run_simulation(row, phase=2)
    score = r['risk_score']
    flag = "" if score <= prev + 0.001 else "  !! VIOLATION"
    if score > prev + 0.001:
        passed = False
    print("  G1=" + str(g1_val) + ": " + str(round(score, 4)) + "  " + r['risk_level'] + flag)
    prev = score
print("  Result:", "PASS" if passed else "FAIL")

print()

# 5. failures increasing should NEVER decrease risk
print("TEST 5: failures increasing -> risk must increase or stay same")
prev = 0.0
passed = True
for f_val in [0, 1, 2, 3]:
    row = dict(base_row); row['failures'] = f_val; row['Walc'] = 3
    r = run_simulation(row, phase=0)
    score = r['risk_score']
    flag = "" if score >= prev - 0.001 else "  !! VIOLATION"
    if score < prev - 0.001:
        passed = False
    print("  failures=" + str(f_val) + ": " + str(round(score, 4)) + "  " + r['risk_level'] + flag)
    prev = score
print("  Result:", "PASS" if passed else "FAIL")

print("\n=== ALL DONE ===")
