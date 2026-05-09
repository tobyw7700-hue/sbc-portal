"""
Extended profile scraper — extracts all student fields from mySBC profile page.
Fields: Email, Student ID, Role, DOB, Class Teacher, Year Level, 
        Year Level Coordinator, Tutor Group, Campus, Class
"""
import re, json, logging
from bs4 import BeautifulSoup
from typing import Dict, Optional

log = logging.getLogger("sbc.profile")
BASE_URL = "https://mysbc.sbc.vic.edu.au"


def fetch_extended_profile(session, user_id: str) -> Dict[str, str]:
    """
    Fetch the student's full profile from /search/user/{user_id}
    Returns a flat dict of all visible profile fields.
    """
    url = f"{BASE_URL}/search/user/{user_id}"
    try:
        resp = session.get(url)
        return parse_profile_page(resp.text, user_id)
    except Exception as e:
        log.error("Profile fetch failed: %s", e)
        return {}


def parse_profile_page(html: str, user_id: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    fields = {}

    # ── Extract from window.schoolboxUser JS object ───────────────────
    m = re.search(r'window\.schoolboxUser\s*=\s*(\{[^;]+\});', html, re.S)
    if m:
        try:
            user = json.loads(m.group(1))
            fields["Student ID"] = str(user.get("externalId", user_id))
            fields["_full_name"] = user.get("fullName", "")
            role = user.get("role", {})
            if role:
                fields["Role"] = role.get("name", "")
        except Exception:
            pass

    # ── Extract from profile detail table / definition list ───────────
    # mySBC profile uses a table or dl with label:value pairs
    for dl in soup.find_all("dl"):
        items = dl.find_all(["dt", "dd"])
        key = None
        for item in items:
            if item.name == "dt":
                key = item.get_text(strip=True)
            elif item.name == "dd" and key:
                val = item.get_text(strip=True)
                if val:
                    fields[key] = val
                key = None

    # Also check table rows: <tr><td>Label</td><td>Value</td></tr>
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                val = cells[1].get_text(strip=True)
                if key and val and len(key) < 60:
                    fields[key] = val

    # ── Extract specific labelled divs ────────────────────────────────
    # Some Schoolbox versions use .profile-field or similar
    for div in soup.find_all(class_=re.compile(r"profile|field|detail")):
        label_el = div.find(class_=re.compile(r"label|key|title"))
        value_el = div.find(class_=re.compile(r"value|data|content"))
        if label_el and value_el:
            k = label_el.get_text(strip=True)
            v = value_el.get_text(strip=True)
            if k and v:
                fields[k] = v

    # ── Extract from page text using known field patterns ─────────────
    text = soup.get_text("\n", strip=True)

    patterns = {
        "Email":                  r"[A-Za-z0-9._%+\-]+@sbc\.vic\.edu\.au",
        "Date of Birth":          r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b",
        "Tutor Group":            r"\b(09[A-Z]|10[A-Z]|11[A-Z]|12[A-Z])\b",
    }
    for field, pattern in patterns.items():
        if field not in fields:
            m2 = re.search(pattern, text)
            if m2:
                fields[field] = m2.group(0)

    # ── Look for email specifically ───────────────────────────────────
    if "Email" not in fields:
        m3 = re.search(r'href="mailto:([^"]+)"', html)
        if m3:
            fields["Email"] = m3.group(1)
        else:
            m4 = re.search(r'[\w.+\-]+@sbc\.vic\.edu\.au', html)
            if m4:
                fields["Email"] = m4.group(0)

    # ── Look for teacher/coordinator names ────────────────────────────
    # These often appear as links in the profile
    for a in soup.find_all("a", href=re.compile(r"/search/user/")):
        name = a.get_text(strip=True)
        if not name or name == fields.get("_full_name",""):
            continue
        # Try to classify by context
        parent_text = (a.parent.get_text(strip=True) if a.parent else "").lower()
        if "class teacher" in parent_text or "form teacher" in parent_text:
            fields["Class Teacher"] = name
        elif "coordinator" in parent_text or "year level" in parent_text:
            fields["Year Level Coordinator"] = name

    # ── Look for structured profile sections in the HTML ─────────────
    # Schoolbox often renders profile as a list of key:value spans
    for row in soup.find_all(class_=re.compile(r"row|item|entry")):
        spans = row.find_all(["span","div","td"])
        if len(spans) >= 2:
            k = spans[0].get_text(strip=True)
            v = spans[1].get_text(strip=True)
            if k and v and ":" not in k and len(k) < 50 and len(v) < 200:
                # Likely a field
                if k not in fields and v not in fields.values():
                    fields[k] = v

    # Clean up private fields
    fields.pop("_full_name", None)

    log.info("Profile fields extracted: %s", list(fields.keys()))
    return fields
