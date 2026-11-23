"""
One command to build everything on your laptop:
  1. generate dataset  ->  data/transit_data.csv
  2. run MapReduce     ->  output/*.txt
  3. load SQL database ->  database/transit.db

Usage: python run_all.py            (then: python backend/app.py)
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(ROOT, "data", "transit_data.csv")
py = sys.executable

steps = [
    ("Generating dataset", [py, os.path.join(ROOT, "data", "generate_data.py"), "100000", CSV]),
    ("Running MapReduce jobs", [py, os.path.join(ROOT, "mapreduce", "run_local.py"), CSV]),
    ("Loading SQL database", [py, os.path.join(ROOT, "database", "load_db.py"), CSV]),
]

for title, cmd in steps:
    print(f"\n==== {title} ====")
    subprocess.run(cmd, check=True)

print("\nAll done! Now start the backend:  python backend/app.py")
print("Then open http://localhost:5000")
