# app.py

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/match-jobs", methods=["GET"])
def match_jobs():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
