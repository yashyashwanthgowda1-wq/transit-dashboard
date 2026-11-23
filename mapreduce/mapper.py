#!/usr/bin/env python3
"""
Generic Hadoop Streaming MAPPER.
Usage: mapper.py <job>

Jobs:
  hourly   -> key = hour,        value = passengers
  route    -> key = route_id,    value = passengers
  revenue  -> key = route_id,    value = fare
  stop     -> key = stop_name,   value = passengers
  day      -> key = day_of_week, value = passengers
  daily    -> key = date,        value = passengers
  delay    -> key = route_id,    value = delay_min   (use reducer avg)

Input CSV columns:
trip_id,date,day_of_week,hour,route_id,stop_name,passengers,fare,delay_min
"""
import sys

COL = {"trip_id": 0, "date": 1, "day_of_week": 2, "hour": 3, "route_id": 4,
       "stop_name": 5, "passengers": 6, "fare": 7, "delay_min": 8}

JOBS = {
    "hourly":  ("hour", "passengers"),
    "route":   ("route_id", "passengers"),
    "revenue": ("route_id", "fare"),
    "stop":    ("stop_name", "passengers"),
    "day":     ("day_of_week", "passengers"),
    "daily":   ("date", "passengers"),
    "delay":   ("route_id", "delay_min"),
}


def main():
    job = sys.argv[1] if len(sys.argv) > 1 else "hourly"
    key_col, val_col = JOBS[job]
    k, v = COL[key_col], COL[val_col]

    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("trip_id"):   # skip header / blanks
            continue
        parts = line.split(",")
        if len(parts) < 9:                            # skip bad rows
            continue
        try:
            value = float(parts[v])
        except ValueError:
            continue
        key = parts[k].strip()
        if job == "hourly":
            key = key.zfill(2)                        # 07 sorts before 10
        print(f"{key}\t{value}")


if __name__ == "__main__":
    main()
