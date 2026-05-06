"""
Parses the mySBC timetable HTML into structured data.
Structure: 10-day cycle × 7 rows (Homeroom + P1-P6)
Each cell: subject_code, room, teacher
"""
import re
import os
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

log = logging.getLogger("sbc.timetable")

SUBJECT_COLOURS = {
    "MATH":     "#dbeafe",  # blue
    "ENGL":     "#dcfce7",  # green
    "SCIE":     "#fef9c3",  # yellow
    "HUMS":     "#fce7f3",  # pink
    "RELS":     "#ede9fe",  # purple
    "HEPE":     "#ffedd5",  # orange
    "ITAL":     "#cffafe",  # cyan
    "FREN":     "#cffafe",
    "JAPN":     "#cffafe",
    "VISCOM":   "#f3e8ff",  # violet
    "BUSMAN":   "#fee2e2",  # red/salmon
    "HR":       "#f1f5f9",  # grey
    "ASSEMBLY": "#f1f5f9",
    "SEL":      "#f1f5f9",
}

SUBJECT_COLOURS_DARK = {
    "MATH":     "#1e3a8a",
    "ENGL":     "#14532d",
    "SCIE":     "#713f12",
    "HUMS":     "#831843",
    "RELS":     "#4c1d95",
    "HEPE":     "#7c2d12",
    "ITAL":     "#164e63",
    "FREN":     "#164e63",
    "JAPN":     "#164e63",
    "VISCOM":   "#4a1d96",
    "BUSMAN":   "#7f1d1d",
    "HR":       "#334155",
    "ASSEMBLY": "#334155",
    "SEL":      "#334155",
}


def _subject_key(code: str) -> str:
    """Extract subject type from class code e.g. 09MATH10 → MATH"""
    c = re.sub(r"^(0?[7-9]|1[0-2])", "", code.upper()).strip()
    c = re.sub(r"^[A-Z]\s+", "", c).strip()
    c = re.sub(r"\d+$", "", c).strip()
    return c


def _friendly(code: str) -> str:
    from scraper.parser import _friendly_name
    return _friendly_name(code)


def _cell_colour(code: str) -> tuple:
    """Returns (bg_hex, fg_hex) for a subject code."""
    key = _subject_key(code)
    bg = SUBJECT_COLOURS.get(key, "#e2e8f0")
    fg = SUBJECT_COLOURS_DARK.get(key, "#1e293b")
    return bg, fg


