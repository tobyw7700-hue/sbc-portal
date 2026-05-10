"""
Student Services Homepage — navigation grid + absences info.
"""
import tkinter as tk
import webbrowser
from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider

BASE_URL = "https://mysbc.sbc.vic.edu.au"

# Services grid matching the mySBC page
SERVICES = [
    ("Canteen",                          "🍽", "https://shop.sbc.vic.edu.au/mymonitor/main.php"),
    ("Careers",                          "💼", f"{BASE_URL}/homepage/5352"),
    ("ICT Support",                      "💻", f"{BASE_URL}/homepage/3601"),
    ("Immunisations",                    "💉", f"{BASE_URL}/homepage/24200"),
    ("Student Council",                  "🏫", f"{BASE_URL}/homepage/22574"),
    ("Transport Information",            "🚌", f"{BASE_URL}/homepage/22605"),
    ("Mitchell Library",                 "📚", f"{BASE_URL}/homepage/6966"),
    ("St Bernard's College Music Dept",  "🎵", f"{BASE_URL}/homepage/3918"),
    ("Uniform",                          "👕", f"{BASE_URL}/homepage/10057"),
    ("Sport",                            "⚽", f"{BASE_URL}/homepage/997"),
    ("Boys Writing",                     "✏️", f"{BASE_URL}/homepage/3135"),
]


class StudentServicesPage(tk.Frame):
    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._build()

    def _build(self):
        hdr = PageHeader(self, "Student Services",
                         subtitle="Student Services Homepage")
        hdr.pack(fill="x")
        GoldDivider(self).pack(fill="x")

        scroll = ScrollableFrame(self, bg=BG_DARK)
        scroll.pack(fill="both", expand=True)
        area = scroll.inner

        # Services grid
        tk.Label(area, text="Services",
                 bg=BG_DARK, fg=ACCENT,
                 font=("Georgia", 14, "bold"),
                 padx=20, pady=12).pack(anchor="w")

        grid = tk.Frame(area, bg=BG_DARK)
        grid.pack(fill="x", padx=16, pady=16)
        for col in range(5):
            grid.columnconfigure(col, weight=1)

        for i, (name, icon, url) in enumerate(SERVICES):
            row = i // 5
            col = i % 5
            grid.rowconfigure(row, weight=1)

            cell = tk.Label(grid,
                            text=f"{icon}\n{name}",
                            bg=ACCENT, fg=BG_DARK,
                            font=("TkDefaultFont", 10, "bold"),
                            padx=8, pady=14,
                            cursor="hand2",
                            wraplength=130,
                            justify="center")
            cell.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            cell.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            cell.bind("<Enter>",    lambda e, c=cell: c.configure(bg=ACCENT_DIM))
            cell.bind("<Leave>",    lambda e, c=cell: c.configure(bg=ACCENT))

        # Divider
        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)

        # Student Absences section
        tk.Label(area, text="Student Absences",
                 bg=BG_DARK, fg=ACCENT,
                 font=("Georgia", 14, "bold"),
                 padx=20, pady=8).pack(anchor="w")

        abs_card = tk.Frame(area, bg=BG_CARD,
                            highlightbackground=BORDER,
                            highlightthickness=1)
        abs_card.pack(fill="x", padx=16, pady=8)

        body = tk.Frame(abs_card, bg=BG_CARD)
        body.pack(fill="x", padx=20, pady=16)

        intro = ("The College requires notification from a parent/caregiver should your son be absent "
                 "from school on any given day during the term. This notification should be sent using "
                 "the nominated parent/caregiver mobile number or email registered in the MySBC parent "
                 "portal and sent prior to, or before 8:15 am on the day of absence.")
        tk.Label(body, text=intro, bg=BG_CARD, fg=FG_SEC,
                 font=("TkDefaultFont", 11), wraplength=720,
                 justify="left", anchor="w").pack(fill="x", pady=12)

        # Contact info
        contacts = [
            ("📧 Email",  "attendance@sbc.vic.edu.au", "mailto:attendance@sbc.vic.edu.au"),
            ("💬 SMS",    "0436 015 842",               None),
            ("📞 Phone",  "03 9289 1000 (Select 'Attendance' option)", None),
        ]
        for label, value, link in contacts:
            row = tk.Frame(body, bg=BG_CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=BG_CARD, fg=ACCENT,
                     font=("TkDefaultFont", 10, "bold"),
                     width=12, anchor="w").pack(side="left")
            if link:
                lbl = tk.Label(row, text=value, bg=BG_CARD, fg="#4a90d9",
                               font=("TkDefaultFont", 11, "underline"),
                               cursor="hand2", anchor="w")
                lbl.pack(side="left")
                lbl.bind("<Button-1>", lambda e, u=link: webbrowser.open(u))
            else:
                tk.Label(row, text=value, bg=BG_CARD, fg=FG_PRIMARY,
                         font=("TkDefaultFont", 11), anchor="w").pack(side="left")

        # Early departures
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=12)
        tk.Label(body, text="Early Departures",
                 bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=6)

        early_txt = ("The College requires notification from a parent/caregiver should your son need "
                     "to leave early from school on any given day during the term. This notification "
                     "should be sent using the nominated parent/caregiver mobile number or email "
                     "registered in the MySBC parent portal and sent prior to, or before 8:15 am "
                     "on the day of early departure.")
        tk.Label(body, text=early_txt, bg=BG_CARD, fg=FG_SEC,
                 font=("TkDefaultFont", 11), wraplength=720,
                 justify="left", anchor="w").pack(fill="x", pady=8)

        required = [
            "Student's full name",
            "Year level and home room",
            "Date and time of early departure",
            "Reason for early departure",
            "Name and relationship of notifier to student",
        ]
        tk.Label(body,
                 text="The following information is required in the SMS to 0436 015 842 or email attendance@sbc.vic.edu.au:",
                 bg=BG_CARD, fg=FG_SEC,
                 font=("TkDefaultFont", 11), wraplength=720,
                 justify="left", anchor="w").pack(fill="x", pady=6)
        for item in required:
            row = tk.Frame(body, bg=BG_CARD)
            row.pack(fill="x", pady=1)
            tk.Label(row, text="•", bg=BG_CARD, fg=ACCENT,
                     font=("TkDefaultFont", 11), width=3).pack(side="left")
            tk.Label(row, text=item, bg=BG_CARD, fg=FG_SEC,
                     font=("TkDefaultFont", 11), anchor="w").pack(side="left")
