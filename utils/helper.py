from datetime import datetime


def get_current_time():
    return datetime.now()


def format_prediction(prediction):

    if prediction == 1:
        return "Phishing"

    return "Safe"


def calculate_risk_score(probabilities):

    return round(max(probabilities) * 100, 2)