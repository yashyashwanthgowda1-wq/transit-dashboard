"""
Generates a realistic sample public-transport trips dataset (CSV).
Use this if you don't have a real dataset. To use a real Kaggle dataset,
just make sure it has the same columns (or edit the mappers).

Columns:
trip_id,date,day_of_week,hour,route_id,stop_name,passengers,fare,delay_min
"""
import csv
import random
import sys
from datetime import date, timedelta

ROWS = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
OUT = sys.argv[2] if len(sys.argv) > 2 else "transit_data.csv"

ROUTES = ["R101", "R102", "R205", "R310", "R412", "R518", "R620", "R777"]
STOPS = ["Central Station", "City Mall", "University Gate", "Tech Park",
         "Airport", "Bus Depot", "Old Market", "Hospital", "Stadium",
         "Railway Junction", "IT Hub", "Lake View"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday"]
FARE_PER_PASSENGER = {"R101": 15, "R102": 20, "R205": 25, "R310": 10,
                      "R412": 30, "R518": 18, "R620": 22, "R777": 40}

# Rush hours get more passengers
HOUR_WEIGHTS = [1, 1, 1, 1, 2, 4, 7, 10, 10, 7, 5, 5,
                5, 5, 5, 6, 8, 10, 10, 7, 5, 3, 2, 1]

random.seed(42)
start = date(2026, 1, 1)

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["trip_id", "date", "day_of_week", "hour", "route_id",
                "stop_name", "passengers", "fare", "delay_min"])
    for i in range(1, ROWS + 1):
        d = start + timedelta(days=random.randint(0, 89))
        day = DAYS[d.weekday()]
        hour = random.choices(range(24), weights=HOUR_WEIGHTS)[0]
        route = random.choice(ROUTES)
        stop = random.choice(STOPS)
        base = HOUR_WEIGHTS[hour] * 4
        if day in ("Saturday", "Sunday"):
            base = int(base * 0.6)
        passengers = max(1, int(random.gauss(base, base * 0.3 + 1)))
        fare = passengers * FARE_PER_PASSENGER[route]
        delay = max(0, int(random.gauss(HOUR_WEIGHTS[hour] * 0.8, 3)))
        w.writerow([f"T{i:07d}", d.isoformat(), day, hour, route, stop,
                    passengers, fare, delay])

print(f"Wrote {ROWS} rows to {OUT}")
