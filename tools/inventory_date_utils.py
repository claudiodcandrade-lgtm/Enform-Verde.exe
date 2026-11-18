"""Normalize IFN workbook measurement dates without losing Excel serial dates."""
from __future__ import annotations

from datetime import date, datetime
from numbers import Real

from openpyxl.utils.datetime import from_excel


def normalize_inventory_date(value):
    """Return an ISO date, handling Excel dates/serials and common text formats.

    Empty/zero serials and unparsable values return None so they cannot silently
    enter temporal pairing as strings or be mistaken for valid acquisition dates.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, Real) and not isinstance(value, bool):
        if value <= 59:
            return None
        try:
            parsed = from_excel(float(value))
        except (TypeError, ValueError, OverflowError):
            return None
        if isinstance(parsed, datetime):
            parsed = parsed.date()
        elif not isinstance(parsed, date):
            return None
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            numeric = float(text)
        except ValueError:
            numeric = None
        if numeric is not None:
            if numeric <= 59:
                return None
            try:
                parsed = from_excel(numeric)
            except (TypeError, ValueError, OverflowError):
                return None
            if isinstance(parsed, datetime):
                parsed = parsed.date()
            elif not isinstance(parsed, date):
                return None
        else:
            parsed = None
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%Y"):
                try:
                    parsed = datetime.strptime(text, fmt).date()
                    break
                except ValueError:
                    continue
            if parsed is None:
                try:
                    parsed = datetime.fromisoformat(text.replace("Z", "+00:00")).date()
                except ValueError:
                    return None
    if parsed.year < 1901:
        return None
    return parsed.isoformat()
