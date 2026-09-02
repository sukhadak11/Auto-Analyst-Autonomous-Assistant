from collections import Counter
from typing import List
from explanation_schema import Explanation


def format_analytical_decisions(explanations: List[Explanation]) -> str:
    if not explanations:
        return "No analytical decisions were logged."
    lines = []
    for e in explanations:
        lines.append(f"- {e['action']} — {e['reason']} (Confidence: {e['confidence']})")
    return "\n".join(lines)


def format_confidence_assessment(explanations: List[Explanation]) -> str:
    if not explanations:
        return "No confidence data available."
    counts = Counter(e["confidence"] for e in explanations if e.get("confidence") not in (None, "N/A"))
    total = sum(counts.values())
    if total == 0:
        return "No confidence-scored decisions."
    low_items = [e["action"] for e in explanations if e.get("confidence") == "Low"]
    summary = f"{counts.get('High', 0)} High, {counts.get('Medium', 0)} Medium, {counts.get('Low', 0)} Low confidence ({total} total)."
    if low_items:
        summary += " Low-confidence items: " + "; ".join(low_items) + "."
    return summary