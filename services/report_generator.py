import json

class ReportGenerator:
    """Module 7: Generates structured JSON reports."""
    
    @staticmethod
    def generate_scan_report(risk_result):
        """Generates a structured report from the Risk Engine output."""
        return {
            "report_type": "Website Scan",
            "summary": {
                "url": risk_result.get("url"),
                "classification": risk_result.get("classification"),
                "risk_score": risk_result.get("overall_risk_score")
            },
            "reasoning": risk_result.get("reasoning", []),
            "details": {
                "connectivity": risk_result.get("connectivity_details"),
                "trust_analysis": risk_result.get("trust_details"),
                "ml_prediction": risk_result.get("ml_details")
            }
        }
        
    @staticmethod
    def generate_news_report(claim, verification_result):
        """Generates a structured report from the News Verification output."""
        return {
            "report_type": "News Verification",
            "claim": claim,
            "prediction": verification_result.get("prediction"),
            "confidence_percentage": verification_result.get("confidence"),
            "closest_matching_article": verification_result.get("closest_article"),
            "sources_checked": verification_result.get("supporting_sources")
        }
