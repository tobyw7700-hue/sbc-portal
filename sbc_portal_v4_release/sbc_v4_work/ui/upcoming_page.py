"""
Upcoming Assignments — sorted by due date, year dropdown, fixed colours.
"""
import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime, date
from ui.theme import *
from ui.widgets import (ScrollableFrame, Card, PageHeader,
                        GoldDivider, SectionTitle, Divider)
from data.models import AcademicData
from scraper.grade_logic import is_formative, fmt_grade


def _is_submitted(assignment) -> bool:
    """Return True if assignment has been submitted (any form)."""
    s = (assignment.status or "").lower()
    return any(x in s for x in ["submitted", "reviewed", "marked"])


def _parse_date(date_str: str):
    if not date_str:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            return None
    for fmt in ["%b %d, %Y", "%B %d, %Y", "%d/%m/%Y", "%d-%m-%Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except Exception:
            continue
    return None


def _days_until(d: date) -> int:
    return (d - date.today()).days


def _urgency_color(days) -> str:
    if days is None:
        return FG_MUTED
    if days < 0:
        return FG_MUTED
    if days == 0:
        return DANGER
    if days <= 3:
        return DANGER
    if days <= 7:
        return WARNING
    if days <= 14:
        return ACCENT
    return SUCCESS


def _due_label(days: int, due_str: str) -> str:
    if days < 0:
        return f"Overdue {abs(days)}d"
    if days == 0:
        return "Due TODAY"
    if days == 1:
        return "Tomorrow"
    if days <= 7:
        return f"In {days} days"
    return due_str[:10] if due_str else ""


class UpcomingPage(tk.Frame):

    def __init__(self, parent, data: AcademicData, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data = data
        self.filter_var = tk.StringVar(value="All")
        self.year_var   = tk.StringVar()
        self._build()

    def _build(self):
        hdr = PageHeader(self, "Upcoming Assignments",
                         subtitle="Sorted by due date · Formative tasks excluded")
        hdr.pack(fill="x")

        # Controls in header right frame
        ctrl = tk.Frame(hdr.right_frame, bg=BG_MID)
        ctrl.pack()

        # Year selector
        years = self.data.all_years()
        if years:
            tk.Label(ctrl, text="Year:", bg=BG_MID, fg=FG_MUTED,
                     font=FONT_SMALL).pack(side="left", padx=(0,4))
            self.year_var.set(str(years[0]))
            cb = ttk.Combobox(ctrl, textvariable=self.year_var,
                               values=[str(y) for y in years],
                               state="readonly", width=7)
            cb.pack(side="left", padx=(0,12))
            cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Filter buttons
        self._filter_btns = {}
        for label in ["All", "This Week", "Overdue"]:
            is_active = (label == "All")
            btn = tk.Button(
                ctrl, text=label,
                bg=ACCENT if is_active else BG_CARD,
                fg=BG_DARK if is_active else FG_PRIMARY,
                font=("TkDefaultFont", 9, "bold"),
                relief="flat", padx=10, pady=4,
                cursor="hand2", bd=0,
                activebackground=ACCENT_DIM,
                activeforeground=BG_DARK,
                command=lambda l=label: self._set_filter(l),
            )
            btn.pack(side="left", padx=2)
            self._filter_btns[label] = btn

        GoldDivider(self).pack(fill="x")

        self.scroll = ScrollableFrame(self, bg=BG_DARK)
        self.scroll.pack(fill="both", expand=True)
        self.area = self.scroll.inner
        self._refresh()

    def _set_filter(self, f):
        self.filter_var.set(f)
        for label, btn in self._filter_btns.items():
            if label == f:
                btn.configure(bg=ACCENT, fg=BG_DARK,
                              activebackground=ACCENT_DIM, activeforeground=BG_DARK)
            else:
                btn.configure(bg=BG_CARD, fg=FG_PRIMARY,
                              activebackground=BG_LIGHT, activeforeground=FG_PRIMARY)
        self._refresh()

    def _collect_tasks(self):
        try:
            year = int(self.year_var.get())
        except (ValueError, tk.TclError):
            year = None

        tasks = []
        from datetime import date
        today = date.today()
        subjects = self.data.subjects_by_year.get(year, []) if year else []
        for subj in subjects:
            for a in subj.assignments:
                if is_formative(a):
                    continue
                # Skip items due more than 30 days ago UNLESS they haven't been submitted
                if a.due_date:
                    d = _parse_date(a.due_date)
                    if d and (today - d).days > 30:
                        continue
                tasks.append((subj, a))
        return tasks

    def _refresh(self):
        for w in self.area.winfo_children():
            w.destroy()

        raw   = self._collect_tasks()
        f     = self.filter_var.get()

        dated   = []
        undated = []
        for subj, a in raw:
            d = _parse_date(a.due_date)
            if d:
                days = _days_until(d)
                if f == "This Week" and (days < 0 or days > 7):
                    continue
                if f == "Overdue" and (days >= 0 or _is_submitted(a)):
                    continue
                dated.append((d, days, subj, a))
            else:
                undated.append((subj, a))

        dated.sort(key=lambda x: x[0])

        if not dated and not undated:
            self._empty_state()
            return

        # Stats strip
        overdue  = sum(1 for _,days,*_ in dated if days < 0)
        due_soon = sum(1 for _,days,*_ in dated if 0 <= days <= 7)
        graded   = sum(1 for _,_,_,a in dated if a.grade_raw is not None)

        strip = tk.Frame(self.area, bg=BG_MID)
        strip.pack(fill="x")
        tk.Frame(strip, bg=ACCENT, height=2).pack(fill="x")
        sf = tk.Frame(strip, bg=BG_MID)
        sf.pack(fill="x", padx=28, pady=12)

        for n, label, color in [
            (len(dated)+len(undated), "Total",      FG_PRIMARY),
            (overdue,                 "Overdue",     DANGER),
            (due_soon,                "This Week",   WARNING),
            (graded,                  "Graded",      SUCCESS),
        ]:
            f2 = tk.Frame(sf, bg=BG_MID)
            f2.pack(side="left", padx=16)
            tk.Label(f2, text=str(n), bg=BG_MID, fg=color,
                     font=("Georgia", 22, "bold")).pack()
            tk.Label(f2, text=label, bg=BG_MID, fg=FG_MUTED,
                     font=FONT_SMALL).pack()

        # Task list
        pad = tk.Frame(self.area, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=4)
        SectionTitle(pad, "Tasks").pack(anchor="w")

        prev_group = None
        for d, days, subj, a in dated:
            submitted = _is_submitted(a)
            if days < 0 and not submitted:
                group = "⚠  Overdue"
            elif days < 0 and submitted:
                group = "✅  Submitted (Past Due Date)"
            elif days == 0:
                group = "🔴  Due Today"
            elif days <= 3:
                group = "🟠  Due Very Soon"
            elif days <= 7:
                group = "🟡  This Week"
            elif days <= 14:
                group = "🔵  Next Two Weeks"
            else:
                group = "🟢  Later"

            if group != prev_group:
                prev_group = group
                gf = tk.Frame(self.area, bg=BG_DARK)
                gf.pack(fill="x", padx=20, pady=4)
                tk.Label(gf, text=group, bg=BG_DARK, fg=FG_SEC,
                         font=("TkDefaultFont", 9, "bold")).pack(anchor="w")

            self._task_card(self.area, subj, a, days, d)

        if undated:
            gf = tk.Frame(self.area, bg=BG_DARK)
            gf.pack(fill="x", padx=20, pady=4)
            tk.Label(gf, text="📋  No Due Date", bg=BG_DARK, fg=FG_SEC,
                     font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
            for subj, a in undated:
                self._task_card(self.area, subj, a, None, None)

    def _task_card(self, parent, subj, a, days, d):
        submitted = _is_submitted(a)
        graded    = a.grade_raw is not None

        # Stripe colour: green if submitted/graded, urgency colour otherwise
        if graded:
            stripe = grade_color(a.grade_raw)
        elif submitted:
            stripe = SUCCESS
        elif days is not None and days < 0:
            stripe = DANGER
        else:
            stripe = _urgency_color(days)

        card = Card(parent, bg=BG_CARD)
        card.pack(fill="x", padx=16, pady=3)
        tk.Frame(card, bg=stripe, width=5).pack(side="left", fill="y")

        body = tk.Frame(card, bg=BG_CARD)
        body.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        # Top row: title + grade/due badge
        top = tk.Frame(body, bg=BG_CARD)
        top.pack(fill="x")

        tk.Label(top, text=a.title or "Untitled",
                 bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"),
                 anchor="w", wraplength=460).pack(side="left", anchor="w")

        # Right badge
        if graded:
            g_color = grade_color(a.grade_raw)
            tk.Label(top, text=fmt_grade(a.grade_raw),
                     bg=BG_CARD, fg=g_color,
                     font=("Georgia", 13, "bold")).pack(side="right")
        elif days is not None and not submitted:
            due_color = _urgency_color(days)
            tk.Label(top, text=_due_label(days, a.due_date or ""),
                     bg=BG_CARD, fg=due_color,
                     font=("TkDefaultFont", 9, "bold")).pack(side="right")

        # Submission status badge — prominent
        status_row = tk.Frame(body, bg=BG_CARD)
        status_row.pack(fill="x", pady=0)

        # Subject name
        tk.Label(status_row, text=subj.name,
                 bg=BG_CARD, fg=ACCENT,
                 font=("TkDefaultFont", 9, "bold")).pack(side="left")

        # Status pill
        if a.status:
            s = a.status.strip()
            s_lower = s.lower()
            if "reviewed" in s_lower or "marked" in s_lower:
                pill_bg, pill_fg, pill_text = SUCCESS, BG_DARK, f"✓ {s}"
            elif "submitted" in s_lower:
                pill_bg, pill_fg = "#1e4d2b", SUCCESS
                pill_text = f"↑ {s}"
            elif "not submitted" in s_lower or "incomplete" in s_lower:
                pill_bg, pill_fg, pill_text = "#4d1e1e", DANGER, f"✗ {s}"
            else:
                pill_bg, pill_fg, pill_text = BG_MID, FG_MUTED, s

            pill = tk.Label(status_row, text=f"  {pill_text}  ",
                            bg=pill_bg, fg=pill_fg,
                            font=("TkDefaultFont", 9, "bold"),
                            padx=4, pady=1)
            pill.pack(side="left", padx=(8,0))

        # Due date (only if not graded and no due label shown)
        if a.due_date and (graded or days is None):
            tk.Label(status_row, text=f"  📅 {a.due_date[:10]}",
                     bg=BG_CARD, fg=FG_MUTED,
                     font=FONT_SMALL).pack(side="left")

    def _empty_state(self):
        f = tk.Frame(self.area, bg=BG_DARK)
        f.pack(fill="both", expand=True, pady=80)
        tk.Label(f, text="🎉", bg=BG_DARK,
                 font=("TkDefaultFont", 36)).pack()
        tk.Label(f, text="No upcoming assignments!",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=("Georgia", 16, "bold")).pack(pady=8)
        tk.Label(f, text="All caught up.",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY).pack()
