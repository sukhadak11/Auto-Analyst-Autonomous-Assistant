import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


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
# Utility Functions
# ============================================================

def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def display_name(column: str) -> str:
    return str(column).replace("_", " ").strip().title()


def safe_filename(value: str) -> str:
    value = str(value)
    value = re.sub(r"[^a-zA-Z0-9_-]", "_", value)
    return value[:100]


def is_visualization_request(question: str) -> bool:
    question_text = normalize_text(question)

    return any(
        keyword in question_text
        for keyword in VISUALIZATION_KEYWORDS
    )


def column_matches_question(
    column: str,
    question: str,
) -> bool:

    normalized_question = normalize_text(question)
    normalized_column = normalize_text(column)

    if normalized_column in normalized_question:
        return True

    compact_column = normalized_column.replace(" ", "")
    compact_question = normalized_question.replace(" ", "")

    return compact_column in compact_question


def find_mentioned_columns(
    df: pd.DataFrame,
    question: str,
) -> list:

    return [
        column
        for column in df.columns
        if column_matches_question(column, question)
    ]


def save_chart(
    fig,
    output_path: Path,
):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
        format="png",
    )

    plt.close(fig)


def chart_metadata(
    chart_type: str,
    path: Path,
) -> dict:

    return {
        "chart_type": chart_type,
        "filename": path.name,
    }


def make_explanation(
    action: str,
    reason: str,
    alternative: str,
    why_not_chosen: str,
    impact: str,
    learning_note: str,
    confidence: str = "High",
) -> dict:

    return {
        "action": action,
        "reason": reason,
        "alternative_considered": alternative,
        "why_not_chosen": why_not_chosen,
        "expected_impact": impact,
        "learning_note": learning_note,
        "confidence": confidence,
    }


# ============================================================
# Target Distribution
# ============================================================

def generate_target_distribution(
    df: pd.DataFrame,
    target_col: str,
    job_id: str,
    output_dir: Path,
):

    if not target_col or target_col not in df.columns:
        return None

    series = df[target_col].dropna()

    if series.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    if pd.api.types.is_numeric_dtype(series):

        series.plot(
            kind="hist",
            bins=20,
            ax=ax,
        )

        ax.set_xlabel(
            display_name(target_col)
        )

        ax.set_ylabel("Frequency")

        title = (
            f"Distribution of "
            f"{display_name(target_col)}"
        )

    else:

        counts = (
            series
            .astype(str)
            .value_counts()
            .head(15)
        )

        counts.plot(
            kind="bar",
            ax=ax,
        )

        ax.set_xlabel(
            display_name(target_col)
        )

        ax.set_ylabel("Count")

        title = (
            f"Distribution of "
            f"{display_name(target_col)}"
        )

    ax.set_title(title)

    path = output_dir / (
        f"target_distribution_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata(
        "target_distribution",
        path,
    )


# ============================================================
# Categorical Comparison
# ============================================================

def generate_categorical_comparison(
    df: pd.DataFrame,
    category_col: str,
    target_col: str,
    job_id: str,
    output_dir: Path,
):

    if (
        category_col not in df.columns
        or target_col not in df.columns
    ):
        return None

    data = df[
        [category_col, target_col]
    ].dropna()

    if data.empty:
        return None

    if data[category_col].nunique() > 15:
        data = data[
            data[category_col].isin(
                data[category_col]
                .value_counts()
                .head(15)
                .index
            )
        ]

    fig, ax = plt.subplots(
        figsize=(9, 5)
    )

    # Numeric target
    if pd.api.types.is_numeric_dtype(
        data[target_col]
    ):

        grouped = (
            data.groupby(category_col)[target_col]
            .mean()
            .sort_values(ascending=False)
        )

        grouped.plot(
            kind="bar",
            ax=ax,
        )

        ax.set_ylabel(
            f"Average {display_name(target_col)}"
        )

        chart_type = "categorical_target_mean"

    # Binary target
    elif data[target_col].nunique() == 2:

        categories = list(
            data[target_col]
            .astype(str)
            .unique()
        )

        positive = categories[-1]

        rate = (
            data[target_col]
            .astype(str)
            .eq(positive)
            .groupby(data[category_col])
            .mean()
            .mul(100)
            .sort_values(ascending=False)
        )

        rate.plot(
            kind="bar",
            ax=ax,
        )

        ax.set_ylabel(
            f"Percentage of {positive} (%)"
        )

        chart_type = "categorical_target_rate"

    # Multi-class target
    else:

        counts = pd.crosstab(
            data[category_col],
            data[target_col],
        )

        counts.plot(
            kind="bar",
            ax=ax,
        )

        ax.set_ylabel("Count")
        chart_type = "categorical_target_counts"

    ax.set_title(
        f"{display_name(target_col)} by "
        f"{display_name(category_col)}"
    )

    ax.set_xlabel(
        display_name(category_col)
    )

    path = output_dir / (
        f"categorical_comparison_"
        f"{safe_filename(category_col)}_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata(
        chart_type,
        path,
    )


