from flask import Blueprint, render_template, request
from services.risk_engine import RiskEngine
from services.report_generator import ReportGenerator
from database.mongodb import scans_collection, db_available
from utils.helpers import normalize_url
from datetime import datetime, timezone

scan_bp = Blueprint("scan", __name__)
risk_engine = RiskEngine()

@scan_bp.route("/scan", methods=["POST", "GET"])
def scan_url():
    if request.method == "GET":
        return render_template("index.html")
        
    raw_input = request.form.get("url", "").strip()
    if not raw_input:
        return render_template("result.html", error="Please enter a URL.")

    # Users only need to type a domain, e.g. "example.com" - we resolve the
    # correct scheme (preferring https) here so every downstream check
    # (trust, connectivity, ML) scores the real, final URL.
    url = normalize_url(raw_input)

    # 1. Run Risk Engine
    try:
        risk_result = risk_engine.analyze_url(url)
    except Exception as e:
        return render_template("result.html", error=f"Scan failed: {e}")

    # 2. Generate Report
    report = ReportGenerator.generate_scan_report(risk_result)
    
    # 3. Save to DB
    scan_data = {
        "url": url,
        "prediction": risk_result["classification"],
        "risk_score": risk_result["overall_risk_score"],
        "created_at": datetime.now(timezone.utc),
        "report": report
    }

    if db_available and scans_collection is not None:
        try:
            scans_collection.insert_one(scan_data)
        except Exception as e:
            print(f"Error saving to MongoDB: {e}")
    else:
        print("MongoDB unavailable - skipping history save for this scan.")
        
    # We can pass the new structured report to the template if it's updated,
    # but for backward compatibility, we pass the basic variables too.
    return render_template(
        "result.html",
        url=url,
        prediction=risk_result["classification"],
        risk_score=risk_result["overall_risk_score"],
        report=report
    )