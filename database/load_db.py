"""
Loads the dataset and the MapReduce results into the SQL database.

Steps:
 1. Create tables from schema.sql
 2. Insert raw trips from the CSV into `trips`
 3. Insert each MapReduce output (output/*.txt) into its result table

Usage: python database/load_db.py data/transit_data.csv
"""
import csv
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB_PATH = os.path.join(HERE, "transit.db")
OUTPUT_DIR = os.path.join(ROOT, "output")
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "transit_data.csv")

DAY_ORDER = {d: i for i, d in enumerate(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])}


def read_output(job):
    rows = []
    with open(os.path.join(OUTPUT_DIR, f"{job}.txt")) as f:
        for line in f:
            if "\t" in line:
                k, v = line.rstrip("\n").split("\t", 1)
                rows.append((k, float(v)))
    return rows


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Schema
    with open(os.path.join(HERE, "schema.sql")) as f:
        cur.executescript(f.read())
    print("[ok] tables created")

    # 2. Raw trips
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        rows = [(r["trip_id"], r["date"], r["day_of_week"], int(r["hour"]),
                 r["route_id"], r["stop_name"], int(r["passengers"]),
                 float(r["fare"]), int(r["delay_min"])) for r in reader]
    cur.executemany("INSERT INTO trips VALUES (?,?,?,?,?,?,?,?,?)", rows)
    print(f"[ok] trips: {len(rows)} rows inserted")

    # 3. MapReduce results
    loaders = {
        "hourly":  ("INSERT INTO hourly_ridership VALUES (?,?)",
                    lambda k, v: (int(k), int(v))),
        "route":   ("INSERT INTO route_ridership VALUES (?,?)",
                    lambda k, v: (k, int(v))),
        "revenue": ("INSERT INTO route_revenue VALUES (?,?)",
                    lambda k, v: (k, v)),
        "stop":    ("INSERT INTO stop_ridership VALUES (?,?)",
                    lambda k, v: (k, int(v))),
        "day":     ("INSERT INTO weekday_ridership VALUES (?,?,?)",
                    lambda k, v: (k, DAY_ORDER.get(k, 7), int(v))),
        "daily":   ("INSERT INTO daily_ridership VALUES (?,?)",
                    lambda k, v: (k, int(v))),
        "delay":   ("INSERT INTO route_delay VALUES (?,?)",
                    lambda k, v: (k, v)),
    }
    for job, (sql, convert) in loaders.items():
        data = [convert(k, v) for k, v in read_output(job)]
        cur.executemany(sql, data)
        cur.execute("INSERT INTO job_runs (job_name, keys_out) VALUES (?,?)",
                    (job, len(data)))
        print(f"[ok] {job:8s} -> {len(data)} rows")

    conn.commit()
    conn.close()
    print(f"Database ready: {DB_PATH}")


if __name__ == "__main__":
    main()
