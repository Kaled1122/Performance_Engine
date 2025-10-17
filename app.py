import os
import json
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# -----------------------------
# Database connection setup
# -----------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgres://", 1)

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Create table if not exists."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id SERIAL PRIMARY KEY,
            learner_id VARCHAR(100),
            domain VARCHAR(50),
            lesson VARCHAR(100),
            score FLOAT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized")

# ✅ Make sure table is created even when Gunicorn runs
with app.app_context():
    try:
        init_db()
    except Exception as e:
        print("⚠️ DB Init Error:", e)

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return jsonify({"status": "✅ Performance Engine Running"})

@app.route("/update_score", methods=["POST"])
def update_score():
    try:
        data = request.get_json()
        learner_id = data.get("learner_id")
        domain = data.get("domain")
        lesson = data.get("lesson")
        score = float(data.get("score", 0))

        if not learner_id or not domain or not lesson:
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO scores (learner_id, domain, lesson, score)
            VALUES (%s, %s, %s, %s);
        """, (learner_id, domain, lesson, score))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "✅ Score updated successfully"})
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/get_scores", methods=["GET"])
def get_scores():
    try:
        learner_id = request.args.get("learner_id")
        conn = get_connection()
        cur = conn.cursor()
        if learner_id:
            cur.execute("SELECT * FROM scores WHERE learner_id = %s;", (learner_id,))
        else:
            cur.execute("SELECT * FROM scores;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = [
            {
                "id": r[0],
                "learner_id": r[1],
                "domain": r[2],
                "lesson": r[3],
                "score": r[4],
                "date": r[5].strftime("%Y-%m-%d %H:%M")
            }
            for r in rows
        ]
        return jsonify(results)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