# ============================================================
# Numeric vs Target
# ============================================================

def generate_numeric_target_comparison(
    df: pd.DataFrame,
    numeric_col: str,
    target_col: str,
    job_id: str,
    output_dir: Path,
):

    if (
        numeric_col not in df.columns
        or target_col not in df.columns
    ):
        return None

    data = df[
        [numeric_col, target_col]
    ].dropna()

    if data.empty:
        return None

    if data[target_col].nunique() < 2:
        return None

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    sns.boxplot(
        data=data,
        x=target_col,
        y=numeric_col,
        ax=ax,
    )

    ax.set_title(
        f"{display_name(numeric_col)} by "
        f"{display_name(target_col)}"
    )

    ax.set_xlabel(
        display_name(target_col)
    )

    ax.set_ylabel(
        display_name(numeric_col)
    )

    path = output_dir / (
        f"numeric_comparison_"
        f"{safe_filename(numeric_col)}_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata(
        "numeric_target_comparison",
        path,
    )


# ============================================================
# Scatter Plot
# ============================================================

def generate_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    job_id: str,
    output_dir: Path,
):

    if (
        x_col not in df.columns
        or y_col not in df.columns
    ):
        return None

    data = df[
        [x_col, y_col]
    ].dropna()

    if len(data) < 2:
        return None

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    ax.scatter(
        data[x_col],
        data[y_col],
        alpha=0.6,
    )

    ax.set_title(
        f"{display_name(x_col)} vs "
        f"{display_name(y_col)}"
    )

    ax.set_xlabel(
        display_name(x_col)
    )

    ax.set_ylabel(
        display_name(y_col)
    )

    path = output_dir / (
        f"scatter_"
        f"{safe_filename(x_col)}_"
        f"{safe_filename(y_col)}_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata(
        "scatter",
        path,
    )


# ============================================================
# Correlation Heatmap
# ============================================================

def generate_correlation_heatmap(
    df: pd.DataFrame,
    job_id: str,
    output_dir: Path,
):

    numeric_df = df.select_dtypes(
        include="number"
    )

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
        f"correlation_heatmap_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata(
        "correlation_heatmap",
        path,
    )


# ============================================================
# Feature Importance
# ============================================================

def generate_feature_importance_chart(
    feature_importance: list,
    job_id: str,
    output_dir: Path,
):

    if not feature_importance:
        return None

    cleaned = []

    for item in feature_importance:

        try:
            feature, importance = item

            if feature is None:
                continue

            importance = float(
                importance
            )

            cleaned.append(
                (
                    str(feature),
                    importance,
                )
            )

        except (
            ValueError,
            TypeError,
        ):
            continue

    if not cleaned:
        return None

    importance_df = pd.DataFrame(
        cleaned,
        columns=[
            "feature",
            "importance",
        ],
    )

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=True,
        )
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
        "Top Important Features"
    )

    ax.set_xlabel(
        "Importance"
    )

    ax.set_ylabel(
        "Feature"
    )

    path = output_dir / (
        f"feature_importance_"
        f"{safe_filename(job_id)}.png"
    )

    save_chart(fig, path)

    return chart_metadata(
        "feature_importance_bar",
        path,
    )


# ============================================================
# Main Visualization Selection
# ============================================================

