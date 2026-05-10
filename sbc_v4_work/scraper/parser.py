"""
Parser for mySBC (Schoolbox 26.0.9).

CONFIRMED from network inspection:
  - Grade data is loaded via POST to /learning/grades/{uid}/{year}-{sem}/{class_id}
  - Response is JSON: {"status": 200, "content": "<html fragment>"}
  - HTML fragment contains:
      <div data-learner-mark class="grade gradient-none-bg"><span>94 %</span></div>
      <li class="assessment"> with title, due date, status, feedback
  - infoIndex JS var: [{"displayMark":"94 %","info":"feedback text"}, ...]
  - assessments JS var: ["26S1: Jobs and the Future", ...]
"""
import re
import os
import json
import logging
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from bs4 import BeautifulSoup

from data.models import Subject, Assignment, UserProfile, AcademicData
from scraper.auth import SBCSession, PROFILE_URL, CLASSES_URL, BASE_URL

log = logging.getLogger("sbc.parser")

GRADES_BASE = f"{BASE_URL}/learning/grades"
DEBUG_DIR   = os.path.expanduser("~/.sbc_portal")

SUBJECT_NAME_MAP = {
    # ── Full codes (exact match, all year levels) ─────────────────────────────
    # Year 7-10 core subjects
    "07MATH":    "Mathematics",   "08MATH":    "Mathematics",
    "09MATH10":  "Mathematics",   "10MATH":    "Mathematics",
    "07ENGL":    "English",       "08ENGL":    "English",
    "09ENGL10":  "English",       "10ENGL":    "English",
    "07SCIE":    "Science",       "08SCIE":    "Science",
    "09SCIE10":  "Science",       "10SCIE":    "Science",
    "07HUMS":    "Humanities",    "08HUMS":    "Humanities",
    "09HUMS10":  "Humanities",    "10HUMS":    "Humanities",
    "07RELS":    "Religion & Society", "08RELS": "Religion & Society",
    "09RELS10":  "Religion & Society", "10RELS": "Religion & Society",
    "07HEPE":    "Health & PE",   "08HEPE":    "Health & PE",
    "09HEPE10":  "Health & PE",   "10HEPE":    "Health & PE",
    "07ITAL":    "Italian",       "08ITAL":    "Italian",
    "09ITAL5":   "Italian",       "10ITAL":    "Italian",
    "07JAPN":    "Japanese",      "08JAPN":    "Japanese",
    "09JAPN5":   "Japanese",      "10JAPN":    "Japanese",
    # Year 9-10 electives
    "09BUSMAN01":"Business Management",
    "09VISCOM02":"Visual Communication",
    "09DIGT":    "Digital Technology",
    "09FOOD":    "Food Technology",
    "09WOOD":    "Wood Technology",
    "09METL":    "Metal Technology",
    "09DRAM":    "Drama",
    "09MUSI":    "Music",
    "09ARTS":    "Visual Art",
    "09PHYED":   "Physical Education",
    "09MEDIA":   "Media Studies",
    "10BUSMAN":  "Business Management",
    "10VISCOM":  "Visual Communication",
    "10DIGT":    "Digital Technology",
    "10FOOD":    "Food Technology",
    "10WOOD":    "Wood Technology",
    "10METL":    "Metal Technology",
    "10DRAM":    "Drama",
    "10MUSI":    "Music",
    "10ARTS":    "Visual Art",
    "10PHYED":   "Physical Education",
    "10MEDIA":   "Media Studies",
    "10ECON":    "Economics",
    "10HIST":    "History",
    "10GEOG":    "Geography",
    # Homeroom / admin
    "09J ASSEMBLY": "Assembly",
    "08J ASSEMBLY": "Assembly",
    "07J ASSEMBLY": "Assembly",
    "10J ASSEMBLY": "Assembly",
    "09J HR":    "Home Room",
    "08J HR":    "Home Room",
    "07J HR":    "Home Room",
    "10J HR":    "Home Room",
    "09J SEL":   "Social & Emotional Learning",
    "08J SEL":   "Social & Emotional Learning",
    "07J SEL":   "Social & Emotional Learning",
    "10J SEL":   "Social & Emotional Learning",
    # VCE Units 1-4
    "11ENGL":    "English",           "12ENGL":    "English",
    "11ENGLLANG":"English Language",  "12ENGLLANG":"English Language",
    "11ENGLLIT": "English Literature","12ENGLLIT": "English Literature",
    "11MATH":    "Mathematics",       "12MATH":    "Mathematics",
    "11MATHMETH":"Maths Methods",     "12MATHMETH":"Maths Methods",
    "11MATHSPEC":"Specialist Maths",  "12MATHSPEC":"Specialist Maths",
    "11MATHGEN": "General Mathematics","12MATHGEN":"General Mathematics",
    "11SCIE":    "Science",           "12SCIE":    "Science",
    "11BIOL":    "Biology",           "12BIOL":    "Biology",
    "11CHEM":    "Chemistry",         "12CHEM":    "Chemistry",
    "11PHYS":    "Physics",           "12PHYS":    "Physics",
    "11PSYCH":   "Psychology",        "12PSYCH":   "Psychology",
    "11ENVIRON": "Environmental Science","12ENVIRON":"Environmental Science",
    "11HIST":    "History",           "12HIST":    "History",
    "11ANCEHIST":"Ancient History",   "12ANCEHIST":"Ancient History",
    "11MODEHIST":"Modern History",    "12MODEHIST":"Modern History",
    "11GEOG":    "Geography",         "12GEOG":    "Geography",
    "11ECON":    "Economics",         "12ECON":    "Economics",
    "11ACCT":    "Accounting",        "12ACCT":    "Accounting",
    "11LEGAL":   "Legal Studies",     "12LEGAL":   "Legal Studies",
    "11BUSMAN":  "Business Management","12BUSMAN": "Business Management",
    "11RELS":    "Religion & Society","12RELS":    "Religion & Society",
    "11ITAL":    "Italian",           "12ITAL":    "Italian",
    "11JAPN":    "Japanese",          "12JAPN":    "Japanese",
    "11FREN":    "French",            "12FREN":    "French",
    "11HEPE":    "Health & PE",       "12HEPE":    "Health & PE",
    "11PHYED":   "Physical Education","12PHYED":   "Physical Education",
    "11OUTDOOR": "Outdoor Education", "12OUTDOOR": "Outdoor Education",
    "11VISCOM":  "Visual Communication","12VISCOM":"Visual Communication",
    "11STUDIOAR":"Studio Arts",       "12STUDIOAR":"Studio Arts",
    "11PHOTOIM": "Photography",       "12PHOTOIM": "Photography",
    "11DRAM":    "Drama",             "12DRAM":    "Drama",
    "11THEATST": "Theatre Studies",   "12THEATST": "Theatre Studies",
    "11MUSI":    "Music",             "12MUSI":    "Music",
    "11MUSICP":  "Music Performance", "12MUSICP":  "Music Performance",
    "11MUSICTH": "Music Theory",      "12MUSICTH": "Music Theory",
    "11SOFTDEV": "Software Development","12SOFTDEV":"Software Development",
    "11DIGT":    "Digital Technology","12DIGT":    "Digital Technology",
    "11SYSTEMS": "Systems Engineering","12SYSTEMS":"Systems Engineering",
    "11ENGTECH": "Engineering Technology","12ENGTECH":"Engineering Technology",
    "11FOOD":    "Food Studies",      "12FOOD":    "Food Studies",
    "11GLOBPOL": "Global Politics",   "12GLOBPOL": "Global Politics",
    "11SOCIOL":  "Sociology",         "12SOCIOL":  "Sociology",
    "11DEBATE":  "Debating",          "12DEBATE":  "Debating",
    "11MEDIA":   "Media Studies",     "12MEDIA":   "Media Studies",

    # ── Partial-code fallbacks (for codes not matched above) ──────────────────
    "MATH":      "Mathematics",
    "ENGL":      "English",
    "SCIE":      "Science",
    "HUMS":      "Humanities",
    "RELS":      "Religion & Society",
    "HEPE":      "Health & PE",
    "ITAL":      "Italian",
    "JAPN":      "Japanese",
    "FREN":      "French",
    "GERM":      "German",
    "BUSMAN":    "Business Management",
    "VISCOM":    "Visual Communication",
    "DIGT":      "Digital Technology",
    "FOOD":      "Food Technology",
    "WOOD":      "Wood Technology",
    "METL":      "Metal Technology",
    "DRAM":      "Drama",
    "MUSI":      "Music",
    "ARTS":      "Visual Art",
    "PHYED":     "Physical Education",
    "MEDIA":     "Media Studies",
    "ECON":      "Economics",
    "ACCT":      "Accounting",
    "LEGAL":     "Legal Studies",
    "HIST":      "History",
    "GEOG":      "Geography",
    "BIOL":      "Biology",
    "CHEM":      "Chemistry",
    "PHYS":      "Physics",
    "PSYCH":     "Psychology",
    "ENVIRON":   "Environmental Science",
    "OUTDOOR":   "Outdoor Education",
    "MATHMETH":  "Maths Methods",
    "MATHSPEC":  "Specialist Maths",
    "MATHGEN":   "General Mathematics",
    "ENGLLANG":  "English Language",
    "ENGLLIT":   "English Literature",
    "STUDIOAR":  "Studio Arts",
    "PHOTOIM":   "Photography",
    "THEATST":   "Theatre Studies",
    "MUSICP":    "Music Performance",
    "MUSICTH":   "Music Theory",
    "SOFTDEV":   "Software Development",
    "SYSTEMS":   "Systems Engineering",
    "ENGTECH":   "Engineering Technology",
    "GLOBPOL":   "Global Politics",
    "SOCIOL":    "Sociology",
    "ANCEHIST":  "Ancient History",
    "MODEHIST":  "Modern History",
    "DEBATE":    "Debating",
    "ASSEMBLY":  "Assembly",
    "HR":        "Home Room",
    "SEL":       "Social & Emotional Learning",
    "CHOIR":     "Choir",
    "BAND":      "Concert Band",
    "ORCH":      "Orchestra",
    "SPRT":      "Sport",
    "LIBR":      "Library",
    "COMP":      "Computing",
    "APPDES":    "App Design",
    "ROBOT":     "Robotics",
    "CERAMICS":  "Ceramics",
    "DANCE":     "Dance",
    "CHIN":      "Chinese",
    "LATN":      "Latin",
    "ARABIC":    "Arabic",
    "SPAN":      "Spanish",
    "INDO":      "Indonesian",
}


