import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

from xgboost import XGBClassifier

# =========================
# Paths
# =========================

BASE_DIR = os.path.dirname(__file__)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "dataset.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "phishing_model.pkl"
)

# =========================
# Load Dataset
# =========================

data = pd.read_csv(DATASET_PATH)

print("Dataset Shape:", data.shape)

# First column = URL
# Last column = Label

url_column = data.columns[0]
label_column = data.columns[-1]

X = data[url_column].astype(str)
y = data[label_column]

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)

# =========================
# Train Test Split
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# =========================
# XGBoost Pipeline
# =========================

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            max_features=5000
        )
    ),
    (
        "xgb",
        XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        )
    )
])

print("Training Started...")

model.fit(X_train, y_train)

# =========================
# Evaluation
# =========================

y_pred = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\nAccuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        y_pred
    )
)

# =========================
# Save Model
# =========================

joblib.dump(
    model,
    MODEL_PATH
)

print("\nModel Saved Successfully")
print(MODEL_PATH)