from services.connectivity_service import ConnectivityService
from services.trust_service import TrustService
from ml.phishing_ml import PhishingML

class RiskEngine:
    """Module 4: Risk Engine that combines all factors to generate a final Risk Score."""
    
    def __init__(self):
        self.connectivity = ConnectivityService()
        self.trust = TrustService()
        self.ml_model = PhishingML()
        
    def analyze_url(self, url):
        """Generates the overall risk score and classification."""
        
        conn_result = self.connectivity.check_connectivity(url)
        trust_result = self.trust.analyze(url)
        ml_result = self.ml_model.predict(url)
        
        # Calculate final risk score (0-100)
        # Higher score = Higher risk
        
        risk_score = 0
        reasoning = []
        
        # Factor 1: ML Prediction (Weight: 40%)
        ml_risk = ml_result.get("risk_score", 0)
        risk_score += (ml_risk * 0.40)
        reasoning.append(f"ML Model Risk Score: {ml_risk}%")
        
        # Factor 2: Trust Score (Weight: 40%)
        # Trust score is 0-100 (Higher is safer). We invert it for risk.
        trust_val = trust_result.get("trust_score", 50)
        trust_risk = 100 - trust_val
        risk_score += (trust_risk * 0.40)
        reasoning.append(f"Trust Analyzer Risk Score: {trust_risk}%")
        
        # Factor 3: Connectivity/SSL (Weight: 20%)
        conn_risk = 0
        if not conn_result.get("reachable"):
            conn_risk = 100
            reasoning.append("Website is unreachable.")
        elif not conn_result.get("https_enabled"):
            conn_risk = 50
            reasoning.append("No HTTPS encryption.")
        elif not conn_result.get("ssl_valid"):
            conn_risk = 80
            reasoning.append("Invalid SSL Certificate.")
        else:
            reasoning.append("Connection is secure.")
            
        risk_score += (conn_risk * 0.20)
        
        risk_score = round(risk_score, 2)
        
        # Classification
        if risk_score >= 70:
            classification = "Dangerous"
        elif risk_score >= 40:
            classification = "Suspicious"
        else:
            classification = "Safe"
            
        return {
            "url": url,
            "overall_risk_score": risk_score,
            "classification": classification,
            "reasoning": reasoning,
            "connectivity_details": conn_result,
            "trust_details": trust_result,
            "ml_details": ml_result
        }
