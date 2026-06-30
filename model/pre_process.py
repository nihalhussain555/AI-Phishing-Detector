import os
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import SMOTE


def preprocess_phishing_data(
    file_path,
    test_size=0.2,
    random_state=42,
    use_smote=True,
    export_csv=False,
    export_dir=None
):
    """
    Preprocess phishing dataset.

    Steps:
    1. Load dataset
    2. Remove unnecessary columns
    3. Handle missing values
    4. Split train/test data
    5. Scale features
    6. Apply SMOTE (optional)
    7. Export processed data (optional)

    Returns:
        X_train, X_test, y_train, y_test, scaler
    """

    print("Loading dataset...")
    df = pd.read_csv(file_path)

    # Features and target
    X = df.drop(columns=["url", "status"], errors="ignore")
    y = df["status"]

    # -----------------------------
    # Handle Missing Values
    # -----------------------------
    print("Checking missing values...")

    if X.isnull().sum().sum() > 0:
        print("Missing values found. Applying median imputation...")

        imputer = SimpleImputer(strategy="median")
        X = pd.DataFrame(
            imputer.fit_transform(X),
            columns=X.columns
        )

    else:
        print("No missing values found.")

    # -----------------------------
    # Train-Test Split
    # -----------------------------
    print("Splitting dataset...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )

    print(f"Training Samples : {len(X_train)}")
    print(f"Testing Samples  : {len(X_test)}")

    # -----------------------------
    # Feature Scaling
    # -----------------------------
    print("Scaling features using RobustScaler...")

    scaler = RobustScaler()

    X_train = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X.columns
    )

    X_test = pd.DataFrame(
        scaler.transform(X_test),
        columns=X.columns
    )

    # -----------------------------
    # Apply SMOTE
    # -----------------------------
    if use_smote:
        print("Applying SMOTE...")

        smote = SMOTE(random_state=random_state)

        X_train, y_train = smote.fit_resample(
            X_train,
            y_train
        )

        print("\nClass Distribution After SMOTE:")
        print(pd.Series(y_train).value_counts())

    # -----------------------------
    # Export CSV Files
    # -----------------------------
    if export_csv:

        save_dir = export_dir or os.path.dirname(file_path) or "."
        os.makedirs(save_dir, exist_ok=True)

        train_df = pd.concat(
            [pd.DataFrame(X_train), pd.Series(y_train, name="status")],
            axis=1
        )

        test_df = pd.concat(
            [pd.DataFrame(X_test), pd.Series(y_test, name="status")],
            axis=1
        )

        train_path = os.path.join(save_dir, "processed_train.csv")
        test_path = os.path.join(save_dir, "processed_test.csv")

        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)

        print(f"\nSaved: {train_path}")
        print(f"Saved: {test_path}")

    return X_train, X_test, y_train, y_test, scaler


# ---------------------------------------------------
# Example Usage
# ---------------------------------------------------
if __name__ == "__main__":

    DATASET_PATH = "model/dataset.csv"

    X_train, X_test, y_train, y_test, scaler = preprocess_phishing_data(
        file_path=DATASET_PATH,
        test_size=0.2,
        random_state=42,
        use_smote=True
    )

    print("\n========== SUMMARY ==========")
    print("X_train shape:", X_train.shape)
    print("X_test shape :", X_test.shape)
    print("\nFirst 5 rows:")
    print(X_train.head())