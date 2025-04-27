from flask import Flask, request, render_template_string, jsonify
from notion_client import Client
import openai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Flask app
app = Flask(__name__)

# Setup Notion client
notion = Client(auth=os.getenv("BEEFCAKE_LOGGER_NOTION_API_KEY"))
database_id = os.getenv("BEEFCAKE_LOGGER_NOTION_DATABASE_ID")

# Setup OpenAI client
openai.api_key = os.getenv("BEEFCAKE_LOGGER_OPENAI_API_KEY")

# HTML Template for Web Form
form_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GainsBot 800</title>
</head>
<body style="font-family: Arial, sans-serif; padding: 1rem; margin: 0;">
    <h1 style="font-size: 1.5rem;">GainsBot 800</h1>
    <form action="/log-workout" method="post" style="display: flex; flex-direction: column;">
        <textarea name="workout_text" rows="10" style="font-size: 1rem; padding: 0.5rem; width: 100%; box-sizing: border-box;" placeholder="Paste your Strong export here..." autofocus required></textarea>
        <button type="submit" style="margin-top: 1rem; padding: 0.75rem; font-size: 1rem;">Log Workout</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(form_html)

def log_to_notion(parsed_json):
    """Create a workout log in Notion."""
    try:
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Session": {"title": [{"text": {"content": parsed_json["session"]}}]},
                "Date": {"date": {"start": parsed_json["date"]}},
                "Focus": {"multi_select": [{"name": tag} for tag in parsed_json["focus"]]},
                "Exercises": {"rich_text": [{"text": {"content": parsed_json["exercises"]}}]},
                "Notes": {"rich_text": [{"text": {"content": parsed_json["notes"]}}]},
                "Tags": {"multi_select": [{"name": tag} for tag in parsed_json["tags"]]}
            }
        )
        print("[log_to_notion] Workout logged successfully.")
    except Exception as e:
        print("[log_to_notion] ERROR:", str(e))
        raise

@app.route("/log-workout", methods=["POST"], strict_slashes=False)
def log_workout():
    try:
        raw_text = request.form['workout_text']
        print("[/log-workout] Raw text received:", raw_text)

        parsed_json = parse_with_gpt4o(raw_text)
        print("[/log-workout] Parsed JSON:", parsed_json)

        log_to_notion(parsed_json)

        return "<h2>✅ Workout logged successfully!</h2><p><a href='/'>Log another workout</a></p>", 200

    except Exception as e:
        print("[/log-workout] Error occurred:", str(e))
        return f"<h2>❌ Error:</h2><pre>{str(e)}</pre><p><a href='/'>Go back</a></p>", 500

@app.route("/api-log-workout", methods=["POST"], strict_slashes=False)
def api_log_workout():
    try:
        parsed_json = request.get_json(force=True)
        print("[/api-log-workout] Parsed JSON received:", parsed_json)

        required_fields = ["session", "date", "focus", "exercises", "notes", "tags"]
        missing = [field for field in required_fields if field not in parsed_json]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        log_to_notion(parsed_json)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("[/api-log-workout] Error occurred:", str(e))
        return jsonify({"error": str(e)}), 500

def parse_with_gpt4o(raw_text):
    """Send raw workout text to GPT-4o and get structured JSON."""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Parse the following workout text into clean JSON with these fields only: "
                    "session (string), date (ISO date string), focus (list of strings), "
                    "exercises (string), notes (string), tags (list of strings). "
                    "Return pure JSON only. No markdown. No explanations. No extra text."
                ),
            },
            {"role": "user", "content": raw_text}
        ],
        temperature=0
    )
    parsed_text = response['choices'][0]['message']['content']
    parsed_json = json.loads(parsed_text)
    return parsed_json

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
