from flask import Blueprint, render_template, request
from services.risk_engine import RiskEngine
from services.report_generator import ReportGenerator
from database.mongodb import scans_collection
from datetime import datetime

scan_bp = Blueprint("scan", __name__)
risk_engine = RiskEngine()

@scan_bp.route("/scan", methods=["POST", "GET"])
def scan_url():
    if request.method == "GET":
        return render_template("index.html")
        
    url = request.form.get("url", "").strip()
    if not url:
        return render_template("result.html", error="Please enter a URL.")

    # 1. Run Risk Engine
    risk_result = risk_engine.analyze_url(url)
    
    # 2. Generate Report
    report = ReportGenerator.generate_scan_report(risk_result)
    
    # 3. Save to DB
    scan_data = {
        "url": url,
        "prediction": risk_result["classification"],
        "risk_score": risk_result["overall_risk_score"],
        "created_at": datetime.utcnow(),
        "report": report
    }
    
    try:
        scans_collection.insert_one(scan_data)
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        
    # We can pass the new structured report to the template if it's updated,
    # but for backward compatibility, we pass the basic variables too.
    return render_template(
        "result.html",
        url=url,
        prediction=risk_result["classification"],
        risk_score=risk_result["overall_risk_score"],
        report=report
    )