from flask import Blueprint, render_template

from database.mongodb import scans_collection, db_available

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/dashboard")
def dashboard():

    total_scans = 0
    phishing_count = 0
    safe_count = 0
    suspicious_count = 0
    db_error = None

    if db_available and scans_collection is not None:
        try:
            total_scans = scans_collection.count_documents({})
            phishing_count = scans_collection.count_documents(
                {"prediction": {"$in": ["Phishing", "Dangerous"]}}
            )
            safe_count = scans_collection.count_documents(
                {"prediction": "Safe"}
            )
            suspicious_count = scans_collection.count_documents(
                {"prediction": {"$in": ["Suspicious", "Unreachable", "Not Found", "No Real Website"]}}
            )
        except Exception as e:
            db_error = f"Could not load stats from the database: {e}"
    else:
        db_error = "Database is not connected. Set MONGO_URI to enable the dashboard."

    return render_template(
        "dashboard.html",
        total_scans=total_scans,
        phishing_count=phishing_count,
        safe_count=safe_count,
        suspicious_count=suspicious_count,
        db_error=db_error
    )