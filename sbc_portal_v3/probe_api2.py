"""
Phase 2 API probe — targets 401 endpoints and extracts API paths from JS bundle.
Usage: .venv/bin/python3 probe_api2.py
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
})

# ── Login ─────────────────────────────────────────────────────────────
print("=== mySBC API Probe Phase 2 ===\n")
username = input("Username: ").strip()
password = getpass.getpass("Password: ")

r = s.get(f"{BASE}/login", timeout=15)
soup = BeautifulSoup(r.text, "html.parser")
form = soup.find("form")
fields = {i["name"]: i.get("value","") for i in form.find_all("input") if i.get("name")}
action = form.get("action","").strip()
if not action or action in ("?","#"):
    action = f"{BASE}/login"
elif action.startswith("/"):
    action = BASE + action
for uf in ["username","email","user"]:
    if uf in fields: fields[uf] = username; break
else: fields["username"] = username
for pf in ["password","pass","passwd"]:
    if pf in fields: fields[pf] = password; break
else: fields["password"] = password

r2 = s.post(action, data=fields, allow_redirects=True, timeout=20)
print(f"Logged in: {r2.url}\n")
if "login" in r2.url:
    print("ERROR: Login failed"); exit(1)

# Extract CSRF token from page
csrf = None
for pattern in [
    r'"csrfToken"\s*:\s*"([^"]+)"',
    r'_token.*?value="([^"]+)"',
    r'csrf.*?content="([^"]+)"',
    r'"csrf"\s*:\s*"([^"]+)"',
]:
    m = re.search(pattern, r2.text)
    if m:
        csrf = m.group(1)
        print(f"Found CSRF token: {csrf[:20]}...")
        break

# Get token from meta tag too
soup2 = BeautifulSoup(r2.text, "html.parser")
meta_csrf = soup2.find("meta", {"name": re.compile("csrf|token", re.I)})
if meta_csrf:
    csrf = meta_csrf.get("content", csrf)
    print(f"Meta CSRF: {csrf[:20] if csrf else 'none'}...")

# ── Phase 1: retry 401s with various auth headers ─────────────────────
print("\n--- Retrying 401 endpoints with auth headers ---")

auth_variants = [
    {},
    {"X-Requested-With": "XMLHttpRequest"},
    {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/learning/grades/11953"},
]
if csrf:
    auth_variants.append({
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRF-Token": csrf,
        "X-Token": csrf,
    })

for ep in [
    "/api/assessment/list",
    "/api/assessment/list?userId=11953",
    "/api/assessment/list?homepageId=31892",
    "/api/assessment/result",
    "/api/assessment/result?userId=11953",
    "/api/assessment/result?homepageId=31892",
    "/api/assessment/result?courseId=31892",
    "/api/assessment/result/list?homepageId=31892",
]:
    for headers in auth_variants:
        try:
            r = s.get(f"{BASE}{ep}",
                      headers={"Accept": "application/json", **headers},
                      timeout=6)
            if r.status_code == 200:
                print(f"  ✓ 200  {len(r.content)}b  {ep}")
                print(f"    headers: {headers}")
                print(f"    response: {r.text[:300]}")
                break
            elif r.status_code != 401:
                print(f"  {r.status_code}  {ep}  (headers={list(headers.keys())})")
        except Exception as e:
            print(f"  ERR {ep}: {e}")

# ── Phase 2: fetch and search JS bundle for API routes ────────────────
print("\n--- Searching JS bundles for API routes ---")

# Get the main bundle URL from the page
rg = s.get(f"{BASE}/learning/grades/11953", timeout=15)
bundle_urls = re.findall(r'src="(/static/js/bundle/[^"]+)"', rg.text)
bundle_urls += re.findall(r'src="(/static/js/[^"]+\.js[^"]*)"', rg.text)
bundle_urls = list(dict.fromkeys(bundle_urls))  # dedupe
print(f"Found {len(bundle_urls)} JS files: {bundle_urls[:5]}")

api_paths = set()
for burl in bundle_urls[:4]:  # check first 4 bundles
    try:
        rb = s.get(f"{BASE}{burl}", timeout=15)
        content = rb.text
        print(f"  Bundle {burl}: {len(content)} chars")
        # Find API-like paths
        found = re.findall(r'["\`](/api/[a-zA-Z0-9/_\-?=&.]+)["\`]', content)
        found += re.findall(r'["\`](\/learning\/[a-zA-Z0-9/_\-?=&.]+)["\`]', content)
        found += re.findall(r'url\s*[=:]\s*["\`]([^"` ]+)["\`]', content)
        for f in found:
            if any(x in f for x in ["grade","assess","result","task","mark","score"]):
                api_paths.add(f)
    except Exception as e:
        print(f"  Error fetching {burl}: {e}")

if api_paths:
    print(f"\nFound {len(api_paths)} grade-related paths in JS bundles:")
    for p in sorted(api_paths):
        print(f"  {p}")
else:
    print("No grade API paths found in bundles")

# ── Phase 3: check what the grades HTML page actually contains ─────────
print("\n--- Examining rendered grades page structure ---")
rg2 = s.get(f"{BASE}/learning/grades/11953/2026-1/31892", timeout=15)
soup3 = BeautifulSoup(rg2.text, "html.parser")

# Look for data attributes, ng-*, data-*, vue bindings
data_attrs = []
for tag in soup3.find_all(True):
    for attr, val in tag.attrs.items():
        if any(x in attr.lower() for x in ["data-","ng-","v-","x-","api","url","endpoint","grade","assess"]):
            if isinstance(val, str) and len(val) > 3:
                data_attrs.append(f"{tag.name}[{attr}]={val[:80]}")

if data_attrs:
    print("Data attributes found:")
    for d in data_attrs[:30]:
        print(f"  {d}")

# Look for inline JSON data
scripts = soup3.find_all("script")
for script in scripts:
    text = script.string or ""
    if any(x in text for x in ["grade","assessment","result","task"]) and len(text) > 50:
        # Extract any JSON-like objects
        json_matches = re.findall(r'\{[^{}]{20,500}\}', text)
        for match in json_matches[:3]:
            if any(x in match.lower() for x in ["grade","assess","result"]):
                print(f"\nInline script JSON: {match[:300]}")

print("\nDone.")
