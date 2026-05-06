"""
API probe script — run this directly to find Schoolbox grade endpoints.
Usage: .venv/bin/python3 probe_api.py
"""
import requests
import getpass
import json
import re
from bs4 import BeautifulSoup

BASE = "https://mysbc.sbc.vic.edu.au"

s = requests.Session()
s.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

# ── Login ─────────────────────────────────────────────────────────────
print("=== mySBC API Probe ===\n")
username = input("Username: ").strip()
password = getpass.getpass("Password: ")

r = s.get(f"{BASE}/login", timeout=15)
soup = BeautifulSoup(r.text, "html.parser")
form = soup.find("form")
fields = {}
for inp in form.find_all("input"):
    name = inp.get("name")
    if name:
        fields[name] = inp.get("value", "")

# Resolve form action
action = form.get("action", "").strip()
if not action or action in ("?", "#"):
    action = f"{BASE}/login"
elif action.startswith("/"):
    action = BASE + action

# Fill credentials
for uf in ["username", "email", "user", "login"]:
    if uf in fields:
        fields[uf] = username
        break
else:
    fields["username"] = username

for pf in ["password", "pass", "passwd"]:
    if pf in fields:
        fields[pf] = password
        break
else:
    fields["password"] = password

r2 = s.post(action, data=fields, allow_redirects=True, timeout=20)
print(f"\nLogged in: {r2.url}\n")

if "login" in r2.url:
    print("ERROR: Still on login page — check credentials")
    exit(1)

# ── Probe endpoints ───────────────────────────────────────────────────
print("Probing API endpoints...\n")

endpoints = [
    # Assessment / grade APIs
    "/api/assessment/result/list",
    "/api/assessment/result/list?userId=11953",
    "/api/assessment/list",
    "/api/assessment/list?userId=11953",
    "/api/grade/list",
    "/api/grade/list?userId=11953",
    "/api/task/list",
    "/api/task/list?userId=11953",
    # Learning APIs
    "/api/learning/grades",
    "/api/v1/grades",
    "/api/v1/assessment",
    "/api/user/11953/grades",
    "/api/user/11953/assessments",
    # Schoolbox-specific
    "/api/course/31892/grades",
    "/api/course/31892/assessments",
    "/api/homepage/31892/assessment",
    "/api/assessment/result?courseId=31892",
    "/api/assessment/result?homepageId=31892",
    # JSON format flags
    "/learning/grades/11953?format=json",
    "/learning/grades/11953/2026-1?format=json",
    "/learning/grades/11953/2026-1/31892?format=json",
    # Alternative endpoints
    "/api/report/grades",
    "/api/report/assessment",
    "/api/student/11953/grades",
    "/api/student/11953/assessments",
    "/api/student/11953/tasks",
    # Schoolbox widget endpoints
    "/api/widget/grades",
    "/api/widget/assessment",
    "/learning/assessment/list",
    "/learning/assessment/result/list",
]

json_hits = []
for ep in endpoints:
    try:
        r = s.get(
            f"{BASE}{ep}",
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=6,
        )
        ct = r.headers.get("content-type", "")
        size = len(r.content)
        is_json = "json" in ct or (r.text.strip().startswith(("{", "[")))
        tag = "✓ JSON" if is_json and r.status_code == 200 else \
              "HTML " if "html" in ct else ct[:15]
        print(f"  {r.status_code}  {size:7}b  {tag:10}  {ep}")
        if is_json and r.status_code == 200 and size > 50:
            json_hits.append((ep, r.text))
    except Exception as e:
        print(f"  ERR              {ep}  ({e})")

# ── Print JSON hits ───────────────────────────────────────────────────
if json_hits:
    print("\n\n=== JSON RESPONSES ===")
    for ep, text in json_hits:
        print(f"\n--- {ep} ---")
        try:
            parsed = json.loads(text)
            print(json.dumps(parsed, indent=2)[:800])
        except Exception:
            print(text[:400])
else:
    print("\n\nNo JSON API endpoints found in standard locations.")
    print("Schoolbox may use a non-standard API path.")
    print("\nChecking page source for API calls...")

    # Look for API URLs in the grades page JS
    rg = s.get(f"{BASE}/learning/grades/11953", timeout=15)
    api_urls = re.findall(r'["\'](/api/[^"\']+)["\']', rg.text)
    api_urls += re.findall(r'url\s*:\s*["\']([^"\']+)["\']', rg.text)
    api_urls = sorted(set(api_urls))
    if api_urls:
        print("\nFound these URLs referenced in page JS:")
        for u in api_urls[:30]:
            print(f"  {u}")
    else:
        print("No API URLs found in page source either.")
        print("Grades are likely loaded via the JS bundle (webpack).")
        print("\nSaving grades page HTML for inspection...")
        with open("/tmp/grades_raw.html", "w") as f:
            f.write(rg.text)
        print("Saved to /tmp/grades_raw.html")

print("\nDone.")
