"""
Timetable page — 10-day cycle grid matching mySBC layout.
Colour-coded by subject, shows room + teacher per cell.
"""
import tkinter as tk
from tkinter import ttk
from ui.theme import *
from ui.widgets import PageHeader, GoldDivider, ScrollableFrame
from scraper.timetable_parser import load_timetable, _cell_colour, _subject_key

# Subject background colours (light, for cells)
CELL_COLOURS = {
    "MATH":     ("#1e3a8a", "#dbeafe"),  # (text, bg) dark-on-light
    "ENGL":     ("#14532d", "#dcfce7"),
    "SCIE":     ("#713f12", "#fef9c3"),
    "HUMS":     ("#831843", "#fce7f3"),
    "RELS":     ("#4c1d95", "#ede9fe"),
    "HEPE":     ("#7c2d12", "#ffedd5"),
    "ITAL":     ("#164e63", "#cffafe"),
    "FREN":     ("#164e63", "#cffafe"),
    "JAPN":     ("#164e63", "#e0f2fe"),
    "VISCOM":   ("#4a1d96", "#f3e8ff"),
    "BUSMAN":   ("#7f1d1d", "#fee2e2"),
    "HR":       ("#334155", "#f1f5f9"),
    "ASSEMBLY": ("#334155", "#f1f5f9"),
    "SEL":      ("#334155", "#f0fdf4"),
}
DEFAULT_CELL = ("#1e293b", "#f8fafc")

# Day button colours for the selector
DAY_GROUPS = {
    "Week A": [f"Day {i}" for i in range(1, 6)],
    "Week B": [f"Day {i}" for i in range(6, 11)],
}


def _cell_colors(code: str):
    key = _subject_key(code) if code else ""
    return CELL_COLOURS.get(key, DEFAULT_CELL)


