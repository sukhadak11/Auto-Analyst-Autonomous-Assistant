# src/evaluate.py
import matplotlib
matplotlib.use("Agg") 
matplotlib.rcParams['text.parse_math'] = False   
import matplotlib.pyplot as plt
import shap
import joblib
import pandas as pd
from pathlib import Path
MODEL_PATH = Path("data/model.joblib")
CLEAN_PATH = Path("data/clean_data.csv")
PLOTS_DIR = Path("data/plots")
PLOTS_DIR.mkdir(exist_ok=True)


def load_model_and_data(target_col: str):
    model = joblib.load(MODEL_PATH)
    df = pd.read_csv(CLEAN_PATH)
    X = df.drop(columns=[target_col])
    y = df[target_col]
    return model, X, y


def describe_dataset(X: pd.DataFrame, y: pd.Series, target_col: str):
    """Print a full summary so nothing about the dataset is left undefined."""
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Rows: {X.shape[0]}   Features: {X.shape[1]}")
    print(f"Target column: {target_col}")
    print(f"Target distribution:\n{y.value_counts(normalize=True).round(3)}\n")
    print("Feature list and dtypes:")
    print(X.dtypes.to_string())
    print("=" * 60 + "\n")


def explain_global(model, X: pd.DataFrame, sample_size: int = 200):
    X_sample = X.sample(min(sample_size, len(X)), random_state=42)

    explainer = shap.TreeExplainer(model)
    # modern API: calling the explainer returns an Explanation object,
    # not a raw list/array
    explanation = explainer(X_sample)

    # for binary classifiers, output is often (n_samples, n_features, 2)
    # -> slice to the "positive class" (index 1) explanation
    if explanation.values.ndim == 3:
        explanation_to_plot = explanation[:, :, 1]
    else:
        explanation_to_plot = explanation

    plt.figure()
    shap.plots.beeswarm(explanation_to_plot, show=False)
    plt.title("Which features drive predictions, and in which direction\n"
               "(red = high feature value, blue = low; right = pushes prediction up)")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "global_importance_beeswarm.png", dpi=150)
    plt.close()
    print(f"Saved: {PLOTS_DIR / 'global_importance_beeswarm.png'}")

    plt.figure()
    shap.plots.bar(explanation_to_plot, show=False)
    plt.title("Average impact of each feature on the model's output\n"
               "(mean absolute SHAP value, ranked most to least important)")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "global_importance_bar.png", dpi=150)
    plt.close()
    print(f"Saved: {PLOTS_DIR / 'global_importance_bar.png'}")

    return explainer, explanation


def explain_one_prediction(explainer, X: pd.DataFrame, row_index: int = 0):
    row = X.iloc[[row_index]]
    explanation = explainer(row)

    if explanation.values.ndim == 3:
        explanation_to_plot = explanation[0, :, 1]
    else:
        explanation_to_plot = explanation[0]

    plt.figure()
    shap.plots.waterfall(explanation_to_plot, show=False)
    plt.title(f"Why the model predicted this for row {row_index}\n"
               "(starts at average prediction, each bar shows one feature's push)")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / f"local_explanation_row{row_index}.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {PLOTS_DIR / f'local_explanation_row{row_index}.png'}")

'''
if __name__ == "__main__":
    target_col = "churn"  
    model, X, y = load_model_and_data(target_col)
    describe_dataset(X, y, target_col)
    explainer, explanation = explain_global(model, X)
    explain_one_prediction(explainer, X, row_index=0)
    '''