"""
Canteen page — info, online orders link, notices, staff contacts.
"""
import tkinter as tk
import webbrowser
from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider


def _lbl_btn(parent, text, bg, fg, cmd, font=None, padx=12, pady=8):
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg,
                   font=font or ("TkDefaultFont", 11, "bold"),
                   padx=padx, pady=pady, cursor="hand2")
    lbl.bind("<Button-1>", lambda e: cmd())
    lbl.bind("<Enter>",    lambda e: lbl.configure(bg=_dk(bg)))
    lbl.bind("<Leave>",    lambda e: lbl.configure(bg=bg))
    return lbl


def _dk(h):
    try:
        h = h.lstrip("#")
        r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        return f"#{max(0,r-25):02x}{max(0,g-25):02x}{max(0,b-25):02x}"
    except: return "#"+h


class CanteenPage(tk.Frame):
    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._build()

    def _build(self):
        hdr = PageHeader(self, "Canteen", subtitle="St Bernard's College Essendon")
        hdr.pack(fill="x")
        GoldDivider(self).pack(fill="x")

        scroll = ScrollableFrame(self, bg=BG_DARK)
        scroll.pack(fill="both", expand=True)
        area = scroll.inner

        # Online orders banner
        banner = tk.Frame(area, bg="#1a56db")
        banner.pack(fill="x", padx=20, pady=0)
        btn = _lbl_btn(banner,
                       "🛒  Online Orders — Click Here",
                       "#1a56db", "#f0c040",
                       lambda: webbrowser.open("https://shop.sbc.vic.edu.au/mymonitor/main.php"),
                       font=("Georgia", 16, "bold"),
                       padx=0, pady=24)
        btn.pack(fill="x")

        # Notices
        notices = [
            ("⚠", "As of Term 3 2024, Tap and Go via Student Card is the preferred method for purchasing in person at the Canteen."),
            ("⚠", "As of Term 4 2020 we no longer use Cash in the Canteen."),
        ]
        notice_frame = tk.Frame(area, bg=BG_DARK)
        notice_frame.pack(fill="x", padx=20, pady=16)
        for icon, msg in notices:
            row = tk.Frame(notice_frame, bg="#4d1e00",
                           highlightbackground=DANGER, highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=icon, bg="#4d1e00", fg=DANGER,
                     font=("TkDefaultFont", 14), padx=12, pady=10).pack(side="left")
            tk.Label(row, text=msg, bg="#4d1e00", fg="#ffcdd2",
                     font=("TkDefaultFont", 10), anchor="w",
                     wraplength=700, justify="left",
                     padx=8, pady=10).pack(side="left", fill="x", expand=True)

        # Support notice
        support = tk.Frame(area, bg=BG_CARD,
                           highlightbackground=BORDER, highlightthickness=1)
        support.pack(fill="x", padx=20, pady=4)
        tk.Label(support,
                 text="📧  Issues with the Online Order System? Email ",
                 bg=BG_CARD, fg=FG_SEC, font=("TkDefaultFont", 10),
                 padx=16, pady=10).pack(side="left")
        link = tk.Label(support, text="itsupport@sbc.vic.edu.au",
                        bg=BG_CARD, fg="#4a90d9",
                        font=("TkDefaultFont", 10, "underline"),
                        cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open("mailto:itsupport@sbc.vic.edu.au"))
        tk.Label(support, text=" with your name, login number and student name — do not call.",
                 bg=BG_CARD, fg=FG_SEC, font=("TkDefaultFont", 10),
                 padx=0, pady=10).pack(side="left")

        # Canteen staff
        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=16)
        tk.Label(area, text="Canteen Staff",
                 bg=BG_DARK, fg=ACCENT,
                 font=("Georgia", 14, "bold"),
                 padx=20).pack(anchor="w")

        staff_card = tk.Frame(area, bg=BG_CARD,
                              highlightbackground=BORDER, highlightthickness=1)
        staff_card.pack(fill="x", padx=20, pady=8)

        cols = tk.Frame(staff_card, bg=BG_CARD)
        cols.pack(fill="x", padx=20, pady=16)

        # Col 1: role
        col1 = tk.Frame(cols, bg=BG_CARD)
        col1.pack(side="left", expand=True, fill="x")
        tk.Label(col1, text="Unit Manager SBC Canteen",
                 bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")
        tk.Label(col1, text="Karen Fox",
                 bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=0)

        # Col 2: contact
        col2 = tk.Frame(cols, bg=BG_CARD)
        col2.pack(side="left", expand=True, fill="x")
        email_lbl = tk.Label(col2, text="canteen@sbc.vic.edu.au",
                             bg=BG_CARD, fg="#4a90d9",
                             font=("TkDefaultFont", 11, "underline"),
                             cursor="hand2")
        email_lbl.pack(anchor="w")
        email_lbl.bind("<Button-1>", lambda e: webbrowser.open("mailto:canteen@sbc.vic.edu.au"))
        tk.Label(col2, text="03 9289 1010",
                 bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 11)).pack(anchor="w", pady=0)
        tk.Label(col2, text="All calls will be redirected to leave a voice message",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=FONT_SMALL).pack(anchor="w", pady=0)
