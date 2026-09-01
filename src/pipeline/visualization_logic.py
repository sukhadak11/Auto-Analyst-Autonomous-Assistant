import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))

import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['text.parse_math'] = False
import matplotlib.pyplot as plt
from explanation_schema import make_explanation


def select_and_generate_visualizations(
    df: pd.DataFrame,
    target_col: str,
    question: str,
    feature_importance: list,
    job_id: str,
    output_dir: str = "data/plots",
):
    """Decides which charts are useful based on real data characteristics
    and the question, then actually generates them. Returns a list of
    (chart_type, file_path) and explanations for each choice."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    explanations = []
    generated_charts = []

    question_lower = question.lower()
    num_cols = [c for c in df.select_dtypes(include="number").columns if c != target_col]

    # 1. Feature importance bar chart — generated whenever real importance data exists,
    #    since this is almost always the most useful single chart for "why" questions
    if feature_importance:
        top_n = feature_importance[:8]
        names = [f[0] for f in top_n]
        values = [f[1] for f in top_n]

        plt.figure(figsize=(8, 5))
        plt.barh(names[::-1], values[::-1])
        plt.xlabel("Mean |SHAP value| (impact on prediction)")
        plt.title("Top feature drivers")
        plt.tight_layout()
        path = f"{output_dir}/feature_importance_{job_id}.png"
        plt.savefig(path, dpi=150)
        plt.close()

        generated_charts.append(("feature_importance_bar", path))
        explanations.append(make_explanation(
            action="Generated a feature importance bar chart",
            reason="Real SHAP-based feature importance values were available from Model Training, and the business question relates to what drives the outcome.",
            alternative_considered="Skip visualization, describe drivers in text only",
            why_not_chosen="A ranked bar chart communicates relative driver strength faster than a text list, especially for non-technical stakeholders.",
            expected_impact="Report includes a chart showing the top drivers ranked by actual impact on predictions.",
            learning_note="Bar charts are effective for ranked, named categories — better than pie/line charts for this kind of comparison.",
            confidence="High",
        ))

    # 2. Target class distribution — useful whenever the question touches on
    #    "how many/what proportion" or class imbalance is relevant
    balance_keywords = ["how many", "proportion", "rate", "percentage", "distribution", "balance"]
    if any(kw in question_lower for kw in balance_keywords) or target_col in df.columns:
        plt.figure(figsize=(6, 4))
        df[target_col].value_counts().plot(kind="bar")
        plt.xlabel(target_col)
        plt.ylabel("Count")
        plt.title(f"Distribution of {target_col}")
        plt.tight_layout()
        path = f"{output_dir}/target_distribution_{job_id}.png"
        plt.savefig(path, dpi=150)
        plt.close()

        generated_charts.append(("target_distribution", path))
        explanations.append(make_explanation(
            action=f"Generated a distribution chart for '{target_col}'",
            reason="The target column's class balance is directly relevant to interpreting model results and was computed during Cleaning.",
            alternative_considered="Pie chart",
            why_not_chosen="Bar charts are more accurate for comparing two or more category sizes than pie charts, which can visually distort proportions.",
            expected_impact="Report includes a visual showing the real class split in the data.",
            learning_note="Bar charts are generally preferred over pie charts for precise quantity comparison.",
            confidence="Medium",
        ))

    # 3. Correlation heatmap — only if the question is explicitly about relationships/patterns,
    #    and there are enough numeric features for it to be meaningful
    relationship_keywords = ["relationship", "correlat", "pattern", "relate", "connection"]
    if any(kw in question_lower for kw in relationship_keywords) and len(num_cols) >= 3:
        corr = df[num_cols].corr()
        plt.figure(figsize=(8, 6))
        plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
        plt.colorbar(label="Correlation")
        plt.xticks(range(len(num_cols)), num_cols, rotation=90, fontsize=7)
        plt.yticks(range(len(num_cols)), num_cols, fontsize=7)
        plt.title("Feature correlation matrix")
        plt.tight_layout()
        path = f"{output_dir}/correlation_heatmap_{job_id}.png"
        plt.savefig(path, dpi=150)
        plt.close()

        generated_charts.append(("correlation_heatmap", path))
        explanations.append(make_explanation(
            action="Generated a correlation heatmap",
            reason=f"The question explicitly asks about relationships/patterns, and {len(num_cols)} numeric features are available for comparison.",
            alternative_considered="Individual scatter plots for each feature pair",
            why_not_chosen="A heatmap summarizes all pairwise relationships in one view; scatter plots would require one chart per pair, too many to include.",
            expected_impact="Report includes a visual showing which features move together.",
            learning_note="Heatmaps are effective for showing many pairwise relationships at once, but don't show the shape of individual relationships — use scatter plots for that when only 1-2 pairs matter.",
            confidence="High",
        ))

    if not generated_charts:
        explanations.append(make_explanation(
            action="No visualizations generated",
            reason="Neither feature importance data, class-balance relevance, nor relationship/correlation language was found to justify a specific chart.",
            alternative_considered="Generate a default chart regardless",
            why_not_chosen="Generating charts without a clear reason adds clutter rather than clarity.",
            expected_impact="Report proceeds with text-only findings.",
            learning_note="Not every analysis benefits from a visualization — charts should be added when they clarify, not by default.",
            confidence="Medium",
        ))

    return generated_charts, explanations