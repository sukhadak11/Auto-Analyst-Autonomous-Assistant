import pandas as pd
import joblib
from pathlib import Path

from src.agent.graph_state import AgentState
from src.agent.explanation_schema import format_explanations

import sys

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "pipeline")
)

from src.pipeline.model_training_logic import (
    train_and_compare_models,
    explain_model,
)


def model_training_agent_node(state: AgentState) -> AgentState:

    # ---------------------------------------------------------------
    # Get pipeline configuration from state
    # ---------------------------------------------------------------

    clean_path = state.get(
        "clean_path",
        "data/clean_data.csv"
    )

    target_col = state.get(
        "target_col"
    )

    needs_interpretability = state.get(
        "needs_interpretability",
        True
    )

    job_id = state.get(
        "job_id",
        "manual_test"
    )

    # ---------------------------------------------------------------
    # Load cleaned dataset
    # ---------------------------------------------------------------

    df = pd.read_csv(
        clean_path
    )

    # ---------------------------------------------------------------
    # Train and compare candidate models
    #
    # train_and_compare_models returns:
    #   1. trained model
    #   2. model name
    #   3. X_test
    #   4. y_test
    #   5. test score
    #   6. explanations
    # ---------------------------------------------------------------

    (
        model,
        model_name,
        X_test,
        y_test,
        test_score,
        explanations,
    ) = train_and_compare_models(
        df,
        target_col,
        needs_interpretability
    )

    # ---------------------------------------------------------------
    # SHAP feature importance
    #
    # We need X_train for LinearExplainer.
    # Since train_and_compare_models currently returns only X_test,
    # reconstruct the training split using the same random_state.
    # ---------------------------------------------------------------

    feature_importance = []

    try:

        # Recreate the same feature preprocessing used during
        # model training.

        from src.pipeline.model_training_logic import (
            encode_categoricals,
            encode_target_if_needed,
        )

        processed_df, _ = encode_categoricals(
            df.copy(),
            target_col
        )

        X = processed_df.drop(
            columns=[target_col]
        )

        y_raw = processed_df[target_col]

        y, _, _ = encode_target_if_needed(
            y_raw,
            target_col
        )

        from sklearn.model_selection import train_test_split

        X_train, _, _, _ = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=(
                y
                if y.nunique() <= 10
                else None
            ),
        )

        # -----------------------------------------------------------
        # Run SHAP explanation
        # -----------------------------------------------------------

        feature_importance, shap_explanations = explain_model(
            model,
            model_name,
            X_train,
            X_test
        )

        # Add SHAP explanations to the existing explanations.
        explanations.extend(
            shap_explanations
        )

    except Exception as e:

        # SHAP should not stop the complete model-training pipeline.

        shap_explanations = [{
            "action": "SHAP explanation skipped",
            "reason": (
                f"SHAP analysis could not be completed: "
                f"{str(e)[:150]}"
            ),
            "alternative_considered": (
                "Model-specific feature importance"
            ),
            "why_not_chosen": (
                "The SHAP analysis was not available "
                "for this model/data combination."
            ),
            "expected_impact": (
                "Model training completed, but "
                "feature-level SHAP explanations "
                "are unavailable."
            ),
            "learning_note": (
                "Feature explanation methods depend "
                "on the model type and input data."
            ),
            "confidence": "N/A",
        }]

        explanations.extend(
            shap_explanations
        )

    # ---------------------------------------------------------------
    # Save trained model
    # ---------------------------------------------------------------

    model_path = (
        f"data/model_{job_id}.joblib"
    )

    joblib.dump(
        model,
        model_path
    )

    # ---------------------------------------------------------------
    # Update AgentState
    # ---------------------------------------------------------------

    state["model_path"] = model_path

    state["model_name"] = model_name

    state["feature_importance"] = (
        feature_importance
    )

    state["explanations"] = (
        state.get("explanations", [])
        + explanations
    )

    # ---------------------------------------------------------------
    # Convert structured explanations into readable findings
    # ---------------------------------------------------------------

    state["data_findings"] = (
        state.get("data_findings", "")
        + "\n"
        + format_explanations(
            explanations
        )
    )

    # ---------------------------------------------------------------
    # Add agent message
    # ---------------------------------------------------------------

    state["messages"] = (
        state.get("messages", [])
        + [
            (
                f"Model Training Agent: selected "
                f"{model_name} with test score "
                f"{test_score:.3f} and generated "
                "SHAP-based feature explanations."
            )
        ]
    )

    return state