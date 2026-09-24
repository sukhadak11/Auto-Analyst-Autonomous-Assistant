from pathlib import Path


# Project root
BASE_DIR = Path(__file__).resolve().parents[2] # This correctly points to your project root.

# Data directories
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
PLOTS_DIR = DATA_DIR / "plots"
UPLOAD_DIR = DATA_DIR / "uploads"


def ensure_directories():
    """Create required project directories."""
    for directory in (OUTPUT_DIR, PLOTS_DIR, UPLOAD_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def get_job_output_dir(job_id: str) -> Path:
    """Return job output directory."""
    return OUTPUT_DIR / job_id


def get_job_csv_dir(job_id: str) -> Path:
    """Return job CSV directory."""
    return get_job_output_dir(job_id) / "csv"


def get_job_model_dir(job_id: str) -> Path:
    """Return job model directory."""
    return get_job_output_dir(job_id) / "model"


def get_job_csv_path(job_id: str) -> Path:
    """Return original dataset CSV path."""
    return get_job_csv_dir(job_id) / "original_dataset.csv"


def get_job_model_path(job_id: str) -> Path:
    """Return trained model path."""
    return get_job_model_dir(job_id) / "trained_model.joblib"


def ensure_job_output_dirs(job_id: str):
    """Create CSV and model directories for a job."""
    get_job_csv_dir(job_id).mkdir(
        parents=True,
        exist_ok=True
    )

    get_job_model_dir(job_id).mkdir(
        parents=True,
        exist_ok=True
    )


ensure_directories()