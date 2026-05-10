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

## Step 1 — Install PyCharm (Recommended IDE)

[PyCharm Community Edition](https://www.jetbrains.com/pycharm/download/) is free and makes running the app much easier than Terminal.

1. Go to [jetbrains.com/pycharm/download](https://www.jetbrains.com/pycharm/download/)
2. Scroll to **PyCharm Community Edition** — click **Download** for macOS
3. Open the `.dmg` and drag **PyCharm CE** to Applications
4. Open PyCharm → **Open** → select the `sbc_v4_work` folder
5. Bottom-right corner → click the Python version → **Add Interpreter** → **Add Local Interpreter** → **Virtual Environment** → set location to `.venv` inside the project → **OK**
6. Open the **Terminal** tab at the bottom → run `pip install -r requirements.txt`
7. Open `main.py` → click the green **▶ Run** button

> If you prefer Terminal, skip to Installation below.

---

## Requirements

- **macOS** (tested on macOS Tahoe 26.x)
- **Python 3.13** at `/usr/local/bin/python3.13` — already installed on school Macs
- An active mySBC account (your school login)

---

## Installation

### Step 1 — Download

Download `sbc_portal_v4_release.zip` from the [latest release](https://github.com/tobyw7700-hue/sbc-portal/releases/latest).

---

### Step 2 — Extract

Double-click the zip — Mac extracts it automatically. Move the `sbc_v4_work` folder to **Documents** (not Downloads).

> ⚠️ **Do not run from the Downloads folder** — macOS blocks scripts there.

---

### Step 3 — Run

Double-click **`run.command`** inside the folder.

> If macOS says it can't be opened: right-click → **Open** → **Open**.

`run.command` automatically finds the correct Python, patches the bundled environment, and launches the app. No Terminal needed.

**Or run from Terminal:**
```bash
cd ~/Documents/sbc_v4_work
python3.13 main.py
```

> On school Macs always use `python3.13` — the default `python3` is an older broken version.

---

## Logging In

Use your mySBC username and password (same as [mysbc.sbc.vic.edu.au](https://mysbc.sbc.vic.edu.au)).

- **Remember Me** saves credentials securely for next time
- On school WiFi the app retries automatically if SSL is intercepted
- If mySBC is unreachable the app loads cached data from your last login

---

## Updates

The app checks for updates automatically on launch. If a new version is available a green banner appears at the top — click it to download.

---

## Features

| Page | Description |
|---|---|
| 📊 **Grades** | All subjects with grades, SBC letter grades (A+/A/B/C/D/UG), per-assignment breakdown |
| 📝 **Assessments** | Every graded task with teacher feedback and submission status |
| 📅 **Upcoming** | Pending assignments sorted by urgency |
| 🏫 **My Classes** | Class homepages with live lesson feed |
| 🗓 **Timetable** | 10-day cycle timetable, colour-coded by subject |
| 📆 **Calendar** | Monthly school events and due dates |
| 📋 **Study Planner** | Fortnight planner — auto-generate, subject selection, PNG export |
| 🐾 **My Pet** | Crates, wardrobe, market, collection index, achievements |
| ⚙️ **Settings** | Themes, gamification, refresh, data management |
| 👤 **Profile** | Student profile with academic summary |
| 🍽 **Canteen** | Info and online ordering link |
| 👥 **Groups** | Your mySBC groups |
| 🏫 **Student Services** | Quick links to all school services |

---

## My Pet — Gamification

### Coins
Earn coins from grades and crate openings:

| Grade | Coins | Other |
|---|---|---|
| A+ | 20 | +3 per crate opened |
| A | 14 | |
| B | 9 | |
| C | 5 | |
| D | 2 | |

### Rarities (7 tiers)

| Rarity | Colour | Notes |
|---|---|---|
| Divine | ⚪ White | Extremely rare |
| Mythic | 🟠 Orange | Very rare |
| Legendary | 🟡 Gold | Rare |
| Epic | 🟣 Purple | Uncommon |
| Rare | 🔵 Blue | Somewhat common |
| Uncommon | 🟢 Green | Common |
| Common | 🩶 Grey | Very common |

### Crate chances

| Rarity | A+ (Golden) | A (Silver) | B (Bronze) | C (Common) | D (Worn) |
|---|---|---|---|---|---|
| Divine | 2% | 0% | 0% | 0% | 0% |
| Mythic | 5% | 1% | 0% | 0% | 0% |
| Legendary | 12% | 6% | 2% | 0% | 0% |
| Epic | 20% | 16% | 8% | 3% | 0% |
| Rare | 28% | 28% | 22% | 12% | 5% |
| Uncommon | 20% | 30% | 35% | 35% | 20% |
| Common | 13% | 19% | 33% | 50% | 75% |

### Market prices

| Rarity | Cost |
|---|---|
| Common | 8 coins |
| Uncommon | 20 coins |
| Rare | 55 coins |
| Epic | 130 coins |
| Legendary | 300 coins |
| Mythic | 700 coins |
| Divine | 1500 coins |

### Pet evolution
Pets visually evolve every 10 levels. At level 30 an aura appears, level 60 eyes glow, level 80 divine sparkles orbit the pet, level 90+ full white glow.

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
> Overall average = sum of all individual task grades ÷ total tasks.

---

## Data & Privacy

All data is saved to **`~/.sbc_portal/`** — a hidden folder in your home directory.

To open it in Finder:
```bash
open ~/.sbc_portal
```

| File | Contents |
|---|---|
| `sbc_portal.log` | App error log |
| `settings.json` | App preferences |
| `remembered.json` | Encrypted saved credentials |
| `cache_{username}.json` | Cached academic data |
| `crates_{username}.json` | Crate counts (HMAC-signed) |
| `pet_{username}.json` | Pet data (HMAC-signed) |
| `timetable_{username}.html` | Cached timetable |
| `planner.json` | Study planner data |

Nothing is sent anywhere except directly to mySBC.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `macOS 26 or later required` | Use `python3.13 main.py` or double-click `run.command` |
| `Operation not permitted` | Move folder out of Downloads to Documents |
| `No module named tkinter` | Reinstall Python from python.org |
| Login says wrong password | School WiFi may be intercepting — app retries automatically |
| Timetable not loading in planner | Visit the Timetable page first while logged in |
| Crate count resetting | Don't edit `crates_*.json` manually — it's integrity-checked |
| Can't find `.sbc_portal` folder | Run `open ~/.sbc_portal` in Terminal |

> **Still stuck?** [Open an issue on GitHub](https://github.com/tobyw7700-hue/sbc-portal/issues/new)

---

## Optional — PyCharm IDE

[Download PyCharm Community Edition](https://www.jetbrains.com/pycharm/download/) (free).

1. Open PyCharm → **Open** → select the `sbc_v4_work` folder
2. Bottom-right → Python version → **Add Interpreter** → **Virtual Environment** → set to `.venv`
3. Open Terminal tab → `pip install -r requirements.txt`
4. Open `main.py` → click ▶ **Run**

---

## First Run Notes

- First login fetches 2024–2026 grade data — takes 10–20 seconds
- Data auto-refreshes every 10 minutes while the app is open
- Timetable is cached after first visit to the Timetable page
- App checks for updates 2 seconds after launch

---

*Built for St Bernard's College, Essendon — v4.2. Not affiliated with or endorsed by the school.*
