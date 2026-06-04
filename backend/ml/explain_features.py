import pandas as pd, numpy as np, joblib, json, sys
sys.path.insert(0, '.')
from ml.preprocess import PHASE_FEATURES, preprocess_dataframe

df = pd.read_csv('../data/student-mat.csv', sep=';')
features = PHASE_FEATURES[0]

descriptions = {
    'school':     'Which school: GP or MS',
    'sex':        'Gender: M or F',
    'address':    'Home: U=Urban, R=Rural',
    'famsize':    'Family size: LE3 (<=3) or GT3 (>3)',
    'Pstatus':    'Parents: T=Together, A=Apart',
    'Mjob':       'Mother job: teacher/health/services/at_home/other',
    'Fjob':       'Father job: teacher/health/services/at_home/other',
    'reason':     'Why chose school: home/reputation/course/other',
    'guardian':   'Guardian: mother/father/other',
    'schoolsup':  'Extra school support: yes/no',
    'famsup':     'Family educational support: yes/no',
    'paid':       'Extra paid classes: yes/no',
    'activities': 'Extra-curricular activities: yes/no',
    'nursery':    'Attended nursery school: yes/no',
    'higher':     'Wants higher education: yes/no',
    'internet':   'Internet at home: yes/no',
    'romantic':   'In a romantic relationship: yes/no',
    'age':        'Age (15-22)',
    'Medu':       'Mother education: 0=none to 4=higher degree',
    'Fedu':       'Father education: 0=none to 4=higher degree',
    'traveltime': 'Travel time to school: 1(<15min) to 4(>1hr)',
    'studytime':  'Weekly study time: 1(<2hrs) to 4(>10hrs)',
    'failures':   'Past class failures: 0,1,2,3',
    'famrel':     'Family relationship quality: 1(very bad) to 5(excellent)',
    'freetime':   'Free time after school: 1(low) to 5(very high)',
    'goout':      'Going out with friends: 1(low) to 5(very high)',
    'Dalc':       'Workday alcohol: 1(low) to 5(very high)',
    'Walc':       'Weekend alcohol: 1(low) to 5(very high)',
    'health':     'Health status: 1(very bad) to 5(very good)',
    'absences':   'School absences count (0-93)',
}

groups = {
    'CATEGORICAL (17 features)': ['school','sex','address','famsize','Pstatus','Mjob','Fjob','reason','guardian','schoolsup','famsup','paid','activities','nursery','higher','internet','romantic'],
    'NUMERIC - Socio-demographic (3 features)': ['age','Medu','Fedu'],
    'NUMERIC - Academic behaviour (3 features)': ['traveltime','studytime','failures'],
    'NUMERIC - Social & Lifestyle (4 features)': ['famrel','freetime','goout','Dalc','Walc','health'],
    'NUMERIC - Attendance (1 feature)': ['absences'],
}

print("=" * 65)
print("  ALL 30 PHASE-0 FEATURES")
print("=" * 65)
for grp, flist in groups.items():
    print(f"\n--- {grp} ---")
    for f in flist:
        if f in df.columns:
            vals = sorted(df[f].unique().tolist())
            if len(vals) <= 8:
                val_str = str(vals)
            else:
                val_str = "range " + str(int(df[f].min())) + "-" + str(int(df[f].max()))
            print(f"  {f:<14} {val_str}")
            print(f"               {descriptions.get(f,'')}")

print()
print("=" * 65)
print("  HOW XGBOOST SCORES EACH STUDENT")
print("=" * 65)
model  = joblib.load('ml/models/model_phase0.pkl')
scaler = joblib.load('ml/models/scaler_phase0.pkl')
threshold = json.load(open('ml/models/threshold_phase0.json'))['threshold']

X = preprocess_dataframe(df, phase=0)
X_s = scaler.transform(X)
probs = model.predict_proba(X_s)[:, 1]
df_out = df[['absences','studytime','failures','Walc','Dalc','goout','G3']].copy()
df_out['risk_score'] = probs.round(3)
df_out['at_risk_pred'] = (probs >= threshold).astype(int)
df_out['actually_failed'] = (df['G3'] < 10).astype(int)

print("\nSample of 15 students - showing key features + model score:")
print(df_out.head(15).to_string())

print()
print("Correlation of each feature with at-risk label (G3<10):")
y = (df['G3'] < 10).astype(int)
for f in ['absences','failures','studytime','Walc','Dalc','goout','famrel','higher','internet']:
    if f in df.columns:
        if df[f].dtype == object:
            enc = (df[f].str.lower() == 'no').astype(int)
        else:
            enc = df[f]
        corr = enc.corr(y)
        direction = "HIGHER = MORE RISK" if corr > 0 else "HIGHER = LESS RISK"
        print(f"  {f:<14} corr={corr:+.3f}  <- {direction}")

print()
print("Feature importance from trained model (top 10):")
importances = model.feature_importances_
features_ohe = json.load(open('ml/models/features_phase0.json'))['features']
feat_imp = sorted(zip(features_ohe, importances), key=lambda x: x[1], reverse=True)
for f, imp in feat_imp[:10]:
    bar = "#" * int(imp * 300)
    print(f"  {f:<14} {imp:.4f}  {bar}")
