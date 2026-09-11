import pandas as pd


def format_status(status: str) -> str:
    """
    Convert an API status value into a user-friendly label.

    Example:
        "awaiting_approval" → "Awaiting Approval"
        "completed" → "Completed"
    """
    if not status:
        return "Unknown"

    return str(status).replace("_", " ").title()


def get_status_type(status: str) -> str:
    """
    Return the Streamlit status type to use for a job.

    Possible values:
        success
        info
        error
        warning
    """
    status = str(status).lower()

    if status in (
        "completed",
        "approved",
        "awaiting_approval",
    ):
        return "success"

    if status in (
        "running",
        "queued",
    ):
        return "info"

    if status in (
        "failed",
        "rejected",
    ):
        return "error"

    return "warning"


def format_datetime(value) -> str:
    """
    Format a datetime value for display.
    """
    if value is None:
        return "Unknown date"

    try:
        timestamp = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(timestamp):
            return "Unknown date"

        return timestamp.strftime(
            "%d %b %Y, %I:%M %p"
        )

    except Exception:
        return "Unknown date"


def format_file_size(size_bytes: int) -> str:
    """
    Convert bytes into a readable file size.

    Example:
        1048576 → 1.00 MB
    """
    if not size_bytes:
        return "0 B"

    size = float(size_bytes)

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    for unit in units:

        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} TB"


def truncate_text(
    text: str,
    max_length: int = 100,
) -> str:
    """
    Shorten long text for displaying in cards/tables.
    """
    if not text:
        return ""

    text = str(text)

    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def safe_value(value, default: str = "N/A") -> str:
    """
    Safely convert an optional value to display text.
    """
    if value is None:
        return default

    if pd.isna(value):
        return default

    text = str(value).strip()

    if not text:
        return default

    return text