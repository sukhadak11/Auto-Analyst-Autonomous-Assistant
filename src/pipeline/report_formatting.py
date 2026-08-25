from collections import Counter
from typing import List
from src.agent.explanation_schema import Explanation


def format_analytical_decisions(explanations: List[Explanation]) -> str:
    """Turns the raw explanations list into a readable Decisions section."""
    if not explanations:
        return "No analytical decisions were logged for this run."

    blocks = []
    for e in explanations:
        blocks.append(
            f"- **{e['action']}**\n"
            f"  Reason: {e['reason']}\n"
            f"  Alternative considered: {e['alternative_considered']}\n"
            f"  Why not chosen: {e['why_not_chosen']}\n"
            f"  Expected impact: {e['expected_impact']}\n"
            f"  Confidence: {e['confidence']}"
        )
    return "\n\n".join(blocks)


def format_educational_insights(explanations: List[Explanation]) -> str:
    """Pulls learning_note fields into a teaching-focused summary,
    deduplicated so repeated lessons (e.g. multiple median-imputation
    decisions) don't repeat the same note over and over."""
    if not explanations:
        return "No educational insights were generated for this run."

    seen = set()
    notes = []
    for e in explanations:
        note = e.get("learning_note", "").strip()
        if note and note not in seen:
            seen.add(note)
            notes.append(f"- {note}")

    if not notes:
        return "No educational insights were generated for this run."

    return "\n".join(notes)


def format_confidence_assessment(explanations: List[Explanation]) -> str:
    """Computes a real rollup of confidence across all decisions —
    never invented, always counted from the actual explanations list."""
    if not explanations:
        return "No decisions were logged, so no confidence assessment is available."

    counts = Counter(e["confidence"] for e in explanations if e.get("confidence") not in (None, "N/A"))
    total_scored = sum(counts.values())

    if total_scored == 0:
        return "No confidence-scored decisions were logged for this run."

    lines = [
        f"Across {total_scored} scored decisions in this analysis: "
        f"{counts.get('High', 0)} High confidence, "
        f"{counts.get('Medium', 0)} Medium confidence, "
        f"{counts.get('Low', 0)} Low confidence."
    ]

    low_confidence_items = [e for e in explanations if e.get("confidence") == "Low"]
    if low_confidence_items:
        lines.append("\nThe following decisions had Low confidence and are worth extra scrutiny before relying on this report:")
        for e in low_confidence_items:
            lines.append(f"- {e['action']} — {e['reason']}")

    return "\n".join(lines)