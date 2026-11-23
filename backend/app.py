"""
Flask BACKEND (SQL version) for the Public Transportation Dashboard.

All data comes from the SQLite database (database/transit.db) through
SQL queries. The MapReduce results are stored in result tables, and the
raw records are in the `trips` table.

Run:  python backend/app.py      then open http://localhost:5000
"""
import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory, g

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "database", "transit.db")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR)


# ---------------- DATABASE HELPERS ----------------

def get_db():
    if "db" not in g:
        if not os.path.exists(DB_PATH):
            raise RuntimeError("Database not found. Run database/load_db.py first.")
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=()):
    return [dict(r) for r in get_db().execute(sql, params).fetchall()]


def chart(sql, label_col, value_col, params=()):
    rows = query(sql, params)
    return jsonify({"labels": [r[label_col] for r in rows],
                    "values": [r[value_col] for r in rows]})


@app.errorhandler(RuntimeError)
def handle_runtime(e):
    return jsonify({"error": str(e)}), 500


@app.after_request
def allow_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


# ---------------- API: MapReduce result tables ----------------

@app.route("/api/hourly")
def hourly():
    return chart("""SELECT printf('%02d:00', hour) AS label, total_passengers
                    FROM hourly_ridership ORDER BY hour""",
                 "label", "total_passengers")


@app.route("/api/routes")
def routes():
    return chart("""SELECT route_id, total_passengers FROM route_ridership
                    ORDER BY total_passengers DESC""",
                 "route_id", "total_passengers")


@app.route("/api/revenue")
def revenue():
    return chart("""SELECT route_id, total_revenue FROM route_revenue
                    ORDER BY total_revenue DESC""",
                 "route_id", "total_revenue")


@app.route("/api/stops")
def stops():
    return chart("""SELECT stop_name, total_passengers FROM stop_ridership
                    ORDER BY total_passengers DESC""",
                 "stop_name", "total_passengers")


@app.route("/api/days")
def days():
    return chart("""SELECT day_of_week, total_passengers FROM weekday_ridership
                    ORDER BY day_order""",
                 "day_of_week", "total_passengers")


@app.route("/api/daily")
def daily():
    return chart("""SELECT trip_date, total_passengers FROM daily_ridership
                    ORDER BY trip_date""",
                 "trip_date", "total_passengers")


@app.route("/api/delays")
def delays():
    return chart("""SELECT route_id, avg_delay_min FROM route_delay
                    ORDER BY avg_delay_min DESC""",
                 "route_id", "avg_delay_min")


@app.route("/api/summary")
def summary():
    s = query("""
        SELECT
          (SELECT SUM(total_passengers) FROM route_ridership)            AS total_passengers,
          (SELECT ROUND(SUM(total_revenue)) FROM route_revenue)          AS total_revenue,
          (SELECT route_id FROM route_ridership
             ORDER BY total_passengers DESC LIMIT 1)                     AS busiest_route,
          (SELECT stop_name FROM stop_ridership
             ORDER BY total_passengers DESC LIMIT 1)                     AS busiest_stop,
          (SELECT printf('%02d:00', hour) FROM hourly_ridership
             ORDER BY total_passengers DESC LIMIT 1)                     AS peak_hour,
          (SELECT ROUND(AVG(avg_delay_min), 2) FROM route_delay)         AS avg_delay,
          (SELECT COUNT(*) FROM trips)                                   AS total_trips
    """)[0]
    return jsonify(s)


# ---------------- API: raw trips table (SQL filters) ----------------

@app.route("/api/route-list")
def route_list():
    rows = query("SELECT DISTINCT route_id FROM trips ORDER BY route_id")
    return jsonify([r["route_id"] for r in rows])


@app.route("/api/trips")
def trips():
    """Recent trips, filterable: /api/trips?route=R101&stop=Airport&limit=20"""
    sql = "SELECT * FROM trips WHERE 1=1"
    params = []
    if request.args.get("route"):
        sql += " AND route_id = ?"
        params.append(request.args["route"])
    if request.args.get("stop"):
        sql += " AND stop_name = ?"
        params.append(request.args["stop"])
    limit = min(int(request.args.get("limit", 20)), 200)
    sql += " ORDER BY trip_date DESC, hour DESC LIMIT ?"
    params.append(limit)
    return jsonify(query(sql, params))


