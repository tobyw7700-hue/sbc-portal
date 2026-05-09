"""
SBC Authentication — SAML login with cache fallback.
"""
import os, re, json, logging
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger("sbc.auth")

BASE_URL    = "https://mysbc.sbc.vic.edu.au"
PROFILE_URL = BASE_URL + "/search/user/"
CLASSES_URL = BASE_URL + "/learning/classes"
CACHE_DIR = os.path.expanduser("~/.sbc_portal")


class AuthError(Exception):
    pass

class NetworkError(Exception):
    pass


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


class SBCSession:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        })
        self.logged_in     = False
        self.username      = ""
        self.on_school_wifi = False

    def login(self, username: str, password: str) -> bool:
        log.info("Logging in as: %s", username)
        self.username = username

        # Attempt 1: strict SSL
        try:
            return self._do_login(username, password, verify=True)
        except requests.exceptions.SSLError:
            log.warning("SSL error — retrying without verification (school WiFi)")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Cannot reach mySBC — check your internet connection.") from e
        except requests.exceptions.Timeout:
            raise NetworkError("Connection timed out.")
        except AuthError:
            raise

        # Attempt 2: no SSL verify (school WiFi / ZScaler)
        self.on_school_wifi = True
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        })
        try:
            return self._do_login(username, password, verify=False)
        except Exception as e:
            raise NetworkError(f"Login failed: {e}") from e

    def _do_login(self, username: str, password: str, verify: bool) -> bool:
        """
        Three-step SAML login for cloudworkengine:
          Step 1: POST username_check=<user> → server returns form with username+password+AuthState
          Step 2: POST username=<user> + password=<pw> + AuthState=<token> → SAMLResponse
          Step 3: POST SAMLResponse to /saml/consume.php → logged in
        """
        def post_url(form, current_url):
            action = form.get("action", "")
            if not action or action in ("?", "#"): return current_url
            if action.startswith("http"): return action
            p = urlparse(current_url)
            return ("%s://%s%s" % (p.scheme, p.netloc, action)
                    if action.startswith("/") else urljoin(current_url, action))

        def get_fields(soup):
            return {i["name"]: i.get("value", "")
                    for i in soup.find_all("input") if i.get("name")}

        # Initial GET
        r   = self.session.get("%s/login" % BASE_URL, verify=verify,
                               timeout=20, allow_redirects=True)
        url = r.url
        log.debug("Login start: %s", url)

        # Step 1: submit username_check only
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form")
        if not form:
            raise AuthError("No login form found.")
        fields = get_fields(soup)
        fields["username_check"] = username
        purl = post_url(form, url)
        log.debug("Step 1 POST → %s fields=%s", purl[:60], list(fields.keys()))
        r   = self.session.post(purl, data=fields, verify=verify,
                                timeout=20, allow_redirects=True)
        url = r.url
        log.debug("Step 1 → %d %s", r.status_code, url[:60])

        # Step 2: now we get username + password + AuthState form
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form")
        if not form:
            raise AuthError("No password form after username step.")
        fields = get_fields(soup)
        fields["username"] = username
        fields["password"] = password
        purl = post_url(form, url)
        log.debug("Step 2 POST → %s fields=%s", purl[:60], list(fields.keys()))
        r   = self.session.post(purl, data=fields, verify=verify,
                                timeout=20, allow_redirects=True)
        url = r.url
        log.debug("Step 2 → %d %s", r.status_code, url[:60])

        # Check for auth error
        soup = BeautifulSoup(r.text, "html.parser")
        for sel in [".error", ".alert", "#error"]:
            err = soup.select_one(sel)
            if err and err.get_text(strip=True):
                raise AuthError("Login failed: %s" % err.get_text(strip=True)[:200])

        # Step 3: submit SAMLResponse
        if "SAMLResponse" not in r.text:
            raise AuthError("No SAMLResponse received — login may have failed.")
        fields = get_fields(soup)
        log.debug("Step 3 POST SAMLResponse → /saml/consume.php")
        r   = self.session.post("%s/saml/consume.php" % BASE_URL, data=fields,
                                verify=verify, timeout=20, allow_redirects=True)
        url = r.url
        log.debug("Step 3 → %d %s", r.status_code, url[:60])

        if BASE_URL in url and "/login" not in url and "/saml" not in url:
            log.info("Login successful: %s", url)
            self.logged_in = True
            return True

        raise AuthError("Login failed — could not complete SAML handshake.")

    def get(self, url: str, **kwargs) -> requests.Response:
        if not self.logged_in:
            raise AuthError("Not logged in.")
        try:
            log.debug("GET %s", url)
            timeout = kwargs.pop("timeout", 20)
            verify  = not self.on_school_wifi
            r = self.session.get(url, timeout=timeout, verify=verify, **kwargs)
            r.raise_for_status()
            log.debug("  → %d (%d bytes)", r.status_code, len(r.content))
            return r
        except requests.exceptions.SSLError as e:
            raise NetworkError(f"SSL error: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Request failed: {e}") from e
        except requests.exceptions.Timeout:
            raise NetworkError(f"Request timed out: {url}")
        except requests.exceptions.HTTPError as e:
            raise NetworkError(f"HTTP {e.response.status_code}: {url}") from e

    def logout(self):
        try:
            self.session.get(f"{BASE_URL}/logout", allow_redirects=True, timeout=10)
        except Exception:
            pass
        self.logged_in = False


