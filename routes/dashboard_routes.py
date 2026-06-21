from flask import Blueprint, render_template

from database.mongodb import scans_collection

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/dashboard")
def dashboard():

    total_scans = scans_collection.count_documents({})

    phishing_count = scans_collection.count_documents(
        {"prediction": "Phishing"}
    )

    safe_count = scans_collection.count_documents(
        {"prediction": "Safe"}
    )

    return render_template(
        "dashboard.html",
        total_scans=total_scans,
        phishing_count=phishing_count,
        safe_count=safe_count
    )