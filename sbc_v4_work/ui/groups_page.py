"""
Groups page — shows groups the student is a member of.
Fetched from /groups API.
"""
import tkinter as tk
from tkinter import ttk
import threading, re, json
import webbrowser
from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider

BASE_URL = "https://mysbc.sbc.vic.edu.au"

# Pastel colours matching mySBC group cards
CARD_COLOURS = [
    "#c7d2fe", "#bbf7d0", "#fef08a", "#bfdbfe",
    "#fbcfe8", "#fed7aa", "#a5f3fc", "#ddd6fe",
]


class GroupsPage(tk.Frame):
    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.session = session
        self.data    = data
        self.groups  = []
        self._build()
        # Show cached groups immediately, then refresh live
        if data and hasattr(data, 'groups') and data.groups:
            self._on_loaded(data.groups)
        self._load()

    def _build(self):
        hdr = PageHeader(self, "My Groups", subtitle="Groups I'm in")
        hdr.pack(fill="x")
        GoldDivider(self).pack(fill="x")

        self.status = tk.Label(self, text="Loading groups…",
                               bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL)
        self.status.pack(fill="x", padx=16, pady=6)

        self.scroll = ScrollableFrame(self, bg=BG_DARK)
        self.scroll.pack(fill="both", expand=True)
        self.area = self.scroll.inner

    def _load(self):
        if not self.session:
            self.status.configure(text="Not connected")
            return
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            resp = self.session.get(f"{BASE_URL}/groups")
            self._parse_html(resp.text, resp.url)
        except Exception as e:
            self.after(0, lambda: self.status.configure(
                text=f"Could not load groups: {e}"))

    def _parse_html(self, html, base_url=""):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        groups = []

        # Schoolbox renders groups as <a> tiles with data attributes or class names
        # Try multiple selectors in order of specificity
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Group links look like /groups/NNN or /homepage/NNN
            import re
            if not re.search(r"/(groups|homepage)/\d+", href):
                continue
            # Get the display name — could be in a heading, span, or text
            name = ""
            for sel in ["h2","h3","h4",".title",".name","strong","span"]:
                el = a.select_one(sel)
                if el:
                    name = el.get_text(strip=True)
                    break
            if not name:
                name = a.get_text(strip=True)
            # Clean up whitespace
            name = re.sub(r"\s+", " ", name).strip()
            if name and len(name) < 100:
                full_url = (href if href.startswith("http")
                           else f"{BASE_URL}{href}")
                gid = re.search(r"/(\d+)/?$", href)
                groups.append({
                    "name": name,
                    "url":  full_url,
                    "id":   gid.group(1) if gid else "",
                })

        # Deduplicate by name
        seen = set()
        unique = []
        for g in groups:
            if g["name"] not in seen:
                seen.add(g["name"])
                unique.append(g)

        self.after(0, lambda: self._on_loaded(unique))

    def _on_loaded(self, data):
        groups = []
        if isinstance(data, list):
            for g in data:
                if isinstance(g, dict):
                    groups.append({
                        "name": g.get("name", g.get("title", "")),
                        "id":   str(g.get("id", "")),
                        "url":  g.get("url", ""),
                    })
                elif isinstance(g, str):
                    groups.append({"name": g, "id": "", "url": ""})
        elif isinstance(data, dict):
            items = data.get("groups", data.get("items", data.get("data", [])))
            for g in items:
                groups.append({
                    "name": g.get("name", g.get("title", "")),
                    "id":   str(g.get("id", "")),
                    "url":  g.get("url", ""),
                })

        self.groups = [g for g in groups if g["name"]]
        n = len(self.groups)
        self.status.configure(text=f"{n} group{'s' if n!=1 else ''}")
        self._render()

    def _render(self):
        for w in self.area.winfo_children():
            w.destroy()

        if not self.groups:
            tk.Label(self.area,
                     text="No groups found.\nYou may not be a member of any groups yet.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY,
                     justify="center").pack(pady=40)
            return

        grid = tk.Frame(self.area, bg=BG_DARK)
        grid.pack(fill="x", padx=16, pady=12)
        for col in range(3):
            grid.columnconfigure(col, weight=1)

        for i, group in enumerate(self.groups):
            row  = i // 3
            col  = i % 3
            clr  = CARD_COLOURS[i % len(CARD_COLOURS)]

            card = tk.Frame(grid, bg="white",
                            highlightbackground="#ccc",
                            highlightthickness=1)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            grid.rowconfigure(row, weight=1)

            # Colour header
            header = tk.Frame(card, bg=clr, height=80)
            header.pack(fill="x")
            header.pack_propagate(False)

            # Name
            name_lbl = tk.Label(card,
                                 text=group["name"],
                                 bg="white", fg="#1e40af",
                                 font=("TkDefaultFont", 11, "bold"),
                                 anchor="w", padx=12, pady=10,
                                 wraplength=180, cursor="hand2")
            name_lbl.pack(fill="x")

            # Click to open in browser
            url = group.get("url", "")
            if not url and group.get("id"):
                url = f"{BASE_URL}/groups/{group['id']}"
            if not url:
                url = f"{BASE_URL}/groups"

            for widget in [card, header, name_lbl]:
                widget.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
                widget.bind("<Enter>",    lambda e, h=header, c=clr: h.configure(bg=_dk(c)))
                widget.bind("<Leave>",    lambda e, h=header, c=clr: h.configure(bg=c))


def _dk(h):
    try:
        h = h.lstrip("#")
        r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        return f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
    except: return "#"+h
