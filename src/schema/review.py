# This preserves the existing approval request structure. review
from pydantic import BaseModel
class ApprovalRequest(BaseModel):
    decision: str
    notes: str | None = None