import sys
from pathlib import Path
from llm_config import llm, safe_invoke
sys.path.append(str(Path(__file__).resolve().parents[1] / "agent"))
import pandas as pd
from src.agent.explanation_schema import make_explanation


def detect_target_column(df: pd.DataFrame, user_specified: str | bytes) -> tuple:
    """Returns (target_col, explanation). Never hardcodes a column name."""
    if user_specified and user_specified in df.columns:
        return user_specified, make_explanation(
            action=f"Used user-specified target column '{user_specified}'",
            reason="The user explicitly specified this column as the prediction target.",
            alternative_considered="Automatic target detection",
            why_not_chosen="Not needed — an explicit target was provided.",
            expected_impact="Model will be trained to predict this column.",
            learning_note="Specifying the target directly avoids ambiguity in what the model should predict.",
            confidence="High",  # a user-specified target removes all guesswork
        )

    # Heuristic: prefer a low-cardinality column (likely categorical outcome),
    # searched from the last column backward, since target columns are
    # conventionally placed last in tabular datasets.
    candidates = []
    for col in reversed(df.columns.tolist()):
        nunique = df[col].nunique()
        if 2 <= nunique <= 10:
            candidates.append((col, nunique))

    if candidates:
        target_col, nunique = candidates[0]
        # confidence based on how many competing candidates existed —
        # one clear candidate is a confident guess, several is a coin flip
        confidence = "High" if len(candidates) == 1 else "Medium" if len(candidates) <= 3 else "Low"

        return target_col, make_explanation(
            action=f"Auto-detected '{target_col}' as the likely target column",
            reason=f"'{target_col}' has {nunique} unique values, consistent with a classification target, and is positioned near the end of the dataset.",
            alternative_considered=f"Other low-cardinality columns: {[c for c, _ in candidates[1:4]]}" if len(candidates) > 1 else "None",
            why_not_chosen="Other candidates were further from the end of the column order, or had more unique values." if len(candidates) > 1 else "N/A",
            expected_impact="The model will be trained to predict this column. Confirm this is correct before relying on results.",
            learning_note="When no target is specified, a common convention is a low-cardinality column near the end of the dataset — but this is a guess, not a certainty.",
            confidence=confidence,
        )

    # Fallback: just use the last column — genuinely a low-confidence guess
    target_col = df.columns[-1]
    return target_col, make_explanation(
        action=f"Defaulted to last column '{target_col}' as target",
        reason="No column had the low-cardinality pattern typical of a classification target.",
        alternative_considered="All other columns",
        why_not_chosen="No stronger signal was found to prefer another column.",
        expected_impact="This is a low-confidence guess — the user should confirm or override this.",
        learning_note="Automatic target detection is a best-effort guess and should always be confirmed by the user when possible.",
        confidence="Low",
    )


def detect_dataset_type(df: pd.DataFrame) -> tuple:
    """Returns ('tabular'|'time_series', explanation)."""
    datetime_cols = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)
        elif df[col].dtype == object:
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().mean() > 0.9:
                    datetime_cols.append(col)
            except Exception:
                pass

    if datetime_cols:
        return "time_series", make_explanation(
            action=f"Classified dataset as time series (datetime column: '{datetime_cols[0]}')",
            reason=f"Found a column ('{datetime_cols[0]}') that parses as dates/times for over 90% of rows.",
            alternative_considered="Treat as standard tabular data",
            why_not_chosen="A reliable datetime column strongly suggests the data is ordered in time.",
            expected_impact="Routes to time-series-specific analysis instead of standard classification/regression.",
            learning_note="The presence of a consistent datetime column is the standard signal for time-series data.",
            confidence="High",  # a >90% parse rate is a clear, directly observed signal
        )

    return "tabular", make_explanation(
        action="Classified dataset as standard tabular data",
        reason="No column was found that reliably parses as a date/time.",
        alternative_considered="Time series",
        why_not_chosen="No datetime signal was present.",
        expected_impact="Routes to standard classification/regression analysis.",
        learning_note="Tabular data has no inherent ordering; time series data does.",
        confidence="High",  # absence of a datetime column is also a directly observed fact
    )


def detect_id_columns(df: pd.DataFrame, target_col: str | bytes) -> tuple:
    """Flags columns that look like identifiers, not predictive features."""
    id_cols = []
    for col in df.columns:
        if col == target_col:
            continue
        if df[col].nunique() == len(df):
            id_cols.append(col)

    if id_cols:
        return id_cols, make_explanation(
            action=f"Flagged {len(id_cols)} column(s) as likely identifiers: {id_cols}",
            reason="These columns have a unique value for every single row, matching the pattern of an ID or index rather than a predictive feature.",
            alternative_considered="Include them as model features",
            why_not_chosen="A column with 100% unique values (like a customer ID) provides no generalizable pattern for prediction and can cause the model to memorize rather than learn.",
            expected_impact="These columns will be excluded from model training.",
            learning_note="ID-like columns should almost always be excluded from predictive models — they carry no transferable signal.",
            confidence="High",  # 100% uniqueness is a directly observed, unambiguous fact
        )

    return [], make_explanation(
        action="No identifier-like columns detected",
        reason="No column had a unique value for every row.",
        alternative_considered="N/A",
        why_not_chosen="N/A",
        expected_impact="All non-target columns will be considered as potential features.",
        learning_note="Checking for ID-like columns prevents accidentally training a model on non-predictive identifiers.",
        confidence="High",
    )


def profile_dataset(df: pd.DataFrame, user_specified_target: str | bytes) -> dict:
    """The single entry point — runs all profiling steps and returns a
    full profile plus every explanation generated along the way."""
    explanations = []

    target_col, exp1 = detect_target_column(df, user_specified_target)
    explanations.append(exp1)

    dataset_type, exp2 = detect_dataset_type(df)
    explanations.append(exp2)

    id_cols, exp3 = detect_id_columns(df, target_col)
    explanations.append(exp3)

    return {
        "target_col": target_col,
        "dataset_type": dataset_type,
        "id_cols": id_cols,
        "explanations": explanations,
    }