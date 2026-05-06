"""
One-time probe to discover class homepage CIDs for English, Italian, Religion.
Run: python3 probe_cids.py
"""
import requests, getpass, re, json, os
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

# Discover CIDs for unknown classes
DISCOVER = {
    "31827": "09ENGL10 (English)",
    "31885": "09ITAL5 (Italian)",
    "31914": "09RELS10 (Religion)",
}

found = {}
for class_id, name in DISCOVER.items():
    print(f"\nChecking {name} (class_id={class_id})...")
    try:
        resp = s.get(f"{BASE}/homepage/{class_id}", timeout=10, allow_redirects=True)
        html = resp.text
        
        # Look for cid in news feed URL
        m = re.search(r'/news/lists/folder/\d+\?[^"\'<>]*cid=(\d+)', html)
        if m:
            cid = m.group(1)
            found[class_id] = cid
            print(f"  ✅ Found cid={cid}")
            print(f"  URL: {BASE}/news/lists/folder/{class_id}?c=0&l=50&hp=1&ref=homepage&cid={cid}&readonly=1")
        else:
            # Try other patterns
            for pat in [r'"cid"\s*:\s*(\d+)', r'cid=(\d+)', r'"id"\s*:\s*(\d{5,6})']:
                m2 = re.search(pat, html)
                if m2 and m2.group(1) != class_id:
                    cid = m2.group(1)
                    found[class_id] = cid
                    print(f"  ✅ Found cid={cid} (pattern: {pat})")
                    break
            else:
                print(f"  ❌ Could not find cid automatically")
                # Show snippet for manual inspection
                idx = html.find("news/lists/folder")
                if idx > 0:
                    print(f"  Snippet: ...{html[idx:idx+150]}...")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n=== RESULTS ===")
cache_file = os.path.expanduser("~/.sbc_portal/cids.json")
existing = {}
if os.path.exists(cache_file):
    with open(cache_file) as f:
        existing = json.load(f)
existing.update(found)
os.makedirs(os.path.dirname(cache_file), exist_ok=True)
with open(cache_file, "w") as f:
    json.dump(existing, f, indent=2)
print(f"Saved {len(found)} new CIDs to {cache_file}")
for k, v in found.items():
    print(f"  {k}: {v}")
