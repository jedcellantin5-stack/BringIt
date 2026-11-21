from flask import Flask, render_template, send_from_directory
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/")
def home():
    # Only the PUBLIC (publishable) key goes to the browser. Never the secret/service_role key.
       return render_template(
        "index.html",
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_PUBLISHABLE_KEY"),
        onesignal_app_id=os.getenv("ONESIGNAL_APP_ID", "9425e366-760f-43b6-a709-ea6b7f88de92"),
    )


@app.route("/OneSignalSDKWorker.js")
def onesignal_worker():
    return send_from_directory(app.root_path, "OneSignalSDKWorker.js")


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
