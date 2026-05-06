"""
Probe real mySBC sidebar pages — saves full HTML to page_probes/
Run: python3 probe_pages.py
"""
import requests, getpass, os
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

BASE    = "https://mysbc.sbc.vic.edu.au"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page_probes")
os.makedirs(OUT_DIR, exist_ok=True)

print("Username: ", end="", flush=True)
username = input().strip()
password = getpass.getpass("Password: ")

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})

# Login
r = s.get(f"{BASE}/login", timeout=20, allow_redirects=True)
soup = BeautifulSoup(r.text, "html.parser")
form = soup.find("form")
fields = {i["name"]: i.get("value","") for i in form.find_all("input") if i.get("name")}
fields["username_check"] = username
r = s.post(r.url, data=fields, timeout=20, allow_redirects=True)
soup = BeautifulSoup(r.text, "html.parser")
form = soup.find("form")
fields = {i["name"]: i.get("value","") for i in form.find_all("input") if i.get("name")}
fields["username"] = username
fields["password"] = password
r = s.post(r.url, data=fields, timeout=20, allow_redirects=True)
soup = BeautifulSoup(r.text, "html.parser")
fields = {i["name"]: i.get("value","") for i in soup.find_all("input") if i.get("name")}
r = s.post(f"{BASE}/saml/consume.php", data=fields, timeout=20, allow_redirects=True)
print(f"Logged in: {r.url}\n")

pages = {
    "canteen":         f"{BASE}/homepage/11951",
    "weather":         "https://www.weatherlink.com/embeddablePage/show/9b5cf09d97c94493b7aab5fa60b2a2e0/summary",
    "students":        f"{BASE}/homepage/6966",
    "groups":          f"{BASE}/groups",
    "college_website": "https://www.sbc.vic.edu.au/",
    "student_service": f"{BASE}/homepage/25692",
}

for name, url in pages.items():
    try:
        r2 = s.get(url, timeout=15, allow_redirects=True)
        out_path = f"{OUT_DIR}/{name}.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(r2.text)
        print(f"[{name}] {r2.status_code} {r2.url}")
        print(f"  → {out_path} ({len(r2.content):,} bytes)")
        
        # Also check for API/JSON endpoints on homepage nodes
        if "homepage" in url:
            node_id = url.split("/")[-1]
            # Try news feed
            news_url = f"{BASE}/news/lists/folder/{node_id}?c=0&l=20&hp=1&ref=homepage&cid={node_id}&readonly=1"
            r3 = s.get(news_url, timeout=10)
            try:
                data = r3.json()
                if isinstance(data, list):
                    print(f"  News feed: {len(data)} posts")
                    import json
                    with open(f"{OUT_DIR}/{name}_news.json", "w") as f:
                        json.dump(data, f, indent=2)
            except Exception:
                pass
    except Exception as e:
        print(f"[{name}] ERROR: {e}")

print(f"\nSaved to: {OUT_DIR}/")
print("Open .html files in Safari to inspect each page.")
