# src/pipeline/model_training_logic.py
import sys
from pathlib import Path
from llm_config import llm, safe_invoke
sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))

import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, r2_score

try:
    from explanation_schema import make_explanation  # type: ignore[reportMissingImports]
except ImportError:
    def make_explanation(**kwargs):
        return kwargs

try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

INTERPRETABLE_MODELS = {"Logistic Regression", "Linear Regression"}
TOLERANCE = 0.03


def detect_problem_type(y: pd.Series) -> str:
    is_text = y.dtype == "object" or pd.api.types.is_string_dtype(y)
    if is_text or y.nunique() <= 10:
        return "classification"
    return "regression"
def encode_categoricals(df: pd.DataFrame, target_col: str | bytes):
    cat_cols = [c for c in df.select_dtypes(include="object").columns if c != target_col]
    explanations = []

    if cat_cols:
        before_cols = df.shape[1]
        df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
        after_cols = df.shape[1]
        explanations.append(make_explanation(
            action=f"One-hot encoded {len(cat_cols)} categorical column(s): {cat_cols}",
            reason="Models require numeric input; these columns contained text categories.",
            alternative_considered="Label encoding (assigning each category an integer)",
            why_not_chosen="Label encoding implies a false numeric order between categories, which one-hot encoding avoids.",
            expected_impact=f"Feature count increased from {before_cols} to {after_cols} columns.",
            learning_note="One-hot encoding is the standard, order-free way to convert categorical text into numeric features.",
            confidence="High",
        ))
    else:
        explanations.append(make_explanation(
            action="No categorical encoding needed",
            reason="No text-based categorical columns remained at this stage.",
            alternative_considered="N/A",
            why_not_chosen="N/A",
            expected_impact="Data proceeds to model training unchanged.",
            learning_note="Encoding is only needed when categorical (text) columns are present.",
            confidence="N/A",
        ))

    return df, explanations


def encode_target_if_needed(y: pd.Series, target_col: str):
    explanations = []

    # Catch classic 'object' dtype AND pandas' newer nullable string dtype
    is_text = y.dtype == "object" or pd.api.types.is_string_dtype(y)

    if is_text:
        original_classes = sorted(y.dropna().unique().tolist())
        encoder = LabelEncoder()
        y_encoded = pd.Series(encoder.fit_transform(y.astype(str)), index=y.index)
        mapping = {cls: int(code) for cls, code in zip(encoder.classes_, encoder.transform(encoder.classes_))}

        explanations.append(make_explanation(
            action=f"Encoded target column '{target_col}' from text labels to numeric",
            reason=f"Target contained text categories {original_classes}; some models (e.g. XGBoost) require numeric class labels.",
            alternative_considered="Leave as text labels",
            why_not_chosen="Several candidate models cannot train on non-numeric target labels.",
            expected_impact=f"Mapping applied: {mapping}.",
            learning_note="Classification targets are commonly stored as text but need numeric encoding for many ML libraries to process them.",
            confidence="High",
        ))
        return y_encoded, explanations, encoder

    return y, explanations, None

def train_and_compare_models(df: pd.DataFrame, target_col: str, needs_interpretability: bool = True):
    explanations = []

    df, encode_explanations = encode_categoricals(df, target_col)
    explanations.extend(encode_explanations)

    X = df.drop(columns=[target_col])
    y_raw = df[target_col]

    problem_type = detect_problem_type(y_raw)

    y, target_encode_explanations, target_encoder = encode_target_if_needed(y_raw, target_col)
    explanations.extend(target_encode_explanations)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if problem_type == "classification" else None,
    )

    if problem_type == "classification":
        candidates = {
            "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
            "Decision Tree": DecisionTreeClassifier(random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
        }
        if XGBOOST_AVAILABLE:
            candidates["XGBoost"] = XGBClassifier(eval_metric="logloss", random_state=42)
        scoring = "roc_auc" if y.nunique() == 2 else "accuracy"
    else:
        candidates = {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(random_state=42),
            "Random Forest": RandomForestRegressor(n_estimators=200, random_state=42),
        }
        if XGBOOST_AVAILABLE:
            candidates["XGBoost"] = XGBRegressor(random_state=42)
        scoring = "r2"

    if problem_type == "classification":
        min_class_count = y_train.value_counts().min()
        n_folds = min(5, min_class_count)
    else:
        n_folds = 5

    if n_folds < 5:
        explanations.append(make_explanation(
            action=f"Reduced cross-validation folds from 5 to {n_folds}",
            reason=f"The smallest class in the training data has only {min_class_count} examples, too few for standard 5-fold CV.",
            alternative_considered="Standard 5-fold cross-validation",
            why_not_chosen="Each fold needs at least one example of every class; a 5-fold split isn't possible with this few minority-class examples.",
            expected_impact="Model evaluation is still valid, but with less statistical stability than a full 5-fold split would provide.",
            learning_note="Cross-validation fold count must be adapted to the smallest class size in imbalanced or small datasets.",
            confidence="High",
        ))

    cv_scores = {}
    for name, model in candidates.items():
        scores = cross_val_score(model, X_train, y_train, cv=n_folds, scoring=scoring)
        cv_scores[name] = scores.mean()

    ranked = sorted(cv_scores.items(), key=lambda x: x[1], reverse=True)
    top_name, top_score = ranked[0]

    chosen_name = top_name
    if needs_interpretability:
        for name, score in ranked:
            if name in INTERPRETABLE_MODELS and (top_score - score) <= TOLERANCE:
                chosen_name = name
                break

    chosen_model = candidates[chosen_name]
    chosen_model.fit(X_train, y_train)

    if problem_type == "classification":
        if scoring == "roc_auc":
            test_score = roc_auc_score(y_test, chosen_model.predict_proba(X_test)[:, 1])
            metric_name = "ROC-AUC"
        else:
            test_score = accuracy_score(y_test, chosen_model.predict(X_test))
            metric_name = "Accuracy"
    else:
        preds = chosen_model.predict(X_test)
        test_score = r2_score(y_test, preds)
        metric_name = "R2"

    runner_up_name, runner_up_score = ranked[1] if len(ranked) > 1 else (None, None)
    score_gap = (cv_scores[chosen_name] - runner_up_score) if runner_up_score is not None else 1.0

    if score_gap > 0.05:
        confidence = "High"
    elif score_gap > 0.01:
        confidence = "Medium"
    else:
        confidence = "Low"

    alt_summary = ", ".join(f"{n} ({s:.3f})" for n, s in ranked if n != chosen_name)

    if chosen_name != top_name:
        why_not = (
            f"'{top_name}' scored marginally higher ({top_score:.3f} vs {cv_scores[chosen_name]:.3f}), "
            f"but the gap was within the {TOLERANCE:.0%} tolerance for preferring an interpretable model."
        )
    else:
        why_not = f"Other candidates scored lower on {scoring}: {alt_summary}."

    explanations.append(make_explanation(
        action=f"Selected {chosen_name} as the final model",
        reason=f"Cross-validated {scoring} score: {cv_scores[chosen_name]:.3f} (5-fold CV on training data).",
        alternative_considered=alt_summary,
        why_not_chosen=why_not,
        expected_impact=f"Test set {metric_name}: {test_score:.3f}.",
        learning_note="Model selection should be based on cross-validated performance, not a single train/test split, to avoid choosing a model that got lucky.",
        confidence=confidence,
    ))

    return chosen_model, chosen_name, X_test, y_test, test_score, explanations