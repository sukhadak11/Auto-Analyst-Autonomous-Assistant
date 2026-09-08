from typing import TypedDict, List, Any


class Explanation(TypedDict):
    action: str
    reason: str
    alternative_considered: str
    why_not_chosen: str
    expected_impact: str
    learning_note: str
    confidence: str


def make_explanation(
    action,
    reason,
    alternative_considered,
    why_not_chosen,
    expected_impact,
    learning_note,
    confidence,
):
    return {
        "action": action,
        "reason": reason,
        "alternative_considered": alternative_considered,
        "why_not_chosen": why_not_chosen,
        "expected_impact": expected_impact,
        "learning_note": learning_note,
        "confidence": confidence,
    }


def format_explanations(explanations: List[Any]) -> str:
    """Convert explanation objects into readable text without crashing."""

    if not explanations:
        return "No significant decisions were logged."

    blocks = []

    for e in explanations:

        # Handle properly structured explanation dictionaries
        if isinstance(e, dict):
            blocks.append(
                f"Decision: {e.get('action', 'Not specified')}\n"
                f"Reason: {e.get('reason', 'Not specified')}\n"
                f"Alternative considered: {e.get('alternative_considered', 'None')}\n"
                f"Why not chosen: {e.get('why_not_chosen', 'Not specified')}\n"
                f"Expected impact: {e.get('expected_impact', 'Not specified')}\n"
                f"Learning note: {e.get('learning_note', 'Not specified')}\n"
                f"Confidence: {e.get('confidence', 'Not specified')}"
            )

        # Handle string explanations
        elif isinstance(e, str):
            blocks.append(
                f"Decision: Visualization decision\n"
                f"Reason: {e}\n"
                f"Alternative considered: Not specified\n"
                f"Why not chosen: Not specified\n"
                f"Expected impact: Not specified\n"
                f"Learning note: Not specified\n"
                f"Confidence: Not specified"
            )

        # Handle any unexpected object
        else:
            blocks.append(
                f"Decision: Visualization decision\n"
                f"Reason: {str(e)}\n"
                f"Alternative considered: Not specified\n"
                f"Why not chosen: Not specified\n"
                f"Expected impact: Not specified\n"
                f"Learning note: Not specified\n"
                f"Confidence: Not specified"
            )

    return "\n\n".join(blocks)