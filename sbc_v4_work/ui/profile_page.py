"""
Profile page — shows all student data fetched from mySBC.
Displays: Name, Email, Student ID, Role, DOB, Class Teacher,
          Year Level, Year Level Coordinator, Tutor Group, Campus, Class
"""
import tkinter as tk
from tkinter import ttk
import re, threading, json
from bs4 import BeautifulSoup

from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider, Card
from ui.crest import CrestImage


# Known field order for display
FIELD_ORDER = [
    "Email",
    "Student ID",
    "Role",
    "Date of Birth",
    "Class Teacher",
    "Year Level",
    "Year Level Coordinator",
    "Tutor Group",
    "Campus",
    "Class",
    "House",
    "Gender",
    "Nationality",
    "Religion",
]

# Fields that should be rendered as links (blue text)
LINK_FIELDS = {"Email", "Class Teacher", "Year Level Coordinator"}


class ProfilePage(tk.Frame):

    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data    = data
        self.session = session
        self.profile_fields: dict = {}
        self._build()
        self._load()

    def _build(self):
        hdr = PageHeader(self, "My Profile")
        hdr.pack(fill="x")
        GoldDivider(self).pack(fill="x")

        self.scroll = ScrollableFrame(self, bg=BG_DARK)
        self.scroll.pack(fill="both", expand=True)
        self.area = self.scroll.inner

        self.status = tk.Label(self.area, text="Loading profile…",
                               bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL)
        self.status.pack(pady=12)

    def _load(self):
        # Load pet data
        from ui.settings_page import load_settings
        from data.pet_models import load_pet
        settings = load_settings()
        username = (self.data.profile.username if self.data and self.data.profile else "default")
        self._pet = load_pet(username) if settings.get("show_pet_profile", True) else None
        self._show_pet = settings.get("gamification", True) and settings.get("show_pet_profile", True)

        if not self.data:
            self.status.configure(text="No profile data")
            return
        # Render basic data immediately from what we already have
        self._render_basic()
        # Then fetch extended data in background
        if self.session and self.data.profile:
            uid = self.data.profile.student_id or "11953"
            threading.Thread(target=self._fetch_extended,
                             args=(uid,), daemon=True).start()

    def _render_basic(self):
        """Render whatever we have from the scraper immediately."""
        profile = self.data.profile
        if not profile:
            return

        # Build initial fields from what parser already extracted
        basic = {}
        if profile.display_name:
            basic["Name"] = profile.display_name
        if profile.email:
            basic["Email"] = profile.email
        if profile.student_id:
            basic["Student ID"] = profile.student_id
        if profile.username:
            basic["Username"] = profile.username
        if profile.year_level:
            basic["Year Level"] = profile.year_level.replace("Students - Year ", "Year ")

        self._render(profile.display_name or "Student", basic)

    def _fetch_extended(self, user_id: str):
        """Fetch the full profile page and extract all fields."""
        try:
            BASE = "https://mysbc.sbc.vic.edu.au"
            resp = self.session.get(f"{BASE}/search/user/{user_id}")
            fields = self._parse_schoolbox_profile(resp.text, user_id)
            self.profile_fields = fields
            self.after(0, lambda: self._render(
                self.data.profile.display_name if self.data.profile else "Student",
                fields))
        except Exception as e:
            self.after(0, lambda: self.status.configure(
                text=f"Could not fetch extended profile: {e}"))

    def _parse_schoolbox_profile(self, html: str, user_id: str) -> dict:
        """
        Parse Schoolbox 26.0.9 profile page.
        The profile renders as a table or definition list with field:value pairs.
        """
        soup = BeautifulSoup(html, "html.parser")
        fields = {}

        # 1. Extract from window.schoolboxUser
        m = re.search(r'window\.schoolboxUser\s*=\s*(\{[^;]+\});', html, re.S)
        if m:
            try:
                user = json.loads(m.group(1))
                fields["Student ID"] = str(user.get("externalId",""))
                fields["_id"]        = str(user.get("id",""))
                role = user.get("role",{})
                if role.get("name"):
                    fields["Role"] = role["name"]
            except Exception:
                pass

        # 2. Look for profile field table — Schoolbox renders these as
        # <tr><td class="profile-label">Email</td><td>value</td></tr>
        for row in soup.find_all("tr"):
            cells = row.find_all(["td","th"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).rstrip(":")
                # Get value with any links preserved
                val_cell = cells[1]
                link = val_cell.find("a")
                if link:
                    val = link.get_text(strip=True)
                    href = link.get("href","")
                    if "mailto:" in href:
                        val = href.replace("mailto:","")
                else:
                    val = val_cell.get_text(strip=True)

                if key and val and 2 < len(key) < 60 and len(val) < 200:
                    # Normalise common key names
                    key = self._normalise_key(key)
                    fields[key] = val

        # 3. Definition lists
        for dl in soup.find_all("dl"):
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt, dd in zip(dts, dds):
                key = self._normalise_key(dt.get_text(strip=True).rstrip(":"))
                link = dd.find("a")
                val = (link.get_text(strip=True) if link
                       else dd.get_text(strip=True))
                if key and val:
                    fields[key] = val

        # 4. Scan for specific patterns in text
        text = soup.get_text("\n")
        # Email
        if "Email" not in fields:
            em = re.search(r'[\w.+\-]+@sbc\.vic\.edu\.au', html)
            if em:
                fields["Email"] = em.group(0)
        # DOB patterns: "Aug 18, 2011" or "18/08/2011"
        if "Date of Birth" not in fields:
            dob = re.search(
                r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b',
                text)
            if dob:
                fields["Date of Birth"] = dob.group(0)

        # 5. Look for teacher/coordinator links
        for a in soup.find_all("a", href=re.compile(r"/search/user/\d+")):
            name = a.get_text(strip=True)
            if not name or name == fields.get("_id",""):
                continue
            href = a.get("href","")
            # Don't include self
            if user_id in href:
                continue
            # Classify by surrounding text
            ctx = ""
            for parent in [a.parent, a.parent.parent if a.parent else None]:
                if parent:
                    ctx = parent.get_text(" ", strip=True).lower()
                    break
            if "class teacher" in ctx or "form teacher" in ctx:
                fields["Class Teacher"] = name
            elif "coordinator" in ctx or "year level coord" in ctx:
                fields["Year Level Coordinator"] = name
            elif "year level" in ctx:
                pass  # don't override year level number

        # 6. Tutor group / class
        tg = re.search(r'\b(0[7-9][A-Z]|1[0-2][A-Z])\b', text)
        if tg and "Tutor Group" not in fields:
            fields["Tutor Group"] = tg.group(0)

        # Clean up private fields
        fields.pop("_id", None)

        # Ensure Year Level is just the number
        if "Year Level" in fields:
            yl = fields["Year Level"]
            m2 = re.search(r'\d+', yl)
            if m2:
                fields["Year Level"] = m2.group(0)

        return fields

    def _normalise_key(self, key: str) -> str:
        """Normalise field key variations to canonical names."""
        mapping = {
            "e-mail": "Email",
            "e mail": "Email",
            "emailaddress": "Email",
            "studentid": "Student ID",
            "student number": "Student ID",
            "dateofbirth": "Date of Birth",
            "dob": "Date of Birth",
            "birthday": "Date of Birth",
            "classteacher": "Class Teacher",
            "form teacher": "Class Teacher",
            "homeroom teacher": "Class Teacher",
            "yearlevel": "Year Level",
            "year": "Year Level",
            "yearcoordinator": "Year Level Coordinator",
            "year coordinator": "Year Level Coordinator",
            "tutorgroup": "Tutor Group",
            "tutor": "Tutor Group",
            "house": "House",
        }
        return mapping.get(key.lower().replace(" ",""), key)

    def _render(self, display_name: str, fields: dict):
        """Render profile with all fields."""
        for w in self.area.winfo_children():
            w.destroy()

        profile = self.data.profile if self.data else None

        # ── Header card with name + crest ────────────────────────────
        header_card = tk.Frame(self.area, bg=ACCENT)
        header_card.pack(fill="x")

        hf = tk.Frame(header_card, bg=ACCENT)
        hf.pack(fill="x", padx=24, pady=16)

        CrestImage(hf, width=80, bg=ACCENT).pack(side="left", padx=(0,20))

        name_block = tk.Frame(hf, bg=ACCENT)
        name_block.pack(side="left", fill="x", expand=True)

        # Pet display (right side of header)
        if getattr(self, "_show_pet", False) and getattr(self, "_pet", None):
            pet_frame = tk.Frame(hf, bg=ACCENT)
            pet_frame.pack(side="right", padx=20)
            tk.Label(pet_frame, text=self._pet.display(),
                     bg=ACCENT, font=("TkDefaultFont", 40)).pack()
            tk.Label(pet_frame, text=f"{self._pet.name}  Lv.{self._pet.level}",
                     bg=ACCENT, fg=BG_DARK,
                     font=("TkDefaultFont", 10, "bold")).pack()

        tk.Label(name_block, text=display_name,
                 bg=ACCENT, fg=BG_DARK,
                 font=("Georgia", 22, "bold")).pack(anchor="w")

        # Sub-labels
        parts = []
        if fields.get("Role"):
            r = fields["Role"].replace("Students - ", "")
            parts.append(r)
        if fields.get("Tutor Group"):
            parts.append(f"Tutor Group {fields['Tutor Group']}")
        if fields.get("Campus"):
            parts.append(fields["Campus"])

        if parts:
            tk.Label(name_block, text="  ·  ".join(parts),
                     bg=ACCENT, fg=BG_DARK,
                     font=("TkDefaultFont", 11)).pack(anchor="w", pady=0)

        # ── Fields table ──────────────────────────────────────────────
        body = tk.Frame(self.area, bg=BG_DARK)
        body.pack(fill="x", padx=24, pady=20)

        # Build ordered field list
        shown = set()
        ordered = []
        for key in FIELD_ORDER:
            if key in fields:
                ordered.append((key, fields[key]))
                shown.add(key)
        # Add any remaining fields not in order
        for key, val in fields.items():
            if key not in shown and not key.startswith("_"):
                ordered.append((key, val))

        if not ordered:
            tk.Label(body, text="No additional profile data available.\nRun the app and log in to load full profile.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY,
                     justify="center").pack(pady=30)
            return
        # ── Grades summary strip ──────────────────────────────────────
        if self.data and self.data.subjects_by_year:
            import datetime
            yr = datetime.datetime.now().year
            subjects = self.data.subjects_by_year.get(yr, [])
            if subjects:
                tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=0)
                tk.Label(body, text=f"Academic Summary — {yr}",
                         bg=BG_DARK, fg=ACCENT,
                         font=("Georgia", 13, "bold")).pack(anchor="w", pady=8)

                from scraper.grade_logic import compute_subject_grade, fmt_grade, grade_label
                from ui.theme import grade_color

                grid = tk.Frame(body, bg=BG_DARK)
                grid.pack(fill="x")

                for i, subj in enumerate(subjects):
                    g, _ = compute_subject_grade(subj.assignments)
                    if g is None:
                        g = subj.grade_raw
                    color = grade_color(g) if g else FG_MUTED
                    col = i % 3

                    sf = tk.Frame(grid, bg=BG_CARD,
                                  highlightbackground=BORDER,
                                  highlightthickness=1)
                    sf.grid(row=i//3, column=col, padx=4, pady=4, sticky="nsew")
                    grid.columnconfigure(col, weight=1)

                    tk.Label(sf, text=subj.name or subj.code,
                             bg=BG_CARD, fg=FG_SEC,
                             font=("TkDefaultFont", 9),
                             anchor="w", padx=10, pady=4).pack(fill="x")
                    tk.Label(sf, text=fmt_grade(g) if g else "—",
                             bg=BG_CARD, fg=color,
                             font=("Georgia", 14, "bold"),
                             anchor="w", padx=10, pady=6).pack(fill="x")