# ── Data cache ────────────────────────────────────────────────────────────────

def save_data_cache(data, username: str):
    _ensure_cache_dir()
    try:
        def to_json(obj):
            if hasattr(obj, '__dict__'):
                return {k: to_json(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, list):
                return [to_json(i) for i in obj]
            if isinstance(obj, dict):
                return {str(k): to_json(v) for k, v in obj.items()}
            return obj

        path = os.path.join(CACHE_DIR, f"cache_{username}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"username": username,
                       "saved_at": datetime.now().isoformat(),
                       "data": to_json(data)}, f, indent=2, default=str)
        # Also save groups separately (list of dicts, easy)
        groups_path = os.path.join(CACHE_DIR, f"groups_{username}.json")
        if hasattr(data, 'groups') and data.groups:
            with open(groups_path, "w", encoding="utf-8") as f:
                json.dump(data.groups, f, indent=2)

        # Save calendar events
        cal_path = os.path.join(CACHE_DIR, f"calendar_{username}.json")
        if hasattr(data, 'calendar_events') and data.calendar_events:
            with open(cal_path, "w", encoding="utf-8") as f:
                json.dump(data.calendar_events, f, indent=2, default=str)

        log.info("Data cached for %s", username)
        return True
    except Exception as e:
        log.error("Cache save failed: %s", e)
        return False


def load_data_cache(username: str):
    from data.models import AcademicData, UserProfile, Subject, Assignment
    path = os.path.join(CACHE_DIR, f"cache_{username}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            cache = json.load(f)
        saved_at = cache.get("saved_at", "unknown")
        raw      = cache.get("data", {})
        data     = AcademicData()

        prof_raw = raw.get("profile", {})
        if prof_raw:
            p = UserProfile()
            for k, v in prof_raw.items():
                if hasattr(p, k): setattr(p, k, v)
            data.profile = p

        for yr_str, subj_list in raw.get("subjects_by_year", {}).items():
            yr = int(yr_str)
            subjects = []
            for sd in subj_list:
                s = Subject(name=sd.get("name",""), code=sd.get("code",""))
                s.grade     = sd.get("grade")
                s.grade_raw = sd.get("grade_raw")
                s.teacher   = sd.get("teacher","")
                s.year      = sd.get("year", yr)
                s.period    = sd.get("period","")
                for ad in sd.get("assignments", []):
                    a = Assignment(title=ad.get("title",""))
                    a.grade      = ad.get("grade")
                    a.grade_raw  = ad.get("grade_raw")
                    a.status     = ad.get("status","")
                    a.due_date   = ad.get("due_date","")
                    a.description = ad.get("description","")
                    s.assignments.append(a)
                subjects.append(s)
            data.subjects_by_year[yr] = subjects

        # Load groups
        groups_path = os.path.join(CACHE_DIR, f"groups_{username}.json")
        if os.path.exists(groups_path):
            try:
                with open(groups_path) as f:
                    data.groups = json.load(f)
            except Exception:
                pass

        # Load calendar events
        cal_path = os.path.join(CACHE_DIR, f"calendar_{username}.json")
        if os.path.exists(cal_path):
            try:
                with open(cal_path) as f:
                    data.calendar_events = json.load(f)
            except Exception:
                pass

        log.info("Loaded cache for %s (saved %s)", username, saved_at)
        return data, saved_at
    except Exception as e:
        log.error("Cache load failed: %s", e)
        return None
