"""
Reusable widgets — modern flat design.
"""
import tkinter as tk
from tkinter import ttk
from ui.theme import *


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg=BG_DARK, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        # macOS: bind_all on enter so scroll works regardless of which child widget
        # the mouse is over. Unbind on leave to not interfere with other scrollables.
        self.bind("<Enter>", lambda e: self._bind_scroll())
        self.bind("<Leave>", lambda e: self._unbind_scroll())

    def _bind_scroll(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>",   self._on_scroll_up)
        self.canvas.bind_all("<Button-5>",   self._on_scroll_down)

    def _unbind_scroll(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_inner_configure(self, e):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except tk.TclError:
            pass

    def _on_canvas_configure(self, e):
        try:
            self.canvas.itemconfig(self._win, width=e.width)
        except tk.TclError:
            pass

    _scroll_speed = 3  # class-level, updated by settings

    def _on_mousewheel(self, e):
        try:
            import platform
            delta = e.delta
            speed = getattr(ScrollableFrame, "_scroll_speed", 3)
            if platform.system() == "Darwin":
                units = max(-speed, min(speed, int(-1 * delta)))
                if units:
                    self.canvas.yview_scroll(units, "units")
            elif abs(delta) >= 100:
                self.canvas.yview_scroll(int(-1 * delta / 50), "units")
            else:
                self.canvas.yview_scroll(int(-1 * delta / 120), "units")
        except tk.TclError:
            pass

    def _on_scroll_up(self, e):
        try:
            self.canvas.yview_scroll(-1, "units")
        except tk.TclError:
            pass

    def _on_scroll_down(self, e):
        try:
            self.canvas.yview_scroll(1, "units")
        except tk.TclError:
            pass


class Card(tk.Frame):
    """Flat card with subtle border."""
    def __init__(self, parent, bg=BG_CARD, border=BORDER, **kwargs):
        super().__init__(parent, bg=bg,
                         highlightbackground=border,
                         highlightthickness=1,
                         relief="flat", bd=0, **kwargs)


class AccentCard(tk.Frame):
    """Card with gold left accent stripe."""
    def __init__(self, parent, bg=BG_CARD, accent=ACCENT, **kwargs):
        super().__init__(parent, bg=bg,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         relief="flat", bd=0, **kwargs)
        self._stripe = tk.Frame(self, bg=accent, width=3)
        self._stripe.pack(side="left", fill="y")
        self.body = tk.Frame(self, bg=bg)
        self.body.pack(side="left", fill="both", expand=True)


class PageHeader(tk.Frame):
    """Page header with title and optional right widget."""
    def __init__(self, parent, title, subtitle=None, **kwargs):
        super().__init__(parent, bg=BG_MID, **kwargs)
        # Gold top stripe
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")
        inner = tk.Frame(self, bg=BG_MID)
        inner.pack(fill="x", padx=24, pady=14)
        left = tk.Frame(inner, bg=BG_MID)
        left.pack(side="left")
        tk.Label(left, text=title, bg=BG_MID, fg=FG_PRIMARY,
                 font=FONT_HEADING).pack(anchor="w")
        if subtitle:
            tk.Label(left, text=subtitle, bg=BG_MID, fg=FG_SEC,
                     font=FONT_SMALL).pack(anchor="w")
        self.right_frame = tk.Frame(inner, bg=BG_MID)
        self.right_frame.pack(side="right")


class GradePill(tk.Frame):
    """Coloured pill showing a grade."""
    def __init__(self, parent, grade_str, grade_raw=None, size="normal", **kwargs):
        color = grade_color(grade_raw)
        bg_color = color + "22"  # semi-transparent version approximated with card bg
        super().__init__(parent, bg=BG_CARD, **kwargs)
        font = ("TkDefaultFont", 13, "bold") if size == "large" else ("TkDefaultFont", 10, "bold")
        tk.Label(self, text=grade_str or "—",
                 bg=BG_CARD, fg=color, font=font).pack(padx=8, pady=2)


class StatusPill(tk.Frame):
    """Coloured status badge."""
    STATUS_MAP = {
        "reviewed":        (SUCCESS,  "✓ Reviewed"),
        "submitted":       (ACCENT,   "↑ Submitted"),
        "submitted on time": (ACCENT, "↑ Submitted"),
        "pending":         (WARNING,  "⏳ Pending"),
        "not submitted":   (DANGER,   "✗ Not Submitted"),
        "incomplete":      (DANGER,   "✗ Not Submitted"),
        "mark required":   (WARNING,  "⏳ Awaiting Mark"),
    }

    def __init__(self, parent, status, **kwargs):
        super().__init__(parent, bg=BG_CARD, **kwargs)
        s = (status or "").lower().strip()
        color, label = FG_MUTED, status or "Unknown"
        for key, (c, l) in self.STATUS_MAP.items():
            if key in s:
                color, label = c, l
                break
        tk.Label(self, text=label, bg=BG_CARD, fg=color,
                 font=("TkDefaultFont", 9, "bold")).pack(padx=6, pady=2)


class Divider(tk.Frame):
    def __init__(self, parent, color=BORDER, **kwargs):
        super().__init__(parent, bg=color, height=1, **kwargs)


class GoldLine(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=ACCENT, height=2, **kwargs)


class NavButton(tk.Button):
    def __init__(self, parent, icon, label, active=False, **kwargs):
        self._active = active
        text = f"  {icon}  {label}"
        super().__init__(
            parent, text=text,
            font=("TkDefaultFont", 10, "bold"),
            relief="flat", anchor="w",
            padx=16, pady=10,
            cursor="hand2", bd=0,
            **kwargs
        )
        self.set_active(active)

    def set_active(self, active):
        self._active = active
        if active:
            self.configure(bg=ACCENT, fg=BG_DARK,
                           activebackground=ACCENT_DIM, activeforeground=BG_DARK)
        else:
            self.configure(bg=BG_MID, fg=FG_SEC,
                           activebackground=BG_LIGHT, activeforeground=FG_PRIMARY)


class StatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_MID, height=24, **kwargs)
        tk.Label(self, text="St Bernard's College  ·",
                 bg=BG_MID, fg=ACCENT,
                 font=("Georgia", 8, "italic"), padx=10).pack(side="left")
        self._lbl = tk.Label(self, text="Ready",
                             bg=BG_MID, fg=FG_MUTED,
                             font=FONT_SMALL, anchor="w")
        self._lbl.pack(side="left")

    def set(self, text, color=None):
        self._lbl.configure(text=text, fg=color or FG_MUTED)


class PrimaryButton(tk.Button):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", ACCENT)
        kwargs.setdefault("fg", BG_DARK)
        kwargs.setdefault("font", ("Georgia", 11, "bold"))
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("cursor", "hand2")
        kwargs.setdefault("activebackground", ACCENT_DIM)
        kwargs.setdefault("activeforeground", FG_PRIMARY)
        kwargs.setdefault("padx", 18)
        kwargs.setdefault("pady", 10)
        super().__init__(parent, **kwargs)


class SecondaryButton(tk.Button):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", BG_LIGHT)
        kwargs.setdefault("fg", FG_PRIMARY)
        kwargs.setdefault("font", FONT_LABEL)
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("cursor", "hand2")
        kwargs.setdefault("activebackground", BORDER_LT)
        kwargs.setdefault("activeforeground", FG_PRIMARY)
        kwargs.setdefault("padx", 14)
        kwargs.setdefault("pady", 8)
        super().__init__(parent, **kwargs)


class SectionTitle(tk.Label):
    def __init__(self, parent, text, **kwargs):
        try:
            bg = parent.cget("bg")
        except Exception:
            bg = BG_DARK
        kwargs.setdefault("bg", bg)
        kwargs.setdefault("fg", ACCENT)
        kwargs.setdefault("font", ("Georgia", 12, "bold"))
        kwargs.setdefault("anchor", "w")
        super().__init__(parent, text=text, **kwargs)


class GoldDivider(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=ACCENT, height=2, **kwargs)
