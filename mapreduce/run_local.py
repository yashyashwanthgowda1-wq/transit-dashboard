"""
Runs the SAME mapper.py and reducer.py without Hadoop, by imitating
what Hadoop Streaming does:  cat input | mapper | sort | reducer

Use this for testing or if Hadoop isn't installed on your laptop.
Usage: python mapreduce/run_local.py data/transit_data.csv
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INPUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "transit_data.csv")
OUT_DIR = os.path.join(ROOT, "output")

JOBS = [("hourly", "sum"), ("route", "sum"), ("revenue", "sum"),
        ("stop", "sum"), ("day", "sum"), ("daily", "sum"), ("delay", "avg")]

os.makedirs(OUT_DIR, exist_ok=True)
py = sys.executable

for job, mode in JOBS:
    # MAP phase
    with open(INPUT) as f:
        mapped = subprocess.run([py, os.path.join(HERE, "mapper.py"), job],
                                stdin=f, capture_output=True, text=True,
                                check=True).stdout
    # SHUFFLE & SORT phase (Hadoop sorts by key)
    shuffled = "\n".join(sorted(mapped.splitlines(),
                                key=lambda l: l.split("\t", 1)[0])) + "\n"
    # REDUCE phase
    reduced = subprocess.run([py, os.path.join(HERE, "reducer.py"), mode],
                             input=shuffled, capture_output=True, text=True,
                             check=True).stdout
    with open(os.path.join(OUT_DIR, f"{job}.txt"), "w") as out:
        out.write(reduced)
    print(f"[done] {job:8s} -> output/{job}.txt ({len(reduced.splitlines())} keys)")

print("All jobs finished.")
