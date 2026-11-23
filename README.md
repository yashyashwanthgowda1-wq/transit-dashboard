# Public Transportation Data Visualization Dashboard using MapReduce

Big Data mini project: transit trip data is processed with **MapReduce**
(Python mapper/reducer, Hadoop Streaming style), the results are stored in a
**SQL database (SQLite)**, served by a **Flask REST API** (backend), and shown
on a **Chart.js dashboard** (frontend).

## Architecture

```
 CSV dataset ──► MapReduce jobs (mapper.py → sort → reducer.py)
      │                       │
      │                       ▼
      │               output/*.txt (results)
      │                       │
      ▼                       ▼
   trips table      result tables (hourly_ridership, route_revenue, ...)
      └──────────┬────────────┘
                 ▼
        SQLite database (database/transit.db)
                 │   SQL queries
                 ▼
        Flask backend (REST API /api/...)
                 │   JSON
                 ▼
        Dashboard (HTML + Chart.js)
```

## Folder structure

```
transit-dashboard/
├── run_all.py                # ONE command: data → MapReduce → database
├── data/generate_data.py     # creates sample dataset (transit_data.csv)
├── mapreduce/
│   ├── mapper.py             # generic mapper (job name as argument)
│   ├── reducer.py            # sum / avg reducer
│   ├── run_local.py          # runs jobs on the laptop (map → sort → reduce)
│   └── run_hadoop.sh         # optional: same jobs on a Hadoop cluster
├── database/
│   ├── schema.sql            # all CREATE TABLE statements
│   ├── load_db.py            # loads CSV + MapReduce results into SQL
│   └── transit.db            # SQLite database (created by load_db.py)
├── backend/app.py            # Flask REST API – every route uses SQL
├── frontend/index.html       # dashboard UI
└── requirements.txt
```

## How to run (on your laptop)

```bash
pip install flask
python run_all.py          # builds dataset, runs MapReduce, loads database
python backend/app.py      # starts backend
```
Open **http://localhost:5000**

## Database tables

| Table              | Filled by        | Columns                                    |
|--------------------|------------------|--------------------------------------------|
| trips              | raw CSV          | trip_id, trip_date, day_of_week, hour, route_id, stop_name, passengers, fare, delay_min |
| hourly_ridership   | MapReduce hourly | hour, total_passengers                     |
| route_ridership    | MapReduce route  | route_id, total_passengers                 |
| route_revenue      | MapReduce revenue| route_id, total_revenue                    |
| stop_ridership     | MapReduce stop   | stop_name, total_passengers                |
| weekday_ridership  | MapReduce day    | day_of_week, day_order, total_passengers   |
| daily_ridership    | MapReduce daily  | trip_date, total_passengers                |
| route_delay        | MapReduce delay  | route_id, avg_delay_min                    |
| job_runs           | load_db.py       | run_id, job_name, keys_out, run_at         |

## MapReduce jobs

| Job      | Map: key → value          | Reduce | Stored in table    |
|----------|---------------------------|--------|--------------------|
| hourly   | hour → passengers         | sum    | hourly_ridership   |
| route    | route_id → passengers     | sum    | route_ridership    |
| revenue  | route_id → fare           | sum    | route_revenue      |
| stop     | stop_name → passengers    | sum    | stop_ridership     |
| day      | day_of_week → passengers  | sum    | weekday_ridership  |
| daily    | date → passengers         | sum    | daily_ridership    |
| delay    | route_id → delay_min      | avg    | route_delay        |

## API endpoints (all backed by SQL)

| Endpoint                       | What it returns                          |
|--------------------------------|------------------------------------------|
| /api/summary                   | KPI numbers (sub-queries)                |
| /api/hourly, /api/routes, /api/revenue, /api/stops, /api/days, /api/daily, /api/delays | chart data from result tables |
| /api/trips?route=R101&limit=20 | raw trip rows with filters               |
| /api/route/R101                | live GROUP BY stats for one route        |
| /api/route-list                | list of routes                           |
| /api/jobs                      | MapReduce job log                        |

## Viewing the database

Open `database/transit.db` in **DB Browser for SQLite** (free), or:
```bash
sqlite3 database/transit.db
sqlite> SELECT * FROM route_revenue ORDER BY total_revenue DESC;
```

## Show how MapReduce works (for viva)

```bash
cat data/transit_data.csv | python mapreduce/mapper.py hourly | sort | python mapreduce/reducer.py sum
```
(On Windows: `type data\transit_data.csv | python mapreduce\mapper.py hourly | sort | python mapreduce\reducer.py sum`)
