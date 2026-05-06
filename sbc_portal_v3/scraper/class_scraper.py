"""
Class homepage scraper.
API: GET /news/lists/folder/{class_id}?c=0&l=50&hp=1&ref=homepage&cid={cid}&readonly=1

CID discovery strategy (at launch, in background):
  1. Check CLASS_HOMEPAGE_IDS for known cid
  2. Fetch /homepage/{class_id} and scan HTML for the news feed URL pattern
  3. Try /news/lists/folder/{class_id}?c=0&l=5&hp=1 without cid (some endpoints work)
  4. Cache discovered cids to ~/.sbc_portal/cids.json for future runs
"""
import re, json, os, logging
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

log = logging.getLogger("sbc.class")
BASE_URL   = "https://mysbc.sbc.vic.edu.au"
CACHE_FILE = os.path.expanduser("~/.sbc_portal/cids.json")

# Confirmed CIDs from network inspector
CLASS_HOMEPAGE_IDS: Dict[str, str] = {
    "31805": "283904",  # 09BUSMAN01 Business Management
    "31827": "",        # 09ENGL10   English        — to be discovered
    "31852": "284233",  # 09HEPE10   Health & PE
    "31873": "284380",  # 09HUMS10   Humanities
    "31885": "",        # 09ITAL5    Italian        — to be discovered
    "31892": "294720",  # 09MATH10   Mathematics
    "31914": "",        # 09RELS10   Religion       — to be discovered
    "31924": "284737",  # 09SCIE10   Science
    "31926": "284751",  # 09VISCOM02 Visual Communication
}


def _load_cached_cids():
    """Load any previously discovered CIDs from disk, filtering out bad values."""
    INVALID_CIDS = {"11953", "41631"}  # user IDs that got falsely cached
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            for class_id, cid in cached.items():
                if cid and cid not in INVALID_CIDS and not CLASS_HOMEPAGE_IDS.get(class_id):
                    CLASS_HOMEPAGE_IDS[class_id] = cid
    except Exception:
        pass


def _save_cids():
    """Persist discovered CIDs to disk, excluding known-bad values."""
    INVALID = {"11953", "41631", ""}
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        clean = {k: v for k, v in CLASS_HOMEPAGE_IDS.items() if v not in INVALID}
        with open(CACHE_FILE, "w") as f:
            json.dump(clean, f, indent=2)
    except Exception:
        pass


def _clean_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["p","br","h1","h2","h3","li"]):
        tag.insert_before("\n")
    text = soup.get_text()
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _parse_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        # Compatible with Python 3.9 (fromisoformat is limited in 3.9)
        clean = date_str.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean)
        except ValueError:
            # Fallback: parse manually for formats like 2026-05-04T12:53:00+10:00
            import re as _re
            m = _re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", clean)
            if m:
                dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                              int(m.group(4)), int(m.group(5)))
            else:
                return date_str[:10]
        return dt.strftime("%-d %B %Y")
    except Exception:
        return date_str[:10]


def _discover_cid(session, class_id: str) -> Optional[str]:
    """
    Try multiple strategies to find the cid for a class.
    Strategy 1: Fetch /homepage/{class_id}, scan for news feed URL with cid= param
    Strategy 2: Try the news endpoint without cid (works on some Schoolbox versions)
    Strategy 3: Scan page JS for homepageId or pageId variable
    """
    strategies = [
        f"{BASE_URL}/homepage/{class_id}",
    ]

    for url in strategies:
        try:
            resp = session.get(url, allow_redirects=True)
            html = resp.text

            # Strategy 1: news feed URL with cid param
            m = re.search(r"cid=([0-9]+)", html)
            if m and m.group(1) not in {"11953","41631"}:
                log.info("Discovered cid=%s for class %s", m.group(1), class_id)
                return m.group(1)

            # Strategy 2: JS variables containing page/homepage ID
            for pattern in [
                r'"homepageId"\s*:\s*([0-9]+)',
                r'"homepage_id"\s*:\s*([0-9]+)',
                r'"pageId"\s*:\s*([0-9]+)',
                r'[?&]cid=([0-9]{5,7})',
            ]:
                for m2 in re.finditer(pattern, html):
                    c = m2.group(1)
                    if c != class_id and c not in {"11953","41631"} and 4 < len(c) <= 7:
                        log.info("Discovered cid=%s for class %s (js)", c, class_id)
                        return c

        except Exception as e:
            log.warning("CID discovery failed for %s at %s: %s", class_id, url, e)

    # Strategy 3: try without cid at all — some Schoolbox configs don't require it
    try:
        url = f"{BASE_URL}/news/lists/folder/{class_id}?c=0&l=5&hp=1&ref=homepage&readonly=1"
        resp = session.get(url)
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            log.info("Class %s works without cid!", class_id)
            return "NOCID"  # Special marker meaning no cid needed
    except Exception:
        pass

    log.warning("Could not discover cid for class %s", class_id)
    return None


def discover_all_cids(session, class_ids: List[str]) -> Dict[str, str]:
    """
    Discover CIDs for all classes that don't already have one.
    Called at app startup in a background thread.
    Returns updated {class_id: cid} mapping.
    """
    _load_cached_cids()
    changed = False

    for class_id in class_ids:
        if not class_id or not str(class_id).isdigit():
            continue
        existing = CLASS_HOMEPAGE_IDS.get(str(class_id), "")
        if existing:
            continue
        cid = _discover_cid(session, str(class_id))
        if cid:
            CLASS_HOMEPAGE_IDS[str(class_id)] = cid
            changed = True
            log.info("Saved cid=%s for class_id=%s", cid, class_id)

    if changed:
        _save_cids()

    return dict(CLASS_HOMEPAGE_IDS)


def fetch_class_posts(session, class_id: str,
                      cid: str = None, limit: int = 30) -> List[dict]:
    """Fetch lesson posts for a class via the news feed API."""
    # Try cached/known cid first
    if not cid:
        cid = CLASS_HOMEPAGE_IDS.get(class_id, "")

    # If still unknown, try to discover it now (blocking but only once)
    if not cid:
        cid = _discover_cid(session, class_id) or ""
        if cid:
            CLASS_HOMEPAGE_IDS[class_id] = cid
            _save_cids()

    # Build URL
    if cid and cid != "NOCID":
        url = (f"{BASE_URL}/news/lists/folder/{class_id}"
               f"?c=0&l={limit}&hp=1&ref=homepage&cid={cid}&readonly=1")
    else:
        url = (f"{BASE_URL}/news/lists/folder/{class_id}"
               f"?c=0&l={limit}&hp=1&ref=homepage&readonly=1")

    try:
        resp = session.get(url)
        posts_raw = resp.json()
        if not isinstance(posts_raw, list):
            log.warning("Unexpected response for class %s: %s", class_id, type(posts_raw))
            return []

        results = []
        for p in posts_raw:
            results.append({
                "id":        p.get("id"),
                "title":     p.get("title","").strip(),
                "body_html": p.get("body",""),
                "body_text": _clean_html(p.get("body","")),
                "author":    p.get("author",{}).get("fullName",""),
                "date":      _parse_date(p.get("publishAt","")),
                "status":    p.get("status",""),
                "sticky":    p.get("sticky", False),
            })

        log.info("Class %s: %d posts", class_id, len(results))
        return results

    except Exception as e:
        log.error("Failed to fetch posts for %s: %s", class_id, e)
        return []