def _friendly_name(code: str) -> str:
    """Convert a subject code like 09MATH10 or VCEMATHMETH to a friendly name."""
    # Direct full-code lookup first (handles e.g. 09MATH10, 09HUMS10 exactly)
    upper = code.strip().upper()
    if upper in SUBJECT_NAME_MAP:
        return SUBJECT_NAME_MAP[upper]

    c = upper
    # Strip year-level prefix: 07, 08, 09, 10, 11, 12
    c = re.sub(r"^(0?[7-9]|1[0-2])", "", c).strip()
    # Strip class letter+space prefix (e.g. "J " in "09J ASSEMBLY")
    c = re.sub(r"^[A-Z]\s+", "", c).strip()
    # Try lookup after prefix strip
    if c in SUBJECT_NAME_MAP:
        return SUBJECT_NAME_MAP[c]
    # Strip trailing digits only (class number suffix like "10" in "MATH10")
    c2 = re.sub(r"\d+$", "", c).strip()
    if c2 in SUBJECT_NAME_MAP:
        return SUBJECT_NAME_MAP[c2]
    # startswith match against map keys
    for key, name in SUBJECT_NAME_MAP.items():
        if c2 == key or c2.startswith(key) or c.startswith(key):
            return name
    # If still looks like a code, title-case it nicely
    if c2 and len(c2) > 2:
        return c2.title()
    return code.strip()


