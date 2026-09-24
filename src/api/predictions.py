from pathlib import Path

import joblib
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import User

from src.utils.auth import get_authorized_job
from src.utils.paths import get_job_model_path


router = APIRouter()


# ============================================================
# REQUEST MODEL
# ============================================================

class PredictionRequest(BaseModel):
    features: dict


# ============================================================
# PREDICTION
# ============================================================

@router.post("/predict/{job_id}")
def predict(
    job_id: str,
    request: PredictionRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Generate a prediction using the trained
    model associated with the job.
    """

    # Verify authorization
    job = get_authorized_job(
        job_id,
        current_user,
        db,
    )

    # --------------------------------------------------------
    # Find trained model
    # --------------------------------------------------------

    model_path = get_job_model_path(job_id)

    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Trained model not found.",
        )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    try:
        model = joblib.load(model_path)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load model: {exc}",
        )

    # --------------------------------------------------------
    # Prepare input
    # --------------------------------------------------------

    if not request.features:
        raise HTTPException(
            status_code=400,
            detail="Prediction features are required.",
        )

    try:
        input_df = pd.DataFrame(
            [request.features]
        )

        prediction = model.predict(
            input_df
        )

        result = {
            "prediction": prediction.tolist()
        }

        # Probability if supported
        if hasattr(
            model,
            "predict_proba",
        ):
            try:
                probability = (
                    model.predict_proba(
                        input_df
                    )
                )

                result[
                    "probability"
                ] = probability.tolist()

            except Exception:
                pass

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Prediction failed: {exc}"
            ),
        )