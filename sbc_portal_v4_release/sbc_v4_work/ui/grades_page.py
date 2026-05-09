"""
Grades Dashboard — 1dp averages, fixed colours, clean design.
"""
import tkinter as tk
from tkinter import ttk
from ui.theme import *
from ui.widgets import (ScrollableFrame, Card, GoldLine,
                        PageHeader, SectionTitle, Divider, GoldDivider)
from data.models import AcademicData
from scraper.grade_logic import compute_subject_grade, is_formative, fmt_grade, grade_label


class GradesDashboard(tk.Frame):

    def __init__(self, parent, data: AcademicData, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data = data
        self.selected_year = tk.StringVar()
        self._build()

    def _build(self):
        hdr = PageHeader(self, "Grades Dashboard")
        hdr.pack(fill="x")

        years = self.data.all_years()
        if years:
            yf = tk.Frame(hdr.right_frame, bg=BG_MID)
            yf.pack()
            tk.Label(yf, text="Year", bg=BG_MID, fg=FG_MUTED,
                     font=FONT_SMALL).pack(side="left", padx=(0,6))
            self.selected_year.set(str(years[0]))
            cb = ttk.Combobox(yf, textvariable=self.selected_year,
                               values=[str(y) for y in years],
                               state="readonly", width=7)
            cb.pack(side="left")
            cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        GoldDivider(self).pack(fill="x")
        self.scroll = ScrollableFrame(self, bg=BG_DARK)
        self.scroll.pack(fill="both", expand=True)
        self.area = self.scroll.inner
        self._refresh()

    def _refresh(self):
        for w in self.area.winfo_children():
            w.destroy()
        try:
            year = int(self.selected_year.get())
        except (ValueError, tk.TclError):
            year = None

        subjects = self.data.subjects_by_year.get(year, []) if year else []
        if not subjects:
            tk.Label(self.area, text="No grade data available for this year.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY,
                     justify="center").pack(pady=60)
            return

        # Compute grades for all subjects
        processed = []
        for subj in subjects:
            g_raw, used = compute_subject_grade(subj.assignments)
            # Fall back to scraped grade if computation yields nothing
            if g_raw is None:
                g_raw = subj.grade_raw
            processed.append((subj, g_raw, used))

        # Overall average — sum of every individual task / total task count
        # (more accurate than averaging subject averages)
        all_task_grades = []
        for subj, _, used in processed:
            all_task_grades.extend(t.grade_raw for t in used if t.grade_raw is not None)
        overall = round(sum(all_task_grades) / len(all_task_grades), 1) if all_task_grades else None

        # ── Summary strip ─────────────────────────────────────────────
        strip = tk.Frame(self.area, bg=BG_MID)
        strip.pack(fill="x")
        tk.Frame(strip, bg=ACCENT, height=2).pack(fill="x")

        metrics = tk.Frame(strip, bg=BG_MID)
        metrics.pack(fill="x", padx=28, pady=16)

        def metric(label, value, color=FG_PRIMARY, sublabel=""):
            f = tk.Frame(metrics, bg=BG_MID)
            f.pack(side="left", padx=24)
            tk.Label(f, text=label, bg=BG_MID, fg=FG_MUTED,
                     font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
            tk.Label(f, text=value, bg=BG_MID, fg=color,
                     font=("Georgia", 28, "bold")).pack(anchor="w")
            if sublabel:
                tk.Label(f, text=sublabel, bg=BG_MID, fg=color,
                         font=("TkDefaultFont", 10)).pack(anchor="w")

        avg_color = grade_color(overall) if overall else FG_MUTED
        metric("OVERALL AVERAGE",
               fmt_grade(overall),
               avg_color,
               grade_label(overall))
        metric("SUBJECTS", str(len(subjects)), FG_PRIMARY)
        metric("GRADED",   str(len([g for _,g,_ in processed if g is not None])), ACCENT)
        metric("PENDING",  str(len([g for _,g,_ in processed if g is None])), FG_MUTED)

        # ── Subject grid ──────────────────────────────────────────────
        pad = tk.Frame(self.area, bg=BG_DARK)
        pad.pack(fill="x", padx=20, pady=4)
        SectionTitle(pad, "Subject Results").pack(anchor="w")

        grid = tk.Frame(self.area, bg=BG_DARK)
        grid.pack(fill="x", padx=16, pady=4)

        for i, (subj, g_raw, tasks) in enumerate(processed):
            self._subject_card(grid, subj, g_raw, tasks).grid(
                row=i//2, column=i%2, padx=6, pady=6, sticky="nsew")

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def _subject_card(self, parent, subj, g_raw, tasks):
        card = Card(parent, bg=BG_CARD)

        bar_color = grade_color(g_raw) if g_raw else BORDER
        tk.Frame(card, bg=bar_color, height=3).pack(fill="x")

        body = tk.Frame(card, bg=BG_CARD)
        body.pack(fill="x", padx=16, pady=14)

        tk.Label(body, text=subj.name or subj.code,
                 bg=BG_CARD, fg=FG_PRIMARY,
                 font=("Georgia", 12, "bold"),
                 anchor="w", wraplength=260).pack(anchor="w")

        if subj.code and subj.code != subj.name:
            tk.Label(body, text=subj.code, bg=BG_CARD, fg=FG_MUTED,
                     font=FONT_SMALL).pack(anchor="w")

        if subj.teacher:
            tk.Label(body, text=f"👤 {subj.teacher}",
                     bg=BG_CARD, fg=FG_SEC, font=FONT_SMALL).pack(anchor="w", pady=0)

        Divider(body, color=BORDER_LT).pack(fill="x", pady=10)

        bottom = tk.Frame(body, bg=BG_CARD)
        bottom.pack(fill="x")

        if g_raw is not None:
            color = grade_color(g_raw)
            # Grade value — 1 decimal
            tk.Label(bottom, text=fmt_grade(g_raw),
                     bg=BG_CARD, fg=color,
                     font=("Georgia", 20, "bold")).pack(side="left")
            lbl = grade_label(g_raw)
            if lbl:
                tk.Label(bottom, text=lbl, bg=BG_CARD, fg=color,
                         font=("TkDefaultFont", 10),
                         padx=4).pack(side="left", anchor="s", pady=2)
        else:
            tk.Label(bottom, text="Pending",
                     bg=BG_CARD, fg=FG_MUTED,
                     font=("TkDefaultFont", 11)).pack(side="left")

        n_tasks = len([t for t in tasks if t.grade_raw is not None])
        if n_tasks:
            tk.Label(bottom, text=f"{n_tasks} task{'s' if n_tasks!=1 else ''}",
                     bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL).pack(
                side="right", anchor="s", pady=2)

        return card
