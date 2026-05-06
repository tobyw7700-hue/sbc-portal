"""
Fetches and saves timetable + calendar HTML for parsing.
Usage: .venv/bin/python3 probe_timetable.py
"""
import requests, getpass, re, os, json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

BASE = "https://mysbc.sbc.vic.edu.au"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
})

def resolve(action, current):
    action = (action or "").strip()
    if not action or action in ("?","#"): return current
    if action.startswith("http"): return action
    p = urlparse(current)
    return f"{p.scheme}://{p.netloc}{action}" if action.startswith("/") else urljoin(current, action)

def submit(html, url, extra=None):
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form: return None, url
    fields = {i["name"]: i.get("value","") for i in form.find_all("input") if i.get("name")}
    if extra: fields.update(extra)
    r = s.post(resolve(form.get("action",""), url), data=fields, allow_redirects=True, timeout=20)
    return r, r.url

print("Username: ", end="", flush=True)
username = input().strip()
password = getpass.getpass("Password: ")

r = s.get(f"{BASE}/login", timeout=15)
r, url = submit(r.text, r.url, {"username": username})
for _ in range(6):
    if "mysbc.sbc.vic.edu.au" in url and "login" not in url: break
    soup = BeautifulSoup(r.text, "html.parser")
    if soup.find("input", {"type":"password"}):
        extra = {"password": password}
        if soup.find("input", {"name": re.compile("username|user",re.I)}):
            extra["username"] = username
        r, url = submit(r.text, url, extra)
    elif soup.find("form"):
        r, url = submit(r.text, url)
    else: break

print(f"Logged in: {url}")
if "mysbc.sbc.vic.edu.au" not in url or "login" in url.split("mysbc.sbc.vic.edu.au")[-1]:
    print("Login failed"); exit(1)

DEBUG_DIR = os.path.expanduser("~/.sbc_portal")

for path, name in [("/timetable", "timetable"), ("/calendar/week", "calendar")]:
    print(f"\nFetching {path}...")
    r = s.get(f"{BASE}{path}", timeout=15)
    html = r.text
    debug_path = os.path.join(DEBUG_DIR, f"debug_{name}.html")
    with open(debug_path, "w") as f:
        f.write(html)
    print(f"Saved {len(html)} bytes to {debug_path}")

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","nav","header","footer","aside"]): tag.decompose()
    text = re.sub(r'\n{3,}', '\n\n', soup.get_text("\n", strip=True))
    print(f"\n--- {name.upper()} PAGE TEXT (first 2000 chars) ---")
    print(text[:2000])
    print("\n--- TABLES ---")
    for i, table in enumerate(BeautifulSoup(r.text,"html.parser").find_all("table")[:3]):
        rows = table.find_all("tr")
        print(f"\nTable {i+1} ({len(rows)} rows):")
        for row in rows[:8]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td","th"])]
            if any(cells): print("  |", " | ".join(cells[:8]))

print("\nDone. Paste output into chat.")
