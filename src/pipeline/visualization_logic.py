# visualization_logic.py

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# ============================================================
# Configuration
# ============================================================

DEFAULT_OUTPUT_DIR = "data/plots"

VISUALIZATION_KEYWORDS = [
    "show",
    "visualize",
    "visualization",
    "visualizations",
    "chart",
    "charts",
    "plot",
    "plots",
    "graph",
    "graphs",
    "trend",
    "compare",
    "comparison",
    "distribution",
    "relationship",
    "correlation",
    "rate",
    "percentage",
    "proportion",
    "breakdown",
]


# ============================================================
# Utility functions
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize text for easier column/question matching."""
    text = str(text).lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def column_matches_question(column: str, question: str) -> bool:
    """
    Check whether a dataframe column is mentioned in the user's question.
    Handles both snake_case and normal text.
    """
    normalized_question = normalize_text(question)
    normalized_column = normalize_text(column)

    if normalized_column in normalized_question:
        return True

    # Handle common compact names
    compact_column = normalized_column.replace(" ", "")
    compact_question = normalized_question.replace(" ", "")

    return compact_column in compact_question


def find_mentioned_columns(df: pd.DataFrame, question: str) -> list:
    """Return dataframe columns explicitly mentioned in the question."""
    mentioned = []

    for column in df.columns:
        if column_matches_question(column, question):
            mentioned.append(column)

    return mentioned


def is_visualization_request(question: str) -> bool:
    """Determine whether the user is asking for a visualization."""
    q = normalize_text(question)

    return any(keyword in q for keyword in VISUALIZATION_KEYWORDS)


def safe_filename(value: str) -> str:
    """Convert a string into a filesystem-safe filename."""
    value = str(value)
    value = re.sub(r"[^a-zA-Z0-9_-]", "_", value)
    return value[:100]


def save_chart(fig, output_path: Path):
    """Save chart consistently."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
        format="png",
    )

    plt.close(fig)


def chart_metadata(chart_type: str, path: Path) -> dict:
    """Return JSON-friendly chart metadata."""
    return {
        "chart_type": chart_type,
        "filename": path.name,
    }


# ============================================================
# Chart generation functions
# ============================================================