@app.route("/api/route/<route_id>")
def route_detail(route_id):
    """Per-route stats calculated live with SQL GROUP BY."""
    stats = query("""SELECT route_id,
                            COUNT(*)                  AS trips,
                            SUM(passengers)           AS passengers,
                            ROUND(SUM(fare))          AS revenue,
                            ROUND(AVG(delay_min), 2)  AS avg_delay
                     FROM trips WHERE route_id = ? GROUP BY route_id""",
                  (route_id,))
    by_hour = query("""SELECT hour, SUM(passengers) AS passengers
                       FROM trips WHERE route_id = ?
                       GROUP BY hour ORDER BY hour""", (route_id,))
    return jsonify({"stats": stats[0] if stats else None, "by_hour": by_hour})


@app.route("/api/jobs")
def jobs():
    return jsonify(query("SELECT * FROM job_runs ORDER BY run_id"))


# ---------------- DATABASE PREVIEW (/db) ----------------

DB_PREVIEW_CSS = """
body{font-family:Segoe UI,sans-serif;margin:0;background:#f5f6f8;color:#222;display:flex}
nav{width:230px;background:#1f2937;color:#fff;height:100vh;position:sticky;top:0;padding:16px;box-sizing:border-box;overflow:auto;flex-shrink:0}
nav h1{font-size:16px} nav a{display:flex;justify-content:space-between;color:#d1d5db;text-decoration:none;padding:6px 8px;border-radius:4px;font-size:14px}
nav a:hover{background:#374151;color:#fff} nav span{color:#9ca3af;font-size:12px}
main{flex:1;padding:20px;min-width:0} section{background:#fff;border-radius:8px;padding:16px;margin-bottom:20px;box-shadow:0 1px 3px #0001}
h2{margin:0 0 10px;font-size:18px} small{color:#888;font-weight:normal;font-size:13px;margin-left:8px}
.wrap{max-height:420px;overflow:auto} table{border-collapse:collapse;width:100%;font-size:13px}
th{position:sticky;top:0;background:#e5e7eb;text-align:left;padding:6px 10px} td{padding:5px 10px;border-bottom:1px solid #eee}
tr:hover td{background:#f0f7ff} pre{background:#111827;color:#e5e7eb;padding:14px;border-radius:6px;overflow:auto;font-size:12px}
textarea{width:100%;box-sizing:border-box;font-family:Consolas,monospace;font-size:13px;padding:8px;border:1px solid #ccc;border-radius:4px}
button{margin-top:8px;padding:6px 16px;background:#2563eb;color:#fff;border:0;border-radius:4px;cursor:pointer}
.err{color:#b91c1c;font-family:Consolas,monospace}
"""


def _html_table(cols, rows):
    from html import escape
    th = "".join(f"<th>{escape(str(c))}</th>" for c in cols)
    tr = "".join("<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in r) + "</tr>"
                 for r in rows)
    return f'<div class="wrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


@app.route("/db")
def db_preview():
    """Browse every table and run read-only SQL: http://localhost:5000/db"""
    from html import escape
    # read-only connection so the query box can't modify data
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name!='sqlite_sequence'")]

        sql = request.args.get("sql", "").strip()
        result = ""
        if sql:
            try:
                cur = conn.execute(sql)
                cols = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchmany(500)
                result = (f"<p><small>{len(rows)} row(s) shown (max 500)</small></p>"
                          + _html_table(cols, rows))
            except sqlite3.Error as e:
                result = f'<p class="err">{escape(str(e))}</p>'

        nav, sections = [], []
        for t in tables:
            n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            cur = conn.execute(f'SELECT * FROM "{t}" LIMIT 100')
            cols = [d[0] for d in cur.description]
            note = f"showing first 100 of {n:,}" if n > 100 else f"{n:,} rows"
            nav.append(f'<a href="#{t}">{t} <span>{n:,}</span></a>')
            sections.append(f'<section id="{t}"><h2>{t}<small>{note}</small></h2>'
                            + _html_table(cols, cur.fetchall()) + "</section>")
    finally:
        conn.close()

    with open(os.path.join(ROOT, "database", "schema.sql")) as f:
        schema = escape(f.read())

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>transit.db preview</title><style>{DB_PREVIEW_CSS}</style></head><body>
<nav><h1>transit.db</h1><a href="#query">Run SQL</a>{''.join(nav)}<a href="#schema">schema.sql</a>
<a href="/">&larr; Dashboard</a></nav>
<main>
<section id="query"><h2>Run SQL <small>read-only</small></h2>
<form method="get"><textarea name="sql" rows="4">{escape(sql or "SELECT route_id, SUM(passengers) AS passengers, ROUND(SUM(fare)) AS revenue FROM trips GROUP BY route_id ORDER BY revenue DESC")}</textarea>
<button type="submit">Run</button></form>{result}</section>
{''.join(sections)}
<section id="schema"><h2>schema.sql</h2><pre>{schema}</pre></section>
</main></body></html>"""


# ---------------- FRONTEND ----------------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
