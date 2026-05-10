"""
Classes overview — grid of subject cards, click to open class homepage.
"""
import tkinter as tk
from tkinter import ttk
import threading
from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider, Card

SUBJECT_COLOURS = {
    "Mathematics":          ("#1e3a8a", "#dbeafe"),
    "English":              ("#14532d", "#dcfce7"),
    "Science":              ("#713f12", "#fef9c3"),
    "Humanities":           ("#831843", "#fce7f3"),
    "Religion & Society":   ("#4c1d95", "#ede9fe"),
    "Health & PE":          ("#7c2d12", "#ffedd5"),
    "Italian":              ("#164e63", "#cffafe"),
    "Visual Communication": ("#4a1d96", "#f3e8ff"),
    "Business Management":  ("#7f1d1d", "#fee2e2"),
    "Home Room":            ("#334155", "#f1f5f9"),
    "Assembly":             ("#334155", "#f1f5f9"),
}

SUBJECT_ICONS = {
    "Mathematics":          "📐",
    "English":              "📖",
    "Science":              "🔬",
    "Humanities":           "🌍",
    "Religion & Society":   "✝️",
    "Health & PE":          "🏃",
    "Italian":              "🇮🇹",
    "Visual Communication": "🎨",
    "Business Management":  "💼",
    "Home Room":            "🏫",
}

# Confirmed CIDs — others discovered at launch via background thread
KNOWN_CIDS = {
    "31805": "283904",  # Business Management
    "31852": "284233",  # Health & PE
    "31873": "284380",  # Humanities
    "31892": "294720",  # Mathematics
    "31924": "284737",  # Science
    "31926": "284751",  # Visual Communication
}


