"""
Study Planner — fully rewritten. Uses tk.Label+bindings instead of tk.Button
to avoid macOS white button rendering bug.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json, os, re
from datetime import date, timedelta
from typing import List, Dict, Optional

from ui.theme import *
from ui.widgets import ScrollableFrame, Card, PageHeader, GoldDivider, SectionTitle, Divider
from scraper.grade_logic import is_formative

PLANNER_FILE = os.path.expanduser("~/.sbc_portal/planner.json")

# (stripe_colour, icon, default_label, default_duration_min)
BLOCK_TYPES = {
    "study":    (ROYAL,    "📚", "Study",      60),
    "sleep":    ("#4a1d96","😴", "Sleep",      480),
    "meal":     (WARNING,  "🍽", "Meal",        30),
    "break":    (SUCCESS,  "☕", "Break",       15),
    "activity": (DANGER,   "🏃", "Activity",    60),
    "free":     (FG_MUTED, "🎮", "Free Time",   60),
    "school":   (TEAL,     "🏫", "School",      50),
    "goal":     (ACCENT,   "🎯", "Goal",         5),
}

SUBJECT_COLOURS = {
    "Mathematics":          ROYAL,
    "English":              "#14532d",
    "Science":              "#713f12",
    "Humanities":           "#831843",
    "Religion & Society":   "#4c1d95",
    "Health & PE":          "#7c2d12",
    "Italian":              "#164e63",
    "Visual Communication": "#4a1d96",
    "Business Management":  "#7f1d1d",
}

# Correct period times from the timetable
PERIOD_TIMES = {
    "Homeroom": ("08:45", 10),
    "Period 1": ("08:55", 50),
    "Period 2": ("09:45", 50),
    "Period 3": ("11:00", 50),
    "Period 4": ("11:50", 50),
    "Period 5": ("13:15", 50),
    "Period 6": ("14:05", 50),
}

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday",
        "Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
DAY_LABELS = [f"{'W1' if i<7 else 'W2'} {DAYS[i][:3]} (Day {i+1})" for i in range(14)]

SLEEP_WARN = 8
SLEEP_MIN  = 6


def _lbl_btn(parent, text, bg, fg, command, font=None, padx=8, pady=5, anchor="center", width=None):
    """A tk.Label that acts as a button — always shows correct colours on macOS."""
    kw = dict(bg=bg, fg=fg, text=text,
               font=font or ("TkDefaultFont", 10, "bold"),
               cursor="hand2", relief="flat",
               padx=padx, pady=pady, anchor=anchor)
    if width:
        kw["width"] = width
    lbl = tk.Label(parent, **kw)
    lbl.bind("<Button-1>", lambda e: command())
    lbl.bind("<Enter>",    lambda e: lbl.configure(bg=_darken(bg)))
    lbl.bind("<Leave>",    lambda e: lbl.configure(bg=bg))
    return lbl


def _tooltip(widget, text):
    tip = None
    def show(e):
        nonlocal tip
        try:
            tip = tk.Toplevel(widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{e.x_root+12}+{e.y_root+6}")
            tk.Label(tip, text=text, bg="#fef9c3", fg="#1a1a1a",
                     font=FONT_SMALL, relief="solid", bd=1,
                     padx=6, pady=3, wraplength=260).pack()
        except Exception: pass
    def hide(e):
        nonlocal tip
        if tip:
            try: tip.destroy()
            except Exception: pass
            tip = None
    widget.bind("<Enter>", show, add="+")
    widget.bind("<Leave>", hide, add="+")


def _darken(hex_color):
    """Return a slightly darker version of a hex colour."""
    try:
        h = hex_color.lstrip("#")
        if len(h) != 6: return hex_color
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        r,g,b = max(0,r-20), max(0,g-20), max(0,b-20)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


class Block:
    def __init__(self, block_type="study", label="", start="08:00",
                 duration=60, subject="", note=""):
        self.block_type = block_type
        self.label      = label
        self.start      = start
        self.duration   = duration
        self.subject    = subject
        self.note       = note

    def end_time(self):
        h, m = map(int, self.start.split(":"))
        total = (h * 60 + m + self.duration) % (24 * 60)
        return f"{total//60:02d}:{total%60:02d}"

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        b = cls()
        b.__dict__.update(d)
        return b


class DayPlan:
    def __init__(self, i):
        self.day_index = i
        self.blocks: List[Block] = []
        self.notes = ""

    def sleep_hours(self):
        return sum(b.duration for b in self.blocks if b.block_type=="sleep") / 60

    def study_hours(self):
        return sum(b.duration for b in self.blocks if b.block_type=="study") / 60

    def sleep_warning(self):
        h = self.sleep_hours()
        if h == 0: return None
        if h < SLEEP_MIN:  return f"⚠ Only {h:.1f}h sleep — dangerously low!"
        if h < SLEEP_WARN: return f"⚠ {h:.1f}h sleep — aim for {SLEEP_WARN}h+"
        return None

    def to_dict(self):
        return {"day_index": self.day_index,
                "blocks": [b.to_dict() for b in self.blocks],
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
        self.data       = data
        self.session    = session
        self.day_plans  = [DayPlan(i) for i in range(14)]
        self.goals      = []
        self.priorities = {}
        self.activities = []
        self.timetable  = {}
        self.selected_day = 0
        self._load_timetable()
        self._load_saved()
        self._build()

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
                self.activities = d.get("activities", [])
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
                           "priorities": self.priorities,
                           "activities": self.activities}, f, indent=2)
        except Exception:
            pass

    def _get_subjects(self) -> List[str]:
        if not self.data:
            return list(SUBJECT_COLOURS.keys())
        import datetime
        current_year = datetime.datetime.now().year
        subjects = set()
        for yr, subs in self.data.subjects_by_year.items():
            if yr == current_year:
                for s in subs:
                    if s.name and "Assembly" not in s.name and "Home Room" not in s.name:
                        subjects.add(s.name)
        return sorted(subjects) if subjects else list(SUBJECT_COLOURS.keys())

    def _build(self):
        # ── Header ────────────────────────────────────────────────────
        hdr = PageHeader(self, "Study Planner",
                         subtitle="14-day fortnight · Timetable integrated")
        hdr.pack(fill="x")

        btn_f = tk.Frame(hdr.right_frame, bg=BG_MID)
        btn_f.pack()

        for text, cmd, tip, colour in [
            ("⚡ Auto-Generate", self._auto_generate, "Auto-fill based on due dates & priorities", ACCENT),
            ("🎯 Goals",         self._edit_goals,    "Set exam goals and subject priorities",      BG_LIGHT),
            ("💾 Save",          self._save_confirm,  "Save planner to disk",                       BG_LIGHT),
            ("📸 Export PNG",    self._export_png,    "Save planner as a PNG image",                BG_LIGHT),
        ]:
            fg = BG_DARK if colour == ACCENT else FG_PRIMARY
            b = _lbl_btn(btn_f, text, colour, fg, cmd, padx=10, pady=5)
            b.pack(side="left", padx=3)
            _tooltip(b, tip)

        GoldDivider(self).pack(fill="x")

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True)

        # ── Left: day selector ────────────────────────────────────────
        left = tk.Frame(body, bg=BG_MID, width=170)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Frame(left, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(left, text="WEEK 1", bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 8, "bold"),
                 padx=12, pady=6, anchor="w").pack(fill="x")

        self.day_buttons = []
        for i in range(14):
            if i == 7:
                tk.Frame(left, bg=ACCENT, height=1).pack(fill="x", padx=8)
                tk.Label(left, text="WEEK 2", bg=BG_MID, fg=ACCENT,
                         font=("TkDefaultFont", 8, "bold"),
                         padx=12, pady=6, anchor="w").pack(fill="x")
            is_we = DAYS[i] in ("Saturday","Sunday")
            fg_col = FG_MUTED if is_we else FG_SEC
            lbl = tk.Label(left, text=f"  {DAY_LABELS[i]}",
                           bg=BG_MID, fg=fg_col,
                           font=("TkDefaultFont", 9),
                           anchor="w", padx=8, pady=6,
                           cursor="hand2")
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, idx=i: self._select_day(idx))
            lbl.bind("<Enter>",    lambda e, l=lbl: l.configure(bg=BG_LIGHT))
            lbl.bind("<Leave>",    lambda e, l=lbl, idx=DAYS.index(DAYS[i]):
                     l.configure(bg=ACCENT if self.selected_day == i else BG_MID))
            self.day_buttons.append(lbl)

        # ── Centre: day view ──────────────────────────────────────────
        centre = tk.Frame(body, bg=BG_DARK)
        centre.pack(side="left", fill="both", expand=True)

        self.day_header = tk.Label(centre, text="",
                                   bg=BG_MID, fg=FG_PRIMARY,
                                   font=("Georgia", 13, "bold"),
                                   anchor="w", padx=16, pady=10)
        self.day_header.pack(fill="x")

        self.warn_lbl = tk.Label(centre, text="",
                                 bg=BG_DARK, fg=DANGER,
                                 font=("TkDefaultFont", 9, "bold"),
                                 anchor="w", padx=16)
        self.warn_lbl.pack(fill="x")

        self.blocks_scroll = ScrollableFrame(centre, bg=BG_DARK)
        self.blocks_scroll.pack(fill="both", expand=True)
        self.blocks_area = self.blocks_scroll.inner

        # ── Right: tools ──────────────────────────────────────────────
        right = tk.Frame(body, bg=BG_MID, width=230)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        tk.Frame(right, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(right, text="ADD BLOCK", bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 8, "bold"),
                 padx=12, pady=8, anchor="w").pack(fill="x")
        self._build_tools(right)
        self._select_day(0)

    def _build_tools(self, parent):
        sp = tk.Frame(parent, bg=BG_MID)
        sp.pack(fill="x", padx=12)

        # Block type selector — label buttons with visible colours
        tk.Label(sp, text="Block type:", bg=BG_MID, fg=FG_SEC,
                 font=FONT_SMALL).pack(anchor="w", pady=2)

        self.block_type_var = tk.StringVar(value="study")
        self._type_btns = {}

        for btype, (stripe, icon, deflabel, defdur) in BLOCK_TYPES.items():
            # Use a contrasting text colour based on stripe brightness
            btn_fg = BG_DARK if stripe in (ACCENT, WARNING, SUCCESS, "#c9a030") else FG_PRIMARY
            btn = tk.Label(sp,
                           text=f"{icon}  {btype.title()}",
                           bg=BG_CARD, fg=FG_PRIMARY,
                           font=("TkDefaultFont", 9, "bold"),
                           anchor="w", padx=8, pady=5,
                           cursor="hand2", relief="flat")
            btn.pack(fill="x", pady=1)
            btn.bind("<Button-1>", lambda e, t=btype: self._set_type(t))
            btn.bind("<Enter>",    lambda e, b=btn, t=btype: b.configure(
                bg=BLOCK_TYPES[t][0], fg=BG_DARK if BLOCK_TYPES[t][0] in (ACCENT,WARNING,SUCCESS) else FG_PRIMARY))
            btn.bind("<Leave>",    lambda e, b=btn, t=btype: b.configure(
                bg=BLOCK_TYPES[t][0] if self.block_type_var.get()==t else BG_CARD,
                fg=BG_DARK if self.block_type_var.get()==t and BLOCK_TYPES[t][0] in (ACCENT,WARNING,SUCCESS) else FG_PRIMARY))
            self._type_btns[btype] = btn
            _tooltip(btn, {"study":"Study session for a subject",
                           "sleep":"Sleep time — app warns if under 8h",
                           "meal":"Breakfast, lunch or dinner",
                           "break":"Short rest between sessions",
                           "activity":"Gym, sport, music etc",
                           "free":"Unstructured free time",
                           "school":"Class from timetable",
                           "goal":"Exam/assessment goal milestone"}.get(btype,""))

        tk.Frame(sp, bg=BORDER, height=1).pack(fill="x", pady=8)

        # Input fields
        tk.Label(sp, text="Label:", bg=BG_MID, fg=FG_SEC, font=FONT_SMALL).pack(anchor="w", pady=1)
        self.lbl_var = tk.StringVar()
        tk.Entry(sp, textvariable=self.lbl_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=ACCENT, font=FONT_SMALL,
                 relief="flat", bd=0).pack(fill="x", ipady=5)

        tk.Label(sp, text="Subject:", bg=BG_MID, fg=FG_SEC, font=FONT_SMALL).pack(anchor="w", pady=1)
        self.subj_var = tk.StringVar()
        subj_cb = ttk.Combobox(sp, textvariable=self.subj_var,
                                values=[""] + self._get_subjects(),
                                state="readonly", width=24)
        subj_cb.pack(fill="x")
        _tooltip(subj_cb, "Pick subject for study blocks")

        tk.Label(sp, text="Start (HH:MM):", bg=BG_MID, fg=FG_SEC, font=FONT_SMALL).pack(anchor="w", pady=1)
        self.start_var = tk.StringVar(value="08:00")
        tk.Entry(sp, textvariable=self.start_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=ACCENT, font=FONT_SMALL,
                 relief="flat", bd=0, width=8).pack(anchor="w", ipady=5)
        _tooltip(sp, "24h format, e.g. 14:30")

        tk.Label(sp, text="Duration (min):", bg=BG_MID, fg=FG_SEC, font=FONT_SMALL).pack(anchor="w", pady=1)
        self.dur_var = tk.IntVar(value=60)
        dur_row = tk.Frame(sp, bg=BG_MID)
        dur_row.pack(fill="x")
        ttk.Scale(dur_row, from_=15, to=480, variable=self.dur_var,
                  orient="horizontal").pack(fill="x")
        self.dur_lbl = tk.Label(dur_row, textvariable=self.dur_var,
                                bg=BG_MID, fg=ACCENT,
                                font=("Georgia", 12, "bold"))
        self.dur_lbl.pack()

        tk.Label(sp, text="Note:", bg=BG_MID, fg=FG_SEC, font=FONT_SMALL).pack(anchor="w", pady=1)
        self.note_var = tk.StringVar()
        tk.Entry(sp, textvariable=self.note_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=ACCENT, font=FONT_SMALL,
                 relief="flat", bd=0).pack(fill="x", ipady=4)

        # Add block button
        add = _lbl_btn(sp, "+ Add Block", ACCENT, BG_DARK, self._add_block,
                       font=("Georgia", 11, "bold"), padx=0, pady=10, anchor="center")
        add.pack(fill="x", pady=4)
        _tooltip(add, "Add this block to the current day")

        # Load timetable
        tt = _lbl_btn(sp, "📅 Load Timetable", BG_CARD, FG_PRIMARY,
                      self._load_timetable_day, padx=0, pady=7, anchor="center")
        tt.pack(fill="x", pady=2)
        _tooltip(tt, "Pre-fill today with your class schedule from the timetable")

        tk.Frame(sp, bg=BORDER, height=1).pack(fill="x", pady=8)
        tk.Label(sp, text="DAY SUMMARY", bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 8, "bold")).pack(anchor="w")
        self.stats_lbl = tk.Label(sp, text="",
                                  bg=BG_MID, fg=FG_SEC,
                                  font=FONT_SMALL, justify="left",
                                  anchor="w", wraplength=200)
        self.stats_lbl.pack(anchor="w", pady=4)

        # Activate study type
        self._set_type("study")

    def _set_type(self, btype):
        self.block_type_var.set(btype)
        stripe, icon, deflabel, defdur = BLOCK_TYPES[btype]
        btn_fg = BG_DARK if stripe in (ACCENT, WARNING, SUCCESS) else FG_PRIMARY

        for t, btn in self._type_btns.items():
            if t == btype:
                btn.configure(bg=BLOCK_TYPES[t][0], fg=btn_fg)
            else:
                btn.configure(bg=BG_CARD, fg=FG_PRIMARY)

        self.lbl_var.set(deflabel)
        self.dur_var.set(defdur)

    # ── Day view ──────────────────────────────────────────────────────

    def _select_day(self, idx):
        self.selected_day = idx
        for i, btn in enumerate(self.day_buttons):
            is_we = DAYS[i] in ("Saturday","Sunday")
            if i == idx:
                btn.configure(bg=ACCENT, fg=BG_DARK,
                              font=("TkDefaultFont", 9, "bold"))
            else:
                btn.configure(bg=BG_MID,
                              fg=FG_MUTED if is_we else FG_SEC,
                              font=("TkDefaultFont", 9))
        self._refresh_day()

    def _refresh_day(self):
        plan = self.day_plans[self.selected_day]
        self.day_header.configure(
            text=f"  {DAY_LABELS[self.selected_day]}  —  {DAYS[self.selected_day]}")
        self.warn_lbl.configure(text=plan.sleep_warning() or "")

        try:
            for w in self.blocks_area.winfo_children():
                w.destroy()
        except Exception:
            return

        if not plan.blocks:
            tk.Label(self.blocks_area,
                     text="No blocks yet.\nUse the tools on the right to add blocks,\nor click '📅 Load Timetable' to auto-fill your classes.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY,
                     justify="center").pack(pady=40)
        else:
            for block in sorted(plan.blocks, key=lambda b: b.start):
                self._block_card(plan, block)

        study_h  = plan.study_hours()
        sleep_h  = plan.sleep_hours()
        school_h = sum(b.duration for b in plan.blocks if b.block_type=="school") / 60
        total_h  = sum(b.duration for b in plan.blocks) / 60
        self.stats_lbl.configure(
            text=f"📚 Study: {study_h:.1f}h\n"
                 f"🏫 School: {school_h:.1f}h\n"
                 f"😴 Sleep: {sleep_h:.1f}h\n"
                 f"⏱ Total: {total_h:.1f}h")

    def _block_card(self, plan: DayPlan, block: Block):
        btype = block.block_type
        stripe_col, icon, _, _ = BLOCK_TYPES.get(btype, (BORDER, "•", "", 60))

        if btype == "study" and block.subject:
            stripe_col = SUBJECT_COLOURS.get(block.subject, ROYAL)

        card = tk.Frame(self.blocks_area, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=12, pady=2)

        # Left colour stripe
        tk.Frame(card, bg=stripe_col, width=5).pack(side="left", fill="y")

        body = tk.Frame(card, bg=BG_CARD)
        body.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # Top row: time + delete
        top = tk.Frame(body, bg=BG_CARD)
        top.pack(fill="x")

        h, m = divmod(block.duration, 60)
        dur_str = (f"{h}h{m:02d}m" if h and m else f"{h}h" if h else f"{m}m")
        tk.Label(top, text=f"{block.start}–{block.end_time()}  ({dur_str})",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=("TkDefaultFont", 8)).pack(side="left")

        del_lbl = tk.Label(top, text="  ✕  ",
                           bg=BG_CARD, fg=FG_MUTED,
                           font=("TkDefaultFont", 9),
                           cursor="hand2")
        del_lbl.pack(side="right")
        del_lbl.bind("<Button-1>", lambda e, b=block: self._delete_block(plan, b))
        del_lbl.bind("<Enter>", lambda e: del_lbl.configure(fg=DANGER))
        del_lbl.bind("<Leave>", lambda e: del_lbl.configure(fg=FG_MUTED))

        # Title
        name = block.label or btype.title()
        subj = block.subject or ""
        # Avoid "English — English" duplication
        if subj and subj.lower() not in name.lower():
            title = f"{icon}  {name} — {subj}"
        else:
            title = f"{icon}  {name}"

        tk.Label(body, text=title, bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w", pady=0)

        if block.note:
            tk.Label(body, text=block.note, bg=BG_CARD, fg=FG_SEC,
                     font=("TkDefaultFont", 9, "italic"), anchor="w").pack(fill="x")

    def _add_block(self):
        plan    = self.day_plans[self.selected_day]
        btype   = self.block_type_var.get()
        label   = self.lbl_var.get().strip()
        subject = self.subj_var.get().strip()
        start   = self.start_var.get().strip()
        dur     = self.dur_var.get()
        note    = self.note_var.get().strip()

        if not re.match(r"^\d{1,2}:\d{2}$", start):
            messagebox.showerror("Invalid time", "Enter time as HH:MM (e.g. 08:30)")
            return

        h, m = start.split(":")
        start = f"{int(h):02d}:{int(m):02d}"

        block = Block(block_type=btype,
                      label=label or BLOCK_TYPES[btype][2],
                      start=start, duration=dur,
                      subject=subject, note=note)
        plan.blocks.append(block)

        # Advance start time
        h2, m2 = map(int, start.split(":"))
        nxt = (h2*60 + m2 + dur) % (24*60)
        self.start_var.set(f"{nxt//60:02d}:{nxt%60:02d}")

        self._refresh_day()
        self._save()

    def _delete_block(self, plan, block):
        if block in plan.blocks:
            plan.blocks.remove(block)
        self._refresh_day()
        self._save()

    def _load_timetable_day(self):
        plan = self.day_plans[self.selected_day]
        
        tt_day  = f"Day {(self.selected_day % 10) + 1}"
        cells   = {}
        periods = []
        
        if self.timetable and self.timetable.get("days"):
            cells   = self.timetable.get("cells", {}).get(tt_day, {})
            periods = self.timetable.get("periods", [])
        
        # If no timetable cached, still create blocks using PERIOD_TIMES order
        if not cells:
            messagebox.showinfo("No Timetable Cache",
                                f"No cached timetable found for {tt_day}.\n"
                                "Run probe_timetable.py to cache your timetable,\n"
                                "then restart the app.")
            return

        # Remove existing school blocks
        plan.blocks = [b for b in plan.blocks if b.block_type != "school"]

        added = 0
        for p in periods:
            lbl  = p["label"]
            cell = cells.get(lbl)
            if not cell:
                continue

            # Parse start time from timetable data (works for any user/school)
            lbl_norm = lbl.strip()
            start_t  = ""
            dur      = 50

            # Primary: use actual time string from parsed timetable
            time_str = p.get("time", "")
            if time_str:
                import re as _re
                tm = _re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)?", time_str, _re.I)
                if tm:
                    h, mn = int(tm.group(1)), int(tm.group(2))
                    suffix = (tm.group(3) or "").lower()
                    if suffix == "pm" and h != 12: h += 12
                    elif suffix == "am" and h == 12: h = 0
                    start_t = f"{h:02d}:{mn:02d}"
                    end_m = _re.search(r"[\u2013\-](\d{1,2}):(\d{2})\s*(am|pm)?", time_str, _re.I)
                    if end_m:
                        eh, emn = int(end_m.group(1)), int(end_m.group(2))
                        esuffix = (end_m.group(3) or "").lower()
                        if esuffix == "pm" and eh != 12: eh += 12
                        dur = max(5, (eh*60+emn) - (h*60+mn))

            # Fallback: hardcoded SBC period times
            if not start_t:
                start_t, dur = PERIOD_TIMES.get(lbl_norm, ("", 50))
            if not start_t:
                import re as _re2
                m2 = _re2.search(r"(?:Period|P)\s*([1-6])", lbl_norm, _re2.I)
                if m2:
                    start_t, dur = PERIOD_TIMES.get(f"Period {m2.group(1)}", ("08:00", 50))
                elif _re2.search(r"homeroom|home room", lbl_norm, _re2.I):
                    start_t, dur = PERIOD_TIMES.get("Homeroom", ("08:45", 10))
            if not start_t:
                start_t = "08:00"
                start_t = "08:00"

            plan.blocks.append(Block(
                block_type="school",
                label=cell["name"],
                start=start_t,
                duration=dur,
                subject=cell["name"],
                note=f"Room {cell.get('room','')} · {cell.get('teacher','')}",
            ))
            added += 1

        self._refresh_day()
        self._save()
        messagebox.showinfo("Done", f"Loaded {added} classes for {tt_day} with correct times.")

    # ── Export PNG ────────────────────────────────────────────────────

    def _export_png(self):
        """Render the current day's plan as a PNG file."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            messagebox.showerror("Missing library",
                                 "Pillow is required for PNG export.\n"
                                 "Run: pip3 install Pillow --break-system-packages")
            return

        plan  = self.day_plans[self.selected_day]
        title = f"{DAY_LABELS[self.selected_day]} — {DAYS[self.selected_day]}"
        blocks = sorted(plan.blocks, key=lambda b: b.start)

        # Canvas
        W, ROW_H, PAD = 700, 70, 20
        H = PAD*2 + 60 + len(blocks)*ROW_H + 20
        img = Image.new("RGB", (W, H), color="#0a1628")
        draw = ImageDraw.Draw(img)

        # Title bar
        draw.rectangle([0, 0, W, 50], fill="#0f2040")
        draw.rectangle([0, 50, W, 53], fill="#c9a030")  # gold stripe
        draw.text((PAD, 12), f"Study Planner — {title}", fill="#f0f4ff",
                  font=ImageFont.load_default())
        draw.text((PAD, 30), f"St Bernard's College  ·  {date.today().strftime('%d %B %Y')}",
                  fill="#8da4cc", font=ImageFont.load_default())

        y = 65
        for block in blocks:
            stripe_col, icon, _, _ = BLOCK_TYPES.get(block.block_type, (BORDER, "•", "", 60))
            if block.block_type == "study" and block.subject:
                stripe_col = SUBJECT_COLOURS.get(block.subject, ROYAL)

            # Convert hex to RGB
            def h2rgb(h):
                h = h.lstrip("#")
                return tuple(int(h[i:i+2], 16) for i in (0,2,4))

            # Card background
            draw.rectangle([PAD, y, W-PAD, y+ROW_H-4], fill="#162d55")
            # Stripe
            draw.rectangle([PAD, y, PAD+5, y+ROW_H-4], fill=h2rgb(stripe_col))
            # Time
            draw.text((PAD+12, y+6), f"{block.start}–{block.end_time()}",
                      fill="#8da4cc", font=ImageFont.load_default())
            # Title
            name = block.label or block.block_type.title()
            subj = block.subject or ""
            title_text = f"{name} — {subj}" if subj and subj.lower() not in name.lower() else name
            draw.text((PAD+12, y+22), f"{icon} {title_text}",
                      fill="#f0f4ff", font=ImageFont.load_default())
            if block.note:
                draw.text((PAD+12, y+40), block.note,
                          fill="#8da4cc", font=ImageFont.load_default())
            y += ROW_H

        # Save
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            initialfile=f"study_plan_{self.selected_day+1}.png",
            title="Save Planner as PNG",
        )
        if path:
            img.save(path)
            messagebox.showinfo("Saved", f"Saved to:\n{path}")

    # ── Goals ─────────────────────────────────────────────────────────

    def _edit_goals(self):
        win = tk.Toplevel(self)
        win.title("Goals & Priorities")
        win.configure(bg=BG_DARK)
        win.geometry("500x580")
        tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(win, text="Goals & Subject Priorities",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=("Georgia", 14, "bold"),
                 padx=16, pady=12).pack(anchor="w")

        scroll = ScrollableFrame(win, bg=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16)
        area = scroll.inner

        SectionTitle(area, "Exam / Assessment Goals").pack(anchor="w", pady=2)
        tk.Label(area, text="e.g. 'Score 90%+ in Maths exam'",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")

        gf = tk.Frame(area, bg=BG_DARK)
        gf.pack(fill="x", pady=4)
        g_var = tk.StringVar()
        tk.Entry(gf, textvariable=g_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=ACCENT, font=FONT_SMALL,
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True, ipady=5, padx=(0,6))

        goals_lf = tk.Frame(area, bg=BG_DARK)
        goals_lf.pack(fill="x")

        def rg():
            for w in goals_lf.winfo_children(): w.destroy()
            for i, g in enumerate(self.goals):
                row = tk.Frame(goals_lf, bg=BG_CARD,
                               highlightbackground=BORDER, highlightthickness=1)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"🎯  {g}", bg=BG_CARD, fg=FG_PRIMARY,
                         font=FONT_BODY, anchor="w", padx=10, pady=5).pack(side="left")
                dl = tk.Label(row, text=" ✕ ", bg=BG_CARD, fg=DANGER,
                              font=FONT_SMALL, cursor="hand2")
                dl.pack(side="right", padx=6)
                dl.bind("<Button-1>", lambda e, idx=i: (self.goals.pop(idx), rg()))

        def ag():
            g = g_var.get().strip()
            if g:
                self.goals.append(g)
                g_var.set("")
                rg()

        add_g = _lbl_btn(gf, "+ Add", ACCENT, BG_DARK, ag, padx=10, pady=4)
        add_g.pack(side="left")
        tk.Entry(gf, textvariable=g_var).bind("<Return>", lambda e: ag())
        rg()

        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", pady=10)
        SectionTitle(area, "Subject Priority (affects auto-generate)").pack(anchor="w", pady=4)
        tk.Label(area, text="Higher priority = more study time allocated",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w", pady=8)

        pri_labels = {1:"Low",2:"Below Avg",3:"Average",4:"High",5:"Critical"}
        for subj in self._get_subjects():
            pf = tk.Frame(area, bg=BG_DARK)
            pf.pack(fill="x", pady=2)
            tk.Label(pf, text=subj, bg=BG_DARK, fg=FG_PRIMARY,
                     font=("TkDefaultFont",10), width=24, anchor="w").pack(side="left")
            pv = tk.IntVar(value=self.priorities.get(subj, 3))
            pl = tk.Label(pf, text=pri_labels[pv.get()], bg=BG_DARK, fg=ACCENT,
                          font=("TkDefaultFont",9,"bold"), width=10)
            pl.pack(side="right")
            def on_ch(val, s=subj, v=pv, l=pl):
                iv = max(1,min(5,round(float(val))))
                self.priorities[s] = iv
                l.configure(text=pri_labels[iv])
            ttk.Scale(pf, from_=1, to=5, variable=pv, orient="horizontal",
                      length=100, command=on_ch).pack(side="left", padx=6)

        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", pady=10)
        SectionTitle(area, "Recurring After-School Activities").pack(anchor="w")
        af = tk.Frame(area, bg=BG_DARK)
        af.pack(fill="x", pady=4)
        an_v=tk.StringVar(); at_v=tk.StringVar(value="17:00")
        ad_v=tk.IntVar(value=60); aw_v=tk.StringVar(value="Mon,Wed,Fri")
        for l2,v2,w2 in [("Name",an_v,12),("Time",at_v,6),("Mins",ad_v,4),("Days",aw_v,12)]:
            ff=tk.Frame(af,bg=BG_DARK); ff.pack(side="left",padx=3)
            tk.Label(ff,text=l2,bg=BG_DARK,fg=FG_MUTED,font=FONT_SMALL).pack()
            tk.Entry(ff,textvariable=v2,bg=BG_CARD,fg=FG_PRIMARY,
                     font=FONT_SMALL,relief="flat",bd=0,width=w2).pack(ipady=4)
        act_lf = tk.Frame(area, bg=BG_DARK); act_lf.pack(fill="x")
        def ra():
            for w in act_lf.winfo_children(): w.destroy()
            for i,a in enumerate(self.activities):
                row=tk.Frame(act_lf,bg=BG_CARD,highlightbackground=BORDER,highlightthickness=1)
                row.pack(fill="x",pady=1)
                tk.Label(row,text=f"🏃 {a['name']}  {a['time']}  {a['duration']}min  [{a['days']}]",
                         bg=BG_CARD,fg=FG_PRIMARY,font=FONT_SMALL,padx=10,pady=4).pack(side="left")
                dl=tk.Label(row,text=" ✕ ",bg=BG_CARD,fg=DANGER,font=FONT_SMALL,cursor="hand2")
                dl.pack(side="right",padx=6)
                dl.bind("<Button-1>",lambda e,idx=i:(self.activities.pop(idx),ra()))
        def aa():
            n=an_v.get().strip()
            if n:
                self.activities.append({"name":n,"time":at_v.get(),"duration":ad_v.get(),"days":aw_v.get()})
                an_v.set(""); ra()
        add_a=_lbl_btn(af,"+ Add",ACCENT,BG_DARK,aa,padx=10,pady=4)
        add_a.pack(side="left",padx=4)
        ra()

        _lbl_btn(win, "Save & Close", ACCENT, BG_DARK,
                 lambda: (self._save(), win.destroy()),
                 font=("Georgia",11,"bold"), padx=16, pady=8).pack(pady=12)

    # ── Auto-generate ─────────────────────────────────────────────────

    def _auto_generate(self):
        win = tk.Toplevel(self)
        win.title("Auto-Generate")
        win.configure(bg=BG_DARK)
        win.geometry("400x400")
        tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(win, text="⚡ Auto-Generate Study Plan",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=("Georgia", 13, "bold"),
                 padx=16, pady=12).pack(anchor="w")

        area = tk.Frame(win, bg=BG_DARK)
        area.pack(fill="both", expand=True, padx=20)

        wake_v=tk.StringVar(value="07:00"); bed_v=tk.StringVar(value="22:30")
        study_v=tk.IntVar(value=3)
        meal_v=tk.BooleanVar(value=True); brk_v=tk.BooleanVar(value=True)
        act_v=tk.BooleanVar(value=True);  clr_v=tk.BooleanVar(value=False)

        for lbl3, var3, tip3 in [("Wake up:  ", wake_v, "e.g. 07:00"),
                                   ("Bedtime:  ", bed_v,  "e.g. 22:30")]:
            ff=tk.Frame(area,bg=BG_DARK); ff.pack(fill="x",pady=4)
            tk.Label(ff,text=lbl3,bg=BG_DARK,fg=FG_SEC,font=FONT_SMALL,width=12,anchor="w").pack(side="left")
            tk.Entry(ff,textvariable=var3,bg=BG_CARD,fg=FG_PRIMARY,
                     insertbackground=ACCENT,font=FONT_SMALL,relief="flat",bd=0,width=8).pack(side="left",ipady=5)

        ff2=tk.Frame(area,bg=BG_DARK); ff2.pack(fill="x",pady=4)
        tk.Label(ff2,text="Study h/day:",bg=BG_DARK,fg=FG_SEC,font=FONT_SMALL,width=12,anchor="w").pack(side="left")
        ttk.Scale(ff2,from_=1,to=8,variable=study_v,orient="horizontal",length=100).pack(side="left")
        tk.Label(ff2,textvariable=study_v,bg=BG_DARK,fg=ACCENT,font=("Georgia",12,"bold"),width=3).pack(side="left")

        for lbl4,var4 in [("Include meals",meal_v),("Include breaks",brk_v),
                           ("Include activities",act_v),("Clear existing",clr_v)]:
            tk.Checkbutton(area,text=lbl4,variable=var4,bg=BG_DARK,fg=FG_PRIMARY,
                           selectcolor=BG_CARD,activebackground=BG_DARK,
                           font=FONT_SMALL,cursor="hand2").pack(anchor="w",pady=2)

        def go():
            self._run_autogen(wake_v.get(),bed_v.get(),study_v.get(),
                              meal_v.get(),brk_v.get(),act_v.get(),clr_v.get())
            win.destroy()
            self._select_day(self.selected_day)

        _lbl_btn(win,"⚡ Generate",ACCENT,BG_DARK,go,
                 font=("Georgia",12,"bold"),padx=0,pady=10).pack(fill="x",padx=20,pady=14)

    def _run_autogen(self, wake, bedtime, study_h, meals, breaks, acts, clear):
        def t2m(t):
            h,m=map(int,t.split(":")); return h*60+m
        def m2t(m):
            m=m%(24*60); return f"{m//60:02d}:{m%60:02d}"

        wake_m=t2m(wake); bed_m=t2m(bedtime)
        sleep_m=(24*60-bed_m)+wake_m
        subjects=self._get_subjects()
        total_w=sum(self.priorities.get(s,3) for s in subjects) or 1

        for idx in range(14):
            plan=self.day_plans[idx]
            if clear: plan.blocks=[]
            is_we=DAYS[idx] in ("Saturday","Sunday")
            cursor=wake_m

            if not is_we and self.timetable.get("days"):
                tt_day=f"Day {(idx%10)+1}"
                cells=self.timetable.get("cells",{}).get(tt_day,{})
                existing={b.start for b in plan.blocks if b.block_type=="school"}
                for p in self.timetable.get("periods",[]):
                    cell=cells.get(p["label"])
                    if not cell: continue
                    lbl=p["label"]
                    # Robust period lookup - try direct, then by number
                    start_t, dur = PERIOD_TIMES.get(lbl, ("", 50))
                    if not start_t:
                        m2 = re.search(r"(?:Period|P)\s*([1-6])", lbl, re.I)
                        if m2:
                            start_t, dur = PERIOD_TIMES.get(f"Period {m2.group(1)}", ("08:00", 50))
                        elif "homeroom" in lbl.lower():
                            start_t, dur = PERIOD_TIMES["Homeroom"]
                        else:
                            start_t = "08:00"
                    if start_t not in existing:
                        plan.blocks.append(Block("school",cell["name"],start_t,dur,
                                                  cell["name"],f"Room {cell.get('room','')}"))
                cursor=t2m("15:10")

            if meals:
                for name,st,dur in [("Breakfast",wake_m+10,20),("Lunch",12*60+30,30),("Dinner",18*60,30)]:
                    if st>=wake_m and not any(b.label==name for b in plan.blocks):
                        plan.blocks.append(Block("meal",name,m2t(st),dur))

            if acts:
                dn=DAYS[idx][:3]
                for a in self.activities:
                    adays=[x.strip()[:3] for x in a["days"].split(",")]
                    if dn in adays and not any(b.label==a["name"] for b in plan.blocks):
                        plan.blocks.append(Block("activity",a["name"],a["time"],int(a["duration"])))

            budget=study_h*60; study_start=max(cursor,t2m("16:00"))
            for subj in sorted(subjects,key=lambda s:-self.priorities.get(s,3)):
                if budget<=0 or study_start>=bed_m-30: break
                w=self.priorities.get(subj,3)
                alloc=max(30,min(int(w/total_w*study_h*60),120))
                if not any(b.subject==subj and b.block_type=="study" for b in plan.blocks):
                    plan.blocks.append(Block("study",f"Study: {subj}",m2t(study_start),
                                             min(alloc,bed_m-study_start-30),subj,"Auto-generated"))
                    study_start+=alloc
                    if breaks:
                        plan.blocks.append(Block("break","Break",m2t(study_start),15))
                        study_start+=15
                    budget-=alloc

            if not any(b.block_type=="sleep" for b in plan.blocks):
                plan.blocks.append(Block("sleep","Sleep",bedtime,sleep_m))

        self._save()
        messagebox.showinfo("Done","Plan generated for all 14 days!")

    def _save_confirm(self):
        self._save()
        messagebox.showinfo("Saved","Planner saved.")
