import requests

url = "http://0.0.0.0:3000/api-log-workout"

headers = {"Content-Type": "application/json"}
data = {
    "session": "Test Push Day",
    "date": "2025-04-27",
    "focus": ["Chest", "Triceps"],
    "exercises": "Bench Press: 3x8\nPushdowns: 3x12",
    "notes": "Test run from Python requests.",
    "tags": ["Beefcake", "Gainsville"]
}

response = requests.post(url, json=data, headers=headers)

print("Status Code:", response.status_code)
print("Response Body:", response.text)
