"""
Classes & Tasks page — modern design with assignment cards.
"""
import tkinter as tk
from tkinter import ttk
from ui.theme import *
from ui.widgets import (ScrollableFrame, Card, AccentCard, PageHeader,
                        GoldDivider, SectionTitle, Divider, StatusPill)
from data.models import AcademicData
from scraper.grade_logic import is_formative, compute_subject_grade, fmt_grade, grade_label


STATUS_COLORS = {
    "reviewed":   SUCCESS,
    "submitted":  ACCENT,
    "pending":    WARNING,
    "not submitted": DANGER,
    "incomplete": DANGER,
}

STATUS_ICONS = {
    "reviewed":      "✓",
    "submitted":     "↑",
    "pending":       "⏳",
    "not submitted": "✗",
    "incomplete":    "✗",
}


def _s_color(status):
    s = (status or "").lower()
    for k, c in STATUS_COLORS.items():
        if k in s:
            return c
    return FG_MUTED


def _s_icon(status):
    s = (status or "").lower()
    for k, i in STATUS_ICONS.items():
        if k in s:
            return i
    return "○"


class ClassesPage(tk.Frame):

    def __init__(self, parent, data: AcademicData, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data = data
        self.selected_year    = tk.StringVar()
        self.selected_subject = tk.StringVar(value="All Subjects")
        self._build()

    def _build(self):
        hdr = PageHeader(self, "Classes & Assessments",
                         subtitle="Formative tasks excluded · Part A/B excluded from averages")
        hdr.pack(fill="x")

        ff = tk.Frame(hdr.right_frame, bg=BG_MID)
        ff.pack()

        years = self.data.all_years()
        if years:
            tk.Label(ff, text="Year", bg=BG_MID, fg=FG_MUTED,
                     font=FONT_SMALL).pack(side="left", padx=(0,6))
            self.selected_year.set(str(years[0]))
            cb = ttk.Combobox(ff, textvariable=self.selected_year,
                               values=[str(y) for y in years],
                               state="readonly", width=7)
            cb.pack(side="left", padx=(0,12))
            cb.bind("<<ComboboxSelected>>", lambda e: self._update_filters())

        tk.Label(ff, text="Subject", bg=BG_MID, fg=FG_MUTED,
                 font=FONT_SMALL).pack(side="left", padx=(0,6))
        self.subject_cb = ttk.Combobox(ff, textvariable=self.selected_subject,
                                        state="readonly", width=22)
        self.subject_cb.pack(side="left")
        self.subject_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        GoldDivider(self).pack(fill="x")

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True)

        # Subject sidebar
        sidebar = tk.Frame(body, bg=BG_MID, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(sidebar, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(sidebar, text="SUBJECTS",
                 bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 8, "bold"),
                 padx=16, pady=10, anchor="w").pack(fill="x")
        self.sb_scroll = ScrollableFrame(sidebar, bg=BG_MID)
        self.sb_scroll.pack(fill="both", expand=True)
        self.sb_inner = self.sb_scroll.inner

        self.main_scroll = ScrollableFrame(body, bg=BG_DARK)
        self.main_scroll.pack(side="right", fill="both", expand=True)
        self.main_area = self.main_scroll.inner

        self._update_filters()

    def _subjects(self):
        try:
            year = int(self.selected_year.get())
        except (ValueError, tk.TclError):
            year = None
        if year:
            return self.data.subjects_by_year.get(year, [])
        return [s for lst in self.data.subjects_by_year.values() for s in lst]

    def _update_filters(self):
        subjects = self._subjects()
        names = ["All Subjects"] + [s.name for s in subjects]
        self.subject_cb.configure(values=names)
        self.selected_subject.set("All Subjects")
        self._build_sidebar(subjects)
        self._refresh()

    def _build_sidebar(self, subjects):
        for w in self.sb_inner.winfo_children():
            w.destroy()
        for subj in subjects:
            computed, _ = compute_subject_grade(subj.assignments)
            g = computed or subj.grade_raw
            color = grade_color(g) if g else FG_MUTED

            row = tk.Frame(self.sb_inner, bg=BG_MID,
                           highlightbackground=BORDER, highlightthickness=0)
            row.pack(fill="x")

            # Active indicator stripe
            stripe = tk.Frame(row, bg=BG_MID, width=3)
            stripe.pack(side="left", fill="y")

            btn = tk.Label(
                row, text=subj.name,
                bg=BG_MID, fg=FG_SEC,
                font=("TkDefaultFont", 10),
                relief="flat", anchor="w",
                padx=10, pady=8,
                cursor="hand2",
                wraplength=150,
            )
            btn.pack(side="left", fill="x", expand=True)
            btn.bind("<Button-1>", lambda e, n=subj.name, s=stripe: self._select(n, s))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BG_LIGHT, fg=FG_PRIMARY))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=BG_MID, fg=FG_SEC))

            if g:
                tk.Label(row, text=fmt_grade(g),
                         bg=BG_MID, fg=color,
                         font=("TkDefaultFont", 9, "bold"),
                         padx=6).pack(side="right")

            tk.Frame(self.sb_inner, bg=BORDER, height=1).pack(fill="x")

    def _select(self, name, stripe_ref=None):
        self.selected_subject.set(name)
        self._refresh()

    def _refresh(self):
        for w in self.main_area.winfo_children():
            w.destroy()
        subjects = self._subjects()
        sel = self.selected_subject.get()
        if sel != "All Subjects":
            subjects = [s for s in subjects if s.name == sel]
        if not subjects:
            tk.Label(self.main_area, text="No data available.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY).pack(pady=40)
            return
        for subj in subjects:
            self._subject_block(subj)

    def _subject_block(self, subj):
        block = tk.Frame(self.main_area, bg=BG_DARK)
        block.pack(fill="x", padx=16, pady=8)

        # Subject header
        hdr = tk.Frame(block, bg=BG_MID,
                       highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill="x")

        hdr_body = tk.Frame(hdr, bg=BG_MID)
        hdr_body.pack(fill="x", padx=16, pady=12)

        left = tk.Frame(hdr_body, bg=BG_MID)
        left.pack(side="left")

        computed, used = compute_subject_grade(subj.assignments)
        g = computed or subj.grade_raw

        name_row = tk.Frame(left, bg=BG_MID)
        name_row.pack(anchor="w")
        tk.Label(name_row, text=subj.name or subj.code,
                 bg=BG_MID, fg=FG_PRIMARY,
                 font=("Georgia", 13, "bold")).pack(side="left")
        if subj.code and subj.code != subj.name:
            tk.Label(name_row, text=f"  ({subj.code})",
                     bg=BG_MID, fg=FG_MUTED,
                     font=FONT_SMALL).pack(side="left")

        if subj.teacher:
            tk.Label(left, text=f"👤 {subj.teacher}",
                     bg=BG_MID, fg=FG_SEC,
                     font=FONT_SMALL).pack(anchor="w", pady=0)

        if g:
            color = grade_color(g)
            right = tk.Frame(hdr_body, bg=BG_MID)
            right.pack(side="right")
            tk.Label(right, text=f"{g:.1f}%",
                     bg=BG_MID, fg=color,
                     font=("Georgia", 20, "bold")).pack()
            tk.Label(right, text=grade_label(g),
                     bg=BG_MID, fg=color,
                     font=("TkDefaultFont", 10)).pack()

        # Assignments
        graded   = [a for a in subj.assignments if a.grade_raw is not None and not is_formative(a)]
        formative = [a for a in subj.assignments if is_formative(a)]
        pending  = [a for a in subj.assignments if a.grade_raw is None and not is_formative(a)]

        if graded:
            SectionTitle(block, f"  Assessed Tasks ({len(graded)})").pack(
                anchor="w", padx=4, pady=2)
            for a in graded:
                self._task_card(block, a, show_grade=True)

        if pending:
            SectionTitle(block, f"  Upcoming / Pending ({len(pending)})").pack(
                anchor="w", padx=4, pady=2)
            for a in pending:
                self._task_card(block, a, show_grade=False)

        if formative:
            details = tk.Frame(block, bg=BG_DARK)
            details.pack(fill="x", padx=4, pady=0)
            tk.Label(details,
                     text=f"  ℹ {len(formative)} formative task{'s' if len(formative)!=1 else ''} excluded from grade calculation",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")

        tk.Frame(self.main_area, bg=BORDER, height=1).pack(fill="x", padx=16, pady=6)

    def _task_card(self, parent, a, show_grade=True):
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", padx=4, pady=2)

        # Left grade/status stripe
        if a.grade_raw is not None:
            stripe_color = grade_color(a.grade_raw)
        else:
            stripe_color = _s_color(a.status)
        tk.Frame(card, bg=stripe_color, width=3).pack(side="left", fill="y")

        body = tk.Frame(card, bg=BG_CARD)
        body.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        top = tk.Frame(body, bg=BG_CARD)
        top.pack(fill="x")

        # Title
        title_text = a.title or "Untitled"
        if is_formative(a):
            title_text = f"[Formative] {title_text}"
        tk.Label(top, text=title_text,
                 bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"),
                 anchor="w", wraplength=500).pack(side="left", anchor="w")

        # Grade badge
        if show_grade and a.grade:
            color = grade_color(a.grade_raw)
            gf = tk.Frame(top, bg=BG_CARD)
            gf.pack(side="right")
            tk.Label(gf, text=fmt_grade(a.grade_raw) if a.grade_raw is not None else (a.grade or "—"),
                     bg=BG_CARD, fg=color,
                     font=("Georgia", 14, "bold")).pack()

        # Meta row
        meta = tk.Frame(body, bg=BG_CARD)
        meta.pack(fill="x", pady=0)

        if a.status:
            icon = _s_icon(a.status)
            color = _s_color(a.status)
            tk.Label(meta, text=f"{icon} {a.status}",
                     bg=BG_CARD, fg=color,
                     font=("TkDefaultFont", 9, "bold")).pack(side="left")

        if a.due_date:
            tk.Label(meta, text=f"  ·  📅 {a.due_date}",
                     bg=BG_CARD, fg=FG_MUTED,
                     font=FONT_SMALL).pack(side="left")

        # Feedback
        if a.description:
            fb = tk.Frame(body, bg=BG_MID)
            fb.pack(fill="x", pady=0)
            tk.Label(fb,
                     text=f"💬  {a.description[:200]}{'…' if len(a.description)>200 else ''}",
                     bg=BG_MID, fg=FG_SEC,
                     font=("TkDefaultFont", 9, "italic"),
                     anchor="w", wraplength=560, justify="left",
                     padx=10, pady=6).pack(fill="x")
