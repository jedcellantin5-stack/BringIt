from flask import Flask, render_template, request, jsonify
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/save-schedule", methods=["POST"])
def save_schedule():

    try:
        data = request.get_json()

        print("DATA RECEIVED:")
        print(data)

        for day, subjects in data.items():

            print("Saving:", day, subjects)

            existing = supabase.table("schedules").select("*").eq("day", day).execute()

            if existing.data:
                response = supabase.table("schedules").update({
                    "subjects": subjects
                }).eq("day", day).execute()

            else:
                response = supabase.table("schedules").insert({
                    "day": day,
                    "subjects": subjects
                }).execute()

            print("SUPABASE RESPONSE:")
            print(response)

        return jsonify({
            "message": "Schedule saved to Supabase!"
        })

    except Exception as e:

        print("ERROR:", repr(e))

        return jsonify({
            "message": "Supabase error",
            "error": repr(e)
        }), 500
@app.route("/clear-schedule", methods=["POST"])
def clear_schedule():

    try:
        data = request.get_json()
        day = data["day"]

        response = supabase.table("schedules").update({
            "subjects": []
        }).eq("day", day).execute()

        return jsonify({
            "message": day + " schedule cleared!"
        })

    except Exception as e:

        print("ERROR:", repr(e))

        return jsonify({
            "message": "Supabase error",
            "error": repr(e)
        }), 500
    
@app.route("/load-schedule", methods=["GET"])
def load_schedule():

    try:
        response = supabase.table("schedules").select("*").execute()

        return jsonify(response.data)

    except Exception as e:

        print("ERROR:", repr(e))

        return jsonify({
            "message": "Supabase error",
            "error": repr(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)