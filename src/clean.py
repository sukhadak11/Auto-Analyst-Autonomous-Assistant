import pandas as pd
from pathlib import Path

# Build paths relative to this file, not current working directory
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_PATH = DATA_DIR / "telecommunications_churn.csv"
CLEAN_PATH = DATA_DIR / "clean_data.csv"


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # numeric columns: fill with median
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())

    # categorical columns: fill with "Unknown"
    cat_cols = df.select_dtypes(include="object").columns
    df[cat_cols] = df[cat_cols].fillna("Unknown")

    return df


def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Example if needed:
    # if "TotalCharges" in df.columns:
    #     df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    return df


def encode_categoricals(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    df = df.copy()

    cat_cols = df.select_dtypes(include="object").columns.drop(target_col, errors="ignore")
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    return df


def clean_pipeline(target_col: str, raw_path: Path = None):
    path_to_use = Path(raw_path) if raw_path else RAW_PATH

    if not path_to_use.exists():
        raise FileNotFoundError(f"Raw data file not found: {path_to_use}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data(path_to_use)
    df = handle_missing(df)
    df = fix_dtypes(df)
    df = encode_categoricals(df, target_col)

    try:
        df.to_csv(CLEAN_PATH, index=False)
    except PermissionError:
        raise PermissionError(
            f"Cannot write to {CLEAN_PATH}. "
            f"Please close the file if it is open in Excel or another program."
        )

    print(f"Saved cleaned data to {CLEAN_PATH}")
    return df


if __name__ == "__main__":
    clean_pipeline(target_col="churn")