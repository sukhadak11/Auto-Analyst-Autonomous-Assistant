# src/pipeline/model_training_logic.py

import sys
from pathlib import Path

from llm_config import llm, safe_invoke

sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))

import pandas as pd
import shap
import numpy as np

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, r2_score


# -------------------------------------------------------------------
# Explanation helper
# -------------------------------------------------------------------

try:
    from explanation_schema import make_explanation  # type: ignore[reportMissingImports]
except ImportError:

    def make_explanation(**kwargs):
        return kwargs


# -------------------------------------------------------------------
# XGBoost availability
# -------------------------------------------------------------------

try:
    from xgboost import XGBClassifier, XGBRegressor

    XGBOOST_AVAILABLE = True

except ImportError:
    XGBOOST_AVAILABLE = False


# -------------------------------------------------------------------
# Model selection configuration
# -------------------------------------------------------------------

INTERPRETABLE_MODELS = {
    "Logistic Regression",
    "Linear Regression",
}

TOLERANCE = 0.03


# -------------------------------------------------------------------
# Problem type detection
# -------------------------------------------------------------------

def detect_problem_type(y: pd.Series) -> str:

    is_text = (
        y.dtype == "object"
        or pd.api.types.is_string_dtype(y)
    )

    if is_text or y.nunique() <= 10:
        return "classification"

    return "regression"


# -------------------------------------------------------------------
# Encode categorical features
# -------------------------------------------------------------------

def encode_categoricals(
    df: pd.DataFrame,
    target_col: str | bytes
):

    cat_cols = [
        c
        for c in df.select_dtypes(include="object").columns
        if c != target_col
    ]

    explanations = []

    if cat_cols:

        before_cols = df.shape[1]

        df = pd.get_dummies(
            df,
            columns=cat_cols,
            drop_first=True
        )

        after_cols = df.shape[1]

        explanations.append(
            make_explanation(
                action=(
                    f"One-hot encoded {len(cat_cols)} "
                    f"categorical column(s): {cat_cols}"
                ),
                reason=(
                    "Models require numeric input; these columns "
                    "contained text categories."
                ),
                alternative_considered=(
                    "Label encoding (assigning each category an integer)"
                ),
                why_not_chosen=(
                    "Label encoding implies a false numeric order "
                    "between categories, which one-hot encoding avoids."
                ),
                expected_impact=(
                    f"Feature count increased from "
                    f"{before_cols} to {after_cols} columns."
                ),
                learning_note=(
                    "One-hot encoding is the standard, order-free way "
                    "to convert categorical text into numeric features."
                ),
                confidence="High",
            )
        )

    else:

        explanations.append(
            make_explanation(
                action="No categorical encoding needed",
                reason=(
                    "No text-based categorical columns remained "
                    "at this stage."
                ),
                alternative_considered="N/A",
                why_not_chosen="N/A",
                expected_impact=(
                    "Data proceeds to model training unchanged."
                ),
                learning_note=(
                    "Encoding is only needed when categorical "
                    "(text) columns are present."
                ),
                confidence="N/A",
            )
        )

    return df, explanations


# -------------------------------------------------------------------
# Encode target if required
# -------------------------------------------------------------------

def encode_target_if_needed(
    y: pd.Series,
    target_col: str
):

    explanations = []

    # Catch classic object dtype and pandas nullable string dtype
    is_text = (
        y.dtype == "object"
        or pd.api.types.is_string_dtype(y)
    )

    if is_text:

        original_classes = sorted(
            y.dropna().unique().tolist()
        )

        encoder = LabelEncoder()

        y_encoded = pd.Series(
            encoder.fit_transform(y.astype(str)),
            index=y.index
        )

        mapping = {
            cls: int(code)
            for cls, code in zip(
                encoder.classes_,
                encoder.transform(encoder.classes_)
            )
        }

        explanations.append(
            make_explanation(
                action=(
                    f"Encoded target column '{target_col}' "
                    "from text labels to numeric"
                ),
                reason=(
                    f"Target contained text categories "
                    f"{original_classes}; some models "
                    "(e.g. XGBoost) require numeric class labels."
                ),
                alternative_considered="Leave as text labels",
                why_not_chosen=(
                    "Several candidate models cannot train "
                    "on non-numeric target labels."
                ),
                expected_impact=(
                    f"Mapping applied: {mapping}."
                ),
                learning_note=(
                    "Classification targets are commonly stored "
                    "as text but need numeric encoding for many "
                    "ML libraries to process them."
                ),
                confidence="High",
            )
        )

        return y_encoded, explanations, encoder

    return y, explanations, None


# -------------------------------------------------------------------
# Train and compare models
# -------------------------------------------------------------------

