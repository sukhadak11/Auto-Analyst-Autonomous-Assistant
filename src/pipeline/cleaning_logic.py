# src/pipeline/cleaning_logic.py
import pandas as pd
from explanation_schema import make_explanation


def analyze_and_clean(df: pd.DataFrame, target_col: str):
    df = df.copy()
    explanations = []

    # 1. Duplicate rows check
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        df = df.drop_duplicates()
        explanations.append(make_explanation(
            action=f"Removed {dup_count} duplicate rows",
            reason=f"{dup_count} exact duplicate rows were found ({dup_count/len(df):.1%} of the dataset).",
            alternative_considered="Keep duplicates",
            why_not_chosen="Duplicate rows can bias the model by over-weighting repeated examples.",
            expected_impact=f"Dataset reduced from {len(df)+dup_count} to {len(df)} rows.",
            learning_note="Duplicate records are a common data quality issue and should be checked before training any model.",
        ))
    else:
        explanations.append(make_explanation(
            action="No duplicate rows removed",
            reason="Checked for exact duplicate rows and found none.",
            alternative_considered="N/A",
            why_not_chosen="N/A — no duplicates existed.",
            expected_impact="No change to dataset size.",
            learning_note="Checking for duplicates is a standard first step, even when the result is 'none found.'",
        ))

    # 2. Class balance check (only if target looks categorical/binary)
    if target_col in df.columns:
        value_counts = df[target_col].value_counts(normalize=True)
        if len(value_counts) <= 10:  # treat as categorical target
            minority_pct = value_counts.min()
            if minority_pct < 0.25:
                explanations.append(make_explanation(
                    action="Flagged class imbalance in target column",
                    reason=f"The minority class in '{target_col}' makes up only {minority_pct:.1%} of the data.",
                    alternative_considered="Oversampling (e.g. SMOTE) or class-weighted training",
                    why_not_chosen="Not applied automatically in this step — flagged for awareness; the Model Training Agent will account for this when evaluating the model.",
                    expected_impact="Without adjustment, the model may be biased toward predicting the majority class.",
                    learning_note="A minority class under 25-30% often needs special handling (class weights, oversampling) to train a fair model.",
                ))

    # 3. Constant / near-constant columns
    for col in df.columns:
        if col == target_col:
            continue
        if df[col].nunique() <= 1:
            explanations.append(make_explanation(
                action=f"Flagged column '{col}' as constant",
                reason=f"'{col}' has only {df[col].nunique()} unique value(s) across all rows.",
                alternative_considered="Drop the column",
                why_not_chosen="Not dropped automatically — flagged for awareness; constant columns add no predictive value but are left for the user to confirm removal.",
                expected_impact="This column contributes no information to the model and can likely be safely removed.",
                learning_note="Constant columns carry zero variance and cannot help a model distinguish between outcomes.",
            ))

    # 4. Missing value handling (from before)
    num_cols = [c for c in df.select_dtypes(include="number").columns if c != target_col]
    cat_cols = [c for c in df.select_dtypes(include="object").columns if c != target_col]

    for col in num_cols:
        missing_count = df[col].isna().sum()
        if missing_count == 0:
            continue
        skew = df[col].skew()
        use_median = abs(skew) > 0.5
        fill_value = df[col].median() if use_median else df[col].mean()
        method = "Median imputation" if use_median else "Mean imputation"
        df[col] = df[col].fillna(fill_value)
        explanations.append(make_explanation(
            action=f"{method} on column '{col}'",
            reason=f"Column '{col}' has a skewness of {skew:.2f}.",
            alternative_considered="Mean imputation" if use_median else "Median imputation",
            why_not_chosen="Sensitive to outliers." if use_median else "Discards distribution shape when data is symmetric.",
            expected_impact=f"Filled {missing_count} missing values.",
            learning_note="Median is preferred over mean when a column is skewed.",
        ))

    for col in cat_cols:
        missing_count = df[col].isna().sum()
        if missing_count == 0:
            continue
        df[col] = df[col].fillna("Unknown")
        explanations.append(make_explanation(
            action=f"Filled missing values in '{col}' with 'Unknown'",
            reason=f"'{col}' had {missing_count} missing values.",
            alternative_considered="Mode imputation",
            why_not_chosen="Can bias toward the majority category.",
            expected_impact=f"Retained all rows.",
            learning_note="An explicit 'Unknown' category preserves the missingness signal.",
        ))

    return df, explanations