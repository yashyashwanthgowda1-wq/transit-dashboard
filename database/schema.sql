-- =========================================================
-- Database schema: Public Transportation Dashboard
-- Engine: SQLite (file: database/transit.db)
-- =========================================================

-- Raw trip records (the dataset)
DROP TABLE IF EXISTS trips;
CREATE TABLE trips (
    trip_id      TEXT PRIMARY KEY,
    trip_date    DATE    NOT NULL,
    day_of_week  TEXT    NOT NULL,
    hour         INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    route_id     TEXT    NOT NULL,
    stop_name    TEXT    NOT NULL,
    passengers   INTEGER NOT NULL,
    fare         REAL    NOT NULL,
    delay_min    INTEGER NOT NULL
);
CREATE INDEX idx_trips_route ON trips(route_id);
CREATE INDEX idx_trips_date  ON trips(trip_date);
CREATE INDEX idx_trips_stop  ON trips(stop_name);

-- ---------- MapReduce result tables ----------

DROP TABLE IF EXISTS hourly_ridership;
CREATE TABLE hourly_ridership (
    hour             INTEGER PRIMARY KEY,
    total_passengers INTEGER NOT NULL
);

DROP TABLE IF EXISTS route_ridership;
CREATE TABLE route_ridership (
    route_id         TEXT PRIMARY KEY,
    total_passengers INTEGER NOT NULL
);

DROP TABLE IF EXISTS route_revenue;
CREATE TABLE route_revenue (
    route_id      TEXT PRIMARY KEY,
    total_revenue REAL NOT NULL
);

DROP TABLE IF EXISTS stop_ridership;
CREATE TABLE stop_ridership (
    stop_name        TEXT PRIMARY KEY,
    total_passengers INTEGER NOT NULL
);

DROP TABLE IF EXISTS weekday_ridership;
CREATE TABLE weekday_ridership (
    day_of_week      TEXT PRIMARY KEY,
    day_order        INTEGER NOT NULL,
    total_passengers INTEGER NOT NULL
);

DROP TABLE IF EXISTS daily_ridership;
CREATE TABLE daily_ridership (
    trip_date        DATE PRIMARY KEY,
    total_passengers INTEGER NOT NULL
);

DROP TABLE IF EXISTS route_delay;
CREATE TABLE route_delay (
    route_id      TEXT PRIMARY KEY,
    avg_delay_min REAL NOT NULL
);

-- Log of every MapReduce job run
DROP TABLE IF EXISTS job_runs;
CREATE TABLE job_runs (
    run_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name   TEXT NOT NULL,
    keys_out   INTEGER NOT NULL,
    run_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
