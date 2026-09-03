from flask import Blueprint, render_template

from database.mongodb import scans_collection, db_available

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():

    scans = []
    db_error = None

    if db_available and scans_collection is not None:
        try:
            scans = list(scans_collection.find().sort("created_at", -1).limit(200))
        except Exception as e:
            db_error = f"Could not load scan history: {e}"
    else:
        db_error = "Database is not connected. Set MONGO_URI to enable scan history."

    return render_template(
        "history.html",
        scans=scans,
        db_error=db_error
    )