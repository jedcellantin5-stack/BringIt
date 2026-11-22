from flask import Flask, render_template, send_from_directory, request, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import hmac
import json
import os
import urllib.error
import urllib.request
import uuid

load_dotenv()

app = Flask(__name__)

DEFAULT_ONESIGNAL_APP_ID = "9425e366-760f-43b6-a709-ea6b7f88de92"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/")
def home():
    # Only the PUBLIC (publishable) key goes to the browser. Never the secret key.
    return render_template(
        "index.html",
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_PUBLISHABLE_KEY"),
        onesignal_app_id=os.getenv("ONESIGNAL_APP_ID", DEFAULT_ONESIGNAL_APP_ID),
    )


@app.route("/OneSignalSDKWorker.js")
def onesignal_worker():
    return send_from_directory(app.root_path, "OneSignalSDKWorker.js")


# ---------------------------------------------------------------------------
# Automatic reminders
# A free cron service opens /cron/reminders every evening. This sends each
# signed-in user a push notification listing tomorrow's classes.
# ---------------------------------------------------------------------------

def http_json(url, method="GET", headers=None, body=None, timeout=25):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None


def tomorrow_info(day_override=None):
    """Philippines time is UTC+8 with no daylight saving."""
    now = datetime.now(timezone.utc) + timedelta(hours=8)
    tomorrow = now + timedelta(days=1)
    if day_override:
        match = next((d for d in DAYS if d.lower() == day_override.strip().lower()), None)
        return match, tomorrow.date().isoformat()
    wd = tomorrow.weekday()
    return (DAYS[wd] if wd < 5 else None), tomorrow.date().isoformat()


def group_by_subjects(rows):
    """Users with the same classes get one shared message."""
    groups = {}
    for row in rows:
        subjects = row.get("subjects")
        uid = row.get("user_id")
        if not uid or not isinstance(subjects, list):
            continue
        clean = [str(s).strip() for s in subjects if str(s).strip()]
        if not clean:
            continue
        groups.setdefault(tuple(clean), []).append(uid)
    return groups


def build_message(day, subjects):
    shown = ", ".join(subjects[:6])
    if len(subjects) > 6:
        shown += " and more"
    return {
        "title": "🎒 Ready for tomorrow?",
        "body": "Tomorrow (" + day + "): " + shown + ". Check your bag in BringIt! ✅",
    }


@app.route("/cron/reminders")
def cron_reminders():
    secret = os.getenv("CRON_SECRET", "")
    given = request.args.get("token", "") or request.headers.get("X-Cron-Token", "")
    if not secret or not hmac.compare_digest(given.encode(), secret.encode()):
        return jsonify({"error": "unauthorized"}), 401

    supabase_url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    supabase_secret = os.getenv("SUPABASE_SECRET_KEY") or ""
    os_key = os.getenv("ONESIGNAL_API_KEY") or ""
    os_app = os.getenv("ONESIGNAL_APP_ID", DEFAULT_ONESIGNAL_APP_ID)
    if not (supabase_url and supabase_secret and os_key):
        return jsonify({"error": "missing settings",
                        "need": ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "ONESIGNAL_API_KEY"]}), 500

    day, date_str = tomorrow_info(request.args.get("day"))
    if not day:
        return jsonify({"sent": 0, "note": "No classes on weekends, nothing to send."})

    dry = request.args.get("dry") == "1"
    force = request.args.get("force") == "1"

    try:
        rows = http_json(
            supabase_url + "/rest/v1/user_schedules?select=user_id,subjects&limit=1000&day=eq." + day,
            headers={"apikey": supabase_secret, "Authorization": "Bearer " + supabase_secret},
        ) or []
    except Exception as exc:
        app.logger.error("Could not read schedules: %r", exc)
        return jsonify({"error": "could not read schedules"}), 502

    groups = group_by_subjects(rows)
    site = request.url_root.rstrip("/")
    sent, failed, preview = 0, 0, []

    for subjects, user_ids in groups.items():
        msg = build_message(day, list(subjects))
        preview.append({"users": len(user_ids), "title": msg["title"], "body": msg["body"]})
        if dry:
            continue
        for i in range(0, len(user_ids), 1000):
            chunk = user_ids[i:i + 1000]
            key = str(uuid.uuid4()) if force else str(
                uuid.uuid5(uuid.NAMESPACE_URL, "bringit|" + date_str + "|" + "|".join(sorted(chunk))))
            payload = {
                "app_id": os_app,
                "target_channel": "push",
                "include_aliases": {"external_id": chunk},
                "headings": {"en": msg["title"]},
                "contents": {"en": msg["body"]},
                "url": site,
                "idempotency_key": key,
            }
            try:
                result = http_json(
                    "https://api.onesignal.com/notifications?c=push",
                    method="POST",
                    headers={"Content-Type": "application/json", "Authorization": "Key " + os_key},
                    body=payload,
                )
                if result and result.get("id"):
                    sent += len(chunk)
                else:
                    failed += len(chunk)
                    app.logger.warning("OneSignal did not send: %s", (result or {}).get("errors"))
            except urllib.error.HTTPError as exc:
                failed += len(chunk)
                app.logger.error("OneSignal error %s", exc.code)
            except Exception as exc:
                failed += len(chunk)
                app.logger.error("OneSignal error: %r", exc)

    return jsonify({"day": day, "date": date_str, "dry_run": dry,
                    "users_with_classes": sum(len(v) for v in groups.values()),
                    "sent": sent, "not_sent": failed, "messages": preview})


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")