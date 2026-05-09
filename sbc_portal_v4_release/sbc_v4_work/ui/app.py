"""
Main app shell — modern SBC portal with full navigation.
"""
import tkinter as tk
import threading

from ui.theme import *
from ui.widgets import NavButton, StatusBar, GoldLine, Divider
from ui.crest import CrestImage
from ui.login_page import LoginPage


class SBCApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.configure(bg=BG_DARK)
        self._apply_style()
        self.session = None
        self.academic_data = None
        self._show_login()

    def _apply_style(self):
        from tkinter import ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=BG_CARD, background=BG_CARD,
                        foreground=FG_PRIMARY,
                        selectbackground=ACCENT, selectforeground=BG_DARK,
                        arrowcolor=ACCENT, borderwidth=0,
                        lightcolor=BG_CARD, darkcolor=BG_CARD)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG_CARD), ("active", BG_CARD)],
                  background=[("readonly", BG_CARD), ("active", BG_CARD)],
                  foreground=[("readonly", FG_PRIMARY)])
        style.configure("Vertical.TScrollbar",
                        background=BG_MID, troughcolor=BG_DARK,
                        arrowcolor=FG_MUTED, bordercolor=BG_DARK,
                        gripcount=0)
        style.configure("Horizontal.TScale",
                        background=BG_MID, troughcolor=BORDER,
                        slidercolor=ACCENT)
        style.configure("TCheckbutton",
                        background=BG_MID, foreground=FG_PRIMARY,
                        activebackground=BG_MID)
        # Make option menus dark
        self.root.option_add("*TCombobox*Listbox.background", BG_CARD)
        self.root.option_add("*TCombobox*Listbox.foreground", FG_PRIMARY)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", BG_DARK)
        # Mac-specific: force all Button widgets to use flat rendering with dark bg
        self.root.option_add("*Button.relief", "flat")
        self.root.option_add("*Button.highlightThickness", "0")
        self.root.option_add("*Button.highlightBackground", BG_DARK)
        self.root.option_add("*Button.borderWidth", "0")
        self.root.option_add("*Button.cursor", "hand2")
        # On Mac, prevent the default system button appearance
        import platform
        if platform.system() == "Darwin":
            style.configure("TButton", relief="flat", background=BG_CARD)
            self.root.tk.call("tk", "scaling", 1.5)

    def _show_login(self):
        self._clear_root()
        LoginPage(self.root, on_login_success=self._on_login_success).pack(
            fill="both", expand=True)

    def _apply_saved_theme(self):
        from scraper.auth import load_settings
        from ui.theme import set_theme
        s = load_settings()
        if "theme" in s:
            set_theme(s["theme"])

    def _on_login_success(self, session):
        self.session  = session
        self._pending_username = session.username
        self._offline_mode = False
        self._offline_saved_at = ""
        self._show_loading()

    def _show_loading(self):
        self._clear_root()
        frame = tk.Frame(self.root, bg=BG_DARK)
        frame.pack(fill="both", expand=True)
        tk.Frame(frame, bg=ACCENT, height=4).pack(fill="x")

        center = tk.Frame(frame, bg=BG_DARK)
        center.place(relx=0.5, rely=0.5, anchor="center")

        CrestImage(center, width=180, bg=BG_DARK).pack(pady=20)

        self._spinner_label = tk.Label(center, text="◐",
                                       bg=BG_DARK, fg=ACCENT,
                                       font=("TkDefaultFont", 24))
        self._spinner_label.pack()

        tk.Label(center, text="Loading academic data…",
                 bg=BG_DARK, fg=FG_SEC,
                 font=("Georgia", 13)).pack(pady=8)

        self.loading_status = tk.Label(
            center, text="Fetching grades from mySBC…",
            bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL,
            wraplength=360)
        self.loading_status.pack()

        self._spinner_idx = 0
        self._animate_spinner()
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _animate_spinner(self):
        try:
            chars = ["◐","◓","◑","◒"]
            self._spinner_idx = (self._spinner_idx+1) % len(chars)
            self._spinner_label.configure(text=chars[self._spinner_idx])
            self.root.after(180, self._animate_spinner)
        except tk.TclError:
            pass

    def _fetch_data(self):
        from scraper.parser import fetch_all_data
        from scraper.auth import NetworkError, save_data_cache, load_data_cache

        def status(msg):
            self.root.after(0, lambda: self._update_status(msg))

        # Offline session (loaded from cache at login screen)
        if hasattr(self.session, "_offline_data"):
            self.academic_data = self.session._offline_data
            self._offline_mode = True
            self._offline_saved_at = getattr(self.session, "_offline_saved_at", "")
            self.root.after(0, self._show_dashboard)
            return

        try:
            status("Fetching grades from mySBC…")
            data = fetch_all_data(self.session)
            self.academic_data = data
            save_data_cache(data, self.session.username)
            self.root.after(0, self._show_dashboard)
        except Exception as e:
            # Any failure — try cache
            username = getattr(self.session, "username", "") or getattr(self, "_pending_username", "")
            cached = load_data_cache(username)
            if cached:
                data, saved_at = cached
                self.academic_data = data
                self._offline_mode = True
                self._offline_saved_at = saved_at
                self.root.after(0, self._show_dashboard)
            else:
                msg = str(e)
                self.root.after(0, lambda: self._show_error(f"Error: {msg}"))

    def _update_status(self, msg):
        try:
            self.loading_status.configure(text=msg)
        except (tk.TclError, AttributeError):
            pass

    def _show_error(self, msg):
        self._clear_root()
        frame = tk.Frame(self.root, bg=BG_DARK)
        frame.pack(fill="both", expand=True)
        tk.Frame(frame, bg=DANGER, height=4).pack(fill="x")
        center = tk.Frame(frame, bg=BG_DARK)
        center.place(relx=0.5, rely=0.5, anchor="center")
        CrestImage(center, width=140, bg=BG_DARK).pack(pady=16)
        tk.Label(center, text=msg, bg=BG_DARK, fg=DANGER,
                 font=FONT_BODY, wraplength=480, justify="center").pack(pady=8)
        tk.Button(center, text="← Back to Login", command=self._show_login,
                  bg=ACCENT, fg=BG_DARK, font=("Georgia", 11, "bold"),
                  relief="flat", padx=18, pady=10, cursor="hand2").pack(pady=8)

    def _show_dashboard(self):
        self._clear_root()
        self._build_shell()
        # Discover CIDs for classes that don't have them yet (background)
        self._discover_cids_background()

    def _discover_cids_background(self):
        """Discover homepage CIDs for all of this user's classes."""
        import threading
        from scraper.class_scraper import discover_all_cids, CLASS_HOMEPAGE_IDS

        # Get class IDs from the user's actual loaded data
        all_ids = set()
        if self.academic_data:
            import datetime
            yr = datetime.datetime.now().year
            for year, subjects in self.academic_data.subjects_by_year.items():
                if year >= yr - 1:  # current and last year
                    for s in subjects:
                        if s.code:
                            # class_id is stored as s.class_id if available
                            cid = getattr(s, 'class_id', None)
                            if cid:
                                all_ids.add(str(cid))

        # Also include hardcoded known IDs as fallback
        all_ids.update([
            "31805","31827","31852","31873","31885",
            "31892","31914","31924","31926"
        ])

        missing = [i for i in all_ids if not CLASS_HOMEPAGE_IDS.get(i)]
        if not missing:
            return

        session = self.session
        def run():
            try:
                discover_all_cids(session, list(missing))
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

    def _build_shell(self):
        # Offline mode banner
        if getattr(self, "_offline_mode", False):
            banner = tk.Frame(self.root, bg=WARNING)
            banner.pack(fill="x", side="top")
            saved = getattr(self, "_offline_saved_at", "")[:16].replace("T"," ")
            tk.Label(banner,
                     text=f"⚠  Offline mode — showing cached data from {saved}  "
                          f"(school WiFi may be blocking mySBC)",
                     bg=WARNING, fg=BG_DARK,
                     font=("TkDefaultFont", 9, "bold"),
                     pady=4).pack()
        if getattr(self, "session", None) and getattr(self.session, "on_school_wifi", False):
            banner2 = tk.Frame(self.root, bg="#7c3d00")
            banner2.pack(fill="x", side="top")
            tk.Label(banner2,
                     text="⚠  Connected via school WiFi — SSL verification disabled",
                     bg="#7c3d00", fg="#ffedd5",
                     font=("TkDefaultFont", 9, "bold"),
                     pady=3).pack()
        tk.Frame(self.root, bg=ACCENT, height=3).pack(fill="x", side="top")
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side="bottom", fill="x")

        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill="both", expand=True)

        # ── Sidebar ───────────────────────────────────────────────────
        sidebar = tk.Frame(main, bg=BG_MID, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Crest
        CrestImage(sidebar, width=150, bg=BG_MID).pack(pady=4)
        tk.Label(sidebar, text="Academic Portal",
                 bg=BG_MID, fg=ACCENT,
                 font=("Georgia", 9, "bold")).pack(pady=2)
        tk.Frame(sidebar, bg=ACCENT, height=1).pack(fill="x", padx=20, pady=8)

        # User chip
        profile = self.academic_data.profile
        name = (profile.display_name or profile.username
                or self.session.username or "Student")
        yr = profile.year_level or ""

        user = tk.Frame(sidebar, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        user.pack(fill="x", padx=12, pady=10)
        ui = tk.Frame(user, bg=BG_CARD)
        ui.pack(fill="x", padx=10, pady=8)
        tk.Label(ui, text="👤", bg=BG_CARD, fg=ACCENT,
                 font=("TkDefaultFont", 13)).pack(side="left")
        txt = tk.Frame(ui, bg=BG_CARD)
        txt.pack(side="left", padx=6)
        tk.Label(txt, text=name[:20], bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 10, "bold"), anchor="w").pack(anchor="w")
        if yr:
            tk.Label(txt, text=yr, bg=BG_CARD, fg=FG_MUTED,
                     font=FONT_SMALL, anchor="w").pack(anchor="w")

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("grades",          "📊", "Grades"),
            ("myclasses",       "🏫", "My Classes"),
            ("assessments",     "📋", "Assessments"),
            ("upcoming",        "📅", "Upcoming"),
            ("calendar",        "📆", "Calendar"),
            ("planner",         "🗓", "Study Planner"),
            ("timetable",       "🕐", "Timetable"),
            ("profile",         "👤", "Profile"),
            ("_sep", "", ""),
            ("canteen",         "🍽", "Canteen"),
            ("groups",          "👥", "My Groups"),
            ("student_services","🏫", "Student Services"),
            ("_sep2", "", ""),
            ("pet",             "🐾", "My Pet"),
            ("settings",        "⚙️", "Settings"),
        ]
        for key, icon, label in nav_items:
            if key in ("_sep", "_sep2"):
                tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)
                label = "SCHOOL" if key == "_sep" else "MORE"
                tk.Label(sidebar, text=label, bg=BG_MID, fg=ACCENT,
                         font=("TkDefaultFont", 8, "bold"),
                         padx=12, pady=4, anchor="w").pack(fill="x")
                continue
            lbl = tk.Label(sidebar,
                           text=f"  {icon}  {label}",
                           bg=BG_MID, fg=FG_SEC,
                           font=("TkDefaultFont", 10, "bold"),
                           anchor="w", padx=16, pady=10,
                           cursor="hand2")
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, k=key: self._navigate(k))
            lbl.bind("<Enter>",    lambda e, l=lbl, k=key:
                     l.configure(bg=ACCENT if self._current_page==k else BG_LIGHT,
                                 fg=BG_DARK if self._current_page==k else FG_PRIMARY))
            lbl.bind("<Leave>",    lambda e, l=lbl, k=key:
                     l.configure(bg=ACCENT if self._current_page==k else BG_MID,
                                 fg=BG_DARK if self._current_page==k else FG_SEC))
            self.nav_buttons[key] = lbl
            lbl.bind("<Enter>",    lambda e, l=lbl, k=key:
                     l.configure(bg=ACCENT if self._current_page==k else BG_LIGHT,
                                 fg=BG_DARK if self._current_page==k else FG_PRIMARY))
            lbl.bind("<Leave>",    lambda e, l=lbl, k=key:
                     l.configure(bg=ACCENT if self._current_page==k else BG_MID,
                                 fg=BG_DARK if self._current_page==k else FG_SEC))

        tk.Frame(sidebar, bg=BG_MID).pack(fill="both", expand=True)
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x")
        so = tk.Label(sidebar, text="  ⇥  Sign Out",
                     bg=BG_MID, fg=FG_MUTED,
                     font=("TkDefaultFont", 10),
                     anchor="w", padx=16, pady=10,
                     cursor="hand2")
        so.pack(fill="x")
        so.bind("<Button-1>", lambda e: self._logout())
        so.bind("<Enter>", lambda e: so.configure(bg=DANGER, fg=FG_PRIMARY))
        so.bind("<Leave>", lambda e: so.configure(bg=BG_MID, fg=FG_MUTED))

        # Content
        self.content = tk.Frame(main, bg=BG_DARK)
        self.content.pack(side="right", fill="both", expand=True)

        self._current_page = "grades"
        self._navigate("grades")

    def _navigate(self, key):
        self._current_page = key
        for k, lbl in self.nav_buttons.items():
            if k == key:
                lbl.configure(bg=ACCENT, fg=BG_DARK,
                              font=("TkDefaultFont", 10, "bold"))
            else:
                is_we = False
                lbl.configure(bg=BG_MID, fg=FG_SEC,
                              font=("TkDefaultFont", 10, "bold"))
        for w in self.content.winfo_children():
            w.destroy()

        data = self.academic_data
        if key == "grades":
            from ui.grades_page import GradesDashboard
            GradesDashboard(self.content, data).pack(fill="both", expand=True)
            self.status_bar.set("Grades Dashboard")
        elif key == "myclasses":
            from ui.classes_home_page import ClassesHomePage
            ClassesHomePage(self.content, data, self.session,
                            on_open_class=self._open_class_page).pack(fill="both", expand=True)
            self.status_bar.set("My Classes")
        elif key == "assessments":
            from ui.classes_page import ClassesPage
            ClassesPage(self.content, data).pack(fill="both", expand=True)
            self.status_bar.set("Assessments")
        elif key == "upcoming":
            from ui.upcoming_page import UpcomingPage
            UpcomingPage(self.content, data).pack(fill="both", expand=True)
            self.status_bar.set("Upcoming Assignments")
        elif key == "planner":
            from ui.planner_page import PlannerPage
            PlannerPage(self.content, data).pack(fill="both", expand=True)
            self.status_bar.set("Study Planner")
        elif key == "calendar":
            from ui.calendar_page import CalendarPage
            uid = data.profile.student_id if data.profile else "11953"
            CalendarPage(self.content, data, self.session, user_id=uid).pack(fill="both", expand=True)
            self.status_bar.set("Calendar")
        elif key == "timetable":
            from ui.timetable_page import TimetablePage
            TimetablePage(self.content, data, self.session).pack(fill="both", expand=True)
            self.status_bar.set("Timetable")
        elif key == "profile":
            from ui.profile_page import ProfilePage
            ProfilePage(self.content, data, self.session).pack(fill="both", expand=True)
            self.status_bar.set("Profile")
        elif key == "canteen":
            from ui.canteen_page import CanteenPage
            CanteenPage(self.content, data, self.session).pack(fill="both", expand=True)
            self.status_bar.set("Canteen")
        elif key == "groups":
            from ui.groups_page import GroupsPage
            GroupsPage(self.content, data, self.session).pack(fill="both", expand=True)
            self.status_bar.set("My Groups")
        elif key == "student_services":
            from ui.student_services_page import StudentServicesPage
            StudentServicesPage(self.content, data, self.session).pack(fill="both", expand=True)
            self.status_bar.set("Student Services")
        elif key == "pet":
            from ui.settings_page import load_settings
            from ui.pet_page import PetPage
            PetPage(self.content, data, self.session,
                    settings=load_settings()).pack(fill="both", expand=True)
            self.status_bar.set("My Pet")
        elif key == "market":
            from ui.market_page import MarketPage
            MarketPage(self.content, data, self.session).pack(fill="both", expand=True)
            self.status_bar.set("Market")
        elif key == "index":
            from ui.index_page import IndexPage
            IndexPage(self.content, data, self.session).pack(fill="both", expand=True)
            self.status_bar.set("Collection Index")
        elif key == "settings":
            from ui.settings_page import SettingsPage
            SettingsPage(self.content, data, self.session,
                         on_settings_change=self._on_settings_change,
                         app=self).pack(fill="both", expand=True)
            self.status_bar.set("Settings")

    def _open_class_page(self, cls_info: dict):
        """Navigate into a specific class homepage."""
        for w in self.content.winfo_children():
            w.destroy()
        from ui.class_home_page import ClassHomePage
        ClassHomePage(self.content, cls_info, self.academic_data,
                      self.session).pack(fill="both", expand=True)
        self.status_bar.set(f"{cls_info.get('name','Class')} — Homepage")

    def _on_settings_change(self, settings: dict):
        """Handle settings changes — apply scroll speed etc immediately."""
        from ui.widgets import ScrollableFrame
        # Update scroll speed globally
        speed = settings.get("scroll_speed", 3)
        ScrollableFrame._scroll_speed = speed

    def _logout(self):
        if self.session:
            self.session.logout()
            self.session = None
        self.academic_data = None
        self._show_login()

    def _clear_root(self):
        for w in self.root.winfo_children():
            w.destroy()