def parse_timetable(html: str) -> dict:
    """
    Returns:
    {
      "days": ["Day 1", ..., "Day 10"],
      "periods": [
        {"label": "Homeroom", "time": "8:45am–8:55am"},
        {"label": "Period 1", "time": "8:55am–9:45am"},
        ...
      ],
      "cells": {
        "Day 1": {
          "Homeroom": {"code":"09J HR","room":"RH501","teacher":"Ms Rebekka Absolon"},
          "Period 1": {...},
          ...
        },
        ...
      }
    }
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {"days": [], "periods": [], "cells": {}}

    table = soup.find("table")
    if not table:
        log.warning("No timetable table found")
        return result

    rows = table.find_all("tr")
    if not rows:
        return result

    # Header row: Day 1 ... Day 10
    header_cells = rows[0].find_all(["th", "td"])
    days = []
    for cell in header_cells[1:]:  # skip first empty cell
        text = cell.get_text(strip=True)
        if text:
            days.append(text)
    result["days"] = days
    for d in days:
        result["cells"][d] = {}

    # Data rows: each row = one period
    for row in rows[1:]:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        # First cell = period label + time
        period_text = cells[0].get_text(" ", strip=True)
        # Split "Period 18:55am–9:45am" or "Homeroom8:45am–8:55am"
        # Handle any school's period naming convention
        m = re.match(r"(Period\s+[1-9][0-9]?|Homeroom|Assembly|Tutorial|Recess|Lunch)(.*?)$",
                     period_text, re.I)
        if m:
            label = m.group(1).strip()
            time_raw = m.group(2).strip()
            # Normalise label: "Period 1" not "Period 18:55..."
            label = re.sub(r"\s*\d{1,2}:\d{2}.*$", "", label).strip()
            if not label:
                label = period_text[:15]
            time  = time_raw
        else:
            # Fallback: everything before the first digit-colon is the label
            tm = re.search(r"(\d{1,2}:\d{2})", period_text)
            if tm:
                label = period_text[:tm.start()].strip() or period_text[:10]
                time  = period_text[tm.start():]
            else:
                label = period_text[:20]
                time  = ""

        result["periods"].append({"label": label, "time": time})

        # Subject cells
        for i, day in enumerate(days):
            if i + 1 >= len(cells):
                result["cells"][day][label] = None
                continue

            cell = cells[i + 1]
            text = cell.get_text(" ", strip=True)

            if not text:
                result["cells"][day][label] = None
                continue

            # Parse: "09MATH10(09MATH10)RH201 Mr Benjamin Wilson"
            # or:    "09MATH10\n(09MATH10)\nRH201\nMr Benjamin Wilson"
            # Match subject codes for any year level: 07MATH, 08ENGL, 09MATH10, VCE subjects, etc.
            code_m  = re.search(r"([A-Z0-9][A-Z0-9\s]{2,20}?)(?:\(|\s+RH|\s+[A-Z]{1,3}\d{3,4}|\s+(?:Mr|Ms|Mrs|Dr|Miss))", text)
            room_m  = re.search(r"\b([A-Z]{1,3}\d{3,4})\b", text)
            # Teacher: starts with Mr/Ms/Mrs/Dr
            teach_m = re.search(r"\b((?:Mr|Ms|Mrs|Dr|Miss)\.?\s+[A-Z][a-z]+ [A-Z][a-z]+)", text)

            code    = code_m.group(1).strip() if code_m else text[:15]
            room    = room_m.group(1) if room_m else ""
            teacher = teach_m.group(1) if teach_m else ""

            result["cells"][day][label] = {
                "code":    code,
                "name":    _friendly(code),
                "room":    room,
                "teacher": teacher,
                "colours": _cell_colour(code),
            }

    log.debug("Timetable: %d days, %d periods", len(days), len(result["periods"]))
    return result


def load_timetable(session=None, username: str = "") -> dict:
    """
    Fetch timetable for the current user.
    - Checks per-user cache first (timetable_{username}.html)
    - Falls back to legacy debug_timetable.html
    - If no cache, fetches live from mySBC and saves to disk
    - Any user gets their own timetable automatically
    """
    cache_dir = os.path.expanduser("~/.sbc_portal")
    os.makedirs(cache_dir, exist_ok=True)

    # Per-user cache path
    user_cache = os.path.join(cache_dir, f"timetable_{username}.html") if username else None
    legacy_cache = os.path.join(cache_dir, "debug_timetable.html")

    # Try per-user cache first, then legacy
    for cache_path in [p for p in [user_cache, legacy_cache] if p]:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    html = f.read()
                log.info("Loaded timetable from cache: %s", os.path.basename(cache_path))
                tt = parse_timetable(html)
                if tt.get("days"):
                    return tt
            except Exception as e:
                log.warning("Cache read failed: %s", e)

    # No cache — fetch live
    if session:
        try:
            resp = session.get("https://mysbc.sbc.vic.edu.au/timetable")
            html = resp.text
            tt   = parse_timetable(html)
            if tt.get("days"):
                # Save to per-user cache
                save_path = user_cache or legacy_cache
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(html)
                log.info("Timetable fetched and cached for %s (%d days)",
                         username or "unknown", len(tt["days"]))
                return tt
        except Exception as exc:
            log.error("Could not fetch timetable: %s", exc)

    return {}