class ClassesHomePage(tk.Frame):

    def __init__(self, parent, data=None, session=None,
                 on_open_class=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data          = data
        self.session       = session
        self.on_open_class = on_open_class  # callback(class_info)
        self.class_list    = []
        self._build()
        self._load_classes()

    def _build(self):
        hdr = PageHeader(self, "My Classes",
                         subtitle="Click a subject to view class posts and resources")
        hdr.pack(fill="x")
        GoldDivider(self).pack(fill="x")

        self.status = tk.Label(self, text="",
                               bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL)
        self.status.pack(fill="x", padx=16, pady=4)

        self.scroll = ScrollableFrame(self, bg=BG_DARK)
        self.scroll.pack(fill="both", expand=True)
        self.area = self.scroll.inner

    def _load_classes(self):
        if not self.data:
            self._render_classes([])
            return

        # Build class list from academic data
        import datetime
        current_year = datetime.datetime.now().year
        subjects = []
        for yr, subs in self.data.subjects_by_year.items():
            if yr == current_year:
                for s in subs:
                    if s.name and "Assembly" not in s.name:
                        subjects.append(s)

        classes = []
        for s in subjects:
            # Try to find class_id from subject code
            code     = s.code or ""
            class_id = self._code_to_id(code)
            classes.append({
                "name":     s.name,
                "code":     code,
                "class_id": class_id,
                "cid":      self._get_cid(class_id),
                "teacher":  s.teacher or "",
                "grade":    s.grade_raw,
                "grade_str": s.grade or "",
            })

        self.class_list = classes
        self._render_classes(classes)

    def _code_to_id(self, code: str) -> str:
        """Map subject code to class_id. Works for any year group."""
        # Strip year prefix (09, 10, 11, 12) and suffix numbers to get subject key
        known = {
            "09BUSMAN01": "31805", "10BUSMAN": "31805",
            "09ENGL10":   "31827", "10ENGL":   "31827",
            "09HEPE10":   "31852", "10HEPE":   "31852",
            "09HUMS10":   "31873", "10HUMS":   "31873",
            "09ITAL5":    "31885", "10ITAL":   "31885",
            "09MATH10":   "31892", "10MATH":   "31892",
            "09RELS10":   "31914", "10RELS":   "31914",
            "09SCIE10":   "31924", "10SCIE":   "31924",
            "09VISCOM02": "31926", "10VISCOM": "31926",
        }
        if code in known:
            return known[code]
        # For unknown codes, use code directly as class_id and rely on discovery
        return code

    def _get_cid(self, class_id: str) -> str:
        """Get cid from local cache, known CIDs, or class_scraper discovery cache."""
        if class_id in KNOWN_CIDS:
            return KNOWN_CIDS[class_id]
        try:
            from scraper.class_scraper import CLASS_HOMEPAGE_IDS
            return CLASS_HOMEPAGE_IDS.get(class_id, "")
        except Exception:
            return ""

    def _render_classes(self, classes):
        for w in self.area.winfo_children():
            w.destroy()

        if not classes:
            tk.Label(self.area, text="No classes found.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY).pack(pady=40)
            return

        self.status.configure(text=f"{len(classes)} classes this year")

        grid = tk.Frame(self.area, bg=BG_DARK)
        grid.pack(fill="x", padx=16, pady=12)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        for i, cls in enumerate(classes):
            row = i // 3
            col = i % 3
            self._class_card(grid, cls).grid(
                row=row, column=col, padx=8, pady=8, sticky="nsew")

    def _class_card(self, parent, cls: dict):
        name    = cls["name"]
        fg, bg  = SUBJECT_COLOURS.get(name, ("#1e293b", "#f8fafc"))
        icon    = SUBJECT_ICONS.get(name, "📚")

        outer = tk.Frame(parent, bg=BG_CARD,
                         highlightbackground=BORDER,
                         highlightthickness=1)

        # Colour header
        header = tk.Frame(outer, bg=bg)
        header.pack(fill="x")

        tk.Label(header, text=icon,
                 bg=bg, fg=fg,
                 font=("TkDefaultFont", 24),
                 pady=10).pack()
        tk.Label(header, text=name,
                 bg=bg, fg=fg,
                 font=("Georgia", 12, "bold"),
                 wraplength=180, pady=4).pack()

        # Card body
        body = tk.Frame(outer, bg=BG_CARD)
        body.pack(fill="x", padx=14, pady=10)

        if cls.get("code"):
            tk.Label(body, text=cls["code"],
                     bg=BG_CARD, fg=FG_MUTED,
                     font=FONT_SMALL).pack(anchor="w")

        if cls.get("teacher"):
            tk.Label(body, text=f"👤 {cls['teacher']}",
                     bg=BG_CARD, fg=FG_SEC,
                     font=("TkDefaultFont", 10)).pack(anchor="w", pady=4)

        if cls.get("grade"):
            from scraper.grade_logic import fmt_grade, grade_label
            from ui.theme import grade_color
            g     = cls["grade"]
            color = grade_color(g)
            gf = tk.Frame(body, bg=BG_CARD)
            gf.pack(anchor="w")
            tk.Label(gf, text=fmt_grade(g),
                     bg=BG_CARD, fg=color,
                     font=("Georgia", 16, "bold")).pack(side="left")
            tk.Label(gf, text=f"  {grade_label(g)}",
                     bg=BG_CARD, fg=color,
                     font=("TkDefaultFont", 10)).pack(side="left", anchor="s", pady=2)

        # Open button
        tk.Frame(outer, bg=bg, height=3).pack(fill="x")
        btn = tk.Label(outer, text="View Class  →",
                       bg=bg, fg=fg,
                       font=("TkDefaultFont", 10, "bold"),
                       pady=8, cursor="hand2")
        btn.pack(fill="x")
        btn.bind("<Button-1>", lambda e, c=cls: self._open_class(c))

        # Make whole card clickable
        for widget in [outer, header, body]:
            widget.bind("<Button-1>", lambda e, c=cls: self._open_class(c))
            widget.bind("<Enter>",    lambda e, o=outer: o.configure(
                highlightbackground=ACCENT, highlightthickness=2))
            widget.bind("<Leave>",    lambda e, o=outer: o.configure(
                highlightbackground=BORDER, highlightthickness=1))

        return outer

    def _open_class(self, cls: dict):
        if self.on_open_class:
            self.on_open_class(cls)
