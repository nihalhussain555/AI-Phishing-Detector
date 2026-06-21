from flask import Blueprint, render_template, request
import joblib

from database.mongodb import scans_collection
from utils.feature_extractor import extract_features
from utils.helper import (
    get_current_time,
    format_prediction,
    calculate_risk_score
)

scan_bp = Blueprint("scan", __name__)

model = joblib.load("model/phishing_model.pkl")


@scan_bp.route("/scan", methods=["POST"])
def scan_url():

    url = request.form["url"]

    features = extract_features(url)

    prediction = model.predict([features])[0]

    probabilities = model.predict_proba([features])[0]

    result = format_prediction(prediction)

    risk_score = calculate_risk_score(probabilities)

    scan_data = {
        "url": url,
        "prediction": result,
        "risk_score": risk_score,
        "created_at": get_current_time()
    }

    scans_collection.insert_one(scan_data)

    return render_template(
        "result.html",
        url=url,
        prediction=result,
        risk_score=risk_score
    )