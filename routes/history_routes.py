from flask import Blueprint, render_template

from database.mongodb import scans_collection

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():

    scans = scans_collection.find().sort(
        "created_at",
        -1
    )

    return render_template(
        "history.html",
        scans=scans
    )