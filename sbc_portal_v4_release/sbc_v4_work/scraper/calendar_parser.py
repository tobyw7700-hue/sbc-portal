"""
Calendar API scraper for mySBC (Schoolbox).
Confirmed endpoint: GET /calendar/ajax/full?start={unix}&end={unix}&userId={uid}
Returns JSON array of event objects.
"""
import re
import json
import logging
import calendar
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

log = logging.getLogger("sbc.calendar")

BASE_URL = "https://mysbc.sbc.vic.edu.au"

# Event type colours from the JSON (matches mySBC exactly)
EVENT_TYPE_COLORS = {
    "type1":  ("#cee6ea", "#0e4a52"),  # Staff/Student Events — teal
    "type2":  ("#f8deb8", "#7c3d00"),  # Events/Excursions — orange
    "type3":  ("#d4efc4", "#2d5a1b"),  # Reports — green
    "type4":  ("#f2ced6", "#7f1d1d"),  # Due Work / Exams — pink/red
    "type7":  ("#8a9478", "#ffffff"),  # Public Holidays / Student Free Days — grey-green
    "type8":  ("#b8ddff", "#1e3a8a"),  # ACC Activities — light blue
    "type11": ("#8ab4f2", "#1e3a8a"),  # School Days — blue
}

EVENT_TYPE_LABELS = {
    "type1":  "School Event",
    "type2":  "Excursion/Camp",
    "type3":  "Reports",
    "type4":  "Due Work",
    "type7":  "Student Free Day",
    "type8":  "ACC Activity",
    "type11": "School Day",
}


def _month_range(year: int, month: int):
    """Return (start_unix, end_unix) for a whole month."""
    first = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = datetime(year, month, last_day, 23, 59, 59)
    import time
    # Convert to UTC unix timestamps
    start = int(first.timestamp())
    end   = int(last.timestamp())
    return start, end


def fetch_events(session, user_id: str, year: int, month: int) -> List[dict]:
    """Fetch calendar events for a given month."""
    start, end = _month_range(year, month)
    url = f"{BASE_URL}/calendar/ajax/full?start={start}&end={end}&userId={user_id}"
    try:
        resp = session.get(url)
        events = json.loads(resp.text)
        log.info("Calendar %d/%d: %d events", year, month, len(events))
        return events
    except Exception as exc:
        log.error("Calendar fetch failed: %s", exc)
        return []


def parse_events(raw_events: List[dict]) -> Dict[str, List[dict]]:
    """
    Returns {date_str: [event, ...]} where date_str is "YYYY-MM-DD".
    Filters out generic "School Day" and "Term X Week Y" noise events.
    Keeps: due work, excursions, ACC, events, holidays, exams.
    """
    by_date: Dict[str, List[dict]] = {}

    for ev in raw_events:
        title     = ev.get("title", "").strip()
        start_raw = ev.get("start", "")
        color     = ev.get("color", "#cccccc")
        class_name = ev.get("className", "")

        # Determine event type
        ev_type = ""
        for part in class_name.split():
            if part.startswith("type"):
                ev_type = part
                break

        # Skip noisy school-day markers and term week labels
        skip_patterns = [
            r"^St Bernards College: Day \d+$",
            r"^Term \d+ - Week \d+$",
        ]
        if any(re.match(p, title) for p in skip_patterns):
            continue

        # Parse date
        date_str = start_raw[:10] if start_raw else ""
        if not date_str or not re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            continue

        # Parse time if present
        time_str = ""
        if "T" in start_raw:
            m = re.search(r"T(\d{2}:\d{2})", start_raw)
            if m:
                # Convert to 12h
                h, mn = int(m.group(1)[:2]), m.group(1)[3:]
                ampm = "am" if h < 12 else "pm"
                h12  = h if h <= 12 else h - 12
                if h12 == 0: h12 = 12
                time_str = f"{h12}:{mn}{ampm}"

        # Build clean event dict
        ev_data = ev.get("data", {})
        meta    = ev_data.get("meta", {})

        # For due work, extract subject
        folder = meta.get("folderName", "")
        subject_match = re.match(r"^([\w\s]+)\s*\(", folder)
        subject = subject_match.group(1).strip() if subject_match else ""

        clean = {
            "title":    title,
            "date":     date_str,
            "time":     time_str,
            "type":     ev_type,
            "color":    color,
            "label":    EVENT_TYPE_LABELS.get(ev_type, "Event"),
            "subject":  subject,
            "location": meta.get("location", ""),
            "detail":   re.sub(r"<[^>]+>", "", meta.get("detail", "")),
            "all_day":  ev.get("allDay", True),
            "is_due_work": ev_type == "type4" and "personal" in class_name,
            "is_exam":     ev_type == "type4" and "personal" not in class_name,
            "is_holiday":  ev_type == "type7",
            "is_acc":      ev_type == "type8",
        }

        by_date.setdefault(date_str, []).append(clean)

    return by_date
