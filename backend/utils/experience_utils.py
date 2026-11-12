import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple


CURRENT_DATE_WORDS = {
    "present",
    "current",
    "now",
    "till date",
    "to date",
    "ongoing",
}


def _parse_date(value: str, is_end_date: bool = False) -> Optional[date]:
    """
    Parse common resume date formats.

    Examples:
    Jan 2022, January 2022, 01/2022, 2022-01,
    2022, 15 Jan 2022.
    """
    if not value or not isinstance(value, str):
        return None

    cleaned = value.strip()

    if not cleaned:
        return None

    if is_end_date and cleaned.lower() in CURRENT_DATE_WORDS:
        return date.today()

    formats = [
        "%b %Y",
        "%B %Y",
        "%m/%Y",
        "%m-%Y",
        "%Y-%m",
        "%Y/%m",
        "%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt).date()

            # A year-only start date begins in January.
            # A year-only end date ends in December.
            if fmt == "%Y" and is_end_date:
                return date(parsed.year, 12, 31)

            return parsed

        except ValueError:
            continue

    return None


def _months_between(start: date, end: date) -> int:
    """Calculate inclusive calendar months between two dates."""
    return max(
        0,
        (end.year - start.year) * 12
        + end.month - start.month + 1
    )


def calculate_experience(experience: List[Dict]) -> Dict:
    """
    Calculate total non-overlapping employment experience.

    Returns total months, years, verified and unverified
    entries, and a status indicating calculation confidence.
    """
    if not isinstance(experience, list):
        experience = []

    valid_periods: List[Tuple[date, date]] = []
    unverified_entries = []
    invalid_entries = []

    today = date.today()

    for index, entry in enumerate(experience):
        if not isinstance(entry, dict):
            continue

        start_raw = str(entry.get("start_date") or "").strip()
        end_raw = str(entry.get("end_date") or "").strip()

        start = _parse_date(start_raw)
        end = _parse_date(end_raw, is_end_date=True)

        if not start_raw or not end_raw:
            unverified_entries.append(index)
            continue

        if start is None or end is None:
            unverified_entries.append(index)
            continue

        if start > today or end > today or start > end:
            invalid_entries.append(index)
            continue

        valid_periods.append((start, end))

    # Sort employment periods by start date.
    valid_periods.sort(key=lambda period: period[0])

    # Merge overlapping or consecutive periods.
    merged_periods: List[List[date]] = []

    for start, end in valid_periods:
        if not merged_periods:
            merged_periods.append([start, end])
            continue

        previous_start, previous_end = merged_periods[-1]

        if start <= previous_end:
            merged_periods[-1][1] = max(previous_end, end)
        else:
            merged_periods.append([start, end])

    total_months = sum(
        _months_between(start, end)
        for start, end in merged_periods
    )

    if invalid_entries:
        status = "partially_verified"
    elif unverified_entries:
        status = "partially_verified"
    elif valid_periods:
        status = "verified"
    else:
        status = "unverified"

    return {
        "total_months": total_months,
        "total_years": round(total_months / 12, 1),
        "verified_entries": len(valid_periods),
        "unverified_entries": unverified_entries,
        "invalid_entries": invalid_entries,
        "status": status,
        "calculation_method": (
            "Python date calculation with overlapping "
            "employment periods merged."
        ),
    }
