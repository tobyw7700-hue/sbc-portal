"""
Probe to examine the profile page structure.
Run: python3 probe_profile.py
"""
import requests, getpass, re, os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

BASE = "https://mysbc.sbc.vic.edu.au"
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})

def resolve(action, current):
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
        r, url = submit(r.text, url, {"password": password, "username": username})
    elif soup.find("form"):
        r, url = submit(r.text, url)
    else: break

print(f"Logged in: {url}")

# Get user ID from JS
m = re.search(r'"id"\s*:\s*(\d+)', r.text)
user_id = m.group(1) if m else "11953"

# Fetch profile page
for path in [f"/search/user/{user_id}", f"/profile/{user_id}"]:
    resp = s.get(f"{BASE}{path}", timeout=10)
    html = resp.text
    print(f"\n=== {path} ({len(html)} bytes) ===")
    
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","nav","footer"]): tag.decompose()
    
    # Show text
    text = re.sub(r'\n{3,}', '\n\n', soup.get_text("\n", strip=True))
    print(text[:3000])
    
    # Save
    debug_path = os.path.expanduser(f"~/.sbc_portal/debug_profile{user_id}.html")
    with open(debug_path, "w") as f:
        f.write(html)
    print(f"\nSaved to {debug_path}")
    break