def select_and_generate_visualizations(
    df: pd.DataFrame,
    target_col: str,
    question: str,
    feature_importance: list,
    job_id: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
):

    output_path = Path(
        output_dir
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_charts = []
    explanations = []

    question_lower = normalize_text(
        question
    )

    # --------------------------------------------------------
    # Visualization request
    # --------------------------------------------------------

    if not is_visualization_request(
        question
    ):

        return (
            generated_charts,
            explanations,
        )

    # --------------------------------------------------------
    # Dataset information
    # --------------------------------------------------------

    mentioned_columns = (
        find_mentioned_columns(
            df,
            question,
        )
    )

    numeric_columns = list(
        df.select_dtypes(
            include="number"
        ).columns
    )

    categorical_columns = list(
        df.select_dtypes(
            include=[
                "object",
                "category",
                "bool",
            ]
        ).columns
    )

    target_exists = (
        target_col
        and target_col in df.columns
    )

    mentioned_numeric = [
        col
        for col in mentioned_columns
        if col in numeric_columns
    ]

    mentioned_categorical = [
        col
        for col in mentioned_columns
        if col in categorical_columns
        and col != target_col
    ]

    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    importance_requested = any(
        keyword in question_lower
        for keyword in [
            "feature importance",
            "important features",
            "important factors",
            "key factors",
            "top factors",
            "top drivers",
            "important drivers",
        ]
    )

    if (
        importance_requested
        and feature_importance
    ):

        chart = (
            generate_feature_importance_chart(
                feature_importance,
                job_id,
                output_path,
            )
        )

        if chart:

            generated_charts.append(
                chart
            )

            explanations.append(
                make_explanation(
                    action="Generate feature importance chart",
                    reason="The question asks for important factors or features.",
                    alternative="Distribution chart",
                    why_not_chosen="A feature-importance view directly answers the requested question.",
                    impact="Highlights the variables with the strongest model-derived importance.",
                    learning_note="Feature importance is most useful when a predictive model has been trained.",
                )
            )

    # --------------------------------------------------------
    # Explicit categorical comparison
    # --------------------------------------------------------

    if target_exists:

        for category_col in mentioned_categorical[:2]:

            chart = (
                generate_categorical_comparison(
                    df,
                    category_col,
                    target_col,
                    job_id,
                    output_path,
                )
            )

            if chart:

                generated_charts.append(
                    chart
                )

                explanations.append(
                    make_explanation(
                        action=f"Compare {target_col} across {category_col}",
                        reason="The question mentions a categorical feature and the target.",
                        alternative="Target distribution",
                        why_not_chosen="A grouped comparison provides more insight into how the target varies across categories.",
                        impact="Shows differences in the target across meaningful groups.",
                        learning_note="Categorical comparisons are useful for identifying segment-level differences.",
                    )
                )

    # --------------------------------------------------------
    # Numeric relationship
    # --------------------------------------------------------

    relationship_requested = any(
        keyword in question_lower
        for keyword in [
            "relationship",
            "correlation",
            "association",
            "versus",
            "vs",
            "against",
        ]
    )

    if (
        relationship_requested
        and len(mentioned_numeric) >= 2
    ):

        chart = generate_scatter_plot(
            df,
            mentioned_numeric[0],
            mentioned_numeric[1],
            job_id,
            output_path,
        )

        if chart:

            generated_charts.append(
                chart
            )

            explanations.append(
                make_explanation(
                    action=(
                        f"Plot {mentioned_numeric[0]} "
                        f"against {mentioned_numeric[1]}"
                    ),
                    reason="The question asks about a relationship between numerical variables.",
                    alternative="Correlation heatmap",
                    why_not_chosen="A scatter plot directly shows the row-level relationship between the selected variables.",
                    impact="Makes the strength, direction, and possible patterns of the relationship easier to inspect.",
                    learning_note="Scatter plots are appropriate for relationships between two numerical variables.",
                )
            )

    # --------------------------------------------------------
    # Numeric feature vs target
    # --------------------------------------------------------

    if (
        target_exists
        and relationship_requested
    ):

        for numeric_col in mentioned_numeric[:2]:

            if numeric_col == target_col:
                continue

            chart = (
                generate_numeric_target_comparison(
                    df,
                    numeric_col,
                    target_col,
                    job_id,
                    output_path,
                )
            )

            if chart:

                generated_charts.append(
                    chart
                )

                explanations.append(
                    make_explanation(
                        action=(
                            f"Compare {numeric_col} "
                            f"across {target_col}"
                        ),
                        reason="The question asks about differences or relationships involving the target.",
                        alternative="Scatter plot",
                        why_not_chosen="A box plot is more suitable when comparing a numerical feature across target groups.",
                        impact="Shows how the numerical feature differs between target groups.",
                        learning_note="Box plots are useful for comparing numerical distributions across categories.",
                    )
                )

    # --------------------------------------------------------
    # Distribution request
    # --------------------------------------------------------

    distribution_requested = any(
        keyword in question_lower
        for keyword in [
            "distribution",
            "proportion",
            "percentage",
            "breakdown",
            "how many",
        ]
    )

    if (
        target_exists
        and (
            distribution_requested
            or target_col in mentioned_columns
        )
    ):

        chart = (
            generate_target_distribution(
                df,
                target_col,
                job_id,
                output_path,
            )
        )

        if chart:

            generated_charts.append(
                chart
            )

            explanations.append(
                make_explanation(
                    action=f"Generate distribution of {target_col}",
                    reason="The question asks for a distribution or breakdown of the target.",
                    alternative="Grouped comparison",
                    why_not_chosen="The distribution provides the requested overall target-level view.",
                    impact="Shows the overall composition or spread of the target variable.",
                    learning_note="Target distributions provide a useful first visual summary of an analysis.",
                )
            )

    # --------------------------------------------------------
    # Correlation heatmap
    # --------------------------------------------------------

    correlation_requested = any(
        keyword in question_lower
        for keyword in [
            "correlation",
            "correlations",
            "heatmap",
        ]
    )

    if correlation_requested:

        chart = (
            generate_correlation_heatmap(
                df,
                job_id,
                output_path,
            )
        )

        if chart:

            generated_charts.append(
                chart
            )

            explanations.append(
                make_explanation(
                    action="Generate numerical correlation heatmap",
                    reason="The question explicitly asks about correlations.",
                    alternative="Scatter plot",
                    why_not_chosen="A heatmap provides a broader view across all available numerical variables.",
                    impact="Shows the strength and direction of pairwise numerical relationships.",
                    learning_note="Correlation heatmaps are useful for screening many numerical relationships at once.",
                )
            )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if not generated_charts:

        # Best option: target distribution
        if target_exists:

            chart = (
                generate_target_distribution(
                    df,
                    target_col,
                    job_id,
                    output_path,
                )
            )

            if chart:

                generated_charts.append(
                    chart
                )

                explanations.append(
                    make_explanation(
                        action=f"Generate overview of {target_col}",
                        reason="The user requested visual analysis but did not specify a particular chart.",
                        alternative="Correlation heatmap",
                        why_not_chosen="The target provides the most direct overview of the analysis outcome.",
                        impact="Provides an immediate visual summary of the target variable.",
                        learning_note="When no specific chart is requested, the target distribution is a useful default when a target exists.",
                    )
                )

        # No target: correlation overview
        elif len(numeric_columns) >= 2:

            chart = (
                generate_correlation_heatmap(
                    df,
                    job_id,
                    output_path,
                )
            )

            if chart:

                generated_charts.append(
                    chart
                )

                explanations.append(
                    make_explanation(
                        action="Generate numerical correlation heatmap",
                        reason="The dataset contains multiple numerical variables and no target was identified.",
                        alternative="Scatter plot",
                        why_not_chosen="The heatmap provides broader coverage of the available numerical relationships.",
                        impact="Provides an overview of relationships between numerical variables.",
                        learning_note="Correlation analysis is a useful generic visualization when no target is available.",
                    )
                )

        # Only categorical data
        elif categorical_columns:

            category_col = categorical_columns[0]

            counts = (
                df[category_col]
                .dropna()
                .astype(str)
                .value_counts()
                .head(15)
            )

            if not counts.empty:

                fig, ax = plt.subplots(
                    figsize=(8, 5)
                )

                counts.plot(
                    kind="bar",
                    ax=ax,
                )

                ax.set_title(
                    f"Distribution of "
                    f"{display_name(category_col)}"
                )

                ax.set_xlabel(
                    display_name(category_col)
                )

                ax.set_ylabel(
                    "Count"
                )

                path = output_path / (
                    f"category_distribution_"
                    f"{safe_filename(category_col)}_"
                    f"{safe_filename(job_id)}.png"
                )

                save_chart(
                    fig,
                    path,
                )

                generated_charts.append(
                    chart_metadata(
                        "category_distribution",
                        path,
                    )
                )

                explanations.append(
                    make_explanation(
                        action=f"Generate distribution of {category_col}",
                        reason="The dataset contains categorical information but no target or multiple numerical variables.",
                        alternative="Target distribution",
                        why_not_chosen="No target variable was available for a target-focused chart.",
                        impact="Provides a basic visual summary of the available categorical data.",
                        learning_note="Category frequency is a useful fallback visualization for categorical datasets.",
                    )
                )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    unique_charts = []
    seen_files = set()

    for chart in generated_charts:

        filename = chart.get(
            "filename"
        )

        if (
            filename
            and filename not in seen_files
        ):

            unique_charts.append(
                chart
            )

            seen_files.add(
                filename
            )

    generated_charts = unique_charts

    return (
        generated_charts,
        explanations,
    )