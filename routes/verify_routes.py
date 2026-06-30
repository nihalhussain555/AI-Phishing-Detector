from flask import Blueprint, render_template, request, jsonify
from services.news_verification import NewsVerificationService
from services.report_generator import ReportGenerator

verify_bp = Blueprint("verify", __name__)

# Initialize it lazily or globally
news_verifier = None

@verify_bp.route("/verify", methods=["GET", "POST"])
def verify_claim():
    global news_verifier
    if news_verifier is None:
        news_verifier = NewsVerificationService()
        
    if request.method == "GET":
        # Create a simple verification page or handle it via an API
        return render_template("verify.html") # We would need to create this template
        
    claim = request.form.get("claim", "").strip()
    if not claim:
        return render_template("verify.html", error="Please enter a claim.")
        
    # 1. Verify Claim
    verification_result = news_verifier.verify_claim(claim)
    
    # 2. Generate Report
    report = ReportGenerator.generate_news_report(claim, verification_result)
    
    return render_template("verify_result.html", report=report, claim=claim)
