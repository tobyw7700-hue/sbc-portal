"""
Grade HTML inspector — handles full SAML flow.
Usage: .venv/bin/python3 probe_html.py
"""
import requests
import getpass
import re
from bs4 import BeautifulSoup

BASE      = "https://mysbc.sbc.vic.edu.au"
SAML_BASE = "https://sbc-login.cloudworkengine.net"

s = requests.Session()
s.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
})

def submit_form(session, html, current_url, extra_fields=None):
    """Find and submit the first form on a page, merging extra_fields."""
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        return None, current_url
    fields = {i["name"]: i.get("value","")
              for i in form.find_all("input") if i.get("name")}
    if extra_fields:
        fields.update(extra_fields)
    action = form.get("action","").strip()
    if not action or action in ("?","#"):
        action = current_url
    elif action.startswith("/"):
        # Determine base from current_url
        from urllib.parse import urlparse
        parsed = urlparse(current_url)
        action = f"{parsed.scheme}://{parsed.netloc}{action}"
    elif not action.startswith("http"):
        from urllib.parse import urljoin
        action = urljoin(current_url, action)
    method = form.get("method","post").lower()
    if method == "post":
        r = session.post(action, data=fields, allow_redirects=True, timeout=20)
    else:
        r = session.get(action, params=fields, allow_redirects=True, timeout=20)
    return r, r.url

print("=== Grade HTML Inspector ===\n")
username = input("Username: ").strip()
password = getpass.getpass("Password: ")

# ── Step 1: GET login page ────────────────────────────────────────────
print("Step 1: GET login page")
r = s.get(f"{BASE}/login", timeout=15)
print(f"  → {r.url}")

# ── Step 2: Submit username to mySBC ─────────────────────────────────
print("Step 2: Submit username")
r, url = submit_form(s, r.text, r.url, {"username": username})
print(f"  → {url}")

# ── Step 3: Follow any intermediate pages until we hit password ───────
max_steps = 8
for step in range(max_steps):
    if not r:
        break
    soup = BeautifulSoup(r.text, "html.parser")
    page_text = r.text.lower()

    # Check if we're on the password page
    has_password = bool(soup.find("input", {"type": "password"}))
    has_username = bool(soup.find("input", {"name": re.compile("username|user", re.I)}))
    is_welcome   = "welcome" in url or "frontpage" in url
    is_mysbc     = "mysbc.sbc.vic.edu.au" in url and "login" not in url

    print(f"Step {step+3}: {url[:80]}")
    print(f"  has_password={has_password}, is_welcome={is_welcome}, is_mysbc={is_mysbc}")

    if is_mysbc:
        print("  → Reached mySBC!")
        break

    if has_password:
        # Submit credentials
        print("  → Submitting password")
        extra = {}
        if has_username:
            extra["username"] = username
        extra["password"] = password
        r, url = submit_form(s, r.text, url, extra)

    elif is_welcome or (not has_password and not is_mysbc):
        # Consent/welcome page — just submit the form as-is
        form = soup.find("form")
        if form:
            print("  → Submitting welcome/consent form")
            r, url = submit_form(s, r.text, url)
        else:
            # No form — try following any redirect links
            meta_refresh = soup.find("meta", {"http-equiv": re.compile("refresh", re.I)})
            if meta_refresh:
                content = meta_refresh.get("content","")
                m = re.search(r"url=(.+)", content, re.I)
                if m:
                    redirect_url = m.group(1).strip("'\" ")
                    if not redirect_url.startswith("http"):
                        from urllib.parse import urljoin
                        redirect_url = urljoin(url, redirect_url)
                    print(f"  → Meta refresh to {redirect_url}")
                    r = s.get(redirect_url, timeout=15)
                    url = r.url
            else:
                print("  → No form, no redirect — stopping")
                break
    else:
        print("  → Unknown state, stopping")
        break

# ── Verify ────────────────────────────────────────────────────────────
if "mysbc.sbc.vic.edu.au" not in url or ("login" in url.split("mysbc.sbc.vic.edu.au")[-1]):
    print(f"\nERROR: Could not reach mySBC. Last URL: {url}")
    print("Page content preview:")
    soup = BeautifulSoup(r.text, "html.parser")
    print(soup.get_text()[:500])
    exit(1)

print(f"\n✓ Logged in to mySBC at {url}\n")

# ── Fetch grade page and dump content ────────────────────────────────
for path, label in [
    ("/learning/grades/11953/2026-1/31892", "Math 2026 Sem1"),
    ("/learning/grades/11953/2026-1",       "All classes 2026 Sem1"),
]:
    print(f"\n{'='*60}")
    print(f"{label}  ({path})")
    print('='*60)

    rg = s.get(f"{BASE}{path}", timeout=15)
    soup = BeautifulSoup(rg.text, "html.parser")

    # Strip noise
    for tag in soup(["script","style","nav","header","footer","aside"]):
        tag.decompose()

    # Main content
    main = (soup.find("main") or
            soup.find(id=re.compile(r"content|main|grade", re.I)) or
            soup.find(class_=re.compile(r"content|main|grade|inner", re.I)) or
            soup.find("body") or soup)

    text = main.get_text("\n", strip=True)
    text = re.sub(r'\n{3,}', '\n\n', text)
    print("\n--- PAGE TEXT ---")
    print(text[:3000])

    print("\n--- TABLES ---")
    for i, table in enumerate(soup.find_all("table")):
        rows = table.find_all("tr")
        if not rows:
            continue
        print(f"\nTable {i+1} ({len(rows)} rows):")
        for row in rows[:10]:
            cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
            if any(c for c in cells):
                print("  |", " | ".join(cells))

    print("\n--- GRADE/ASSESS ELEMENTS ---")
    for el in soup.find_all(True):
        cls = " ".join(el.get("class",[]))
        if re.search(r"grade|assess|result|mark|score|task", cls, re.I):
            t = el.get_text(" ", strip=True)
            if 2 < len(t) < 200:
                print(f"  <{el.name} class='{cls[:50]}'> {t[:120]}")

print("\nDone.")
