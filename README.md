# SBC Academic Portal
A desktop application for St Bernard's College (Essendon) students to view grades, timetables, class homepages, assignments, and more — all pulled live from mySBC.

---

## 🐛 Found a Bug? Have a suggestion?

> ### [👉 Click here to report an issue on GitHub](https://github.com/tobyw7700-hue/sbc-portal/issues/new)
>
> If something isn't working, a subject name is wrong, or you have an idea for a new feature — open an issue on GitHub. It takes 2 minutes and helps improve the app for everyone at SBC.
>
> **You'll need a free GitHub account.** Sign up at [github.com](https://github.com/join) if you don't have one.

---

## Requirements

- **macOS** (tested on macOS 13+)
- **Python 3.9 or higher** — download from [python.org](https://www.python.org/downloads/) if not installed
- An active mySBC account (your school login)

---

## Installation

### Step 1 — Check Python

Open **Terminal** (press `Cmd + Space`, type `Terminal`, hit Enter) and run:

```bash
python3 --version
```

You need **3.9 or higher**. If not installed, download the macOS installer from [python.org](https://www.python.org/downloads/) and run it.

---

### Step 2 — Extract the zip

- Find `sbc_portal_v3.zip` in your Downloads folder
- Double-click it — Mac will extract it automatically
- Move the `sbc_portal_v3` folder somewhere permanent, e.g. **Documents**

> ⚠️ **Do not run the app from the Downloads folder** — macOS Gatekeeper blocks scripts there. Move it to Documents or your home directory.

---

### Step 3 — Open Terminal in the folder

Right-click the `sbc_portal_v3` folder → **New Terminal at Folder**

Or manually navigate:

```bash
cd ~/Documents/sbc_portal_v3
```

---

### Step 4 — Create a virtual environment

```bash
python3 -m venv .venv
```

---

### Step 5 — Install dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

If you get a permissions error, try:

```bash
.venv/bin/pip install --user -r requirements.txt
```

> **Do not use** `pip3 install -r requirements.txt --break-system-packages` — this can interfere with your system Python. Always use the virtual environment above.

#### Manual install (if requirements.txt doesn't work)

If `requirements.txt` causes issues, you can install each library individually:

```bash
.venv/bin/pip install requests
.venv/bin/pip install beautifulsoup4
.venv/bin/pip install lxml
.venv/bin/pip install Pillow
.venv/bin/pip install cryptography
.venv/bin/pip install urllib3
```

What each library is for:

| Library | Purpose |
|---|---|
| `requests` | Making HTTP requests to mySBC (login, fetching pages) |
| `beautifulsoup4` | Parsing HTML from mySBC pages to extract data |
| `lxml` | Fast HTML/XML parser used by BeautifulSoup |
| `Pillow` | Loading and displaying the SBC crest image (`sbc_crest.png`) |
| `cryptography` | Encrypting saved credentials (Remember Me feature) |
| `urllib3` | Low-level HTTP handling used by requests (usually installed automatically) |

`tkinter` is **not** installed via pip — it comes bundled with Python from [python.org](https://www.python.org/downloads/). If you get `No module named tkinter`, reinstall Python from python.org (not Homebrew).

---

### Step 6 — Run the app

```bash
.venv/bin/python3 main.py
```

Or if you used the system Python setup:

```bash
python3 main.py
```

---

## Optional — PyCharm IDE

[PyCharm](https://www.jetbrains.com/pycharm/) is a free Python IDE that makes running and editing the app much easier than using Terminal manually. The **Community Edition** is completely free.

### Download PyCharm

1. Go to [jetbrains.com/pycharm/download](https://www.jetbrains.com/pycharm/download/)
2. Scroll down to **PyCharm Community Edition** (the free one — not Professional)
3. Click **Download** for macOS
4. Open the `.dmg` file and drag **PyCharm CE** into your Applications folder

### Set up the project in PyCharm

1. Open PyCharm
2. Click **Open** and select your `sbc_portal_v3` folder
3. PyCharm will detect the project — click **OK** if it asks about a virtual environment
4. In the bottom-right corner, click the Python version indicator → **Add New Interpreter** → **Add Local Interpreter** → **Virtual Environment**
5. Set the location to `.venv` inside your project folder and click **OK**
6. Open the **Terminal** tab at the bottom of PyCharm and run:
   ```bash
   pip install -r requirements.txt
   ```
7. Open `main.py` and click the green **▶ Run** button in the top-right — the app will launch

### Why use PyCharm?

- See errors highlighted in red as you type
- Click any error in the console to jump straight to that line
- The built-in terminal always opens in the right folder automatically
- Easy to re-run the app with one click instead of typing commands each time

---

## Logging In

Enter your **mySBC username and password** (the same ones you use at [mysbc.sbc.vic.edu.au](https://mysbc.sbc.vic.edu.au)).

- Tick **Remember Me** to save your credentials securely for next time
- If login fails due to school WiFi (ZScaler SSL interception), the app will automatically retry
- If mySBC is unreachable, the app will offer to load **cached data** from your last successful login

---

## Features

| Page | Description |
|---|---|
| 📊 **Grades** | All subjects with grades, class averages, SBC letter grades (A+/A/B/C/D/UG), per-assignment breakdowns |
| 📝 **Assessments** | Every graded task with teacher feedback, submission status, and formative task filtering |
| 📅 **Upcoming** | Pending assignments sorted by urgency (Overdue / This Week / Later), grouped by year |
| 🏫 **My Classes** | Class homepages with live lesson feed from each subject |
| 🗓 **Timetable** | Your 10-day cycle timetable, colour-coded by subject |
| 📆 **Calendar** | Monthly view of school events, excursions, and due work pulled from mySBC |
| 📋 **Study Planner** | Fortnight planner with timetable auto-fill, sleep warnings, goal tracking, and auto-generate |
| 🐾 **My Pet** | Gamification system — earn crates from grades, open lootboxes, level up your pet, unlock achievements |
| ⚙️ **Settings** | Dark/light mode, scroll speed, font size, gamification toggle, clear cache, manual data refresh |
| 👤 **Profile** | Your student profile with academic summary |
| 🍽 **Canteen** | Info and link to online ordering |
| 👥 **Groups** | Your mySBC groups |
| 🏫 **Student Services** | Quick links to all school services |

---

## Grade Scale (SBC)

| Grade | Range |
|---|---|
| A+ | 90–100% |
| A | 80–89% |
| B | 70–79% |
| C | 60–69% |
| D | 40–59% |
| UG | Below 40% |

> Formative tasks and Part A/B sub-components are automatically excluded from averages.
>
> Overall average is calculated as the sum of every individual task grade across all subjects divided by the total number of tasks — not an average of subject averages. This is more accurate and reflects your true performance.

---

## Data & Privacy

All app data is saved to **`~/.sbc_portal/`** — a hidden folder in your home directory.

On macOS this expands to:
```
/Users/YOUR_MAC_USERNAME/.sbc_portal/
```
For example, if your Mac login name is `41631`, the exact path is:
```
/Users/41631/.sbc_portal/
```

To open this folder in Finder, run this in Terminal:

```bash
open ~/.sbc_portal
```

This opens it directly regardless of hidden file settings. The folder is **invisible by default** in Finder because its name starts with a dot. To browse to it manually, press `Cmd + Shift + .` in any Finder window to toggle hidden files visible first.

| File | Contents |
|---|---|
| `sbc_portal.log` | App error and activity log |
| `settings.json` | Your app preferences |
| `remembered.json` | Encrypted saved login credentials |
| `cache_{username}.json` | Cached academic data (grades, subjects, assignments) |
| `crates_{username}.json` | Crate counts (HMAC-signed, tamper-proof) |
| `pet_{username}.json` | Your pet's level, XP, inventory, and achievements |
| `timetable_{username}.html` | Cached timetable HTML |
| `cids.json` | Discovered class homepage IDs |
| `groups_{username}.json` | Cached group membership data |
| `calendar_{username}.json` | Cached calendar events |

Nothing is sent anywhere except directly to mySBC (`mysbc.sbc.vic.edu.au`).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Operation not permitted` | Move the folder out of Downloads to Documents |
| `No module named tkinter` | Reinstall Python from python.org (not Homebrew) |
| Login says wrong password | You may be on school WiFi — the app retries automatically |
| App stuck on "Loading academic data" | Check `/Users/YOUR_MAC_USERNAME/.sbc_portal/sbc_portal.log` for errors |
| Timetable not showing | Navigate to the Timetable page while logged in — it fetches automatically on first open |
| Crate count resetting | Don't edit `~/.sbc_portal/crates_*.json` manually — it's integrity-checked |
| Can't find the `.sbc_portal` folder | Run `open ~/.sbc_portal` in Terminal — the folder is hidden by default |

> **Still stuck?** [Open an issue on GitHub](https://github.com/tobyw7700-hue/sbc-portal/issues/new) and describe the problem.

---

## Project Structure

```
sbc_portal_v3/
├── main.py                  ← Entry point
├── requirements.txt
├── data/
│   └── models.py            ← Data models (UserProfile, Subject, Assignment, etc.)
├── scraper/
│   ├── auth.py              ← Login, SAML, session management, SSL handling
│   ├── parser.py            ← Grade scraping (POST-based, Schoolbox-specific)
│   ├── timetable.py         ← Timetable parser
│   ├── class_scraper.py     ← Class homepage news feed fetcher
│   ├── calendar_scraper.py  ← Calendar event fetcher
│   └── grade_logic.py       ← Formative filtering, Part A/B exclusion, averages
├── ui/
│   ├── app.py               ← Main shell, sidebar, navigation, auto-refresh
│   ├── login_page.py        ← Login form with Remember Me and offline fallback
│   ├── grades_page.py       ← Grades dashboard
│   ├── assessments_page.py  ← Assessment detail view
│   ├── upcoming_page.py     ← Upcoming assignments
│   ├── classes_page.py      ← Classes & assessments overview
│   ├── class_home_page.py   ← Individual class homepage
│   ├── timetable_page.py    ← Timetable grid
│   ├── calendar_page.py     ← Monthly calendar
│   ├── planner_page.py      ← Study planner
│   ├── pet_page.py          ← Pet system (crates, wardrobe, achievements, claim animations)
│   ├── pet_canvas.py        ← Vector pet renderer
│   ├── crate_animation.py   ← Lootbox animation
│   ├── profile_page.py      ← Student profile
│   ├── settings_page.py     ← App settings and manual refresh
│   ├── canteen_page.py      ← Canteen info
│   ├── groups_page.py       ← My Groups
│   ├── student_services_page.py ← Student Services
│   ├── crest.py             ← SBC crest image loader
│   └── widgets.py           ← Shared widgets (ScrollableFrame, etc.)
└── assets/
    └── sbc_crest.png        ← School crest (required)
```

---

## First Run Notes

- The app fetches **2024, 2025, and 2026** grade data on first login — this takes about 10–20 seconds
- Data refreshes automatically **every 10 minutes** while the app is open — or manually via Settings → Refresh Now
- Your timetable is cached after the first visit to the Timetable page
- Class homepage CIDs are auto-discovered in the background on first launch
- All data is cached locally so subsequent launches are much faster

---

*Built for St Bernard's College, Essendon. Not affiliated with or endorsed by the school.*
