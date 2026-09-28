"""Model explainability utilities using SHAP.

This module provides reusable global and local model explanations for
AutoAnalyst. Models and datasets are passed into the functions instead of
being loaded from hard-coded project paths.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False

import matplotlib.pyplot as plt
import pandas as pd
import shap


def _select_positive_class_explanation(explanation):
    """Select the positive-class explanation for binary classifiers."""
    if explanation.values.ndim == 3:
        return explanation[:, :, 1]
    return explanation


def create_explainer(model):
    """Create and return a SHAP TreeExplainer for a tree-based model."""
    return shap.TreeExplainer(model)


def explain_global(
    model,
    X: pd.DataFrame,
    plots_dir: str | Path = "data/plots",
    sample_size: int = 200,
):
    """Generate global SHAP beeswarm and bar plots.

    Args:
        model: Trained tree-based model.
        X: Feature dataframe used for explanation.
        plots_dir: Directory where explanation plots are saved.
        sample_size: Maximum number of rows sampled for explanation.

    Returns:
        tuple: (explainer, explanation)
    """
    plots_dir = Path(plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)

    X_sample = X.sample(min(sample_size, len(X)), random_state=42)

    explainer = create_explainer(model)
    explanation = explainer(X_sample)
    explanation_to_plot = _select_positive_class_explanation(explanation)

    plt.figure()
    shap.plots.beeswarm(explanation_to_plot, show=False)
    plt.title(
        "Which features drive predictions, and in which direction\n"
        "(red = high feature value, blue = low; right = pushes prediction up)"
    )
    plt.tight_layout()
    beeswarm_path = plots_dir / "global_importance_beeswarm.png"
    plt.savefig(beeswarm_path, dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure()
    shap.plots.bar(explanation_to_plot, show=False)
    plt.title(
        "Average impact of each feature on the model's output\n"
        "(mean absolute SHAP value, ranked most to least important)"
    )
    plt.tight_layout()
    bar_path = plots_dir / "global_importance_bar.png"
    plt.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close()

    return explainer, explanation


def explain_one_prediction(
    explainer,
    X: pd.DataFrame,
    row_index: int = 0,
    plots_dir: str | Path = "data/plots",
):
    """Generate a local SHAP waterfall explanation for one prediction."""
    plots_dir = Path(plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)

    if row_index < 0 or row_index >= len(X):
        raise IndexError(f"row_index {row_index} is outside the dataset.")

    row = X.iloc[[row_index]]
    explanation = explainer(row)

    if explanation.values.ndim == 3:
        explanation_to_plot = explanation[0, :, 1]
    else:
        explanation_to_plot = explanation[0]

    plt.figure()
    shap.plots.waterfall(explanation_to_plot, show=False)
    plt.title(
        f"Why the model predicted this for row {row_index}\n"
        "(starts at average prediction, each bar shows one feature's push)"
    )
    plt.tight_layout()

    output_path = plots_dir / f"local_explanation_row{row_index}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    return explanation
