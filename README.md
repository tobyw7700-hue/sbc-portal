# SBC Academic Portal — v4.2
A desktop app for St Bernard's College (Essendon) students. Pulls grades, timetables, class pages, assignments and more live from mySBC (Schoolbox). Includes a full gamification system with pets, crates, a market, and study tools.

---

## 🐛 Found a bug or have a suggestion?

> ### [👉 Report an issue on GitHub](https://github.com/tobyw7700-hue/sbc-portal/issues/new)
> Takes 2 minutes. Needs a free GitHub account — sign up at [github.com](https://github.com/join).

---

## Step 1 — Install PyCharm (recommended)

[PyCharm Community Edition](https://www.jetbrains.com/pycharm/download/) is free and the easiest way to run and edit the app.

1. Go to [jetbrains.com/pycharm/download](https://www.jetbrains.com/pycharm/download/)
2. Scroll to **PyCharm Community Edition** → **Download** for macOS
3. Open the `.dmg` → drag **PyCharm CE** to Applications
4. Open PyCharm → **Open** → select the `sbc_v4_work` folder
5. Bottom-right corner → click the Python version → **Add Interpreter** → **Add Local Interpreter** → **Virtual Environment** → set location to `.venv` inside the project folder → **OK**
6. Open the **Terminal** tab at the bottom of PyCharm and run:
   ```bash
   pip install -r requirements.txt
   ```
7. Open `main.py` → click the green **▶ Run** button

---

## Step 2 — Download the app

Download `sbc_portal_v4_release.zip` from the [latest release](https://github.com/tobyw7700-hue/sbc-portal/releases/latest).

Extract it — double-click the zip. Move the `sbc_v4_work` folder to your **Documents** folder (not Downloads).

> ⚠️ macOS blocks scripts run from the Downloads folder. Always move it first.

---

## Step 3 — Run the app

### Easiest — double-click the launcher

Inside `sbc_v4_work` there is a file called **`run.command`**. Double-click it.

> First time only: right-click → **Open** → **Open** to allow it past Gatekeeper.

**What `run.command` does automatically:**
- Detects which Python is installed and tests that Tkinter works
- Patches the bundled `.venv` to work from wherever you extracted the folder
- Installs any missing dependencies
- Launches the app

**No Python install needed** — Python 3.13 and all required libraries are bundled inside the `.venv` folder included in the zip. The app works out of the box.

---

### Terminal (alternative)

```bash
cd ~/Documents/sbc_v4_work
bash run.command
```

Or directly:

```bash
cd ~/Documents/sbc_v4_work
.venv/bin/python3 main.py
```

> **School Macs:** if you get `macOS 26 or later required`, run `python3.13 main.py` instead. Python 3.13 is pre-installed on school Macs at `/usr/local/bin/python3.13`.

---

## Logging In

Use your normal mySBC username and password (same as [mysbc.sbc.vic.edu.au](https://mysbc.sbc.vic.edu.au)).

- **Remember Me** — saves credentials encrypted so you don't have to type them next time
- **School WiFi** — if login fails due to ZScaler SSL interception the app retries automatically
- **Offline mode** — if mySBC is unreachable the app loads your last cached data with a yellow banner

---

## Updates

The app checks GitHub for a new version 2 seconds after launch. If one is available a **green banner** appears at the top of the window. Click it to open the releases page and download the update.

---

## Features

### 📊 Grades
- All subjects listed with percentage, SBC letter grade, and colour coding
- Per-assignment breakdown with teacher feedback and submission status
- Formative tasks automatically excluded from averages
- Part A/B sub-components excluded — only the final combined mark counts
- Overall average = sum of every individual task ÷ total tasks (more accurate than averaging subject averages)
- Year selector to view 2024, 2025, 2026 data

### 📝 Assessments
- Full list of every graded task across all subjects
- Shows grade, submission status (Reviewed / Submitted / Not Submitted), teacher comment
- Submitted tasks are never marked as overdue
- Tasks older than 30 days are excluded from the Overdue category

### 📅 Upcoming
- All pending assignments sorted by urgency — Overdue / Today / This Week / Later
- Filter by year and subject
- Colour-coded status indicators

### 🏫 My Classes
- Grid of all your subjects as clickable cards
- Each card opens the class homepage with the live lesson feed from mySBC
- Shows teacher name and current grade on each card

### 🗓 Timetable
- Full 10-day cycle timetable (Week A and Week B)
- Colour-coded by subject
- Shows subject, room, and teacher for each period
- Filter by Week A / Week B / All

### 📆 Calendar
- Monthly view of school events pulled live from mySBC
- Shows excursions, sport, exams, school days, due work
- Click any day to see all events for that day in a popup
- Navigate months with Prev/Next buttons

### 📋 Study Planner
A full 14-day fortnight planner with:

**Adding blocks:**
- 7 block types: Study, School, Sleep, Meal, Break, Activity, Free Time
- Each type has its own colour
- Start time auto-advances after adding a block
- "Next free" button jumps to after your last block

**Quick actions:**
- Load Timetable — fills in your school periods for that day automatically
- Add Sleep Block — adds a 9-hour sleep block
- Add Meals — adds breakfast, lunch and dinner
- Add Breaks — adds two short breaks

**Smart suggestions:**
- Shows upcoming assignments sorted by urgency
- Click any to instantly add a study session for it

**Auto-generate:**
- Fills the entire fortnight automatically
- Customise: wake time, bedtime, study hours per day, subjects per day, study start time, gap between sessions
- Choose exactly which subjects to include with individual checkboxes
- Separate weekend settings: sleep-in time, later bedtime, different study hours, Saturday lighter than Sunday toggle
- Add after-school activities (e.g. Gym Mon/Wed/Fri 16:30 for 60 mins) — study sessions automatically schedule after them
- Toggle: load timetable, add meals, add breaks, add free time, overwrite existing

**Goals & Priorities:**
- Priority sliders (1–5) per subject — affects how study time is allocated in auto-generate
- Free-text exam goals list

**Export:**
- 📸 Export PNG — saves all 14 days as a timetable-style grid image

### 🐾 My Pet
A full gamification system with 6 sub-tabs:

#### My Pet tab
- Vector-drawn pet that evolves visually every 10 levels (up to level 99)
- Evolution milestones: aura at 30, glowing eyes at 60, divine sparkles at 80, full white glow at 90
- Rename your pet
- Pet stats: level, XP progress, species, equipped item

#### 📦 Crates
- Earn crates from graded assessments — better grade = rarer crate
- A+ → Golden Crate, A → Silver, B → Bronze, C → Common, D → Worn
- Special Mythic Chest and Divine Chest unlocked through achievements
- Smooth lootbox animation with rarity-specific effects:
  - **Divine** — black hole: particles spiral inward, ring expands outward
  - **Mythic** — fire vortex: particles swirl upward in a spiral
  - **Legendary** — gold starburst radiating outward
  - **Epic** — purple sparkles drifting upward
  - All animations epilepsy-safe — no flashing colours
- Click any crate in the guide to see exact rarity percentages and possible items

#### 👗 Wardrobe
- All owned accessories shown sorted by rarity (Divine → Common) with section headers
- Each card shows your actual pet wearing the item as a preview
- One-click equip

#### 📖 Index
- Browse every pet and accessory in the game
- Sorted by rarity with section headers and rarity descriptions
- Search bar and rarity filter dropdown
- Pets show all 5 evolution stages side by side when owned
- Locked items show a 🔒 icon

#### 🏪 Market
- Refreshes every 15 minutes on the hour
- Same items shown to all users at the same time
- Buy items directly with coins
- Rare items respect rarity chances — not everything available is common
- Live countdown to next refresh

#### 🏆 Achievements
- 100+ achievements across academic, pet, crate, and hidden categories
- Claimable section at top — achievements you've earned but haven't claimed yet
- Claiming triggers: confetti animation, XP counter animating up, level-up display, before/after pet comparison if evolved
- Some achievements grant special Mythic or Divine Chests

#### ⚙️ Pet Settings (inside My Pet)
- Theme selector
- Gamification toggles
- Pet stats summary
- Reset pet data option

---

### 💰 Coin Economy

Coins are earned from grades and crate openings:

| Source | Coins |
|---|---|
| A+ assessment | 20 |
| A assessment | 14 |
| B assessment | 9 |
| C assessment | 5 |
| D assessment | 2 |
| Each crate opened | +3 |

**Market prices:**

| Rarity | Cost |
|---|---|
| Common | 8 🪙 |
| Uncommon | 20 🪙 |
| Rare | 55 🪙 |
| Epic | 130 🪙 |
| Legendary | 300 🪙 |
| Mythic | 700 🪙 |
| Divine | 1,500 🪙 |

---

### Rarity Tiers (7 total)

| Rarity | Colour | Crate chances (A+) |
|---|---|---|
| Divine | ⚪ White | 2% |
| Mythic | 🟠 Orange | 5% |
| Legendary | 🟡 Gold | 12% |
| Epic | 🟣 Purple | 20% |
| Rare | 🔵 Blue | 28% |
| Uncommon | 🟢 Green | 20% |
| Common | 🩶 Grey | 13% |

---

### ⚙️ Settings
- **UI Theme** — 5 themes: Dark (default), Light, Midnight (purple), Forest (green), Crimson (red) — applies instantly
- **Gamification** — toggle the entire My Pet tab on/off
- **Show pet on profile** — toggle pet display on Profile page
- **Scroll speed** — slider 1–5
- **Font size** — Small / Medium / Large
- **Auto Refresh** — data refreshes every 10 minutes; manual Refresh Now button with last-updated timestamp
- **Clear saved password** — removes stored credentials
- **Clear cached data** — forces a fresh fetch on next login

### 👤 Profile
- Full student profile from mySBC
- Academic summary grid with current year grades
- Pet displayed in the header (if enabled)

### 🍽 Canteen
- Tap & Go and online ordering information
- Direct link to the SBC online canteen shop
- Contact details

### 👥 Groups
- All your mySBC groups as clickable cards
- Click any to open it in the browser

### 🏫 Student Services
- Quick-link grid to all school services: Careers, ICT Support, Immunisations, Student Council, Transport, Library, Music, Uniform, Sport, Boys Writing, and more

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

---

## Data & Privacy

All data is stored locally in **`~/.sbc_portal/`** — a hidden folder in your home directory.

To open it in Finder:
```bash
open ~/.sbc_portal
```

The folder is hidden by default (starts with `.`). Press `Cmd + Shift + .` in Finder to show hidden files.

| File | Contents |
|---|---|
| `sbc_portal.log` | Error and activity log |
| `settings.json` | App preferences |
| `remembered.json` | Encrypted login credentials |
| `cache_{username}.json` | Cached grades and subjects |
| `crates_{username}.json` | Crate counts (HMAC-signed, tamper-proof) |
| `pet_{username}.json` | Pet data (HMAC-signed, tamper-proof) |
| `timetable_{username}.html` | Cached timetable |
| `planner.json` | Study planner blocks and goals |
| `cids.json` | Discovered class homepage IDs |
| `groups_{username}.json` | Cached group data |
| `calendar_{username}.json` | Cached calendar events |

Nothing is sent anywhere except directly to mySBC (`mysbc.sbc.vic.edu.au`).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `macOS 26 or later required` | Run `python3.13 main.py` — Python 3.13 is pre-installed on school Macs |
| `Operation not permitted` | Move folder from Downloads to Documents first |
| `No module named tkinter` | Reinstall Python from python.org (not Homebrew) |
| Login says wrong password | School WiFi (ZScaler) may be interfering — the app retries automatically |
| Timetable not loading in planner | Visit the Timetable page first while logged in — it caches automatically |
| Subject names truncated | Clear `~/.sbc_portal/cache_*.json` and re-login to refresh |
| Crate count resetting | Don't edit `crates_*.json` manually — it is HMAC-signed and will reset if tampered with |
| Can't find `.sbc_portal` folder | Run `open ~/.sbc_portal` in Terminal |
| App stuck on loading | Check `~/.sbc_portal/sbc_portal.log` for errors |

> **Still stuck?** [Open an issue on GitHub](https://github.com/tobyw7700-hue/sbc-portal/issues/new)

---

## Project Structure

```
sbc_v4_work/
├── main.py                    ← Entry point + auto-update check
├── run.command                ← Double-click launcher (patches .venv, finds Python)
├── requirements.txt
├── assets/
│   └── sbc_crest.png
├── data/
│   ├── models.py              ← Academic data models
│   ├── pet_models.py          ← Pet species, clothing, rarities, crates, coin economy
│   └── achievements.py        ← All 100+ achievements
├── scraper/
│   ├── auth.py                ← SAML login, session, SSL handling, cache
│   ├── parser.py              ← Grade scraping (Schoolbox POST-based)
│   ├── timetable_parser.py    ← Timetable HTML parser
│   ├── class_scraper.py       ← Class homepage news feed
│   ├── calendar_parser.py     ← Calendar event fetcher
│   └── grade_logic.py         ← Formative filtering, Part A/B exclusion, averages
└── ui/
    ├── app.py                 ← Shell, sidebar, navigation, auto-refresh
    ├── theme.py               ← 5 UI themes, colour variables
    ├── widgets.py             ← ScrollableFrame and shared widgets
    ├── login_page.py          ← Login, Remember Me, offline fallback
    ├── grades_page.py         ← Grades dashboard
    ├── classes_page.py        ← Classes & assessments overview
    ├── class_home_page.py     ← Individual class homepage feed
    ├── upcoming_page.py       ← Upcoming assignments
    ├── timetable_page.py      ← Timetable grid
    ├── calendar_page.py       ← Monthly calendar
    ├── planner_page.py        ← Study planner (full fortnight)
    ├── profile_page.py        ← Student profile
    ├── canteen_page.py        ← Canteen info
    ├── groups_page.py         ← My Groups
    ├── student_services_page.py ← Student Services grid
    ├── settings_page.py       ← App settings
    ├── pet_page.py            ← My Pet (all 6 sub-tabs)
    ├── pet_canvas.py          ← Vector pet and clothing renderer
    ├── crate_animation.py     ← Lootbox animation (epilepsy-safe)
    ├── market_page.py         ← Market (deterministic 15-min refresh)
    └── index_page.py          ← Collection index (all pets & accessories)
```

---

## First Run Notes

- First login fetches 2024, 2025 and 2026 grade data — takes 10–20 seconds
- Data auto-refreshes every 10 minutes while the app is open
- Timetable is cached after the first visit to the Timetable page
- Class homepage CIDs are discovered in the background on first launch
- All data is cached locally so subsequent launches are much faster
- The app checks for updates 2 seconds after launch

---

*SBC Academic Portal v4.2 — Built for St Bernard's College, Essendon. Not affiliated with or endorsed by the school.*
