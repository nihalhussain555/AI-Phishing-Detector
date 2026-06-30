import joblib
import os

from utils.feature_extractor import extract_features

class PhishingML:
    """Handles the existing Phishing ML model for backward compatibility."""

    def __init__(self, model_path="model/phishing_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.load_model()

    def load_model(self):
        """Loads the machine learning model from disk."""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print("ML Model Loaded Successfully")
            else:
                print(f"Warning: Model not found at {self.model_path}")
        except Exception as e:
            print(f"Error Loading Model: {e}")
            self.model = None

    def predict(self, url):
        """Predicts if a URL is phishing using the existing model and feature extractor."""
        if self.model is None:
            return {"prediction": "Unknown", "risk_score": 0, "error": "Model not loaded."}
        
        try:
            features = extract_features(url)
            prediction = self.model.predict([features])[0]
            probabilities = self.model.predict_proba([features])[0]
            risk_score = round(max(probabilities) * 100, 2)
            
            result = "Phishing" if prediction == 1 else "Safe"
            return {
                "prediction": result,
                "risk_score": risk_score
            }
        except Exception as e:
            return {"prediction": "Unknown", "risk_score": 0, "error": str(e)}
