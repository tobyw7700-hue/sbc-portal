"""
Calendar — proper month grid using grid() layout for equal-width equal-height cells.
Click day number to see all events. Event chips are compact coloured labels.
"""
import tkinter as tk
from tkinter import ttk
import re, calendar
from datetime import date
from typing import Dict, List

from ui.theme import *
from ui.widgets import PageHeader, GoldDivider, ScrollableFrame

TYPE_BG = {
    "type1": "#cee6ea", "type2": "#f8deb8", "type3": "#d4efc4",
    "type4": "#f2ced6", "type7": "#c8d4b8", "type8": "#b8ddff",
}
TYPE_FG = {
    "type1": "#0e4a52", "type2": "#7c3d00", "type3": "#2d5a1b",
    "type4": "#7f1d1d", "type7": "#2d3a1e", "type8": "#1e3a8a",
}
DOW        = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
MONTH_NAMES = ["","January","February","March","April","May","June",
               "July","August","September","October","November","December"]


def _nav_btn(parent, text, cmd):
    b = tk.Button(parent, text=text,
                  bg=BG_CARD, fg=FG_PRIMARY,
                  font=("TkDefaultFont", 11, "bold"),
                  relief="flat", padx=10, pady=4,
                  cursor="hand2", bd=0,
                  highlightthickness=0,
                  activebackground=BG_LIGHT,
                  activeforeground=FG_PRIMARY,
                  command=cmd)
    b.pack(side="left", padx=2)
    return b


