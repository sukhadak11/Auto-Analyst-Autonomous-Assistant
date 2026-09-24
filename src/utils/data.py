from pathlib import Path

import pandas as pd


def get_dataset_preview(
    dataset_path: Path,
    preview_rows: int = 10
) -> dict:

    result = {
        "filename": dataset_path.name,
        "rows": 0,
        "columns": 0,
        "column_names": [],
        "preview": [],
    }

    if not dataset_path.exists():
        return result

    try:
        df = pd.read_csv(dataset_path)

        result.update({
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": [
                str(column)
                for column in df.columns
            ],
            "preview": (
                df.head(preview_rows)
                .fillna("")
                .astype(object)
                .to_dict(orient="records")
            ),
        })

    except Exception as exc:
        result["error"] = (
            f"Unable to generate dataset preview: {exc}"
        )

    return result