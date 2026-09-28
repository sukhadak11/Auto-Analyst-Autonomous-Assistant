# This preserves your existing prediction request schema exactly.   predictions
from pydantic import BaseModel
class PredictionRequest(BaseModel):
    features: dict