class CalendarPage(tk.Frame):

    def __init__(self, parent, data=None, session=None, user_id="11953", **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data    = data
        self.session = session
        self.user_id = user_id
        # Pre-load from cache
        if data and hasattr(data, 'calendar_events') and data.calendar_events:
            self.events: Dict[str, List[dict]] = dict(data.calendar_events)
        else:
            self.events: Dict[str, List[dict]] = {}
        today      = date.today()
        self.yr    = today.year
        self.mo    = today.month
        self.today = today
        self._build()
        self._load()

    def _build(self):
        # Nav bar
        nav = tk.Frame(self, bg=BG_MID)
        nav.pack(fill="x")
        tk.Frame(nav, bg=ACCENT, height=3).pack(fill="x")
        bar = tk.Frame(nav, bg=BG_MID)
        bar.pack(fill="x", padx=16, pady=8)

        left = tk.Frame(bar, bg=BG_MID)
        left.pack(side="left")
        _nav_btn(left, "Today", self._go_today)
        _nav_btn(left, "‹", self._prev)
        _nav_btn(left, "›", self._next)

        self.title_lbl = tk.Label(bar, text="",
                                   bg=BG_MID, fg=FG_PRIMARY,
                                   font=("Georgia", 17, "bold"))
        self.title_lbl.pack(side="left", padx=20)

        # Legend
        leg = tk.Frame(bar, bg=BG_MID)
        leg.pack(side="right")
        for label, key in [("Due Work","type4"),("School Event","type1"),
                            ("Excursion","type2"),("ACC","type8"),("Free Day","type7")]:
            f = tk.Frame(leg, bg=BG_MID)
            f.pack(side="left", padx=5)
            tk.Frame(f, bg=TYPE_BG.get(key,"#ccc"), width=10, height=10).pack(side="left", padx=(0,3))
            tk.Label(f, text=label, bg=BG_MID, fg=FG_SEC,
                     font=("TkDefaultFont", 8)).pack(side="left")

        GoldDivider(self).pack(fill="x")

        self.status = tk.Label(self, text="",
                               bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL)
        self.status.pack(fill="x", padx=16, pady=2)

        # Grid container — uses grid() layout internally
        self.cal_frame = tk.Frame(self, bg=BG_DARK)
        self.cal_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Keyboard nav
        self.bind_all("<Left>",  lambda e: self._prev())
        self.bind_all("<Right>", lambda e: self._next())

        # Two-finger swipe on Mac
        self.bind_all("<MouseWheel>", self._on_mwheel)

    def _on_mwheel(self, e):
        # Mac trackpad horizontal swipe or vertical with large delta
        if abs(e.delta) > 100:
            if e.delta < 0:
                self._next()
            else:
                self._prev()

    def _go_today(self):
        self.yr = self.today.year
        self.mo = self.today.month
        self._load()

    def _prev(self):
        self.mo -= 1
        if self.mo < 1:
            self.mo = 12
            self.yr -= 1
        self._load()

    def _next(self):
        self.mo += 1
        if self.mo > 12:
            self.mo = 1
            self.yr += 1
        self._load()

    def _load(self):
        self.title_lbl.configure(text=f"{MONTH_NAMES[self.mo]} {self.yr}")
        self.status.configure(text="Loading…")
        self._draw()
        if not self.session:
            self.status.configure(text="Not connected")
            return
        import threading
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        from scraper.calendar_parser import fetch_events, parse_events
        raw    = fetch_events(self.session, self.user_id, self.yr, self.mo)
        self.events = parse_events(raw)
        self.after(0, self._on_loaded)

    def _on_loaded(self):
        n = sum(len(v) for v in self.events.values())
        self.status.configure(text=f"{n} events · {MONTH_NAMES[self.mo]} {self.yr}")
        self._draw()

    def _draw(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()

        # Configure 7 equal columns
        for col in range(7):
            self.cal_frame.columnconfigure(col, weight=1, uniform="col")

        # Day-of-week header row
        for col, day in enumerate(DOW):
            is_we = day in ("Sun","Sat")
            tk.Label(self.cal_frame, text=day,
                     bg=BG_MID,
                     fg=ACCENT if not is_we else FG_MUTED,
                     font=("TkDefaultFont", 9, "bold"),
                     anchor="center", pady=5).grid(
                row=0, column=col, sticky="nsew", padx=1, pady=1)

        # Calendar weeks
        weeks = calendar.monthcalendar(self.yr, self.mo)
        n_weeks = len(weeks)
        for row_idx in range(n_weeks):
            self.cal_frame.rowconfigure(row_idx + 1, weight=1, uniform="row")

        for row_idx, week in enumerate(weeks):
            for col_idx, day_num in enumerate(week):
                self._make_cell(row_idx + 1, col_idx, day_num)

    def _make_cell(self, grid_row, grid_col, day_num):
        is_today = day_num > 0 and date(self.yr, self.mo, day_num) == self.today
        is_other = day_num == 0
        is_we    = grid_col in (0, 6)  # Sun=0, Sat=6

        if is_today:
            cell_bg = BG_LIGHT
            border  = ACCENT
        elif is_other or is_we:
            cell_bg = BG_DARK
            border  = BORDER
        else:
            cell_bg = BG_MID
            border  = BORDER

        cell = tk.Frame(self.cal_frame, bg=cell_bg,
                        highlightbackground=border,
                        highlightthickness=1)
        cell.grid(row=grid_row, column=grid_col,
                  sticky="nsew", padx=1, pady=1)

        if is_other:
            return

        date_str = f"{self.yr:04d}-{self.mo:02d}-{day_num:02d}"
        events   = self.events.get(date_str, [])

        # Day number button — click to see all events
        num_color = ACCENT if is_today else (FG_MUTED if is_we else FG_PRIMARY)
        num_font  = ("TkDefaultFont", 10, "bold") if is_today else ("TkDefaultFont", 10)

        num_btn = tk.Button(cell, text=str(day_num),
                            bg=cell_bg, fg=num_color,
                            font=num_font,
                            relief="flat", anchor="w",
                            padx=4, pady=2, bd=0,
                            highlightthickness=0,
                            cursor="hand2",
                            activebackground=BG_LIGHT,
                            activeforeground=FG_PRIMARY,
                            command=lambda d=day_num, evs=list(events):
                                self._show_day(d, evs))
        num_btn.pack(fill="x")

        # Event chips — max 3
        MAX = 3
        for ev in events[:MAX]:
            self._chip(cell, ev, cell_bg, events)

        overflow = len(events) - MAX
        if overflow > 0:
            mb = tk.Button(cell, text=f"+{overflow} more",
                           bg=cell_bg, fg=FG_MUTED,
                           font=("TkDefaultFont", 7),
                           relief="flat", anchor="w",
                           padx=4, pady=0, bd=0,
                           highlightthickness=0,
                           cursor="hand2",
                           activebackground=BG_LIGHT,
                           activeforeground=FG_PRIMARY,
                           command=lambda d=day_num, evs=list(events):
                               self._show_day(d, evs))
            mb.pack(fill="x")

        tk.Frame(cell, bg=cell_bg, height=2).pack(side="bottom")

    def _chip(self, parent, ev, cell_bg, all_events):
        t   = ev.get("type","")
        bg  = TYPE_BG.get(t, "#ddd")
        fg  = TYPE_FG.get(t, "#333")

        title = ev.get("title","")
        if ev.get("is_due_work") and ev.get("subject"):
            display = f"📝 {ev['subject']}: {title}"
        elif ev.get("is_acc"):
            display = f"🏆 {title}"
        else:
            display = title

        if ev.get("time") and not ev.get("all_day"):
            display = f"{ev['time']} {display}"

        chip = tk.Button(parent,
                         text=display[:36] + ("…" if len(display) > 36 else ""),
                         bg=bg, fg=fg,
                         font=("TkDefaultFont", 7, "bold"),
                         relief="flat", anchor="w",
                         padx=3, pady=1, bd=0,
                         highlightthickness=0,
                         cursor="hand2",
                         activebackground=bg,
                         activeforeground=fg,
                         command=lambda e=ev: self._event_popup(e))
        chip.pack(fill="x", padx=2, pady=1)

    def _show_day(self, day_num, events):
        win = tk.Toplevel(self)
        win.title(f"{MONTH_NAMES[self.mo]} {day_num}, {self.yr}")
        win.configure(bg=BG_DARK)
        win.geometry("500x520")

        tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(win, text=f"{MONTH_NAMES[self.mo]} {day_num}, {self.yr}",
                 bg=BG_MID, fg=FG_PRIMARY,
                 font=("Georgia", 14, "bold"),
                 padx=16, pady=12).pack(fill="x")

        if not events:
            tk.Label(win, text="No events.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY).pack(pady=30)
        else:
            scroll = ScrollableFrame(win, bg=BG_DARK)
            scroll.pack(fill="both", expand=True, padx=12, pady=8)
            area = scroll.inner

            for ev in events:
                t  = ev.get("type","")
                bg = TYPE_BG.get(t, "#ddd")
                fg = TYPE_FG.get(t, "#333")

                card = tk.Frame(area, bg=bg,
                                highlightbackground=BORDER,
                                highlightthickness=1)
                card.pack(fill="x", pady=3)

                tk.Label(card, text=ev.get("title",""),
                         bg=bg, fg=fg,
                         font=("TkDefaultFont", 10, "bold"),
                         anchor="w", wraplength=450,
                         padx=10, pady=6).pack(fill="x")

                meta = []
                if ev.get("time") and not ev.get("all_day"):
                    meta.append(f"🕐 {ev['time']}")
                if ev.get("location"):
                    meta.append(f"📍 {ev['location']}")
                if ev.get("subject"):
                    meta.append(f"📚 {ev['subject']}")
                if meta:
                    tk.Label(card, text="  ·  ".join(meta),
                             bg=bg, fg=fg,
                             font=("TkDefaultFont", 8),
                             anchor="w", padx=10, pady=2).pack(fill="x")

                detail = ev.get("detail","").strip()
                if detail and detail != ev.get("title",""):
                    tk.Label(card, text=detail[:200],
                             bg=bg, fg=fg,
                             font=("TkDefaultFont", 8, "italic"),
                             anchor="w", wraplength=460,
                             padx=10, pady=3).pack(fill="x")

        tk.Button(win, text="Close",
                  bg=ACCENT, fg=BG_DARK,
                  font=("TkDefaultFont", 10, "bold"),
                  relief="flat", padx=16, pady=6,
                  bd=0, highlightthickness=0,
                  cursor="hand2",
                  activebackground=ACCENT_DIM,
                  activeforeground=BG_DARK,
                  command=win.destroy).pack(pady=8)

    def _event_popup(self, ev):
        win = tk.Toplevel(self)
        win.title(ev.get("title","Event"))
        win.configure(bg=BG_DARK)
        win.geometry("420x280")

        t  = ev.get("type","")
        bg = TYPE_BG.get(t, BG_MID)
        fg = TYPE_FG.get(t, FG_PRIMARY)

        tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(win, text=ev.get("title",""),
                 bg=bg, fg=fg,
                 font=("Georgia", 13, "bold"),
                 wraplength=390, justify="left",
                 padx=16, pady=10).pack(fill="x")

        body = tk.Frame(win, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        def row(lbl, val):
            if not val:
                return
            f = tk.Frame(body, bg=BG_DARK)
            f.pack(fill="x", pady=2)
            tk.Label(f, text=lbl, bg=BG_DARK, fg=ACCENT,
                     font=("TkDefaultFont", 9, "bold"),
                     width=10, anchor="w").pack(side="left")
            tk.Label(f, text=val, bg=BG_DARK, fg=FG_PRIMARY,
                     font=FONT_SMALL, anchor="w",
                     wraplength=280).pack(side="left")

        row("Date:",     ev.get("date",""))
        row("Time:",     ev.get("time","") or "All day")
        row("Location:", ev.get("location",""))
        row("Subject:",  ev.get("subject",""))

        detail = ev.get("detail","").strip()
        if detail and detail != ev.get("title",""):
            tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=4)
            tk.Label(body, text=detail[:250],
                     bg=BG_DARK, fg=FG_SEC,
                     font=FONT_SMALL, wraplength=380,
                     justify="left", anchor="w").pack(fill="x")

        tk.Button(win, text="Close",
                  bg=ACCENT, fg=BG_DARK,
                  font=("TkDefaultFont", 10, "bold"),
                  relief="flat", padx=16, pady=5,
                  bd=0, highlightthickness=0,
                  cursor="hand2",
                  activebackground=ACCENT_DIM, activeforeground=BG_DARK,
                  command=win.destroy).pack(pady=6)