def generate_target_distribution(
    df: pd.DataFrame,
    target_col: str,
    job_id: str,
    output_dir: Path,
):
    """Generate target distribution chart."""

    if not target_col or target_col not in df.columns:
        return None

    counts = df[target_col].value_counts(dropna=False)

    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    counts.plot(
        kind="bar",
        ax=ax,
    )

    ax.set_title(f"Distribution of {target_col}")
    ax.set_xlabel(target_col)
    ax.set_ylabel("Number of Customers")

    path = output_dir / (
        f"target_distribution_{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata("target_distribution", path)


def generate_categorical_comparison(
    df: pd.DataFrame,
    category_col: str,
    target_col: str,
    job_id: str,
    output_dir: Path,
):
    """
    Compare target rate across categories.

    Example:
        international_plan vs churn
    """

    if category_col not in df.columns:
        return None

    if target_col not in df.columns:
        return None

    data = df[[category_col, target_col]].dropna()

    if data.empty:
        return None

    # Convert binary target to numeric when possible
    target_values = data[target_col].dropna().unique()

    if len(target_values) != 2:
        return None

    # Try to identify churn/positive class
    positive_values = {
        "yes",
        "true",
        "1",
        "churn",
        "churned",
    }

    def is_positive(value):
        return str(value).lower() in positive_values

    positive = data[target_col].apply(is_positive)

    # If values aren't recognizable as binary labels,
    # use the second sorted category as positive.
    if positive.sum() == 0:
        sorted_values = sorted(
            [str(v) for v in target_values]
        )

        if len(sorted_values) == 2:
            positive = (
                data[target_col].astype(str)
                == sorted_values[1]
            )

    rates = (
        positive.astype(int)
        .groupby(data[category_col])
        .mean()
        .mul(100)
        .sort_values(ascending=False)
    )

    if rates.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    rates.plot(
        kind="bar",
        ax=ax,
    )

    ax.set_title(
        f"Churn Rate by {category_col.replace('_', ' ').title()}"
    )
    ax.set_xlabel(
        category_col.replace("_", " ").title()
    )
    ax.set_ylabel("Churn Rate (%)")

    path = output_dir / (
        f"grouped_{safe_filename(category_col)}_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata("grouped_comparison", path)


def generate_numeric_target_comparison(
    df: pd.DataFrame,
    numeric_col: str,
    target_col: str,
    job_id: str,
    output_dir: Path,
):
    """
    Compare a numerical feature across target classes.

    Example:
        day_mins vs churn
        total_charge vs churn
    """

    if numeric_col not in df.columns:
        return None

    if target_col not in df.columns:
        return None

    data = df[[numeric_col, target_col]].dropna()

    if data.empty:
        return None

    if data[target_col].nunique() < 2:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    sns.boxplot(
        data=data,
        x=target_col,
        y=numeric_col,
        ax=ax,
    )

    ax.set_title(
        f"{numeric_col.replace('_', ' ').title()} by "
        f"{target_col.replace('_', ' ').title()}"
    )

    ax.set_xlabel(
        target_col.replace("_", " ").title()
    )

    ax.set_ylabel(
        numeric_col.replace("_", " ").title()
    )

    path = output_dir / (
        f"numeric_comparison_{safe_filename(numeric_col)}_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata("numeric_target_comparison", path)


def generate_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    job_id: str,
    output_dir: Path,
):
    """Generate scatter plot for two numerical variables."""

    if x_col not in df.columns or y_col not in df.columns:
        return None

    data = df[[x_col, y_col]].dropna()

    if len(data) < 2:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        data[x_col],
        data[y_col],
        alpha=0.6,
    )

    ax.set_title(
        f"{x_col.replace('_', ' ').title()} vs "
        f"{y_col.replace('_', ' ').title()}"
    )

    ax.set_xlabel(
        x_col.replace("_", " ").title()
    )

    ax.set_ylabel(
        y_col.replace("_", " ").title()
    )

    path = output_dir / (
        f"scatter_{safe_filename(x_col)}_"
        f"{safe_filename(y_col)}_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata("scatter", path)


def generate_correlation_heatmap(
    df: pd.DataFrame,
    job_id: str,
    output_dir: Path,
):
    """Generate correlation heatmap for numerical columns."""

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.shape[1] < 2:
        return None

    correlation = numeric_df.corr()

    fig, ax = plt.subplots(
        figsize=(10, 8)
    )

    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        ax=ax,
    )

    ax.set_title(
        "Correlation Between Numerical Features"
    )

    path = output_dir / (
        f"correlation_heatmap_{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata("correlation_heatmap", path)


def generate_feature_importance_chart(
    feature_importance: list,
    job_id: str,
    output_dir: Path,
):
    """Generate feature importance chart."""

    if not feature_importance:
        return None

    cleaned = []

    for item in feature_importance:
        try:
            feature, importance = item

            if feature is None:
                continue

            importance = float(importance)

            cleaned.append(
                (str(feature), importance)
            )

        except (ValueError, TypeError):
            continue

    if not cleaned:
        return None

    importance_df = pd.DataFrame(
        cleaned,
        columns=["feature", "importance"],
    )

    importance_df = (
        importance_df
        .sort_values("importance", ascending=True)
        .tail(10)
    )

    fig, ax = plt.subplots(
        figsize=(9, 6)
    )

    ax.barh(
        importance_df["feature"],
        importance_df["importance"],
    )

    ax.set_title(
        "Top Factors Associated with Churn"
    )

    ax.set_xlabel("Importance")
    ax.set_ylabel("Feature")

    path = output_dir / (
        f"feature_importance_{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata(
        "feature_importance_bar",
        path,
    )


# ============================================================
# Intelligent visualization selection
# ============================================================

def select_and_generate_visualizations(
    df: pd.DataFrame,
    target_col: str,
    question: str,
    feature_importance: list,
    job_id: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
):
    """
    Automatically select and generate useful visualizations
    based on the user's question and dataset.

    Returns:
        generated_charts: List[dict]
        explanations: List[str]
    """

    output_path = Path(output_dir)
    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_charts = []
    explanations = []

    question_lower = normalize_text(question)

    # --------------------------------------------------------
    # 1. Check whether visualization is requested
    # --------------------------------------------------------

    if not is_visualization_request(question):
        explanations.append(
            "No visualization was generated because "
            "the question does not explicitly request "
            "a chart, plot, graph, comparison, or visualization."
        )

        return generated_charts, explanations

    # --------------------------------------------------------
    # 2. Find columns mentioned by user
    # --------------------------------------------------------

    mentioned_columns = find_mentioned_columns(
        df,
        question,
    )

    numeric_columns = list(
        df.select_dtypes(include="number").columns
    )

    categorical_columns = list(
        df.select_dtypes(
            include=["object", "category", "bool"]
        ).columns
    )

    # --------------------------------------------------------
    # 3. Identify target
    # --------------------------------------------------------

    target_exists = (
        target_col
        and target_col in df.columns
    )

    # --------------------------------------------------------
    # 4. Feature importance request
    # --------------------------------------------------------

    importance_keywords = [
        "top driver",
        "top drivers",
        "important factor",
        "important factors",
        "key factor",
        "key factors",
        "feature importance",
        "important features",
        "driving churn",
        "drivers of churn",
        "factors associated with churn",
    ]

    wants_importance = any(
        keyword in question_lower
        for keyword in importance_keywords
    )

    if wants_importance and feature_importance:
        chart = generate_feature_importance_chart(
            feature_importance,
            job_id,
            output_path,
        )

        if chart:
            generated_charts.append(chart)

            explanations.append(
                "A feature-importance chart was generated "
                "to show the strongest factors associated "
                "with the target."
            )

    # --------------------------------------------------------
    # 5. Explicit categorical comparisons
    # --------------------------------------------------------

    if target_exists:

        mentioned_categorical = [
            col
            for col in mentioned_columns
            if col in categorical_columns
            and col != target_col
        ]

        # If user explicitly mentioned a categorical feature,
        # prioritize it.
        for col in mentioned_categorical[:2]:

            chart = generate_categorical_comparison(
                df=df,
                category_col=col,
                target_col=target_col,
                job_id=job_id,
                output_dir=output_path,
            )

            if chart:
                generated_charts.append(chart)

                explanations.append(
                    f"A churn-rate comparison was generated "
                    f"for {col}."
                )

    # --------------------------------------------------------
    # 6. Numerical feature vs target
    # --------------------------------------------------------

    if target_exists:

        mentioned_numeric = [
            col
            for col in mentioned_columns
            if col in numeric_columns
            and col != target_col
        ]

        wants_relationship = any(
            word in question_lower
            for word in [
                "relationship",
                "association",
                "affect",
                "impact",
                "difference",
                "compare",
                "versus",
                "vs",
                "against",
            ]
        )

        if wants_relationship:

            for col in mentioned_numeric[:2]:

                chart = generate_numeric_target_comparison(
                    df=df,
                    numeric_col=col,
                    target_col=target_col,
                    job_id=job_id,
                    output_dir=output_path,
                )

                if chart:
                    generated_charts.append(chart)

                    explanations.append(
                        f"A numerical comparison chart was "
                        f"generated for {col} against "
                        f"{target_col}."
                    )

    # --------------------------------------------------------
    # 7. Explicit numeric-vs-numeric relationship
    # --------------------------------------------------------

    mentioned_numeric = [
        col
        for col in mentioned_columns
        if col in numeric_columns
    ]

    if len(mentioned_numeric) >= 2:

        relationship_keywords = [
            "relationship",
            "correlation",
            "correlated",
            "association",
            "versus",
            "vs",
            "against",
        ]

        wants_relationship = any(
            word in question_lower
            for word in relationship_keywords
        )

        if wants_relationship:

            chart = generate_scatter_plot(
                df=df,
                x_col=mentioned_numeric[0],
                y_col=mentioned_numeric[1],
                job_id=job_id,
                output_dir=output_path,
            )

            if chart:
                generated_charts.append(chart)

                explanations.append(
                    f"A scatter plot was generated to show "
                    f"the relationship between "
                    f"{mentioned_numeric[0]} and "
                    f"{mentioned_numeric[1]}."
                )

    # --------------------------------------------------------
    # 8. Target distribution
    # --------------------------------------------------------

    distribution_keywords = [
        "distribution",
        "how many",
        "proportion",
        "percentage",
        "churn rate",
        "churn distribution",
        "balance",
    ]

    wants_distribution = any(
        keyword in question_lower
        for keyword in distribution_keywords
    )

    target_was_explicitly_mentioned = (
        target_col
        and target_col in mentioned_columns
    )

    if target_exists and (
        wants_distribution
        or target_was_explicitly_mentioned
    ):

        chart = generate_target_distribution(
            df=df,
            target_col=target_col,
            job_id=job_id,
            output_dir=output_path,
        )

        if chart:
            generated_charts.append(chart)

            explanations.append(
                f"A distribution chart was generated "
                f"for {target_col}."
            )

    # --------------------------------------------------------
    # 9. Correlation request
    # --------------------------------------------------------

    correlation_keywords = [
        "correlation",
        "correlations",
        "correlated",
        "heatmap",
    ]

    wants_correlation = any(
        keyword in question_lower
        for keyword in correlation_keywords
    )

    if wants_correlation:

        chart = generate_correlation_heatmap(
            df=df,
            job_id=job_id,
            output_dir=output_path,
        )

        if chart:
            generated_charts.append(chart)

            explanations.append(
                "A correlation heatmap was generated "
                "for the numerical features."
            )

    # --------------------------------------------------------
    # 10. Fallback visualization
    # --------------------------------------------------------
    #
    # If user explicitly asks for visualization but did not
    # mention a specific feature, use the most useful available
    # visualization rather than returning nothing.
    # --------------------------------------------------------

    if not generated_charts:

        if target_exists and feature_importance:

            chart = generate_feature_importance_chart(
                feature_importance,
                job_id,
                output_path,
            )

            if chart:
                generated_charts.append(chart)

                explanations.append(
                    "A feature-importance chart was selected "
                    "as the most relevant visualization for "
                    "the analysis question."
                )

        elif target_exists:

            chart = generate_target_distribution(
                df=df,
                target_col=target_col,
                job_id=job_id,
                output_dir=output_path,
            )

            if chart:
                generated_charts.append(chart)

                explanations.append(
                    "A target-distribution chart was selected "
                    "as a useful overview of the requested analysis."
                )

        elif len(numeric_columns) >= 2:

            chart = generate_correlation_heatmap(
                df=df,
                job_id=job_id,
                output_dir=output_path,
            )

            if chart:
                generated_charts.append(chart)

                explanations.append(
                    "A correlation heatmap was selected because "
                    "the dataset contains multiple numerical features."
                )

    # --------------------------------------------------------
    # 11. Remove duplicate filenames
    # --------------------------------------------------------

    unique_charts = []
    seen_files = set()

    for chart in generated_charts:

        filename = chart.get("filename")

        if filename and filename not in seen_files:
            unique_charts.append(chart)
            seen_files.add(filename)

    generated_charts = unique_charts

    # --------------------------------------------------------
    # 12. Final explanation
    # --------------------------------------------------------

    if generated_charts:

        explanations.append(
            f"Generated {len(generated_charts)} visualization(s) "
            f"based on the user's question and available dataset features."
        )

    else:

        explanations.append(
            "No suitable visualization could be generated "
            "from the requested analysis and available data."
        )

    return generated_charts, explanations