class TimetablePage(tk.Frame):

    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data      = data
        self.session   = session
        self.timetable = {}
        self.selected_days = tk.StringVar(value="all")
        self._build()

    def _build(self):
        hdr = PageHeader(self, "Timetable",
                         subtitle="10-day cycle · St Bernard's College")
        hdr.pack(fill="x")

        # Day filter controls in header
        ctrl = tk.Frame(hdr.right_frame, bg=BG_MID)
        ctrl.pack()

        self._day_filter_btns = {}
        for label, value in [("All Days","all"), ("Week A (1–5)","weekA"), ("Week B (6–10)","weekB")]:
            is_sel = value == "all"
            lbl = tk.Label(ctrl, text=label,
                           bg=ACCENT if is_sel else BG_CARD,
                           fg=BG_DARK if is_sel else FG_PRIMARY,
                           font=("TkDefaultFont", 9, "bold"),
                           padx=10, pady=4, cursor="hand2")
            lbl.pack(side="left", padx=2)
            lbl.bind("<Button-1>", lambda e, v=value: self._filter_days(v))
            self._day_filter_btns[value] = lbl

        GoldDivider(self).pack(fill="x")

        self.scroll = ScrollableFrame(self, bg=BG_DARK)
        self.scroll.pack(fill="both", expand=True)
        self.area = self.scroll.inner

        # Load timetable data
        username = ""
        if self.data and self.data.profile:
            username = self.data.profile.username or self.data.profile.student_id or ""
        self.timetable = load_timetable(self.session, username)
        self._refresh()

    def _filter_days(self, value):
        self.selected_days.set(value)
        for v, btn in self._day_filter_btns.items():
            if v == value:
                btn.configure(bg=ACCENT, fg=BG_DARK)
            else:
                btn.configure(bg=BG_CARD, fg=FG_PRIMARY)
        self._refresh()

    def _refresh(self):
        for w in self.area.winfo_children():
            w.destroy()

        if not self.timetable or not self.timetable.get("days"):
            self._placeholder()
            return

        days = self.timetable["days"]
        sel  = self.selected_days.get()
        if sel == "weekA":
            days = [d for d in days if int(d.split()[-1]) <= 5]
        elif sel == "weekB":
            days = [d for d in days if int(d.split()[-1]) > 5]

        periods = self.timetable["periods"]
        cells   = self.timetable["cells"]

        # ── Legend ────────────────────────────────────────────────────
        legend = tk.Frame(self.area, bg=BG_DARK)
        legend.pack(fill="x", padx=16, pady=8)
        tk.Label(legend, text="Subject colours:", bg=BG_DARK, fg=FG_MUTED,
                 font=FONT_SMALL).pack(side="left", padx=(0,8))

        shown = set()
        for day in days:
            for p in periods:
                cell = cells.get(day, {}).get(p["label"])
                if not cell:
                    continue
                key = _subject_key(cell["code"])
                if key in shown or key in ("HR","ASSEMBLY","SEL"):
                    continue
                shown.add(key)
                fg, bg = _cell_colors(cell["code"])
                chip = tk.Label(legend, text=cell["name"],
                                bg=bg, fg=fg,
                                font=("TkDefaultFont", 8, "bold"),
                                padx=6, pady=2)
                chip.pack(side="left", padx=2)

        # ── Grid ──────────────────────────────────────────────────────
        grid = tk.Frame(self.area, bg=BG_DARK)
        grid.pack(fill="x", padx=10, pady=4)

        # Column widths — period col needs enough room for "Period 6" + time
        ROW_LABEL_W = 16   # period column (wider to avoid cutoff)
        CELL_W      = 12   # subject cell

        # Header row: Day labels
        tk.Label(grid, text="", bg=BG_MID, width=ROW_LABEL_W,
                 relief="flat", pady=8).grid(row=0, column=0, padx=1, pady=1, sticky="nsew")

        for col, day in enumerate(days):
            # Highlight current day concept (Day 1 = today placeholder)
            bg = ACCENT if col == 0 else BG_MID
            fg = BG_DARK if col == 0 else FG_SEC
            tk.Label(grid, text=day, bg=bg, fg=fg,
                     font=("TkDefaultFont", 9, "bold"),
                     pady=9, anchor="center").grid(
                row=0, column=col+1, padx=1, pady=1, sticky="nsew")

        # Period rows
        for row_idx, period in enumerate(periods):
            label = period["label"]
            time  = period["time"]

            # Period label cell
            lf = tk.Frame(grid, bg=BG_MID,
                          highlightbackground=BORDER, highlightthickness=1)
            lf.grid(row=row_idx+1, column=0, padx=1, pady=1, sticky="nsew")
            tk.Label(lf, text=label, bg=BG_MID, fg=FG_PRIMARY,
                     font=("TkDefaultFont", 9, "bold"),
                     width=ROW_LABEL_W, pady=4).pack()
            if time:
                tk.Label(lf, text=time, bg=BG_MID, fg=FG_MUTED,
                         font=("TkDefaultFont", 7)).pack()

            # Subject cells
            for col, day in enumerate(days):
                cell_data = cells.get(day, {}).get(label)
                self._make_cell(grid, cell_data, row_idx+1, col+1)

        # Configure column weights
        grid.columnconfigure(0, weight=0, minsize=110)
        for i in range(1, len(days)+1):
            grid.columnconfigure(i, weight=1, uniform="daycol")

        # ── Legend note ───────────────────────────────────────────────
        note = tk.Frame(self.area, bg=BG_DARK)
        note.pack(fill="x", padx=16, pady=16)
        tk.Label(note,
                 text="* This is a 10-day rotating cycle. Day 1 may not correspond to Monday.",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")

    def _make_cell(self, parent, cell_data, row, col):
        if not cell_data:
            f = tk.Frame(parent, bg=BG_MID,
                         highlightbackground=BORDER, highlightthickness=1)
            f.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            tk.Label(f, text="", bg=BG_MID, height=4).pack()
            return

        code  = cell_data.get("code","")
        name  = cell_data.get("name","") or code
        room  = cell_data.get("room","")
        teach = cell_data.get("teacher","")

        fg, bg = _cell_colors(code)

        f = tk.Frame(parent, bg=bg,
                     highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")

        inner = tk.Frame(f, bg=bg)
        inner.pack(fill="both", expand=True, padx=4, pady=5)

        # Subject name (friendly)
        tk.Label(inner, text=name, bg=bg, fg=fg,
                 font=("TkDefaultFont", 9, "bold"),
                 wraplength=95, justify="center").pack()

        # Code in smaller text
        tk.Label(inner, text=f"({code})", bg=bg, fg=fg,
                 font=("TkDefaultFont", 7)).pack()

        if room:
            tk.Label(inner, text=room, bg=bg, fg=fg,
                     font=("TkDefaultFont", 8, "bold")).pack()

        # Teacher - shortened
        if teach:
            short = re.sub(r"\b([A-Z])[a-z]+\b", r"\1.", teach)
            # Keep title + last name only: "Ms R. Absolon"
            parts = teach.split()
            if len(parts) >= 3:
                short = f"{parts[0]} {parts[-1]}"
            tk.Label(inner, text=short, bg=bg, fg=fg,
                     font=("TkDefaultFont", 7),
                     wraplength=90, justify="center").pack()

    def _placeholder(self):
        f = tk.Frame(self.area, bg=BG_DARK)
        f.pack(fill="both", expand=True, pady=80)
        tk.Label(f, text="🕐", bg=BG_DARK,
                 font=("TkDefaultFont", 36)).pack()
        tk.Label(f, text="Timetable not yet loaded",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=("Georgia", 14, "bold")).pack(pady=8)
        tk.Label(f,
                 text="Run probe_timetable.py then restart the app.",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY).pack()
        tk.Label(f,
                 text="python3 probe_timetable.py",
                 bg=BG_MID, fg=ACCENT_LT,
                 font=FONT_MONO, padx=14, pady=6).pack(pady=8)


import re