def train_and_compare_models(
    df: pd.DataFrame,
    target_col: str,
    needs_interpretability: bool = True
):

    explanations = []

    # ---------------------------------------------------------------
    # Step 1: Encode categorical features
    # ---------------------------------------------------------------

    df, encode_explanations = encode_categoricals(
        df,
        target_col
    )

    explanations.extend(
        encode_explanations
    )

    # ---------------------------------------------------------------
    # Step 2: Separate X and y
    # ---------------------------------------------------------------

    X = df.drop(
        columns=[target_col]
    )

    y_raw = df[target_col]

    # ---------------------------------------------------------------
    # Step 3: Detect problem type
    # ---------------------------------------------------------------

    problem_type = detect_problem_type(
        y_raw
    )

    # ---------------------------------------------------------------
    # Step 4: Encode target if required
    # ---------------------------------------------------------------

    (
        y,
        target_encode_explanations,
        target_encoder
    ) = encode_target_if_needed(
        y_raw,
        target_col
    )

    explanations.extend(
        target_encode_explanations
    )

    # ---------------------------------------------------------------
    # Step 5: Train/test split
    # ---------------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=(
            y
            if problem_type == "classification"
            else None
        ),
    )

    # ---------------------------------------------------------------
    # Step 6: Define candidate models
    # ---------------------------------------------------------------

    if problem_type == "classification":

        candidates = {

            "Logistic Regression": make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=2000
                )
            ),

            "Decision Tree": DecisionTreeClassifier(
                random_state=42
            ),

            "Random Forest": RandomForestClassifier(
                n_estimators=200,
                random_state=42
            ),
        }

        if XGBOOST_AVAILABLE:

            candidates["XGBoost"] = XGBClassifier(
                eval_metric="logloss",
                random_state=42
            )

        scoring = (
            "roc_auc"
            if y.nunique() == 2
            else "accuracy"
        )

    else:

        candidates = {

            "Linear Regression": LinearRegression(),

            "Decision Tree": DecisionTreeRegressor(
                random_state=42
            ),

            "Random Forest": RandomForestRegressor(
                n_estimators=200,
                random_state=42
            ),
        }

        if XGBOOST_AVAILABLE:

            candidates["XGBoost"] = XGBRegressor(
                random_state=42
            )

        scoring = "r2"

    # ---------------------------------------------------------------
    # Step 7: Determine cross-validation folds
    # ---------------------------------------------------------------

    if problem_type == "classification":

        min_class_count = (
            y_train.value_counts().min()
        )

        n_folds = min(
            5,
            min_class_count
        )

    else:

        n_folds = 5

    # ---------------------------------------------------------------
    # Step 8: Explain CV fold adjustment
    # ---------------------------------------------------------------

    if n_folds < 5:

        explanations.append(
            make_explanation(
                action=(
                    f"Reduced cross-validation folds "
                    f"from 5 to {n_folds}"
                ),
                reason=(
                    f"The smallest class in the training "
                    f"data has only {min_class_count} examples, "
                    "too few for standard 5-fold CV."
                ),
                alternative_considered=(
                    "Standard 5-fold cross-validation"
                ),
                why_not_chosen=(
                    "Each fold needs at least one example "
                    "of every class; a 5-fold split isn't "
                    "possible with this few minority-class examples."
                ),
                expected_impact=(
                    "Model evaluation is still valid, but with "
                    "less statistical stability than a full "
                    "5-fold split would provide."
                ),
                learning_note=(
                    "Cross-validation fold count must be adapted "
                    "to the smallest class size in imbalanced "
                    "or small datasets."
                ),
                confidence="High",
            )
        )

    # ---------------------------------------------------------------
    # Step 9: Cross-validation
    # ---------------------------------------------------------------

    cv_scores = {}

    for name, model in candidates.items():

        scores = cross_val_score(
            model,
            X_train,
            y_train,
            cv=n_folds,
            scoring=scoring
        )

        cv_scores[name] = scores.mean()

    # ---------------------------------------------------------------
    # Step 10: Rank models
    # ---------------------------------------------------------------

    ranked = sorted(
        cv_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_name, top_score = ranked[0]

    chosen_name = top_name

    # ---------------------------------------------------------------
    # Step 11: Prefer interpretable model when performance
    #         difference is within tolerance
    # ---------------------------------------------------------------

    if needs_interpretability:

        for name, score in ranked:

            if (
                name in INTERPRETABLE_MODELS
                and (top_score - score) <= TOLERANCE
            ):

                chosen_name = name

                break

    # ---------------------------------------------------------------
    # Step 12: Train selected model
    # ---------------------------------------------------------------

    chosen_model = candidates[
        chosen_name
    ]

    chosen_model.fit(
        X_train,
        y_train
    )

    # ---------------------------------------------------------------
    # Step 13: Evaluate selected model
    # ---------------------------------------------------------------

    if problem_type == "classification":

        if scoring == "roc_auc":

            test_score = roc_auc_score(
                y_test,
                chosen_model.predict_proba(
                    X_test
                )[:, 1]
            )

            metric_name = "ROC-AUC"

        else:

            test_score = accuracy_score(
                y_test,
                chosen_model.predict(
                    X_test
                )
            )

            metric_name = "Accuracy"

    else:

        preds = chosen_model.predict(
            X_test
        )

        test_score = r2_score(
            y_test,
            preds
        )

        metric_name = "R2"

    # ---------------------------------------------------------------
    # Step 14: Compare selected model against runner-up
    # ---------------------------------------------------------------

    runner_up_name, runner_up_score = (
        ranked[1]
        if len(ranked) > 1
        else (None, None)
    )

    score_gap = (
        cv_scores[chosen_name] - runner_up_score
        if runner_up_score is not None
        else 1.0
    )

    if score_gap > 0.05:

        confidence = "High"

    elif score_gap > 0.01:

        confidence = "Medium"

    else:

        confidence = "Low"

    # ---------------------------------------------------------------
    # Step 15: Explain alternative models
    # ---------------------------------------------------------------

    alt_summary = ", ".join(
        f"{n} ({s:.3f})"
        for n, s in ranked
        if n != chosen_name
    )

    if chosen_name != top_name:

        why_not = (
            f"'{top_name}' scored marginally higher "
            f"({top_score:.3f} vs "
            f"{cv_scores[chosen_name]:.3f}), "
            f"but the gap was within the "
            f"{TOLERANCE:.0%} tolerance for "
            "preferring an interpretable model."
        )

    else:

        why_not = (
            f"Other candidates scored lower on "
            f"{scoring}: {alt_summary}."
        )

    # ---------------------------------------------------------------
    # Step 16: Add model-selection explanation
    # ---------------------------------------------------------------

    explanations.append(
        make_explanation(
            action=(
                f"Selected {chosen_name} "
                "as the final model"
            ),
            reason=(
                f"Cross-validated {scoring} score: "
                f"{cv_scores[chosen_name]:.3f} "
                "(5-fold CV on training data)."
            ),
            alternative_considered=alt_summary,
            why_not_chosen=why_not,
            expected_impact=(
                f"Test set {metric_name}: "
                f"{test_score:.3f}."
            ),
            learning_note=(
                "Model selection should be based on "
                "cross-validated performance, not a single "
                "train/test split, to avoid choosing a model "
                "that got lucky."
            ),
            confidence=confidence,
        )
    )

    # ---------------------------------------------------------------
    # Step 17: Return training results
    # ---------------------------------------------------------------

    return (
        chosen_model,
        chosen_name,
        X_test,
        y_test,
        test_score,
        explanations
    )


# -------------------------------------------------------------------
# SHAP MODEL EXPLANATION
# -------------------------------------------------------------------

def explain_model(chosen_model, chosen_name, X_train, X_test):
    explanations = []

    try:
        if chosen_name in ("Random Forest", "XGBoost", "Decision Tree"):
            explainer = shap.TreeExplainer(chosen_model)
            shap_values = explainer.shap_values(X_test)

            if isinstance(shap_values, list):
                # older SHAP behavior: list of per-class arrays
                values = shap_values[1]
            elif hasattr(shap_values, "ndim") and shap_values.ndim == 3:
                # newer SHAP behavior: single 3D array (n_samples, n_features, n_classes)
                # take the positive class (index 1) for binary classification
                values = shap_values[:, :, 1]
            else:
                values = shap_values

        else:
            explainer = shap.LinearExplainer(chosen_model, X_train)
            values = explainer.shap_values(X_test)
            if hasattr(values, "ndim") and values.ndim == 3:
                values = values[:, :, 1]

        mean_abs_shap = np.abs(values).mean(axis=0)
        feature_importance = sorted(
            zip(X_test.columns, mean_abs_shap), key=lambda x: x[1], reverse=True
        )
        feature_importance = [(name, float(val)) for name, val in feature_importance]  # ensure plain floats

        top_features = feature_importance[:5]
        top_summary = ", ".join(f"{name} ({val:.3f})" for name, val in top_features)

        explanations.append(make_explanation(
            action=f"Computed SHAP feature importance for {chosen_name}",
            reason="SHAP values quantify how much each feature pushed individual predictions toward or away from the predicted class, averaged across the test set.",
            alternative_considered="Built-in model feature_importances_ (e.g. Random Forest's Gini importance)",
            why_not_chosen="SHAP is more reliable for correlated features and gives consistent, per-prediction explanations, not just an overall ranking.",
            expected_impact=f"Top drivers identified: {top_summary}.",
            learning_note="SHAP values show both the magnitude and direction of each feature's effect on individual predictions, not just overall importance.",
            confidence="High",
        ))

        return feature_importance, explanations

    except Exception as e:
        explanations.append(make_explanation(
            action="SHAP explanation skipped",
            reason=f"SHAP computation failed for this model type: {str(e)[:150]}",
            alternative_considered="Model-specific feature importance",
            why_not_chosen="Not automatically substituted — flagged so the limitation is visible in the report.",
            expected_impact="Feature-level driver explanations will not be available for this report.",
            learning_note="Not all model/data combinations support SHAP out of the box.",
            confidence="N/A",
        ))
        return [], explanations