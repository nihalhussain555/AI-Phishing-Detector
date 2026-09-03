import os
import sys
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

from xgboost import XGBClassifier

# Make sure we can import utils.feature_extractor regardless of cwd
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, ".."))
from utils.feature_extractor import extract_features, FEATURE_NAMES  # noqa: E402

DATASET_PATH = os.path.join(BASE_DIR, "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "phishing_model.pkl")

# =========================
# Load Dataset
# =========================

data = pd.read_csv(DATASET_PATH)
print("Dataset Shape:", data.shape)

url_column = data.columns[0]
label_column = data.columns[-1]

raw_urls = data[url_column].astype(str)
y = LabelEncoder().fit_transform(data[label_column])
# LabelEncoder sorts alphabetically: "legitimate"=0, "phishing"=1 - confirm below.
print("Label classes:", dict(zip(*np.unique(data[label_column], return_counts=True))))

# =========================
# Build feature matrix using OUR OWN extractor (utils/feature_extractor.py)
# This guarantees train/serve consistency: the exact same function scores
# live URLs at inference time (services/phishing_ml.py), so there's no
# skew between training-time and runtime feature computation.
# =========================

print("Extracting lexical features from URLs...")
X = np.array([extract_features(u) for u in raw_urls])
print("Feature matrix shape:", X.shape, "| Features:", len(FEATURE_NAMES))

# =========================
# Train / Test Split
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# =========================
# Model
# =========================

model = XGBClassifier(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_lambda=1.0,
    random_state=42,
    eval_metric="logloss",
)

print("Training Started...")
model.fit(X_train, y_train)

# =========================
# Evaluation
# =========================

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print("\nAccuracy:", round(accuracy * 100, 2), "%")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, target_names=["legitimate", "phishing"]))
print("Confusion Matrix (rows=actual, cols=predicted) [legit, phishing]:")
print(confusion_matrix(y_test, y_pred))

# Feature importance - useful for sanity-checking the model actually
# learned meaningful phishing signals rather than noise.
importances = sorted(
    zip(FEATURE_NAMES, model.feature_importances_),
    key=lambda x: x[1],
    reverse=True,
)
print("\nTop 15 most important features:")
for name, imp in importances[:15]:
    print(f"  {name}: {imp:.4f}")

# =========================
# Save Model
# =========================

joblib.dump(model, MODEL_PATH)
print("\nModel Saved Successfully")
print(MODEL_PATH)