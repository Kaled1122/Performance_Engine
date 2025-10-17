import os, sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_FILE = os.path.join(os.getcwd(), "performance.db")

# ------------------------------------------------------------
# DATABASE SETUP
# ------------------------------------------------------------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT,
            domain TEXT,
            lesson INTEGER,
            points REAL,
            max_points REAL,
            cycle INTEGER,
            date TEXT
        )
        """)
    print("✅ Database initialized")

init_db()

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.route("/")
def home():
    return jsonify({"status": "✅ Domain Performance Engine running"})

# ---------- Insert or update learner domain score ----------
@app.route("/update_scores", methods=["POST"])
def update_scores():
    data = request.get_json(force=True)
    required = ["learner_id", "domain", "lesson", "points", "max_points", "cycle"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT INTO performance (learner_id, domain, lesson, points, max_points, cycle, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["learner_id"], data["domain"], data["lesson"],
            data["points"], data["max_points"], data["cycle"],
            datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()
    return jsonify({"message": "✅ Score recorded successfully"})

# ---------- Retrieve learner full score history ----------
@app.route("/get_scores")
def get_scores():
    learner_id = request.args.get("learner_id")
    if not learner_id:
        return jsonify({"error": "Missing learner_id"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM performance WHERE learner_id = ?", (learner_id,))
        rows = cur.fetchall()

    data = [
        {
            "id": r[0],
            "learner_id": r[1],
            "domain": r[2],
            "lesson": r[3],
            "points": r[4],
            "max_points": r[5],
            "cycle": r[6],
            "date": r[7]
        } for r in rows
    ]
    return jsonify(data)

# ---------- Generate summary / averages per domain ----------
@app.route("/summary")
def summary():
    learner_id = request.args.get("learner_id")
    if not learner_id:
        return jsonify({"error": "Missing learner_id"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT domain, SUM(points), SUM(max_points)
            FROM performance
            WHERE learner_id = ?
            GROUP BY domain
        """, (learner_id,))
        results = cur.fetchall()

    summary = []
    for r in results:
        domain, pts, max_pts = r
        pct = round((pts / max_pts) * 100, 1) if max_pts else 0
        summary.append({"domain": domain, "score": pct})

    return jsonify({
        "learner_id": learner_id,
        "summary": summary,
        "date": datetime.now().strftime("%Y-%m-%d")
    })

# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
