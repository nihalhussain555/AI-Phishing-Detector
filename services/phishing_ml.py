import os
import joblib
from utils.feature_extractor import extract_features

class PhishingML:
    """Simple wrapper to load the trained XGBoost model and provide predictions.

    The training pipeline in ``model/train_model.py`` expects raw URL strings as input;
    the pipeline internally applies a character‑level TF‑IDF vectorizer before feeding
    the data to the XGBoost classifier.  Therefore, for inference we can reuse the
    saved ``Pipeline`` object directly.

    The ``predict`` method returns a dictionary compatible with the ``RiskEngine``
    expectations, containing a ``risk_score`` (0‑100) representing the probability
    that the URL is phishing.
    """

    def __init__(self, model_path: str = None):
        # Resolve the default model path relative to this file
        if model_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model"))
            model_path = os.path.join(base_dir, "phishing_model.pkl")
        # Load the pipeline (TF‑IDF + XGBoost) saved by ``train_model.py``
        self.model = joblib.load(model_path)

    def predict(self, url: str) -> dict:
        """Predict phishing risk for a single URL.

        Returns
        -------
        dict
            {"risk_score": <float>} where the score is a percentage (0‑100).
        """
        # The pipeline expects an iterable of strings
        prob = self.model.predict_proba([url])[0]
        # Assuming the second class corresponds to phishing (as in original training)
        risk_score = prob[1] * 100
        return {"risk_score": risk_score}
