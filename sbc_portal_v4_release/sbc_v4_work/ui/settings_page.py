"""
Settings page — all app settings in one place.
"""
import tkinter as tk
from tkinter import ttk
import json, os

from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider

SETTINGS_PATH = os.path.expanduser("~/.sbc_portal/settings.json")

DEFAULT_SETTINGS = {
    "gamification":     True,
    "dark_mode":        True,
    "theme":            "dark",
    "show_pet_profile": True,
    "grade_alerts":     True,
    "cache_on_login":   True,
    "scroll_speed":     3,
    "font_size":        "Medium",
}


def load_settings() -> dict:
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH) as f:
                s = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                s.setdefault(k, v)
            return s
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


class SettingsPage(tk.Frame):

    def __init__(self, parent, data=None, session=None,
                 on_settings_change=None, app=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data      = data
        self.session   = session
        self.app       = app
        self.on_change = on_settings_change
        self.settings  = load_settings()
        self._vars     = {}
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
            tk.Label(area, text=title, bg=BG_DARK, fg=ACCENT,
                     font=("TkDefaultFont", 11, "bold"),
                     padx=20, pady=8).pack(anchor="w")

        def toggle(key, label, subtitle=""):
            row = tk.Frame(area, bg=BG_CARD,
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
            ttk.Checkbutton(row, variable=var,
                            command=lambda k=key, v=var: self._on_toggle(k, v)
                            ).pack(side="right", padx=16)
            return var

        # ── Appearance ────────────────────────────────────────────────────────
        section("🎨 Appearance")
        toggle("dark_mode", "Dark Mode", "Navy/gold colour scheme")

        # Theme selector
        try:
            from ui.theme import THEMES, set_theme, get_theme_name
            theme_row = tk.Frame(area, bg=BG_CARD,
                                 highlightbackground=BORDER, highlightthickness=1)
            theme_row.pack(fill="x", padx=20, pady=2)
            ti = tk.Frame(theme_row, bg=BG_CARD)
            ti.pack(side="left", fill="x", expand=True, padx=16, pady=10)
            tk.Label(ti, text="UI Theme", bg=BG_CARD, fg=FG_PRIMARY,
                     font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
            tk.Label(ti, text="Restart the app to fully apply the new theme",
                     bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL, anchor="w").pack(anchor="w")
            tv = tk.StringVar(value=self.settings.get("theme", get_theme_name()))
            tm = tk.OptionMenu(theme_row, tv, *list(THEMES.keys()),
                               command=lambda v: self._save_theme(v))
            tm.configure(bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SMALL,
                         activebackground=BG_LIGHT, highlightthickness=0, relief="flat")
            tm["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SMALL)
            tm.pack(side="right", padx=16, pady=10)
        except Exception:
            pass

        # Scroll speed
        speed_row = tk.Frame(area, bg=BG_CARD,
                             highlightbackground=BORDER, highlightthickness=1)
        speed_row.pack(fill="x", padx=20, pady=2)
        si = tk.Frame(speed_row, bg=BG_CARD)
        si.pack(side="left", fill="x", expand=True, padx=16, pady=10)
        tk.Label(si, text="Scroll Speed", bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
        tk.Label(si, text="1 = slow, 5 = fast",
                 bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL, anchor="w").pack(anchor="w")
        sv = tk.IntVar(value=self.settings.get("scroll_speed", 3))
        self._vars["scroll_speed"] = sv
        sf = tk.Frame(speed_row, bg=BG_CARD)
        sf.pack(side="right", padx=16)
        ttk.Scale(sf, from_=1, to=5, variable=sv, orient="horizontal", length=120,
                  command=lambda v: self._on_toggle(
                      "scroll_speed", tk.IntVar(value=round(float(v))))).pack()
        tk.Label(sf, textvariable=sv, bg=BG_CARD, fg=ACCENT,
                 font=("Georgia", 12, "bold")).pack()

        # Font size
        font_row = tk.Frame(area, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
        font_row.pack(fill="x", padx=20, pady=2)
        fi = tk.Frame(font_row, bg=BG_CARD)
        fi.pack(side="left", fill="x", expand=True, padx=16, pady=10)
        tk.Label(fi, text="Font Size", bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
        fv = tk.StringVar(value=self.settings.get("font_size", "Medium"))
        self._vars["font_size"] = fv
        ttk.Combobox(font_row, textvariable=fv, values=["Small","Medium","Large"],
                     state="readonly", width=10).pack(side="right", padx=16)
        fv.trace_add("write", lambda *a: self._on_toggle("font_size", fv))

        # ── Gamification ──────────────────────────────────────────────────────
        section("🐾 Gamification")
        toggle("gamification", "Enable Gamification",
               "Show the My Pet tab — crates, achievements, market and XP rewards")
        toggle("show_pet_profile", "Show Pet on Profile",
               "Display your pet on the Profile page")

        # ── Grades ────────────────────────────────────────────────────────────
        section("📊 Grades")
        toggle("grade_alerts", "Grade Change Alerts",
               "Notify when a new grade is posted")
        toggle("cache_on_login", "Cache Data on Login",
               "Save data locally for offline use")

        # ── Data & Sync ───────────────────────────────────────────────────────
        section("🔄 Data & Sync")
        last_updated = "Never"
        if self.app and getattr(self.app, "_last_refreshed", None):
            last_updated = self.app._last_refreshed.strftime("%d %b %Y at %H:%M")

        sync_row = tk.Frame(area, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
        sync_row.pack(fill="x", padx=20, pady=2)
        sync_info = tk.Frame(sync_row, bg=BG_CARD)
        sync_info.pack(side="left", fill="x", expand=True, padx=16, pady=10)
        tk.Label(sync_info, text="Auto Refresh", bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11, "bold"), anchor="w").pack(anchor="w")
        tk.Label(sync_info, text="Data refreshes automatically every 10 minutes.",
                 bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL, anchor="w").pack(anchor="w")
        self._last_updated_var = tk.StringVar(value=f"Last updated: {last_updated}")
        tk.Label(sync_info, textvariable=self._last_updated_var,
                 bg=BG_CARD, fg=ACCENT, font=FONT_SMALL, anchor="w").pack(anchor="w", pady=2)

        self._refresh_btn = tk.Label(sync_row, text="  ↻  Refresh Now  ",
                                     bg=ACCENT, fg=BG_DARK,
                                     font=("TkDefaultFont", 10, "bold"),
                                     padx=14, pady=8, cursor="hand2")
        self._refresh_btn.pack(side="right", padx=16, pady=10)
        self._refresh_btn.bind("<Button-1>", lambda e: self._manual_refresh())

        # ── Account ───────────────────────────────────────────────────────────
        section("🔐 Account")
        for text, bg_col, cmd in [
            ("  🗑  Clear Saved Password  ", DANGER,    self._clear_password),
            ("  🗑  Clear All Cached Data  ", "#7f1d1d", self._clear_cache),
        ]:
            btn = tk.Label(area, text=text, bg=bg_col, fg="white",
                           font=("TkDefaultFont", 10, "bold"),
                           padx=16, pady=8, cursor="hand2", anchor="w")
            btn.pack(anchor="w", padx=20, pady=4)
            btn.bind("<Button-1>", lambda e, c=cmd: c())

        # ── Version ───────────────────────────────────────────────────────────
        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=16)
        tk.Label(area, text="SBC Portal  ·  Version 4.0  ·  St Bernard's College Essendon",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL,
                 padx=20, pady=8).pack(anchor="w")

    def _save_theme(self, name):
        try:
            from ui.theme import THEMES, set_theme
            set_theme(name)
            self.settings["theme"] = name
            save_settings(self.settings)
            import tkinter.messagebox as mb
            mb.showinfo("Theme Changed",
                        f"Theme set to '{THEMES[name]['name']}'.\nRestart the app to fully apply.")
        except Exception:
            pass

    def _on_toggle(self, key, var):
        try:
            self.settings[key] = var.get()
        except Exception:
            pass
        save_settings(self.settings)
        if self.on_change:
            self.on_change(self.settings)

    def _manual_refresh(self):
        if not self.app:
            return
        started = self.app.refresh_now()
        if started:
            self._refresh_btn.configure(text="  ↻  Refreshing…  ",
                                        bg=BG_MID, fg=FG_MUTED)
            self._last_updated_var.set("Last updated: Refreshing…")
            self._poll_refresh()
        else:
            self._last_updated_var.set("Last updated: Already refreshing…")

    def _poll_refresh(self):
        if not self.app:
            return
        if getattr(self.app, "_is_refreshing", False):
            self.after(1000, self._poll_refresh)
        else:
            self._refresh_btn.configure(text="  ↻  Refresh Now  ",
                                        bg=ACCENT, fg=BG_DARK)
            last = getattr(self.app, "_last_refreshed", None)
            if last:
                self._last_updated_var.set(
                    f"Last updated: {last.strftime('%d %b %Y at %H:%M')}")
            else:
                self._last_updated_var.set(
                    "Last updated: Failed — check your connection")

    def _clear_password(self):
        import tkinter.messagebox as mb
        path = os.path.expanduser("~/.sbc_portal/remembered.json")
        if os.path.exists(path):
            os.remove(path)
            mb.showinfo("Password Cleared", "Saved password has been deleted.")
        else:
            mb.showinfo("Nothing to Clear", "No saved password found.")

    def _clear_cache(self):
        import tkinter.messagebox as mb
        if not mb.askyesno("Clear Cache",
                           "This will delete all locally cached data.\n"
                           "You'll need to log in and wait for data to reload.\nContinue?"):
            return
        import glob
        for f in glob.glob(os.path.expanduser("~/.sbc_portal/cache_*.json")):
            os.remove(f)
        mb.showinfo("Cache Cleared", "All cached data has been deleted.")
