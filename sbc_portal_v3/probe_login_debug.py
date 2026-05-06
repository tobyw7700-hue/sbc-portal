import requests, getpass
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import urllib3
urllib3.disable_warnings()

BASE = "https://mysbc.sbc.vic.edu.au"

print("Username: ", end="", flush=True)
username = input().strip()
password = getpass.getpass("Password: ")

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})

def resolve(action, url):
    if not action or action in ("?","#"): return url
    if action.startswith("http"): return action
    p = urlparse(url)
    return "%s://%s%s" % (p.scheme, p.netloc, action) if action.startswith("/") else urljoin(url, action)

# Step 1: GET login
r = s.get("%s/login" % BASE, timeout=20, allow_redirects=True)
soup = BeautifulSoup(r.text, "html.parser")
form = soup.find("form")
fields = {i["name"]: i.get("value","") for i in form.find_all("input") if i.get("name")}
fields["username_check"] = username
print("Step 1 POST fields:", list(fields.keys()))
r = s.post(resolve(form.get("action",""), r.url), data=fields, timeout=20, allow_redirects=True)
print("Step 1 response:", r.status_code, r.url[:60])

# Step 2: now fill username + password + AuthState
soup = BeautifulSoup(r.text, "html.parser")
form = soup.find("form")
fields = {i["name"]: i.get("value","") for i in form.find_all("input") if i.get("name")}
fields["username"] = username
fields["password"] = password
print("Step 2 POST fields:", list(fields.keys()))
r = s.post(resolve(form.get("action",""), r.url), data=fields, timeout=20, allow_redirects=True)
print("Step 2 response:", r.status_code, r.url[:60])

# Step 3: submit SAMLResponse
soup = BeautifulSoup(r.text, "html.parser")
if "SAMLResponse" in r.text:
    fields = {i["name"]: i.get("value","") for i in soup.find_all("input") if i.get("name")}
    print("Step 3: submitting SAMLResponse to consume.php")
    r = s.post("%s/saml/consume.php" % BASE, data=fields, timeout=20, allow_redirects=True)
    print("Result:", r.status_code, r.url)
    if BASE in r.url and "/login" not in r.url:
        print("SUCCESS!")
    else:
        print(soup.get_text()[:300])
else:
    for sel in [".error",".alert","#error"]:
        e = soup.select_one(sel)
        if e: print("Error:", e.get_text(strip=True)[:200])
    print("No SAMLResponse found")
    print("Page text:", soup.get_text()[:400])
