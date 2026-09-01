import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))

import pandas as pd
import numpy as np
from scipy import stats
from explanation_schema import make_explanation


def detect_target_kind(y: pd.Series) -> str:
    """Same style of check used in model_training_logic.py — catches both
    classic object dtype and pandas' newer string dtype."""
    is_text = y.dtype == "object" or pd.api.types.is_string_dtype(y)
    if is_text or y.nunique() <= 10:
        return "binary" if y.nunique() == 2 else "multiclass"
    return "continuous"


def compute_statistical_insights(df: pd.DataFrame, target_col: str, question: str):
    explanations = []
    insights = []

    num_cols = [c for c in df.select_dtypes(include="number").columns if c != target_col]

    # 1. Summary statistics — always computed, regardless of target type
    summary = df[num_cols].describe().T[["mean", "std", "min", "max"]]
    insights.append({"type": "summary_stats", "data": summary.round(2).to_dict(orient="index")})
    explanations.append(make_explanation(
        action=f"Computed summary statistics for {len(num_cols)} numeric columns",
        reason="Summary statistics (mean, std, min, max) provide a baseline understanding of each feature's scale and spread.",
        alternative_considered="Skip summary stats, go straight to relationships",
        why_not_chosen="Relationships are hard to interpret without knowing each feature's typical range first.",
        expected_impact="Report can reference concrete typical values, not just relative comparisons.",
        learning_note="Mean and standard deviation together describe both the center and spread of a distribution.",
        confidence="High",
    ))

    if target_col not in df.columns or len(num_cols) == 0:
        return insights, explanations

    target_kind = detect_target_kind(df[target_col])
    correlations = []

    if target_kind == "binary":
        target_numeric = pd.factorize(df[target_col])[0]
        for col in num_cols:
            valid = df[col].notna()
            if valid.sum() < 3:
                continue
            r, p = stats.pointbiserialr(target_numeric[valid], df[col][valid])
            correlations.append((col, r, p))
        test_name = "Point-biserial correlation"
        test_reason = "the statistically correct method for measuring the relationship between a numeric variable and a binary categorical variable"

    elif target_kind == "multiclass":
        groups_by_col = {}
        for col in num_cols:
            valid = df[col].notna()
            groups = [df.loc[valid & (df[target_col] == cls), col] for cls in df[target_col].dropna().unique()]
            groups = [g for g in groups if len(g) >= 2]  # ANOVA needs at least 2 samples per group
            if len(groups) < 2:
                continue
            f_stat, p = stats.f_oneway(*groups)
            correlations.append((col, f_stat, p))
        test_name = "One-way ANOVA F-test"
        test_reason = f"the target has {df[target_col].nunique()} categories, so a pairwise correlation isn't appropriate — ANOVA tests whether each feature's mean differs significantly across all categories at once"

    else:  # continuous
        for col in num_cols:
            valid = df[col].notna() & df[target_col].notna()
            if valid.sum() < 3:
                continue
            r, p = stats.pearsonr(df[col][valid], df[target_col][valid])
            correlations.append((col, r, p))
        test_name = "Pearson correlation"
        test_reason = "the standard test for measuring linear relationships between two continuous numeric variables"

    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    top_correlations = correlations[:5]

    if top_correlations:
        stat_label = "F-stat" if target_kind == "multiclass" else "r"
        summary_text = ", ".join(f"{col} ({stat_label}={val:.3f}, p={p:.4f})" for col, val, p in top_correlations)
        significant = [c for c in top_correlations if c[2] < 0.05]

        insights.append({"type": "target_relationships", "test": test_name, "data": top_correlations})
        explanations.append(make_explanation(
            action=f"Computed {test_name} between {len(num_cols)} features and '{target_col}' ({target_kind} target)",
            reason=f"Used {test_name} because {test_reason}.",
            alternative_considered="A single generic correlation method regardless of target type",
            why_not_chosen="Using the wrong statistical test for the target's type would produce misleading or invalid results.",
            expected_impact=f"Top relationships found: {summary_text}. {len(significant)} of {len(top_correlations)} shown are statistically significant (p < 0.05).",
            learning_note="The correct statistical test depends on the target's type: point-biserial for binary, ANOVA for multi-class categorical, Pearson for continuous numeric.",
            confidence="High" if significant else "Low",
        ))

    return insights, explanations