# src/pipeline/feature_selection_logic.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from src.agent.explanation_schema import make_explanation


def analyze_and_select_features(df: pd.DataFrame, target_col: str, needs_interpretability: bool = True):
    df = df.copy()
    explanations = []

    num_cols = [c for c in df.select_dtypes(include="number").columns if c != target_col]

    if len(num_cols) < 5:
        explanations.append(make_explanation(
            action="No dimensionality reduction applied",
            reason=f"Only {len(num_cols)} numeric features exist.",
            alternative_considered="PCA",
            why_not_chosen="PCA is generally only useful when there are enough numeric features that redundancy or high dimensionality becomes a problem — 5+ is a common rule of thumb.",
            expected_impact="All numeric features are kept as-is.",
            learning_note="PCA helps most when you have many correlated numeric features; with only a few, it adds complexity without meaningful benefit.",
            confidence="High",
        ))
        return df, explanations, num_cols

    corr_matrix = df[num_cols].corr().abs()
    upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    high_corr_pairs = int((upper_triangle > 0.7).sum().sum())
    max_corr = upper_triangle.max().max() if not upper_triangle.isna().all().all() else 0

    if high_corr_pairs == 0:
        explanations.append(make_explanation(
            action="No dimensionality reduction applied",
            reason=f"Checked correlations between all {len(num_cols)} numeric features; the highest pairwise correlation found was {max_corr:.2f}.",
            alternative_considered="PCA",
            why_not_chosen="PCA is most valuable when features are highly correlated (redundant); no pair exceeded the 0.7 correlation threshold here.",
            expected_impact="All numeric features are kept as-is, preserving full interpretability.",
            learning_note="PCA trades interpretability for compression — it's only worth that trade when real redundancy exists in the data.",
            confidence="High",
        ))
        return df, explanations, num_cols

    if needs_interpretability:
        explanations.append(make_explanation(
            action="Redundant features detected, but PCA was not applied",
            reason=f"Found {high_corr_pairs} feature pair(s) with correlation above 0.7 (highest: {max_corr:.2f}).",
            alternative_considered="PCA",
            why_not_chosen="This analysis requires explaining which specific factors drive the outcome. PCA would compress features into components that can't be tied back to a single named factor, which conflicts with that goal.",
            expected_impact="Original features are kept, so later explanations (e.g. SHAP) can name real factors instead of abstract components.",
            learning_note="PCA improves model efficiency but sacrifices the ability to explain results in terms of the original, named features — a real trade-off, not a free win.",
            confidence="High",
        ))
        return df, explanations, num_cols

    n_components = max(2, len(num_cols) // 2)
    pca = PCA(n_components=n_components)
    pca.fit(df[num_cols].fillna(df[num_cols].median()))
    variance_retained = pca.explained_variance_ratio_.sum()

    confidence = "High" if variance_retained > 0.9 else "Medium" if variance_retained > 0.75 else "Low"

    pca_cols = [f"pca_component_{i+1}" for i in range(n_components)]
    transformed = pca.transform(df[num_cols].fillna(df[num_cols].median()))
    for i, col in enumerate(pca_cols):
        df[col] = transformed[:, i]
    df = df.drop(columns=num_cols)

    explanations.append(make_explanation(
        action=f"Applied PCA, reducing {len(num_cols)} numeric features to {n_components} components",
        reason=f"Found {high_corr_pairs} feature pair(s) with correlation above 0.7 (highest: {max_corr:.2f}), indicating redundant information.",
        alternative_considered="Manual feature selection (dropping one of each correlated pair)",
        why_not_chosen="PCA preserves information from all original features rather than discarding entire columns outright.",
        expected_impact=f"Retained {variance_retained:.1%} of the original variance while reducing dimensionality from {len(num_cols)} to {n_components}.",
        learning_note="PCA transforms correlated features into independent components ranked by how much variance each explains.",
        confidence=confidence,
    ))

    return df, explanations, pca_cols