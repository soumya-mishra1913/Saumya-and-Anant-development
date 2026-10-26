import os
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, request, jsonify

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("STUDIO_DB_PATH", str(BASE_DIR / "studio.db")))
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS project_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            project_type TEXT NOT NULL,
            details TEXT NOT NULL,
            budget TEXT NOT NULL DEFAULT '',
            contact TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL)""")
        db.execute("CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT OR IGNORE INTO site_settings(key,value) VALUES(?,?)", ("studio_name", "Soumya Web Studio"))
        db.execute("INSERT OR IGNORE INTO site_settings(key,value) VALUES(?,?)", ("whatsapp_number", os.environ.get("WHATSAPP_NUMBER", "919956169171")))

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/health")
def health():
    try:
        with get_db() as db: db.execute("SELECT 1").fetchone()
        return jsonify({"status":"ok", "database":"connected"})
    except Exception:
        app.logger.exception("Health check failed")
        return jsonify({"status":"error", "database":"unavailable"}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({"error":"Request is too large."}), 413

@app.post("/api/requests")
def create_request():
    data = request.get_json(silent=True)
    if not isinstance(data, dict): return jsonify({"error":"Invalid form data."}), 400
    name = str(data.get("name", "")).strip()
    project_type = str(data.get("project_type", "")).strip()
    details = str(data.get("details", "")).strip()
    budget = str(data.get("budget", "")).strip()
    contact = str(data.get("contact", "")).strip()
    if not name or not project_type or not details:
        return jsonify({"error":"Please fill in your name, project type, and project details."}), 400
    if len(name)>80 or len(project_type)>100 or len(details)>3000 or len(budget)>80 or len(contact)>120:
        return jsonify({"error":"One or more fields are too long."}), 400
    try:
        with get_db() as db:
            cur = db.execute("INSERT INTO project_requests(customer_name,project_type,details,budget,contact,created_at) VALUES(?,?,?,?,?,?)",
                (name, project_type, details, budget, contact, datetime.now(timezone.utc).isoformat(timespec="seconds")))
            request_id = cur.lastrowid
    except sqlite3.Error:
        app.logger.exception("Could not save enquiry")
        return jsonify({"error":"Could not save the enquiry. Check database write permissions."}), 500
    return jsonify({"message":"Your enquiry was saved successfully.", "request_id":request_id}), 201

def valid_admin_key():
    key = os.environ.get("ADMIN_DEMO_KEY", "")
    return bool(key) and request.headers.get("X-Admin-Demo-Key", "") == key

@app.get("/api/admin/requests")
def list_requests():
    if not valid_admin_key(): return jsonify({"error":"Admin API disabled or unauthorized. Configure ADMIN_DEMO_KEY."}), 401
    with get_db() as db:
        rows=db.execute("SELECT id,customer_name,project_type,details,budget,contact,status,created_at FROM project_requests ORDER BY id DESC").fetchall()
    return jsonify({"requests":[dict(r) for r in rows]})

@app.patch("/api/admin/requests/<int:request_id>")
def update_request(request_id):
    if not valid_admin_key(): return jsonify({"error":"Admin API disabled or unauthorized."}), 401
    data=request.get_json(silent=True) or {}
    status=str(data.get("status", ""))
    if status not in ("New", "In Progress", "Completed", "Archived"): return jsonify({"error":"Invalid status."}), 400
    with get_db() as db:
        cur=db.execute("UPDATE project_requests SET status=? WHERE id=?", (status,request_id))
        if not cur.rowcount: return jsonify({"error":"Request not found."}), 404
    return jsonify({"message":"Request status updated."})

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
