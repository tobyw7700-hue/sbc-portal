"""
Study Planner — redesigned for clarity and ease of use.

Layout:
  Left sidebar  — 14-day fortnight selector with sleep/study summary dots
  Centre        — visual timeline for the selected day (hour blocks)
  Right panel   — add block form, quick actions, smart suggestions

Smart features:
  • Auto-load timetable for the day
  • Sleep warning with recommended hours
  • Smart study suggestions based on upcoming due dates
  • Auto-generate fills the whole fortnight intelligently
  • Goals & priorities influence auto-generate
  • Clear All button per day or for entire fortnight
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional

from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider

PLANNER_FILE = os.path.expanduser("~/.sbc_portal/planner.json")

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"] * 2
DAY_ABBR = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"] * 2

BLOCK_TYPES = {
    "study":    {"colour": "#1e40af", "icon": "📚", "label": "Study",      "default_mins": 60},
    "school":   {"colour": "#0f766e", "icon": "🏫", "label": "School",     "default_mins": 50},
    "sleep":    {"colour": "#5b21b6", "icon": "😴", "label": "Sleep",      "default_mins": 480},
    "meal":     {"colour": "#b45309", "icon": "🍽️", "label": "Meal",       "default_mins": 30},
    "break":    {"colour": "#15803d", "icon": "☕", "label": "Break",      "default_mins": 15},
    "activity": {"colour": "#b91c1c", "icon": "🏃", "label": "Activity",   "default_mins": 60},
    "free":     {"colour": "#374151", "icon": "🎮", "label": "Free Time",  "default_mins": 60},
}

SLEEP_IDEAL = 9
SLEEP_WARN  = 7
STUDY_COLOURS = [
    "#1e40af","#14532d","#7c2d12","#4c1d95","#831843","#7f1d1d","#164e63","#365314"
]

PERIOD_TIMES = {
    "Homeroom": ("08:45", 10),
    "Period 1": ("08:55", 50),
    "Period 2": ("09:45", 50),
    "Period 3": ("11:00", 50),
    "Period 4": ("11:50", 50),
    "Period 5": ("13:15", 50),
    "Period 6": ("14:05", 50),
}


def _time_to_mins(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m

def _mins_to_time(m: int) -> str:
    m = m % (24 * 60)
    return f"{m//60:02d}:{m%60:02d}"

def _btn(parent, text, bg, fg="#ffffff", cmd=None, font=None, padx=10, pady=6):
    b = tk.Label(parent, text=text, bg=bg, fg=fg, cursor="hand2",
                 font=font or ("TkDefaultFont", 10, "bold"),
                 padx=padx, pady=pady, relief="flat")
    if cmd:
        b.bind("<Button-1>", lambda e: cmd())
    b.bind("<Enter>", lambda e: b.configure(bg=_lighten(bg)))
    b.bind("<Leave>", lambda e: b.configure(bg=bg))
    return b

def _lighten(hex_color, amt=20):
    try:
        h = hex_color.lstrip("#")
        if len(h) != 6: return hex_color
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"#{min(255,r+amt):02x}{min(255,g+amt):02x}{min(255,b+amt):02x}"
    except Exception:
        return hex_color

def _tooltip(widget, text):
    tip = [None]
    def show(e):
        if tip[0]:
            try: tip[0].destroy()
            except Exception: pass
        try:
            t = tk.Toplevel(widget)
            t.wm_overrideredirect(True)
            t.wm_geometry(f"+{e.x_root+14}+{e.y_root+8}")
            t.attributes("-topmost", True)
            tk.Label(t, text=text, bg="#fef9c3", fg="#111",
                     font=("TkDefaultFont", 9), relief="solid", bd=1,
                     padx=8, pady=4, wraplength=280).pack()
            tip[0] = t
        except Exception:
            pass
    def hide(e):
        if tip[0]:
            try: tip[0].destroy()
            except Exception: pass
            tip[0] = None
    widget.bind("<Enter>", show, add="+")
    widget.bind("<Leave>", hide, add="+")
    widget.bind("<ButtonPress>", hide, add="+")


class Block:
    def __init__(self, btype="study", label="", start="08:00",
                 duration=60, subject="", note=""):
        self.btype    = btype
        self.label    = label or BLOCK_TYPES.get(btype, {}).get("label", "Block")
        self.start    = start
        self.duration = duration
        self.subject  = subject
        self.note     = note

    def end_time(self) -> str:
        return _mins_to_time(_time_to_mins(self.start) + self.duration)

    def colour(self) -> str:
        if self.btype == "study" and self.subject:
            subjects = list(BLOCK_TYPES.keys())
            idx = hash(self.subject) % len(STUDY_COLOURS)
            return STUDY_COLOURS[idx]
        return BLOCK_TYPES.get(self.btype, {}).get("colour", BG_MID)

    def to_dict(self):  return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        b = cls(); b.__dict__.update(d); return b


class DayPlan:
    def __init__(self, i):
        self.day_index = i
        self.blocks: List[Block] = []
        self.notes = ""

    def sorted_blocks(self):
        return sorted(self.blocks, key=lambda b: _time_to_mins(b.start))

    def sleep_hours(self) -> float:
        return sum(b.duration for b in self.blocks if b.btype == "sleep") / 60

    def study_hours(self) -> float:
        return sum(b.duration for b in self.blocks if b.btype == "study") / 60

    def school_hours(self) -> float:
        return sum(b.duration for b in self.blocks if b.btype == "school") / 60

    def total_scheduled(self) -> float:
        return sum(b.duration for b in self.blocks) / 60

    def next_free_slot(self) -> str:
        if not self.blocks:
            return "07:00"
        end_mins = max(_time_to_mins(b.start) + b.duration for b in self.blocks)
        return _mins_to_time(end_mins + 15)

    def sleep_status(self) -> tuple:
        h = self.sleep_hours()
        if h == 0:     return (None, None)
        if h < 6:      return ("danger",  f"⚠️ {h:.1f}h sleep — dangerously low!")
        if h < SLEEP_WARN: return ("warn", f"😴 {h:.1f}h sleep — aim for {SLEEP_IDEAL}h")
        return ("ok",  f"✓ {h:.1f}h sleep")

    def to_dict(self):
        return {"day_index": self.day_index, "blocks": [b.to_dict() for b in self.blocks],
                "notes": self.notes}

    @classmethod
    def from_dict(cls, d):
        dp = cls(d["day_index"])
        dp.blocks = [Block.from_dict(b) for b in d.get("blocks", [])]
        dp.notes  = d.get("notes", "")
        return dp


class PlannerPage(tk.Frame):

    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data         = data
        self.session      = session
        self.day_plans    = [DayPlan(i) for i in range(14)]
        self.goals        = []
        self.priorities   = {}
        self.timetable    = {}
        self.selected_day = 0
        self._subject_colours: Dict[str, str] = {}
        self._load_timetable()
        self._load_saved()
        self._assign_subject_colours()
        self._build()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_timetable(self):
        try:
            from scraper.timetable_parser import load_timetable
            username = ""
            if self.data and self.data.profile:
                username = self.data.profile.username or self.data.profile.student_id or ""
            self.timetable = load_timetable(self.session, username)
        except Exception:
            self.timetable = {}

    def _load_saved(self):
        try:
            if os.path.exists(PLANNER_FILE):
                with open(PLANNER_FILE) as f:
                    d = json.load(f)
                self.day_plans  = [DayPlan.from_dict(x) for x in d.get("days", [])]
                self.goals      = d.get("goals", [])
                self.priorities = d.get("priorities", {})
                while len(self.day_plans) < 14:
                    self.day_plans.append(DayPlan(len(self.day_plans)))
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(PLANNER_FILE), exist_ok=True)
            with open(PLANNER_FILE, "w") as f:
                json.dump({"days":       [d.to_dict() for d in self.day_plans],
                           "goals":      self.goals,
                           "priorities": self.priorities}, f, indent=2)
        except Exception:
            pass

    def _get_subjects(self) -> List[str]:
        if not self.data: return ["Mathematics","English","Science","Humanities"]
        import datetime as dt
        yr = dt.datetime.now().year
        subs = set()
        for y, ss in self.data.subjects_by_year.items():
            if y == yr:
                for s in ss:
                    if s.name and "Assembly" not in s.name and "Home Room" not in s.name:
                        subs.add(s.name)
        return sorted(subs) if subs else ["Mathematics","English","Science","Humanities"]

    def _assign_subject_colours(self):
        for i, sub in enumerate(self._get_subjects()):
            self._subject_colours[sub] = STUDY_COLOURS[i % len(STUDY_COLOURS)]

    def _get_upcoming_tasks(self) -> list:
        """Return upcoming assignments sorted by due date."""
        if not self.data: return []
        import datetime as dt
        today = dt.date.today()
        tasks = []
        for yr, subjects in self.data.subjects_by_year.items():
            if yr < today.year - 1: continue
            for subj in subjects:
                for a in subj.assignments:
                    if a.due_date and not a.grade_raw:
                        try:
                            due = dt.datetime.strptime(a.due_date[:10], "%Y-%m-%d").date()
                            if due >= today:
                                tasks.append({"title": a.title, "subject": subj.name,
                                              "due": due, "days_left": (due-today).days})
                        except Exception:
                            pass
        return sorted(tasks, key=lambda t: t["due"])[:10]

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr_frame = tk.Frame(self, bg=BG_MID)
        hdr_frame.pack(fill="x")
        tk.Frame(hdr_frame, bg=ACCENT, height=3).pack(fill="x")
        title_row = tk.Frame(hdr_frame, bg=BG_MID)
        title_row.pack(fill="x", padx=16, pady=8)
        tk.Label(title_row, text="📋  Study Planner", bg=BG_MID, fg=FG_PRIMARY,
                 font=("Georgia", 18, "bold")).pack(side="left")
        tk.Label(title_row, text="14-day fortnight · Tap a day · Add blocks to plan your schedule",
                 bg=BG_MID, fg=FG_MUTED, font=FONT_SMALL).pack(side="left", padx=16)

        # Action buttons
        btn_row = tk.Frame(hdr_frame, bg=BG_MID)
        btn_row.pack(fill="x", padx=16, pady=6)
        actions = [
            ("⚡ Auto-Generate",  self._auto_generate,  ACCENT,   BG_DARK,
             "Automatically fill the fortnight based on your timetable, due dates and sleep schedule"),
            ("🎯 Goals & Priorities", self._edit_goals, BG_LIGHT, FG_PRIMARY,
             "Set exam goals and adjust how much time is allocated to each subject"),
            ("🗑️ Clear Day",      self._clear_day,      BG_LIGHT, FG_PRIMARY,
             "Remove all blocks from the selected day"),
            ("🗑️ Clear All",      self._clear_all,      "#7f1d1d", "#fca5a5",
             "Remove all blocks from the entire fortnight"),
            ("💾 Save",           self._save_confirm,   BG_LIGHT, FG_PRIMARY,
             "Save your planner"),
            ("📸 Export PNG",     self._export_png,     BG_LIGHT, FG_PRIMARY,
             "Export all 14 days as a timetable-style PNG image"),
        ]
        for text, cmd, bg, fg, tip in actions:
            b = _btn(btn_row, text, bg, fg, cmd, padx=12, pady=5)
            b.pack(side="left", padx=3)
            _tooltip(b, tip)

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True)

        # Left: day selector
        self._build_day_sidebar(body)

        # Right: add block panel
        self._build_add_panel(body)

        # Centre: timeline
        self._centre = tk.Frame(body, bg=BG_DARK)
        self._centre.pack(side="left", fill="both", expand=True)

        self._select_day(0)

    def _build_day_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=BG_MID, width=155)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(sidebar, text="FORTNIGHT", bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 8, "bold"), padx=10, pady=6).pack(anchor="w")

        self._day_btns = []
        for i in range(14):
            if i == 7:
                tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=8, pady=2)
                tk.Label(sidebar, text="WEEK 2", bg=BG_MID, fg=ACCENT,
                         font=("TkDefaultFont", 8, "bold"), padx=10, pady=4).pack(anchor="w")

            is_we = DAYS[i] in ("Saturday", "Sunday")
            row = tk.Frame(sidebar, bg=BG_MID, cursor="hand2")
            row.pack(fill="x")

            # Status dot (sleep/study indicator)
            dot = tk.Label(row, text="●", bg=BG_MID, fg=BORDER,
                           font=("TkDefaultFont", 7), padx=4)
            dot.pack(side="left")

            lbl = tk.Label(row,
                           text=f"{'W1' if i<7 else 'W2'} {DAY_ABBR[i]} {i%7+1}",
                           bg=BG_MID, fg=FG_MUTED if is_we else FG_SEC,
                           font=("TkDefaultFont", 9, "bold" if not is_we else "normal"),
                           anchor="w", padx=4, pady=7, cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)

            for w in [row, lbl, dot]:
                w.bind("<Button-1>", lambda e, idx=i: self._select_day(idx))
                w.bind("<Enter>", lambda e, r=row: r.configure(bg=BG_LIGHT))
                w.bind("<Leave>", lambda e, r=row: r.configure(bg=ACCENT if r._selected else BG_MID) if hasattr(r, '_selected') else r.configure(bg=BG_MID))

            row._selected = False
            self._day_btns.append((row, lbl, dot))

    def _build_add_panel(self, parent):
        """Right panel: add block form + smart suggestions."""
        panel = tk.Frame(parent, bg=BG_MID, width=260)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        tk.Frame(panel, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(panel, text="Add Block", bg=BG_MID, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), padx=12, pady=8).pack(anchor="w")

        scroll = ScrollableFrame(panel, bg=BG_MID)
        scroll.pack(fill="both", expand=True)
        self._form = scroll.inner

        self._build_form()

    def _build_form(self):
        area = self._form
        for w in area.winfo_children():
            w.destroy()

        def row_label(text, tooltip_text=None):
            lbl = tk.Label(area, text=text, bg=BG_MID, fg=FG_SEC,
                           font=("TkDefaultFont", 9, "bold"), padx=12, anchor="w")
            lbl.pack(fill="x", pady=2)
            if tooltip_text:
                _tooltip(lbl, tooltip_text)
            return lbl

        def field_frame():
            f = tk.Frame(area, bg=BG_MID)
            f.pack(fill="x", padx=10, pady=2)
            return f

        # Block type
        row_label("Block Type", "What kind of activity is this?")
        self._btype_var = tk.StringVar(value="study")
        type_grid = tk.Frame(area, bg=BG_MID)
        type_grid.pack(fill="x", padx=10, pady=4)
        for i, (key, info) in enumerate(BLOCK_TYPES.items()):
            btn = tk.Label(type_grid, text=f"{info['icon']} {info['label']}",
                           bg=BG_CARD, fg=FG_SEC,
                           font=("TkDefaultFont", 8, "bold"),
                           padx=6, pady=5, cursor="hand2",
                           highlightbackground=BORDER, highlightthickness=1)
            btn.grid(row=i//2, column=i%2, padx=3, pady=3, sticky="ew")
            type_grid.columnconfigure(i%2, weight=1)
            btn.bind("<Button-1>", lambda e, k=key, b=btn: self._select_type(k))
            setattr(self, f"_type_btn_{key}", btn)

        self._select_type("study")

        # Subject (shown for study blocks)
        self._subject_frame = tk.Frame(area, bg=BG_MID)
        self._subject_frame.pack(fill="x")
        row_label_sub = tk.Label(self._subject_frame, text="Subject",
                                  bg=BG_MID, fg=FG_SEC,
                                  font=("TkDefaultFont", 9, "bold"), padx=12, anchor="w")
        row_label_sub.pack(fill="x", pady=2)
        _tooltip(row_label_sub, "Which subject are you studying?")
        self._subject_var = tk.StringVar(value="")
        subjects = self._get_subjects()
        subj_menu = ttk.Combobox(self._subject_frame, textvariable=self._subject_var,
                                  values=["(none)"] + subjects, state="readonly")
        subj_menu.pack(fill="x", padx=10, pady=2)
        if subjects:
            self._subject_var.set(subjects[0])

        # Label
        row_label("Label", "Custom name for this block (optional)")
        ff = field_frame()
        self._label_var = tk.StringVar()
        tk.Entry(ff, textvariable=self._label_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief="flat",
                 font=FONT_BODY).pack(fill="x", ipady=5)

        # Start time
        row_label("Start Time", "When does this block begin? (HH:MM)")
        ff2 = field_frame()
        self._start_var = tk.StringVar(value="08:00")
        tk.Entry(ff2, textvariable=self._start_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief="flat",
                 font=FONT_BODY, width=8).pack(side="left", ipady=5)
        _btn(ff2, "Next free", BG_LIGHT, FG_PRIMARY,
             lambda: self._start_var.set(
                 self.day_plans[self.selected_day].next_free_slot()),
             padx=8, pady=3).pack(side="left", padx=6)
        _tooltip(area.winfo_children()[-1] if area.winfo_children() else area,
                 "Jump to the next available time slot")

        # Duration
        row_label("Duration", "How long is this block?")
        dur_frame = field_frame()
        self._dur_var = tk.IntVar(value=60)
        dur_presets = [(15,"15m"), (30,"30m"), (60,"1h"), (90,"1.5h"),
                       (120,"2h"), (180,"3h"), (480,"8h (sleep)")]
        for mins, lbl_text in dur_presets:
            b = tk.Label(dur_frame, text=lbl_text, bg=BG_CARD, fg=FG_SEC,
                         font=("TkDefaultFont", 8), padx=5, pady=4, cursor="hand2",
                         highlightbackground=BORDER, highlightthickness=1)
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e, m=mins: self._dur_var.set(m))
        tk.Frame(area, bg=BG_MID, height=4).pack()
        custom_frame = field_frame()
        tk.Label(custom_frame, text="Custom (mins):", bg=BG_MID, fg=FG_MUTED,
                 font=FONT_SMALL).pack(side="left")
        tk.Entry(custom_frame, textvariable=self._dur_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief="flat",
                 font=FONT_BODY, width=6).pack(side="left", padx=6, ipady=4)

        # Note
        row_label("Note (optional)", "Any extra info, e.g. 'Chapter 5 revision'")
        ff3 = field_frame()
        self._note_var = tk.StringVar()
        tk.Entry(ff3, textvariable=self._note_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief="flat",
                 font=FONT_BODY).pack(fill="x", ipady=4)

        # Add button
        tk.Frame(area, bg=BG_MID, height=8).pack()
        add_btn = _btn(area, "＋  Add Block", ACCENT, BG_DARK,
                       self._add_block, padx=12, pady=10)
        add_btn.pack(fill="x", padx=10)
        _tooltip(add_btn, "Add this block to the selected day")

        # Quick actions
        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=10, pady=10)
        tk.Label(area, text="Quick Actions", bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 9, "bold"), padx=12).pack(anchor="w")

        quick = [
            ("📅 Load Timetable",  self._load_timetable_for_day,
             "Fill in today's school periods from your timetable"),
            ("😴 Add Sleep Block", self._add_sleep_quick,
             "Add a recommended 9h sleep block"),
            ("🍽️ Add Meals",       self._add_meals_quick,
             "Add breakfast, lunch and dinner"),
            ("☕ Add Breaks",      self._add_breaks_quick,
             "Add short break periods between study sessions"),
        ]
        for text, cmd, tip in quick:
            b = _btn(area, text, BG_CARD, FG_SEC, cmd, padx=10, pady=6)
            b.pack(fill="x", padx=10, pady=2)
            _tooltip(b, tip)

        # Smart suggestions
        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=10, pady=10)
        tk.Label(area, text="💡 Smart Suggestions", bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 9, "bold"), padx=12).pack(anchor="w")
        self._suggestions_frame = tk.Frame(area, bg=BG_MID)
        self._suggestions_frame.pack(fill="x", padx=10, pady=4)
        self._refresh_suggestions()

    def _select_type(self, key):
        self._btype_var.set(key)
        for k in BLOCK_TYPES:
            btn = getattr(self, f"_type_btn_{k}", None)
            if btn:
                info = BLOCK_TYPES[k]
                is_sel = k == key
                btn.configure(
                    bg=info["colour"] if is_sel else BG_CARD,
                    fg="white" if is_sel else FG_MUTED,
                    highlightbackground=info["colour"] if is_sel else BORDER)
        # Show/hide subject field
        if hasattr(self, "_subject_frame"):
            if key == "study":
                self._subject_frame.pack(fill="x")
            else:
                self._subject_frame.pack_forget()
        # Set sensible defaults
        info = BLOCK_TYPES.get(key, {})
        if hasattr(self, "_dur_var"):
            self._dur_var.set(info.get("default_mins", 60))
        if hasattr(self, "_label_var"):
            self._label_var.set(info.get("label", ""))

    def _refresh_suggestions(self):
        for w in self._suggestions_frame.winfo_children():
            w.destroy()
        tasks = self._get_upcoming_tasks()
        if not tasks:
            tk.Label(self._suggestions_frame, text="No upcoming tasks found.",
                     bg=BG_MID, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")
            return
        for t in tasks[:5]:
            days_left = t["days_left"]
            urgency   = "🔴" if days_left <= 2 else "🟡" if days_left <= 7 else "🟢"
            text      = f"{urgency} {t['subject'][:14]}: {t['title'][:18]}…"
            due_text  = f"Due in {days_left}d" if days_left > 0 else "Due today!"
            row = tk.Frame(self._suggestions_frame, bg=BG_CARD,
                           highlightbackground=BORDER, highlightthickness=1,
                           cursor="hand2")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=text, bg=BG_CARD, fg=FG_PRIMARY,
                     font=("TkDefaultFont", 8), padx=6, pady=4, anchor="w").pack(anchor="w")
            tk.Label(row, text=due_text, bg=BG_CARD, fg=ACCENT,
                     font=("TkDefaultFont", 8), padx=6, anchor="w").pack(anchor="w")
            row.bind("<Button-1>", lambda e, task=t: self._quick_add_study(task))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, task=t: self._quick_add_study(task))
            _tooltip(row, f"Click to add a study session for {t['subject']}")

    def _quick_add_study(self, task):
        """Add a study block for this task with one click."""
        dp = self.day_plans[self.selected_day]
        block = Block(btype="study", label=f"Study: {task['title'][:20]}",
                      start=dp.next_free_slot(),
                      duration=60, subject=task["subject"])
        dp.blocks.append(block)
        self._save()
        self._refresh_day_view()

    # ── Day selection & timeline ───────────────────────────────────────────────

    def _select_day(self, idx):
        self.selected_day = idx
        # Update sidebar buttons
        for i, (row, lbl, dot) in enumerate(self._day_btns):
            dp = self.day_plans[i]
            is_sel = i == idx
            is_we  = DAYS[i] in ("Saturday","Sunday")
            row.configure(bg=ACCENT if is_sel else BG_MID)
            lbl.configure(bg=ACCENT if is_sel else BG_MID,
                          fg=BG_DARK if is_sel else (FG_MUTED if is_we else FG_SEC))
            # Dot colour shows sleep status
            sl = dp.sleep_hours()
            if sl == 0:     dot.configure(fg=BORDER)
            elif sl < 6:    dot.configure(fg=DANGER)
            elif sl < 7:    dot.configure(fg=WARNING)
            else:           dot.configure(fg=SUCCESS)
            dot.configure(bg=ACCENT if is_sel else BG_MID)
            row._selected = is_sel

        # Update start time to next free slot
        if hasattr(self, "_start_var"):
            dp = self.day_plans[idx]
            self._start_var.set(dp.next_free_slot())

        self._refresh_day_view()
        self._refresh_suggestions()

    def _refresh_day_view(self):
        for w in self._centre.winfo_children():
            w.destroy()

        idx = self.selected_day
        dp  = self.day_plans[idx]
        day_name = f"{'Week 1' if idx<7 else 'Week 2'}  —  {DAYS[idx]}"

        # Day header
        hdr = tk.Frame(self._centre, bg=BG_MID)
        hdr.pack(fill="x")
        tk.Label(hdr, text=day_name, bg=BG_MID, fg=FG_PRIMARY,
                 font=("Georgia", 13, "bold"), padx=16, pady=10).pack(side="left")

        # Stats
        stats = tk.Frame(hdr, bg=BG_MID)
        stats.pack(side="right", padx=12)
        for label, val, col in [
            ("School", f"{dp.school_hours():.1f}h", TEAL),
            ("Study",  f"{dp.study_hours():.1f}h",  ROYAL),
            ("Sleep",  f"{dp.sleep_hours():.1f}h",  "#5b21b6"),
            ("Total",  f"{dp.total_scheduled():.1f}h", ACCENT),
        ]:
            sf = tk.Frame(stats, bg=BG_MID)
            sf.pack(side="left", padx=8)
            tk.Label(sf, text=val, bg=BG_MID, fg=col,
                     font=("Georgia", 12, "bold")).pack()
            tk.Label(sf, text=label, bg=BG_MID, fg=FG_MUTED,
                     font=("TkDefaultFont", 8)).pack()

        # Sleep warning
        status, msg = dp.sleep_status()
        if msg:
            warn_col = DANGER if status == "danger" else WARNING if status == "warn" else SUCCESS
            tk.Label(self._centre, text=msg, bg=BG_DARK, fg=warn_col,
                     font=("TkDefaultFont", 9, "bold"), padx=16, pady=4).pack(fill="x", anchor="w")

        # Timeline scroll area
        scroll = ScrollableFrame(self._centre, bg=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=0, pady=4)
        area = scroll.inner

        blocks = dp.sorted_blocks()
        if not blocks:
            empty = tk.Frame(area, bg=BG_DARK)
            empty.pack(fill="both", expand=True, pady=40)
            tk.Label(empty, text="No blocks yet",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("Georgia", 16)).pack()
            tk.Label(empty,
                     text="Use the panel on the right to add blocks,\n"
                          "or click Quick Actions to auto-fill from your timetable.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY, justify="center").pack(pady=8)
            _btn(empty, "📅 Load Timetable for This Day",
                 ACCENT, BG_DARK, self._load_timetable_for_day,
                 padx=16, pady=8).pack(pady=12)
            return

        for block in blocks:
            self._draw_block(area, block, dp)

    def _draw_block(self, parent, block: Block, dp: DayPlan):
        col = block.colour()
        row = tk.Frame(parent, bg=BG_CARD,
                       highlightbackground=col, highlightthickness=2)
        row.pack(fill="x", padx=16, pady=3)

        # Colour stripe
        tk.Frame(row, bg=col, width=6).pack(side="left", fill="y")

        # Time
        time_frame = tk.Frame(row, bg=BG_CARD, width=90)
        time_frame.pack(side="left", fill="y", padx=8, pady=8)
        time_frame.pack_propagate(False)
        tk.Label(time_frame, text=block.start, bg=BG_CARD, fg=FG_PRIMARY,
                 font=("Georgia", 13, "bold")).pack(anchor="w")
        tk.Label(time_frame, text=f"→ {block.end_time()}", bg=BG_CARD, fg=FG_MUTED,
                 font=FONT_SMALL).pack(anchor="w")
        mins = block.duration
        dur_str = f"{mins//60}h {mins%60}m" if mins >= 60 else f"{mins}m"
        tk.Label(time_frame, text=dur_str, bg=BG_CARD, fg=col,
                 font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

        # Icon + content
        info = tk.Frame(row, bg=BG_CARD)
        info.pack(side="left", fill="both", expand=True, pady=8)
        binfo = BLOCK_TYPES.get(block.btype, {})
        tk.Label(info, text=f"{binfo.get('icon','📌')}  {block.label}",
                 bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
        if block.subject:
            tk.Label(info, text=block.subject, bg=BG_CARD, fg=col,
                     font=("TkDefaultFont", 9), anchor="w").pack(anchor="w")
        if block.note:
            tk.Label(info, text=block.note, bg=BG_CARD, fg=FG_MUTED,
                     font=FONT_SMALL, anchor="w").pack(anchor="w")

        # Delete button
        del_btn = tk.Label(row, text="  ✕  ", bg=BG_CARD, fg=FG_MUTED,
                           font=("TkDefaultFont", 14), cursor="hand2", pady=8)
        del_btn.pack(side="right", padx=4)
        del_btn.bind("<Button-1>", lambda e, b=block: self._delete_block(b, dp))
        del_btn.bind("<Enter>", lambda e, d=del_btn: d.configure(fg=DANGER))
        del_btn.bind("<Leave>", lambda e, d=del_btn: d.configure(fg=FG_MUTED))
        _tooltip(del_btn, "Remove this block")

    # ── Block actions ─────────────────────────────────────────────────────────

    def _add_block(self):
        btype = self._btype_var.get()
        try:
            dur = int(self._dur_var.get())
        except Exception:
            dur = 60
        start = self._start_var.get().strip()
        if not start or ":" not in start:
            messagebox.showwarning("Invalid Time", "Please enter a valid start time (HH:MM)")
            return
        label   = self._label_var.get().strip()
        subject = self._subject_var.get() if btype == "study" else ""
        if subject == "(none)": subject = ""
        note    = self._note_var.get().strip()
        block = Block(btype=btype, label=label, start=start,
                      duration=dur, subject=subject, note=note)
        dp = self.day_plans[self.selected_day]
        dp.blocks.append(block)
        # Advance start time for next block
        self._start_var.set(block.end_time())
        self._label_var.set("")
        self._note_var.set("")
        self._save()
        self._refresh_day_view()
        self._select_day(self.selected_day)  # refresh dots

    def _delete_block(self, block: Block, dp: DayPlan):
        if block in dp.blocks:
            dp.blocks.remove(block)
        self._save()
        self._refresh_day_view()
        self._select_day(self.selected_day)

    # ── Quick actions ─────────────────────────────────────────────────────────

    def _load_timetable_for_day(self):
        dp = self.day_plans[self.selected_day]
        day_name = DAYS[self.selected_day]

        if not self.timetable:
            messagebox.showinfo("No Timetable",
                                "No timetable data found.\nVisit the Timetable page first while logged in.")
            return

        day_map = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,
                   "Saturday":None,"Sunday":None}
        week    = 0 if self.selected_day < 7 else 1
        day_num = day_map.get(day_name)
        if day_num is None:
            messagebox.showinfo("Weekend", "No timetable for weekends.")
            return

        # timetable structure: {"cells": {"Day 1": {"Period 1": {"code":...,"room":...}}}}
        cells    = self.timetable.get("cells", self.timetable)
        tt_key   = f"Day {week * 5 + day_num + 1}"
        day_data = cells.get(tt_key, {})

        if not day_data:
            # Try all keys to help debug
            available = list(cells.keys())[:5]
            messagebox.showinfo("No Timetable Data",
                                f"No data found for {tt_key}.\nAvailable: {available}")
            return

        added = 0
        existing_starts = {b.start for b in dp.blocks if b.btype == "school"}
        for period, (start_time, duration) in PERIOD_TIMES.items():
            if start_time in existing_starts:
                continue
            cell = day_data.get(period, {})
            if not cell:
                continue
            # cell has "code", "room", "teacher" — convert code to friendly name
            code = cell.get("code", "")
            room = cell.get("room", "")
            try:
                from scraper.parser import _friendly_name
                subj = _friendly_name(code) if code else "School"
            except Exception:
                subj = code or "School"
            note = f"Room {room}" if room else ""
            dp.blocks.append(Block(btype="school", label=subj,
                                   start=start_time, duration=duration, note=note))
            added += 1

        if added == 0:
            messagebox.showinfo("Already Loaded",
                                "Timetable already loaded for this day (or no periods found).")
        else:
            self._save()
            self._refresh_day_view()
            self._select_day(self.selected_day)

    def _add_sleep_quick(self):
        dp = self.day_plans[self.selected_day]
        block = Block(btype="sleep", label="Sleep", start="22:00", duration=9*60, note="")
        dp.blocks.append(block)
        self._save()
        self._refresh_day_view()
        self._select_day(self.selected_day)

    def _add_meals_quick(self):
        dp = self.day_plans[self.selected_day]
        for label, start, dur in [("Breakfast","07:15",20),("Lunch","13:00",30),("Dinner","18:30",30)]:
            dp.blocks.append(Block(btype="meal", label=label, start=start, duration=dur))
        self._save()
        self._refresh_day_view()
        self._select_day(self.selected_day)

    def _add_breaks_quick(self):
        dp = self.day_plans[self.selected_day]
        for start in ["10:30","15:30"]:
            dp.blocks.append(Block(btype="break", label="Break", start=start, duration=15))
        self._save()
        self._refresh_day_view()

    def _clear_day(self):
        dp = self.day_plans[self.selected_day]
        if not dp.blocks: return
        if messagebox.askyesno("Clear Day",
                               f"Remove all {len(dp.blocks)} blocks from {DAYS[self.selected_day]}?"):
            dp.blocks.clear()
            self._save()
            self._refresh_day_view()
            self._select_day(self.selected_day)

    def _clear_all(self):
        total = sum(len(dp.blocks) for dp in self.day_plans)
        if total == 0: return
        if messagebox.askyesno("Clear Entire Fortnight",
                               f"This will remove all {total} blocks across the entire fortnight. Are you sure?"):
            for dp in self.day_plans:
                dp.blocks.clear()
            self._save()
            self._refresh_day_view()
            self._select_day(self.selected_day)

    def _save_confirm(self):
        self._save()
        messagebox.showinfo("Saved", "Planner saved successfully.")

    # ── Goals ─────────────────────────────────────────────────────────────────

    def _edit_goals(self):
        win = tk.Toplevel(self.winfo_toplevel())
        win.title("Goals & Priorities")
        win.configure(bg=BG_DARK)
        win.geometry("480x520")
        win.grab_set()

        tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(win, text="🎯 Goals & Study Priorities",
                 bg=BG_DARK, fg=FG_PRIMARY, font=FONT_HEADING,
                 pady=12).pack()
        tk.Label(win, text="Set which subjects to prioritise. Higher priority = more study time in Auto-Generate.",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL,
                 wraplength=420, justify="center").pack(pady=4)

        scroll = ScrollableFrame(win, bg=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=8)
        area = scroll.inner

        tk.Label(area, text="Subject Priorities (1=Low, 5=Critical)",
                 bg=BG_DARK, fg=ACCENT, font=FONT_LABEL, pady=8).pack(anchor="w")

        sliders = {}
        for subj in self._get_subjects():
            row = tk.Frame(area, bg=BG_CARD,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=subj, bg=BG_CARD, fg=FG_PRIMARY,
                     font=FONT_BODY, padx=12, pady=8,
                     width=22, anchor="w").pack(side="left")
            sv = tk.IntVar(value=self.priorities.get(subj, 3))
            sliders[subj] = sv
            ttk.Scale(row, from_=1, to=5, variable=sv,
                      orient="horizontal", length=150).pack(side="left", padx=8)
            lbl = tk.Label(row, textvariable=sv, bg=BG_CARD, fg=ACCENT,
                           font=("Georgia", 12, "bold"), width=2)
            lbl.pack(side="left")

        tk.Label(area, text="Exam / Assessment Goals",
                 bg=BG_DARK, fg=ACCENT, font=FONT_LABEL, pady=8).pack(anchor="w")
        tk.Label(area, text="e.g. Maths Methods Exam, English SAC",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")

        goals_var = tk.StringVar(value="\n".join(self.goals))
        txt_frame = tk.Frame(area, bg=BG_CARD)
        txt_frame.pack(fill="x", pady=4)
        goals_txt = tk.Text(txt_frame, height=5, bg=BG_CARD, fg=FG_PRIMARY,
                            insertbackground=FG_PRIMARY, font=FONT_BODY,
                            relief="flat", padx=8, pady=6)
        goals_txt.insert("1.0", "\n".join(self.goals))
        goals_txt.pack(fill="x")

        def save_goals():
            self.priorities = {s: sv.get() for s, sv in sliders.items()}
            self.goals = [g.strip() for g in goals_txt.get("1.0","end").splitlines() if g.strip()]
            self._save()
            win.destroy()

        _btn(win, "✓  Save Goals", ACCENT, BG_DARK, save_goals, padx=20, pady=10).pack(pady=10)

    # ── Auto-generate ─────────────────────────────────────────────────────────

    def _auto_generate(self):
        subjects_all = self._get_subjects()
        win = tk.Toplevel(self.winfo_toplevel())
        win.title("Auto-Generate Planner")
        win.configure(bg=BG_DARK)
        win.geometry("560x680")
        win.grab_set()

        tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(win, text="⚡ Auto-Generate Planner",
                 bg=BG_DARK, fg=FG_PRIMARY, font=FONT_HEADING, pady=10).pack()
        tk.Label(win,
                 text="Customise your fortnight schedule below.",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack()

        scroll = ScrollableFrame(win, bg=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=20, pady=8)
        area = scroll.inner

        def section(title):
            tk.Frame(area, bg=BORDER, height=1).pack(fill="x", pady=4)
            tk.Label(area, text=title, bg=BG_DARK, fg=ACCENT,
                     font=("TkDefaultFont", 10, "bold"), pady=4).pack(anchor="w")

        def setting_row(label, tip, widget_fn):
            f = tk.Frame(area, bg=BG_DARK)
            f.pack(fill="x", pady=4)
            lbl = tk.Label(f, text=label, bg=BG_DARK, fg=FG_SEC,
                           font=FONT_LABEL, anchor="w", width=24)
            lbl.pack(side="left")
            w = widget_fn(f)
            w.pack(side="left")
            if tip:
                _tooltip(lbl, tip)
            return w

        # ── Schedule ──────────────────────────────────────────────────────────
        section("🕐 Schedule")
        wake_var  = tk.StringVar(value="07:00")
        sleep_var = tk.StringVar(value="22:00")
        setting_row("Wake time", "What time you wake up each day",
                    lambda f: tk.Entry(f, textvariable=wake_var, bg=BG_CARD,
                                       fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                       relief="flat", font=FONT_BODY, width=8, justify="center"))
        setting_row("Bedtime", "What time you go to sleep",
                    lambda f: tk.Entry(f, textvariable=sleep_var, bg=BG_CARD,
                                       fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                       relief="flat", font=FONT_BODY, width=8, justify="center"))

        # ── Study ─────────────────────────────────────────────────────────────
        section("📚 Study Settings")
        study_h_var      = tk.IntVar(value=2)
        subjects_day_var = tk.IntVar(value=2)
        study_start_var  = tk.StringVar(value="15:30")
        study_gap_var    = tk.IntVar(value=15)

        setting_row("Study hours / school day",
                    "Total hours of study to schedule on each school day",
                    lambda f: ttk.Combobox(f, textvariable=study_h_var,
                                           values=[1,2,3,4,5,6], state="readonly", width=6))
        setting_row("Subjects per day",
                    "How many different subjects to study each day (cycles through selected subjects)",
                    lambda f: ttk.Combobox(f, textvariable=subjects_day_var,
                                           values=[1,2,3,4,5,6], state="readonly", width=6))
        setting_row("Study starts at (weekdays)",
                    "What time after school study sessions begin on weekdays",
                    lambda f: tk.Entry(f, textvariable=study_start_var, bg=BG_CARD,
                                       fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                       relief="flat", font=FONT_BODY, width=8, justify="center"))
        setting_row("Gap between sessions (mins)",
                    "Break time between study blocks",
                    lambda f: ttk.Combobox(f, textvariable=study_gap_var,
                                           values=[0,5,10,15,20,30], state="readonly", width=6))

        # ── Weekend settings ──────────────────────────────────────────────────
        section("📅 Weekend Settings")

        weekend_study_var    = tk.BooleanVar(value=True)
        weekend_h_var        = tk.IntVar(value=3)
        weekend_subs_var     = tk.IntVar(value=3)
        weekend_start_var    = tk.StringVar(value="10:00")
        weekend_gap_var      = tk.IntVar(value=20)
        weekend_sleep_var    = tk.BooleanVar(value=True)
        weekend_sleep_in_var = tk.StringVar(value="08:00")
        weekend_bed_var      = tk.StringVar(value="23:00")
        weekend_free_var     = tk.BooleanVar(value=True)
        weekend_free_h_var   = tk.IntVar(value=2)
        weekend_meals_var    = tk.BooleanVar(value=True)
        saturday_diff_var    = tk.BooleanVar(value=False)

        # Weekend study toggle row
        f_we = tk.Frame(area, bg=BG_DARK)
        f_we.pack(fill="x", pady=4)
        ttk.Checkbutton(f_we, variable=weekend_study_var).pack(side="left")
        tk.Label(f_we, text="Include study on weekends", bg=BG_DARK, fg=FG_SEC,
                 font=FONT_BODY).pack(side="left", padx=8)

        # Weekend detail frame (shown/hidden by toggle)
        we_detail = tk.Frame(area, bg=BG_CARD,
                             highlightbackground=BORDER, highlightthickness=1)
        we_detail.pack(fill="x", pady=4, padx=4)

        def toggle_we_detail():
            if weekend_study_var.get():
                we_detail.pack(fill="x", pady=4, padx=4)
            else:
                we_detail.pack_forget()
        weekend_study_var.trace_add("write", lambda *a: toggle_we_detail())

        def we_row(label, tip, widget_fn):
            f = tk.Frame(we_detail, bg=BG_CARD)
            f.pack(fill="x", padx=12, pady=4)
            lbl = tk.Label(f, text=label, bg=BG_CARD, fg=FG_SEC,
                           font=FONT_SMALL, anchor="w", width=26)
            lbl.pack(side="left")
            w = widget_fn(f)
            w.pack(side="left")
            if tip:
                from ui.planner_page import _tooltip
                _tooltip(lbl, tip)
            return w

        we_row("Study hours per day",
               "Total study hours on each weekend day",
               lambda f: ttk.Combobox(f, textvariable=weekend_h_var,
                                      values=[1,2,3,4,5,6,7,8], state="readonly", width=6))
        we_row("Subjects per day",
               "How many subjects to cycle through each weekend day",
               lambda f: ttk.Combobox(f, textvariable=weekend_subs_var,
                                      values=[1,2,3,4,5,6], state="readonly", width=6))
        we_row("Study starts at",
               "What time study begins on weekends",
               lambda f: tk.Entry(f, textvariable=weekend_start_var, bg=BG_MID,
                                  fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                  relief="flat", font=FONT_BODY, width=8, justify="center"))
        we_row("Gap between sessions (mins)",
               "Break between weekend study blocks",
               lambda f: ttk.Combobox(f, textvariable=weekend_gap_var,
                                      values=[0,5,10,15,20,30], state="readonly", width=6))
        we_row("Sleep in until",
               "Wake-up time on weekends (later than weekdays)",
               lambda f: tk.Entry(f, textvariable=weekend_sleep_in_var, bg=BG_MID,
                                  fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                  relief="flat", font=FONT_BODY, width=8, justify="center"))
        we_row("Bedtime on weekends",
               "Later bedtime allowed on weekends",
               lambda f: tk.Entry(f, textvariable=weekend_bed_var, bg=BG_MID,
                                  fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
                                  relief="flat", font=FONT_BODY, width=8, justify="center"))

        # Checkboxes inside we_detail
        for var, label, tip in [
            (weekend_meals_var, "Add meals on weekends",
             "Include breakfast, lunch, dinner on weekend days"),
            (weekend_free_var, "Add free time on weekends",
             "Add unstructured free time blocks"),
            (saturday_diff_var, "Make Saturday lighter than Sunday",
             "Saturday gets half the study hours of Sunday — a lighter day"),
        ]:
            f = tk.Frame(we_detail, bg=BG_CARD)
            f.pack(fill="x", padx=12, pady=3)
            ttk.Checkbutton(f, variable=var).pack(side="left")
            lbl = tk.Label(f, text=label, bg=BG_CARD, fg=FG_SEC, font=FONT_SMALL)
            lbl.pack(side="left", padx=8)

        we_row("Free time hours",
               "How many hours of free time to add each weekend day",
               lambda f: ttk.Combobox(f, textvariable=weekend_free_h_var,
                                      values=[1,2,3,4,5,6], state="readonly", width=6))

        # ── Subject selection ──────────────────────────────────────────────────
        section("🎯 Subjects to Include")
        tk.Label(area, text="Tick the subjects you want in the generated planner:",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")

        subject_vars = {}
        subj_frame = tk.Frame(area, bg=BG_DARK)
        subj_frame.pack(fill="x", pady=4)
        for i, subj in enumerate(subjects_all):
            var = tk.BooleanVar(value=True)
            subject_vars[subj] = var
            f = tk.Frame(subj_frame, bg=BG_DARK)
            f.grid(row=i//2, column=i%2, sticky="w", padx=4, pady=2)
            ttk.Checkbutton(f, variable=var).pack(side="left")
            tk.Label(f, text=subj, bg=BG_DARK, fg=FG_SEC,
                     font=FONT_SMALL).pack(side="left")
        for c in range(2):
            subj_frame.columnconfigure(c, weight=1)

        # Select / deselect all
        sel_row = tk.Frame(area, bg=BG_DARK)
        sel_row.pack(fill="x", pady=2)
        _btn(sel_row, "Select All",   BG_LIGHT, FG_PRIMARY,
             lambda: [v.set(True) for v in subject_vars.values()],
             padx=8, pady=3).pack(side="left", padx=4)
        _btn(sel_row, "Deselect All", BG_LIGHT, FG_PRIMARY,
             lambda: [v.set(False) for v in subject_vars.values()],
             padx=8, pady=3).pack(side="left")

        # ── After-school activities ───────────────────────────────────────────
        section("🏃 After-School & Weekend Activities")
        tk.Label(area,
                 text="Add regular activities so the planner works around them.\n"
                      "Format: Name, Days (Mon/Tue/Wed/Thu/Fri/Sat/Sun), Start time, Duration (mins)",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL, justify="left").pack(anchor="w")

        activities_list = []
        act_frame = tk.Frame(area, bg=BG_DARK)
        act_frame.pack(fill="x", pady=4)

        def refresh_activities():
            for w in act_frame.winfo_children():
                w.destroy()
            for idx, act in enumerate(activities_list):
                row = tk.Frame(act_frame, bg=BG_CARD,
                               highlightbackground=BORDER, highlightthickness=1)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"  🏃 {act['name']}  ·  {act['days']}  ·  {act['start']}  ·  {act['duration']}min",
                         bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SMALL,
                         padx=8, pady=6, anchor="w").pack(side="left", fill="x", expand=True)
                _btn(row, "✕", "#7f1d1d", "#fca5a5",
                     lambda i=idx: (activities_list.pop(i), refresh_activities()),
                     padx=8, pady=4).pack(side="right", padx=4)

        def add_activity():
            popup = tk.Toplevel(win)
            popup.title("Add Activity")
            popup.configure(bg=BG_DARK)
            popup.geometry("360x280")
            popup.grab_set()
            tk.Frame(popup, bg=ACCENT, height=3).pack(fill="x")
            tk.Label(popup, text="Add After-School Activity",
                     bg=BG_DARK, fg=FG_PRIMARY, font=FONT_LABEL, pady=10).pack()

            fields = {}
            for label, default, tip in [
                ("Activity name",    "Gym",    "e.g. Gym, Football, Music Lessons"),
                ("Days",             "Mon,Wed,Fri", "Comma-separated: Mon,Tue,Wed,Thu,Fri,Sat,Sun"),
                ("Start time",       "16:30",  "24h format e.g. 16:30"),
                ("Duration (mins)",  "60",     "How long in minutes"),
            ]:
                f = tk.Frame(popup, bg=BG_DARK)
                f.pack(fill="x", padx=20, pady=4)
                tk.Label(f, text=label, bg=BG_DARK, fg=FG_SEC,
                         font=FONT_SMALL, width=18, anchor="w").pack(side="left")
                var = tk.StringVar(value=default)
                fields[label] = var
                e = tk.Entry(f, textvariable=var, bg=BG_CARD, fg=FG_PRIMARY,
                             insertbackground=FG_PRIMARY, relief="flat", font=FONT_BODY)
                e.pack(side="left", fill="x", expand=True, ipady=4)
                _tooltip(e, tip)

            def save_act():
                activities_list.append({
                    "name":     fields["Activity name"].get().strip(),
                    "days":     fields["Days"].get().strip(),
                    "start":    fields["Start time"].get().strip(),
                    "duration": int(fields["Duration (mins)"].get().strip() or "60"),
                })
                refresh_activities()
                popup.destroy()

            _btn(popup, "Add", ACCENT, BG_DARK, save_act, padx=16, pady=8).pack(pady=10)

        _btn(area, "＋ Add Activity", BG_LIGHT, FG_PRIMARY,
             add_activity, padx=12, pady=5).pack(anchor="w", pady=4)
        refresh_activities()

        # ── Extras ────────────────────────────────────────────────────────────
        section("➕ Include in Schedule")
        timetable_var = tk.BooleanVar(value=True)
        meals_var     = tk.BooleanVar(value=True)
        breaks_var    = tk.BooleanVar(value=True)
        free_var      = tk.BooleanVar(value=True)
        overwrite_var = tk.BooleanVar(value=False)

        for var, label, tip in [
            (timetable_var, "Load timetable",    "Fill in school periods"),
            (meals_var,     "Add meals",          "Breakfast, lunch, dinner"),
            (breaks_var,    "Add breaks",         "Short breaks between study sessions"),
            (free_var,      "Add free time",      "Free time block in the evening"),
            (overwrite_var, "Overwrite existing", "Clear existing blocks before generating"),
        ]:
            f = tk.Frame(area, bg=BG_DARK)
            f.pack(fill="x", pady=2)
            ttk.Checkbutton(f, variable=var).pack(side="left")
            lbl = tk.Label(f, text=label, bg=BG_DARK, fg=FG_SEC, font=FONT_BODY)
            lbl.pack(side="left", padx=8)
            _tooltip(lbl, tip)

        # ── Generate ──────────────────────────────────────────────────────────
        def generate():
            wake     = wake_var.get().strip()
            bed      = sleep_var.get().strip()
            study_h  = int(study_h_var.get())
            subs_day = int(subjects_day_var.get())
            gap      = int(study_gap_var.get())
            st_start = study_start_var.get().strip()

            # Subjects selected and sorted by priority
            selected = [s for s in subjects_all if subject_vars.get(s, tk.BooleanVar()).get()]
            if not selected:
                messagebox.showwarning("No Subjects", "Please select at least one subject.")
                return
            selected = sorted(selected, key=lambda s: self.priorities.get(s, 3), reverse=True)

            for i, dp in enumerate(self.day_plans):
                if dp.blocks and not overwrite_var.get():
                    continue
                if overwrite_var.get():
                    dp.blocks.clear()

                is_we = DAYS[i] in ("Saturday", "Sunday")
                is_sat = DAYS[i] == "Saturday"

                # Weekend-specific hours (Saturday lighter if option set)
                if is_we:
                    base_we_h = int(weekend_h_var.get())
                    day_we_h  = max(1, base_we_h // 2) if (is_sat and saturday_diff_var.get()) else base_we_h
                    wake_time = weekend_sleep_in_var.get().strip()
                    bed_time  = weekend_bed_var.get().strip()
                else:
                    wake_time = wake
                    bed_time  = bed

                # Sleep
                sleep_mins = (_time_to_mins(wake_time) + 24*60 - _time_to_mins(bed_time)) % (24*60)
                dp.blocks.append(Block("sleep", "Sleep", bed_time, sleep_mins))

                # Meals
                add_meals = (meals_var.get() and not is_we) or (is_we and weekend_meals_var.get())
                if add_meals:
                    bfast = wake_time if is_we else "07:15"
                    for lbl, t, d in [("Breakfast", bfast, 20),("Lunch","13:00",30),("Dinner","18:30",30)]:
                        dp.blocks.append(Block("meal", lbl, t, d))

                # Timetable
                if timetable_var.get() and not is_we and self.timetable:
                    week    = 0 if i < 7 else 1
                    wd_list = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
                    if DAYS[i] in wd_list:
                        day_num  = wd_list.index(DAYS[i])
                        cells    = self.timetable.get("cells", self.timetable)
                        tt_key   = f"Day {week*5 + day_num + 1}"
                        day_data = cells.get(tt_key, {})
                        for period, (start_t, dur) in PERIOD_TIMES.items():
                            cell = day_data.get(period, {})
                            if cell:
                                code = cell.get("code","")
                                try:
                                    from scraper.parser import _friendly_name
                                    subj = _friendly_name(code) if code else "School"
                                except Exception:
                                    subj = code or "School"
                                dp.blocks.append(Block("school", subj, start_t, dur))

                # After-school activities for this day
                day_abbr_map = {"Monday":"Mon","Tuesday":"Tue","Wednesday":"Wed",
                                "Thursday":"Thu","Friday":"Fri","Saturday":"Sat","Sunday":"Sun"}
                today_abbr = day_abbr_map.get(DAYS[i], "")
                for act in activities_list:
                    act_days = [d.strip() for d in act["days"].split(",")]
                    if today_abbr in act_days:
                        dp.blocks.append(Block("activity", act["name"],
                                               act["start"], act["duration"]))

                # Study blocks — cycle through selected subjects, subs_day per day
                # Start after the latest activity if one exists today
                act_end = 0
                for b in dp.blocks:
                    if b.btype == "activity":
                        end = _time_to_mins(b.start) + b.duration
                        act_end = max(act_end, end)
                we_start = weekend_start_var.get().strip() if is_we else st_start
                study_start_base = max(_time_to_mins(we_start), act_end + 15)
                if not is_we or weekend_study_var.get():
                    total_study = (study_h if not is_we else day_we_h) * 60
                    start_m = study_start_base
                    # Pick which subjects to study today (cycle based on day index)
                    day_subs_count = subs_day if not is_we else int(weekend_subs_var.get())
                    day_subjects = []
                    for j in range(day_subs_count):
                        idx = (i * subs_day + j) % len(selected)
                        s = selected[idx]
                        if s not in day_subjects:
                            day_subjects.append(s)
                    # Allocate time proportionally to priority
                    total_priority = sum(self.priorities.get(s, 3) for s in day_subjects) or 1
                    we_gap = int(weekend_gap_var.get()) if is_we else gap
                    for subj in day_subjects:
                        prio  = self.priorities.get(subj, 3)
                        alloc = int(total_study * prio / total_priority)
                        alloc = max(30, min(alloc, total_study))
                        dp.blocks.append(Block("study", f"Study: {subj}",
                                               _mins_to_time(start_m), alloc, subj))
                        start_m += alloc + we_gap

                # Breaks
                if breaks_var.get():
                    times = (["16:30","20:00"] if not is_we else ["11:30","15:30"])
                    for t in times:
                        dp.blocks.append(Block("break","Break", t, 15))

                # Free time
                add_free = (free_var.get() and not is_we) or (is_we and weekend_free_var.get())
                if add_free:
                    free_dur = int(weekend_free_h_var.get()) * 60 if is_we else 60
                    free_start = "14:00" if is_we else "20:30"
                    dp.blocks.append(Block("free","Free Time", free_start, free_dur))

            self._save()
            win.destroy()
            self._select_day(self.selected_day)
            messagebox.showinfo("Done",
                                f"Fortnight generated with {len(selected)} subject(s), "
                                f"{subs_day} per day.\nAdjust individual days as needed.")

        _btn(win, "⚡  Generate Fortnight", ACCENT, BG_DARK,
             generate, padx=20, pady=10).pack(pady=10, side="bottom")

    def _export_png(self):
        """Export all 14 days as a timetable-style PNG grid."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            messagebox.showerror("Missing Library",
                                 "Pillow is required for PNG export.\n"
                                 "Run: .venv/bin/pip install Pillow")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image","*.png")],
            initialfile="study_planner_fortnight.png",
            title="Save Planner as PNG")
        if not path:
            return

        # Layout constants
        DAY_W    = 200   # width per day column
        HEADER_H = 60    # top header height
        TIME_W   = 60    # left time column width
        HOUR_H   = 50    # height per hour
        START_H  = 6     # first hour shown (6am)
        END_H    = 24    # last hour (midnight)
        HOURS    = END_H - START_H
        ROW_H    = HOUR_H * HOURS
        IMG_W    = TIME_W + DAY_W * 14
        IMG_H    = HEADER_H + ROW_H + 20

        BG    = (10, 22, 40)
        CARD  = (22, 45, 85)
        ACC   = (201, 160, 48)
        WHITE = (240, 244, 255)
        MUTED = (74, 96, 128)
        BORD  = (26, 51, 88)

        img  = Image.new("RGB", (IMG_W, IMG_H), BG)
        draw = ImageDraw.Draw(img)

        # Try to load a font, fall back to default
        try:
            font_sm  = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
            font_med = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
            font_hdr = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
        except Exception:
            font_sm = font_med = font_hdr = ImageFont.load_default()

        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2],16) for i in (0,2,4))

        def block_to_px(start_str, duration):
            """Convert block time to y pixel position and height."""
            h, m = map(int, start_str.split(":"))
            y = HEADER_H + int((h - START_H + m/60) * HOUR_H)
            h_px = max(int(duration / 60 * HOUR_H), 14)
            return y, h_px

        # Draw header row
        draw.rectangle([0, 0, IMG_W, HEADER_H], fill=(15, 32, 64))
        draw.text((8, 20), "Study Planner — Fortnight", fill=ACC, font=font_hdr)

        for i in range(14):
            x = TIME_W + i * DAY_W
            week = "W1" if i < 7 else "W2"
            draw.rectangle([x, 0, x + DAY_W - 1, HEADER_H], fill=(15,32,64))
            draw.text((x + 6, 8),  f"{week} {DAY_ABBR[i]}", fill=ACC, font=font_med)
            draw.text((x + 6, 30), f"Day {i+1}", fill=MUTED, font=font_sm)
            draw.line([x, 0, x, IMG_H], fill=BORD, width=1)

        # Draw hour grid lines and labels
        for h in range(HOURS + 1):
            y = HEADER_H + h * HOUR_H
            draw.line([0, y, IMG_W, y], fill=BORD, width=1)
            if h < HOURS:
                time_str = f"{START_H + h:02d}:00"
                draw.text((4, y + 4), time_str, fill=MUTED, font=font_sm)

        # Draw blocks for each day
        for i, dp in enumerate(self.day_plans):
            x = TIME_W + i * DAY_W
            for block in dp.sorted_blocks():
                h_str, m = map(int, block.start.split(":"))
                if h_str < START_H or h_str >= END_H:
                    continue
                y, bh = block_to_px(block.start, block.duration)
                # Clamp to grid
                y  = max(y, HEADER_H)
                bh = min(bh, HEADER_H + ROW_H - y)
                if bh < 4:
                    continue

                col = hex_to_rgb(block.colour())
                draw.rectangle([x+2, y+1, x+DAY_W-3, y+bh-1], fill=col)
                # Left stripe (lighter)
                stripe = tuple(min(255, c+60) for c in col)
                draw.rectangle([x+2, y+1, x+7, y+bh-1], fill=stripe)

                # Text
                label = block.label[:22]
                subj  = block.subject[:18] if block.subject else ""
                time  = f"{block.start}–{block.end_time()}"
                ty = y + 3
                if bh >= 18:
                    draw.text((x+10, ty), label, fill=WHITE, font=font_sm)
                    ty += 13
                if bh >= 32 and subj:
                    draw.text((x+10, ty), subj, fill=(200,220,255), font=font_sm)
                    ty += 13
                if bh >= 46:
                    draw.text((x+10, ty), time, fill=(150,180,220), font=font_sm)

        # Vertical border after time column
        draw.line([TIME_W, 0, TIME_W, IMG_H], fill=ACC, width=2)
        # Top border
        draw.rectangle([0, 0, IMG_W, 3], fill=ACC)

        img.save(path)
        messagebox.showinfo("Exported", f"Planner saved to:\n{path}")