def _parse_grade(text: str) -> Optional[float]:
    if not text:
        return None
    text = text.strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", text)
    if m:
        num, den = float(m.group(1)), float(m.group(2))
        return round(num / den * 100, 1) if den else None
    m = re.match(r"^(\d+(?:\.\d+)?)$", text.strip())
    if m:
        v = float(m.group(1))
        return v if v <= 100 else None
    for k, v in {"A+":97,"A":93,"A-":90,"B+":87,"B":83,"B-":80,
                  "C+":77,"C":73,"C-":70,"D":65,"E":55,"F":40}.items():
        if text.upper() == k:
            return float(v)
    return None


def _dump(name: str, content: str):
    try:
        with open(os.path.join(DEBUG_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass


def _abs_url(href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    return href if href.startswith("http") else BASE_URL + href


# ── POST request helper ───────────────────────────────────────────────────────

def _post_grade_fragment(session: SBCSession, url: str) -> Optional[str]:
    """
    POST to a Schoolbox grade URL — returns the HTML fragment from the JSON response.
    The response is: {"status": 200, "content": "<html>..."}
    """
    try:
        r = session.session.post(
            url,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": f"{GRADES_BASE}/{url.split('/grades/')[-1].rsplit('/',1)[0]}",
            },
            data={},
            timeout=20,
            allow_redirects=True,
        )
        log.debug("POST %s → %d (%d bytes)", url, r.status_code, len(r.content))
        data = r.json()
        if data.get("status") == 200:
            return data.get("content", "")
        log.warning("POST returned status %s", data.get("status"))
        return None
    except Exception as exc:
        log.error("POST failed for %s: %s", url, exc)
        return None


# ── Profile ───────────────────────────────────────────────────────────────────

def scrape_profile(session: SBCSession) -> UserProfile:
    """
    Fetch user profile. Works for any mySBC user.
    Step 1: GET homepage → extract user ID from window.schoolboxUser JS
    Step 2: GET /search/user/{id} → extract full profile details
    """
    profile = UserProfile()
    try:
        # Step 1: get user ID from the homepage JS
        resp = session.get(BASE_URL + "/")
        html = resp.text
        m = re.search(r'window\.schoolboxUser\s*=\s*(\{[^;]+\});', html, re.S)
        if m:
            try:
                user = json.loads(m.group(1))
                profile.student_id   = str(user.get("id", ""))
                profile.username     = str(user.get("externalId", ""))
                profile.display_name = user.get("fullName", "")
                role = user.get("role", {})
                profile.year_level   = re.sub(
                    r"Students\s*-\s*", "", role.get("name",""), flags=re.I)
                # Extract email from attributes
                email_m = re.search(r'[\w.+\-]+@[\w.\-]+\.\w+', html)
                if email_m:
                    profile.email = email_m.group(0)
            except Exception as e:
                log.warning("Could not parse schoolboxUser JS: %s", e)

        # Step 2: fetch full profile page using the ID
        if profile.student_id:
            try:
                resp2 = session.get(PROFILE_URL + profile.student_id)
                html2 = resp2.text
                soup2 = BeautifulSoup(html2, "html.parser")

                # Re-extract from profile page JS (more complete)
                m2 = re.search(r'window\.schoolboxUser\s*=\s*(\{[^;]+\});', html2, re.S)
                if m2:
                    try:
                        user2 = json.loads(m2.group(1))
                        if not profile.display_name:
                            profile.display_name = user2.get("fullName","")
                        if not profile.email:
                            profile.email = user2.get("email","")
                    except Exception:
                        pass

                # Extract email from page if still missing
                if not profile.email:
                    em = re.search(r'[\w.+\-]+@[\w.\-]+\.edu\.au', html2)
                    if em:
                        profile.email = em.group(0)

            except Exception as e:
                log.warning("Could not fetch profile page: %s", e)

        # Fallback: try to get name from any page element
        if not profile.display_name:
            resp3 = session.get(BASE_URL + "/")
            soup3 = BeautifulSoup(resp3.text, "html.parser")
            for sel in [".user-name", ".profile-name", ".nav-user", "h1"]:
                el = soup3.select_one(sel)
                if el and el.get_text(strip=True):
                    profile.display_name = el.get_text(strip=True)
                    break

        log.info("Profile: %s (id=%s)", profile.display_name, profile.student_id)
        return profile
    except Exception as exc:
        log.error("Profile failed: %s", exc)
        return profile


# ── Class list ────────────────────────────────────────────────────────────────

def _scrape_class_list(session: SBCSession) -> List[Tuple[str, str, str]]:
    """Returns [(code, homepage_url, class_id)]"""
    html = session.get(CLASSES_URL).text
    soup = BeautifulSoup(html, "html.parser")
    code_to_url: Dict[str,str] = {}
    code_to_id:  Dict[str,str] = {}
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).upper()
        href = a["href"]
        if not re.match(r"^(0?[7-9]|1[0-2])[A-Z]", text):
            continue
        if "/homepage/code/" in href:
            code_to_url[text] = _abs_url(href)
        elif re.search(r"/homepage/(\d+)$", href):
            m = re.search(r"/homepage/(\d+)$", href)
            if m:
                code_to_id[text] = m.group(1)
    results = [(code, url, code_to_id.get(code,""))
               for code, url in code_to_url.items()]
    log.debug("Classes: %d", len(results))
    return results


# ── Semester map from overview ────────────────────────────────────────────────

def _get_semester_map(session: SBCSession, user_id: str) -> Dict[str, List[dict]]:
    """Returns {year: [{period, class_urls: {class_id: url}}]}"""
    html = session.get(f"{GRADES_BASE}/{user_id}").text
    _dump("debug_grades_overview.html", html)
    soup = BeautifulSoup(html, "html.parser")

    by_year: Dict[str, List[dict]] = {}

    # Parse semester options
    for opt in soup.find_all("option"):
        href  = opt.get("data-href","")
        label = opt.get_text(strip=True)
        m = re.search(r"/(\d{4})-(\d+)$", href)
        if not m:
            continue
        year   = m.group(1)
        period = f"{m.group(1)}-{m.group(2)}"
        by_year.setdefault(year, []).append({
            "period": period,
            "label":  label,
            "sem_url": _abs_url(href),
        })

    # For each semester, parse the class links to get class_id→grade_url mapping
    current_year = datetime.now().year
    relevant_years = [str(y) for y in range(current_year - 3, current_year + 1)]
    for year, sems in by_year.items():
        if year not in relevant_years:
            continue
        for sem in sems:
            sem["class_grade_urls"] = {}
            try:
                sem_html = session.get(sem["sem_url"]).text
                sem_soup = BeautifulSoup(sem_html, "html.parser")
                for a in sem_soup.find_all("a", href=re.compile(
                        r"/learning/grades/\d+/\d{4}-\d+/\d+")):
                    href = a["href"]
                    m2   = re.search(r"/(\d+)$", href)
                    if m2:
                        class_id = m2.group(1)
                        sem["class_grade_urls"][class_id] = _abs_url(href)
            except Exception as exc:
                log.warning("Could not fetch sem %s: %s", sem["period"], exc)

    return by_year


# ── Parse grade fragment HTML ─────────────────────────────────────────────────

def _parse_grade_fragment(html_fragment: str, code: str,
                          year: int, period: str) -> Subject:
    """
    Parse the HTML fragment returned by POST to the class grade URL.
    Confirmed structure:
      <div data-learner-mark class="grade ..."><span>94 %</span></div>
      <li class="assessment">
        <div class="flex-grade">
          <a href="..."><p>26S1: Jobs and the Future</p></a>
          <p>...<span data-status-label>Reviewed</span>
             <span class="pipe meta">Common Assessment Task...</span>
             <span class="pipe meta"><time datetime="...">Feb 27, 2026</time></span>
          </p>
        </div>
        <div data-learner-mark class="grade ..."><span>94 %</span></div>
        <div class="content"><blockquote><p>feedback...</p></blockquote></div>
      </li>
    Also parses infoIndex JS variable for grades + feedback.
    """
    soup = BeautifulSoup(html_fragment, "html.parser")

    subj = Subject(
        name   = _friendly_name(code),
        code   = code,
        year   = year,
        period = period,
    )

    # ── Method 1: parse infoIndex from inline JS ──────────────────────
    # let infoIndex = [{"displayMark":"94 %","info":"feedback",...}, ...]
    # let assessments = ["26S1: Jobs and the Future", ...]
    info_index  = []
    assess_names = []

    m_info = re.search(r'let\s+infoIndex\s*=\s*(\[.*?\]);', html_fragment, re.S)
    if m_info:
        try:
            info_index = json.loads(m_info.group(1))
        except Exception:
            pass

    m_assess = re.search(r'let\s+assessments\s*=\s*(\[.*?\]);', html_fragment, re.S)
    if m_assess:
        try:
            assess_names = json.loads(m_assess.group(1))
        except Exception:
            pass

    # ── Method 2: parse <li class="assessment"> elements ─────────────
    assignments = []
    for li in soup.select("li.assessment"):
        a = Assignment(title="")

        # Title from link text
        title_el = li.select_one(".flex-grade a p, .flex-grade a")
        if title_el:
            a.title = title_el.get_text(strip=True)[:150]

        # Grade from data-learner-mark div
        grade_el = li.select_one("[data-learner-mark] span, .grade span")
        if grade_el:
            g = grade_el.get_text(strip=True)
            a.grade     = g
            a.grade_raw = _parse_grade(g)

        # Status
        status_el = li.select_one("[data-status-label]")
        if status_el:
            a.status = status_el.get_text(strip=True)

        # Due date from <time> element
        time_el = li.select_one("time[datetime]")
        if time_el:
            a.due_date = time_el.get("datetime","")[:10]  # just the date part

        # Teacher feedback
        feedback_el = li.select_one(".content blockquote p, .content blockquote")
        if feedback_el:
            a.description = feedback_el.get_text(strip=True)[:500]

        if a.title:
            assignments.append(a)

    # ── Merge infoIndex data into assignments ─────────────────────────
    for i, info in enumerate(info_index):
        # infoIndex entries can be dicts OR nested lists — normalise
        if isinstance(info, list):
            info = info[0] if info and isinstance(info[0], dict) else {}
        if not isinstance(info, dict):
            continue
        mark = info.get("displayMark","")
        feedback = info.get("info","")
        name = assess_names[i] if i < len(assess_names) else ""

        # Find matching assignment or create new one
        matched = None
        for a in assignments:
            if name and name in a.title:
                matched = a
                break
            if mark and a.grade == mark:
                matched = a
                break

        if matched:
            if matched.grade is None and mark:
                matched.grade     = mark
                matched.grade_raw = _parse_grade(mark)
            if not matched.description and feedback:
                matched.description = feedback
        elif name:
            a = Assignment(title=name[:150])
            a.grade     = mark
            a.grade_raw = _parse_grade(mark)
            a.description = feedback
            assignments.append(a)

    subj.assignments = assignments

    # ── Overall subject grade = average of graded assignments ─────────
    graded = [a.grade_raw for a in assignments if a.grade_raw is not None]
    if graded:
        subj.grade_raw = round(sum(graded) / len(graded), 1)
        subj.grade     = f"{subj.grade_raw:.1f}%"

    # Also check graphData JS var for individual scores
    m_graph = re.search(r'let\s+graphData\s*=\s*(\[[\d,\s.null]+\]);', html_fragment)
    if m_graph:
        try:
            vals = [v for v in json.loads(m_graph.group(1)) if isinstance(v, (int,float))]
            if vals and not graded:
                subj.grade_raw = round(sum(vals)/len(vals), 1)
                subj.grade     = f"{subj.grade_raw:.1f}%"
        except Exception:
            pass

    log.debug("  %s: grade=%s, assignments=%d", code, subj.grade, len(assignments))
    return subj


# ── Main scraper ──────────────────────────────────────────────────────────────

def scrape_all(session: SBCSession, user_id: str) -> Dict[int, List[Subject]]:
    class_list = _scrape_class_list(session)
    code_to_id = {code: cid for code, _, cid in class_list}

    semester_map = _get_semester_map(session, user_id)
    if not semester_map:
        log.warning("No semesters found")
        return {}

    current_year = datetime.now().year
    relevant    = [str(y) for y in range(current_year - 3, current_year + 1)]
    by_year: Dict[int, List[Subject]] = {}

    for year_str, sems in semester_map.items():
        if year_str not in relevant:
            continue
        year = int(year_str)
        merged: Dict[str, Subject] = {}

        for sem in sems:
            period = sem["period"]
            grade_urls = sem.get("class_grade_urls", {})
            log.info("Scraping %s — %d classes", period, len(grade_urls))

            for class_id, grade_url in grade_urls.items():
                # Find code for this class_id
                code = next((c for c, _, cid in class_list if cid == class_id), class_id)

                # POST to get the grade fragment
                fragment = _post_grade_fragment(session, grade_url)
                if fragment is None:
                    log.warning("No fragment for %s/%s", period, class_id)
                    continue

                _dump(f"debug_fragment_{class_id}_{period}.html", fragment)
                subj = _parse_grade_fragment(fragment, code, year, period)

                key = subj.code or subj.name
                if key not in merged:
                    merged[key] = subj
                else:
                    ex = merged[key]
                    if subj.grade_raw is not None and (
                        ex.grade_raw is None or subj.grade_raw > ex.grade_raw
                    ):
                        ex.grade     = subj.grade
                        ex.grade_raw = subj.grade_raw
                    ex.assignments.extend(subj.assignments)
                    if subj.teacher and not ex.teacher:
                        ex.teacher = subj.teacher

        if merged:
            by_year[year] = list(merged.values())
            log.info("Year %d: %d subjects", year, len(merged))

    return by_year


def fetch_all_data(session: SBCSession) -> AcademicData:
    data = AcademicData()
    try:
        data.profile = scrape_profile(session)
    except Exception as exc:
        log.error("Profile: %s", exc)
        data.profile = UserProfile()

    user_id = data.profile.student_id if data.profile else ""

    try:
        data.subjects_by_year = scrape_all(session, user_id)
    except Exception as exc:
        log.error("Scrape: %s\n%s", exc, traceback.format_exc())
        data.subjects_by_year = {}

    # Fetch groups
    try:
        data.groups = _fetch_groups(session)
    except Exception as exc:
        log.warning("Groups fetch failed: %s", exc)
        data.groups = []

    return data


fetch_all_data_safe = fetch_all_data


def _fetch_groups(session: SBCSession) -> list:
    """Fetch groups the student is in from /groups page."""
    import re as _re
    resp = session.get(f"{BASE_URL}/groups")
    soup = BeautifulSoup(resp.text, "html.parser")
    groups = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not _re.search(r"/(groups|homepage)/[0-9]+", href):
            continue
        name = ""
        for sel in ["h2","h3","h4",".title",".name","strong","span"]:
            el = a.select_one(sel)
            if el:
                name = el.get_text(strip=True)
                break
        if not name:
            name = a.get_text(strip=True)
        name = _re.sub(r"\s+", " ", name).strip()
        if name and len(name) < 100 and name not in seen:
            seen.add(name)
            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            gid = _re.search(r"/([0-9]+)/?$", href)
            groups.append({
                "name": name,
                "url":  full_url,
                "id":   gid.group(1) if gid else "",
            })
    log.info("Groups: %d found", len(groups))
    return groups
