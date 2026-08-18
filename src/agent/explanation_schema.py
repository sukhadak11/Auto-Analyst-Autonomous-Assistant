# src/agent/explanation_schema.py
from typing import TypedDict, List


# explanation_schema.py — updated
class Explanation(TypedDict):
    action: str
    reason: str
    alternative_considered: str
    why_not_chosen: str
    expected_impact: str
    learning_note: str
    confidence: str


def make_explanation(action, reason, alternative_considered, why_not_chosen,
                      expected_impact, learning_note, confidence):
    return {
        "action": action, "reason": reason,
        "alternative_considered": alternative_considered,
        "why_not_chosen": why_not_chosen,
        "expected_impact": expected_impact,
        "learning_note": learning_note,
        "confidence": confidence,
    }

def format_explanations(explanations: List[Explanation]) -> str:
    """Turns a list of explanations into readable text for the report."""
    if not explanations:
        return "No significant decisions were logged."

    blocks = []
    for e in explanations:
        blocks.append(
            f"Decision: {e['action']}\n"
            f"Reason: {e['reason']}\n"
            f"Alternative considered: {e['alternative_considered']}\n"
            f"Why not chosen: {e['why_not_chosen']}\n"
            f"Expected impact: {e['expected_impact']}\n"
            f"Learning note: {e['learning_note']}\n"
            f"Confidence: {e['confidence']}"
        )
    return "\n\n".join(blocks)