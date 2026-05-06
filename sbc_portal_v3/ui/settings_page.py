"""
Settings page — light/dark mode, gamification toggle, notifications, etc.
"""
import tkinter as tk
from tkinter import ttk
import json, os

from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider

SETTINGS_PATH = os.path.expanduser("~/.sbc_portal/settings.json")

DEFAULT_SETTINGS = {
    "gamification":    True,
    "dark_mode":       True,
    "show_pet_profile": True,
    "grade_alerts":    True,
    "cache_on_login":  True,
    "scroll_speed":    3,
    "font_size":       "Medium",
}


def load_settings() -> dict:
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH) as f:
                s = json.load(f)
            # Merge with defaults for any new keys
            for k, v in DEFAULT_SETTINGS.items():
                s.setdefault(k, v)
            return s
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


class SettingsPage(tk.Frame):

    def __init__(self, parent, data=None, session=None,
                 on_settings_change=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data       = data
        self.on_change  = on_settings_change
        self.settings   = load_settings()
        self._vars      = {}
        self._build()

    def _build(self):
        hdr = PageHeader(self, "⚙️ Settings")
        hdr.pack(fill="x")
        GoldDivider(self).pack(fill="x")

        scroll = ScrollableFrame(self, bg=BG_DARK)
        scroll.pack(fill="both", expand=True)
        area = scroll.inner

        def section(title):
            tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=0)
            tk.Label(area, text=title,
                     bg=BG_DARK, fg=ACCENT,
                     font=("TkDefaultFont", 11, "bold"),
                     padx=20, pady=8).pack(anchor="w")

        def toggle(parent, key, label, subtitle=""):
            row = tk.Frame(parent, bg=BG_CARD,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", padx=20, pady=2)
            info = tk.Frame(row, bg=BG_CARD)
            info.pack(side="left", fill="x", expand=True, padx=16, pady=10)
            tk.Label(info, text=label, bg=BG_CARD, fg=FG_PRIMARY,
                     font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
            if subtitle:
                tk.Label(info, text=subtitle, bg=BG_CARD, fg=FG_MUTED,
                         font=FONT_SMALL, anchor="w").pack(anchor="w")
            var = tk.BooleanVar(value=self.settings.get(key, True))
            self._vars[key] = var
            sw = ttk.Checkbutton(row, variable=var,
                                  command=lambda k=key, v=var: self._on_toggle(k, v))
            sw.pack(side="right", padx=16)
            return var

        # Appearance
        section("🎨 Appearance")
        toggle(area, "dark_mode", "Dark Mode",
               "Navy/gold theme (restart to apply)")

        # Scroll speed
        row = tk.Frame(area, bg=BG_CARD,
                       highlightbackground=BORDER, highlightthickness=1)
        row.pack(fill="x", padx=20, pady=2)
        info = tk.Frame(row, bg=BG_CARD)
        info.pack(side="left", fill="x", expand=True, padx=16, pady=10)
        tk.Label(info, text="Scroll Speed", bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
        tk.Label(info, text="How many lines per trackpad tick (1=slow, 5=fast)",
                 bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL, anchor="w").pack(anchor="w")
        speed_var = tk.IntVar(value=self.settings.get("scroll_speed", 3))
        self._vars["scroll_speed"] = speed_var
        speed_frame = tk.Frame(row, bg=BG_CARD)
        speed_frame.pack(side="right", padx=16)
        ttk.Scale(speed_frame, from_=1, to=5, variable=speed_var,
                  orient="horizontal", length=120,
                  command=lambda v: self._on_toggle("scroll_speed",
                                                     tk.IntVar(value=round(float(v))))).pack()
        tk.Label(speed_frame, textvariable=speed_var,
                 bg=BG_CARD, fg=ACCENT,
                 font=("Georgia", 12, "bold")).pack()

        # Font size
        row2 = tk.Frame(area, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        row2.pack(fill="x", padx=20, pady=2)
        info2 = tk.Frame(row2, bg=BG_CARD)
        info2.pack(side="left", fill="x", expand=True, padx=16, pady=10)
        tk.Label(info2, text="Font Size", bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
        font_var = tk.StringVar(value=self.settings.get("font_size", "Medium"))
        self._vars["font_size"] = font_var
        ttk.Combobox(row2, textvariable=font_var,
                     values=["Small", "Medium", "Large"],
                     state="readonly", width=10).pack(side="right", padx=16)
        font_var.trace_add("write", lambda *a: self._on_toggle("font_size", font_var))

        # Gamification
        section("🐾 Gamification")
        toggle(area, "gamification", "Enable Gamification",
               "Show pet, achievements, crates and XP rewards")
        toggle(area, "show_pet_profile", "Show Pet on Profile",
               "Display your pet on the Profile page")

        # Grades
        section("📊 Grades")
        toggle(area, "grade_alerts", "Grade Change Alerts",
               "Notify when a new grade is posted")
        toggle(area, "cache_on_login", "Cache Data on Login",
               "Save data locally for offline use")

        # Account
        section("🔐 Account")
        clear_btn = tk.Label(area,
                             text="  🗑  Clear Saved Password  ",
                             bg=DANGER, fg="white",
                             font=("TkDefaultFont", 10, "bold"),
                             padx=16, pady=8, cursor="hand2",
                             anchor="w")
        clear_btn.pack(anchor="w", padx=20, pady=4)
        clear_btn.bind("<Button-1>", lambda e: self._clear_password())

        clear_cache = tk.Label(area,
                               text="  🗑  Clear All Cached Data  ",
                               bg="#7f1d1d", fg="white",
                               font=("TkDefaultFont", 10, "bold"),
                               padx=16, pady=8, cursor="hand2",
                               anchor="w")
        clear_cache.pack(anchor="w", padx=20, pady=4)
        clear_cache.bind("<Button-1>", lambda e: self._clear_cache())

        # Version info
        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=16)
        tk.Label(area, text="SBC Portal  ·  Version 2.0  ·  St Bernard's College Essendon",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL,
                 padx=20, pady=8).pack(anchor="w")

    def _on_toggle(self, key, var):
        try:
            self.settings[key] = var.get()
        except Exception:
            pass
        save_settings(self.settings)
        if self.on_change:
            self.on_change(self.settings)

    def _clear_password(self):
        path = os.path.expanduser("~/.sbc_portal/remembered.json")
        if os.path.exists(path):
            os.remove(path)
            tk.messagebox.showinfo("Done", "Saved password cleared.")
        else:
            tk.messagebox.showinfo("Nothing to clear", "No saved password found.")

    def _clear_cache(self):
        import glob, tkinter.messagebox as mb
        if mb.askyesno("Clear Cache", "This will delete all locally cached data. Continue?"):
            for f in glob.glob(os.path.expanduser("~/.sbc_portal/cache_*.json")):
                os.remove(f)
            mb.showinfo("Done", "Cache cleared. Data will reload on next login.")
