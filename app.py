from flask import Flask, render_template, request
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

import os
import joblib

load_dotenv()

app = Flask(__name__)

# ======================
# MongoDB Configuration
# ======================

MONGO_URI = os.getenv("MONGO_URI")

client = None
scans_collection = None

if not MONGO_URI:
    print("MONGO_URI is not set. MongoDB operations will be disabled.")
else:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client["phishing_detector"]
        scans_collection = db["scans"]
        print("Connected to MongoDB Atlas")
    except Exception as e:
        print(f"Error connecting to MongoDB Atlas: {e}")
        client = None
        scans_collection = None

# ======================
# Load ML Model
# ======================

try:
    model = joblib.load("model/phishing_model.pkl")
    print("Model Loaded Successfully")
except Exception as e:
    print(f"Error Loading Model: {e}")
    model = None

# ======================
# Routes
# ======================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan():
    try:
        url = request.form.get("url", "").strip()

        if not url:
            return render_template(
                "result.html",
                error="Please enter a URL."
            )

        if model is None:
            return render_template(
                "result.html",
                error="Machine learning model not loaded."
            )

        prediction = model.predict([url])[0]
        probabilities = model.predict_proba([url])[0]
        risk_score = round(max(probabilities) * 100, 2)

        result = "Phishing" if prediction == 1 else "Safe"

        scan_data = {
            "url": url,
            "prediction": result,
            "risk_score": risk_score,
            "created_at": datetime.utcnow()
        }

        if scans_collection is not None:
            scans_collection.insert_one(scan_data)
        else:
            print("Warning: MongoDB collection unavailable. Scan record not saved.")

        return render_template(
            "result.html",
            url=url,
            prediction=result,
            risk_score=risk_score
        )
    except Exception as e:
        return render_template(
            "result.html",
            error=f"An error occurred while scanning the URL: {e}"
        )


@app.route("/dashboard")
def dashboard():
    if scans_collection is None:
        return render_template(
            "dashboard.html",
            total_scans=0,
            phishing_count=0,
            safe_count=0,
            error="Dashboard unavailable because MongoDB connection is not established."
        )

    total_scans = scans_collection.count_documents({})
    phishing_count = scans_collection.count_documents({"prediction": "Phishing"})
    safe_count = scans_collection.count_documents({"prediction": "Safe"})

    return render_template(
        "dashboard.html",
        total_scans=total_scans,
        phishing_count=phishing_count,
        safe_count=safe_count
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
