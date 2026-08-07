import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

CLEAN_PATH = Path("data/clean_data.csv")
MODEL_PATH = Path("data/model.joblib")

def load_clean_data(target_col: str):
    df = pd.read_csv(CLEAN_PATH)
    X = df.drop(columns=[target_col])
    y = df[target_col]
    return X, y

def train_and_evaluate(target_col: str):
    X, y = load_clean_data(target_col)

    # split BEFORE any further preprocessing to avoid leakage
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=200, random_state=42)

    # cross-validation on training set only
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc")
    print(f"CV ROC-AUC: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    # fit on full training set
    model.fit(X_train, y_train)

    # evaluate on untouched test set
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    print("\nTest set performance:")
    print(classification_report(y_test, preds))
    print(f"Test ROC-AUC: {roc_auc_score(y_test, probs):.3f}")

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    return model, X_test, y_test

if __name__ == "__main__":
    train_and_evaluate(target_col="churn")  