from pathlib import Path


def normalize_generated_charts(charts) -> list[dict]:
    """
    Convert different chart formats into
    one standard format.
    """

    if not charts:
        return []

    normalized = []
    seen_files = set()

    for chart in charts:

        filename = None
        chart_type = "visualization"

        # Dictionary format
        if isinstance(chart, dict):
            filename = (
                chart.get("filename")
                or chart.get("file")
                or chart.get("name")
            )

            chart_type = (
                chart.get("chart_type")
                or "visualization"
            )

        # Tuple/list format
        elif isinstance(chart, (tuple, list)):
            if len(chart) >= 2:
                chart_type = chart[0]
                filename = chart[1]

        # String/path format
        elif chart:
            filename = chart

        if not filename:
            continue

        filename = Path(str(filename)).name

        if filename in seen_files:
            continue

        normalized.append({
            "chart_type": str(chart_type),
            "filename": filename,
        })

        seen_files.add(filename)

    return normalized