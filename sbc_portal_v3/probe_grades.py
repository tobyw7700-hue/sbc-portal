"""
Dumps the grade overview and one class grade page in full.
Usage: .venv/bin/python3 probe_grades.py
"""
import requests, getpass, re, os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

BASE = "https://mysbc.sbc.vic.edu.au"

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

def resolve(action, current):
    action = (action or "").strip()
    if not action or action in ("?","#"): return current
    if action.startswith("http"): return action
    p = urlparse(current)
    if action.startswith("/"): return f"{p.scheme}://{p.netloc}{action}"
    return urljoin(current, action)

def submit(html, url, extra=None):
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form: return None, url
    fields = {i["name"]: i.get("value","") for i in form.find_all("input") if i.get("name")}
    if extra: fields.update(extra)
    action = resolve(form.get("action",""), url)
    r = s.post(action, data=fields, allow_redirects=True, timeout=20)
    return r, r.url

print("Username: ", end="", flush=True)
username = input().strip()
password = getpass.getpass("Password: ")

# Login
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
print(f"Logged in: {url}\n")

# ── Fetch the overview page ───────────────────────────────────────────
print("Fetching /learning/grades/11953 ...")
rg = s.get(f"{BASE}/learning/grades/11953", timeout=15)
soup = BeautifulSoup(rg.text, "html.parser")

# Save full HTML
with open(os.path.expanduser("~/.sbc_portal/grades_overview.html"), "w") as f:
    f.write(rg.text)
print("Saved to ~/.sbc_portal/grades_overview.html\n")

# Print all flex-grade links
print("=== GRADE LINKS ON OVERVIEW PAGE ===")
for a in soup.find_all("a", class_=re.compile("flex-grade|grade.*row|row.*grade", re.I)):
    href = a.get("href","")
    text = a.get_text(" ", strip=True)
    print(f"  href={href}")
    print(f"  text={text[:120]}")
    print()

# Print ALL anchor tags that go to a grades URL
print("=== ALL HREFS CONTAINING 'grades' ===")
for a in soup.find_all("a", href=re.compile("grades")):
    print(f"  {a.get('href','')}  →  {a.get_text(strip=True)[:60]}")

# ── Now fetch the first class grade page we find ──────────────────────
grade_links = [a["href"] for a in soup.find_all("a", href=re.compile(r"/learning/grades/\d+/\d{4}"))
               if a.get("href")]
if not grade_links:
    # Try any link with a class ID
    grade_links = [a["href"] for a in soup.find_all("a", href=re.compile(r"/\d{4}-\d/\d+$"))
                   if a.get("href")]

if grade_links:
    first = grade_links[0]
    url2 = first if first.startswith("http") else BASE + first
    print(f"\n=== FETCHING FIRST CLASS PAGE: {url2} ===")
    rc = s.get(url2, timeout=15)
    soup2 = BeautifulSoup(rc.text, "html.parser")
    with open(os.path.expanduser("~/.sbc_portal/grades_class.html"), "w") as f:
        f.write(rc.text)
    print("Saved to ~/.sbc_portal/grades_class.html\n")

    # Strip noise
    for tag in soup2(["script","style","nav","header","footer","aside"]): tag.decompose()
    text = soup2.get_text("\n", strip=True)
    text = re.sub(r'\n{3,}', '\n\n', text)
    print("--- PAGE TEXT ---")
    print(text[:4000])

    print("\n--- ALL TABLES ---")
    for i, table in enumerate(soup2.find_all("table")):
        rows = table.find_all("tr")
        if not rows: continue
        print(f"\nTable {i+1} ({len(rows)} rows):")
        for row in rows[:15]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td","th"])]
            if any(cells): print("  | " + " | ".join(cells))

    print("\n--- ELEMENTS WITH CLASS CONTAINING grade/assess/result/score/mark ---")
    for el in soup2.find_all(True):
        cls = " ".join(el.get("class",[]))
        if re.search(r"grade|assess|result|score|mark|task|weight", cls, re.I):
            t = el.get_text(" ", strip=True)
            if 1 < len(t) < 300:
                print(f"  <{el.name} .{cls[:60]}> {t[:150]}")
else:
    print("\nNo class grade links found on overview page.")
    print("Printing all links on overview page:")
    for a in soup.find_all("a", href=True)[:40]:
        print(f"  {a['href']}  {a.get_text(strip=True)[:50]}")

print("\nDone.")
