import os
import logging
import joblib

from utils.feature_extractor import extract_features, FEATURE_NAMES

logger = logging.getLogger(__name__)


class PhishingML:
    """Loads the trained XGBoost model and scores URLs for phishing risk.

    The model is trained on purely lexical/structural URL features (see
    utils/feature_extractor.py) - the exact same function is used here at
    inference time, so there's no train/serve skew. No network calls are
    made, so this works instantly even for unreachable sites and stays
    light enough for Render's free tier.
    """

    def __init__(self, model_path: str = None):
        if model_path is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model"))
            model_path = os.path.join(base_dir, "phishing_model.pkl")
        self.model = joblib.load(model_path)

        # Sanity-check that the loaded model actually matches the current
        # feature extractor. If someone updates one without the other
        # (e.g. an old model/phishing_model.pkl left over from before a
        # retrain), predictions would silently be garbage - or crash with
        # a confusing error from deep inside sklearn/xgboost. Catch it
        # here with a clear message instead.
        expected = len(FEATURE_NAMES)
        actual = getattr(self.model, "n_features_in_", None)
        if actual is not None and actual != expected:
            raise ValueError(
                f"phishing_model.pkl expects {actual} input features, but "
                f"the current feature extractor produces {expected}. "
                "The model file is out of sync with utils/feature_extractor.py - "
                "re-run model/train_model.py to retrain, or replace "
                "model/phishing_model.pkl with the matching version."
            )

    def predict(self, url: str) -> dict:
        """Predict phishing risk for a single URL.

        Returns
        -------
        dict
            {"risk_score": <float>} where the score is a percentage (0-100)
            representing the model's confidence that the URL is phishing.
            Falls back to a neutral 50% (and logs the real error) rather
            than crashing the whole scan if something goes wrong here.
        """
        try:
            features = extract_features(url)
            prob = self.model.predict_proba([features])[0]
            # Class 1 = "phishing" (LabelEncoder sorts alphabetically:
            # legitimate=0, phishing=1 - verified at training time).
            risk_score = float(prob[1] * 100)
            return {"risk_score": risk_score}
        except Exception as e:
            logger.error("[PhishingML] Prediction failed for %s: %s", url, e)
            return {"risk_score": 50.0, "error": str(e)}