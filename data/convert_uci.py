"""
Converts UCI student-mat.csv and student-por.csv into FAILSAFE upload format.
- Switches separator from semicolon (;) to comma (,)
- Adds student_code column (e.g. SMAT001, SPOR001)
- Adds a placeholder name column
Output files: student-mat_upload.csv, student-por_upload.csv
"""
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

files = [
    ("student-mat.csv", "SMAT"),
    ("student-por.csv", "SPOR"),
]

for filename, prefix in files:
    input_path = os.path.join(script_dir, filename)
    output_path = os.path.join(script_dir, filename.replace(".csv", "_upload.csv"))

    # Read with semicolon separator (UCI format)
    df = pd.read_csv(input_path, sep=";")

    # Add student_code as first column
    df.insert(0, "student_code", [f"{prefix}{str(i+1).zfill(3)}" for i in range(len(df))])

    # Add name column as second column
    df.insert(1, "name", [f"Student {i+1}" for i in range(len(df))])

    # Save as comma-separated (FAILSAFE upload format)
    df.to_csv(output_path, index=False)

    print(f"✅ Created: {output_path}")
    print(f"   Rows   : {len(df)}")
    print(f"   Columns: {list(df.columns[:8])} ...")
    print()
