# Soumya Web Studio — Fixed Full-Stack Package

Flask + SQLite website with responsive frontend, working navigation, sliding sidebar, project enquiry form, WhatsApp handoff, and admin API.

## Run

Python 3.10+ recommended. In this folder run:

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000. The SQLite database is created automatically as `studio.db`.

## Verify

Open `http://127.0.0.1:5000/api/health`; expected JSON: `{"status":"ok","database":"connected"}`.

## Admin API

Admin routes are disabled unless you configure `ADMIN_DEMO_KEY` as an environment variable. Never expose a demo key publicly. Before deployment add proper login, CSRF protection, rate limiting, HTTPS, privacy notice, and backups.

If the page still returns a 500, read the traceback in the terminal where `python app.py` is running. Confirm the extracted folder still contains `templates/index.html` and `static/style.css` and `static/app.js`.
