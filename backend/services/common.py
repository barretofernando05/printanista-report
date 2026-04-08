from typing import Any

def build_filters(date_from: str | None = None, date_to: str | None = None):
    filters = ["1=1"]
    params: dict[str, Any] = {}
    if date_from:
        filters.append("report_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        filters.append("report_date <= :date_to")
        params["date_to"] = date_to
    return " AND ".join(filters), params
