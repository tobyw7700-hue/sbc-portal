"""
Class Homepage — shows lesson posts, learning intentions, instructions.
Fetched from /news/lists/folder/{class_id}?...
"""
import tkinter as tk
from tkinter import ttk
import re, threading
from datetime import datetime
from bs4 import BeautifulSoup

from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider, SectionTitle, Card


def _lbl(parent, text, bg, fg, font, **kw):
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=font, **kw)


def _lbl_btn(parent, text, bg, fg, cmd, font=None, padx=8, pady=4):
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg,
                   font=font or FONT_LABEL,
                   padx=padx, pady=pady, cursor="hand2")
    lbl.bind("<Button-1>", lambda e: cmd())
    lbl.bind("<Enter>", lambda e: lbl.configure(bg=_dk(bg)))
    lbl.bind("<Leave>", lambda e: lbl.configure(bg=bg))
    return lbl


def _dk(h):
    try:
        h = h.lstrip("#")
        if len(h) != 6: return "#" + h
        r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        return f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
    except Exception:
        return "#" + h


def _clean(html):
    if not html: return ""
    soup = BeautifulSoup(html, "html.parser")
    # Convert headers
    result = []
    for el in soup.descendants:
        if not hasattr(el, 'name') or el.name is None:
            continue
    return soup.get_text("\n", strip=True)


def _parse_sections(html):
    """
    Parse HTML body into structured sections for display.
    Returns list of (type, content):
      type = 'h1','h2','h3','p','li','bold','divider'
    """
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    sections = []
    
    def walk(el):
        if not hasattr(el, 'name'):
            return
        if el.name in ('h1','h2','h3','h4'):
            t = el.get_text(strip=True)
            if t:
                sections.append((el.name, t))
        elif el.name == 'p':
            t = el.get_text(strip=True)
            if t and t != "\xa0":
                # Check if bold
                if el.find('strong') and len(el.get_text(strip=True)) < 80:
                    sections.append(('bold', t))
                else:
                    sections.append(('p', t))
        elif el.name in ('ul','ol'):
            for li in el.find_all('li', recursive=False):
                t = li.get_text(strip=True)
                if t:
                    sections.append(('li', t))
        elif el.name == 'hr':
            sections.append(('divider',''))
        else:
            for child in el.children:
                walk(child)
    
    for child in soup.children:
        walk(child)
    
    return sections


class ClassHomePage(tk.Frame):
    """
    Full class homepage showing lesson posts from mySBC.
    """

    def __init__(self, parent, class_info: dict, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.class_info = class_info  # {"name","code","class_id","cid"}
        self.data       = data
        self.session    = session
        self.posts      = []
        self.selected_post = 0
        self._build()
        self._load()

    def _build(self):
        # Header
        name = self.class_info.get("name", "Class")
        code = self.class_info.get("code", "")
        hdr = PageHeader(self, name, subtitle=f"{code}  ·  Class Homepage")
        hdr.pack(fill="x")
        GoldDivider(self).pack(fill="x")

        # Loading label
        self.status_lbl = tk.Label(self, text="Loading class posts…",
                                   bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL)
        self.status_lbl.pack(fill="x", padx=16, pady=4)

        # Main body: post list | post content
        self.body = tk.Frame(self, bg=BG_DARK)
        self.body.pack(fill="both", expand=True)

        # Left: post list
        self.list_frame = tk.Frame(self.body, bg=BG_MID, width=260)
        self.list_frame.pack(side="left", fill="y")
        self.list_frame.pack_propagate(False)
        tk.Frame(self.list_frame, bg=ACCENT, height=2).pack(fill="x")
        tk.Label(self.list_frame, text="POSTS",
                 bg=BG_MID, fg=ACCENT,
                 font=("TkDefaultFont", 8, "bold"),
                 padx=14, pady=8, anchor="w").pack(fill="x")
        self.list_scroll = ScrollableFrame(self.list_frame, bg=BG_MID)
        self.list_scroll.pack(fill="both", expand=True)
        self.list_inner = self.list_scroll.inner

        # Right: post content
        self.content_scroll = ScrollableFrame(self.body, bg=BG_DARK)
        self.content_scroll.pack(side="right", fill="both", expand=True)
        self.content_area = self.content_scroll.inner

    def _load(self):
        if not self.session:
            self.status_lbl.configure(text="Not connected to mySBC")
            return
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        from scraper.class_scraper import fetch_class_posts
        class_id = self.class_info.get("class_id","")
        cid      = self.class_info.get("cid","")
        posts    = fetch_class_posts(self.session, class_id, cid or None)
        self.posts = posts
        self.after(0, self._on_loaded)

    def _on_loaded(self):
        n = len(self.posts)
        self.status_lbl.configure(
            text=f"{n} post{'s' if n!=1 else ''}  ·  {self.class_info.get('name','')}")
        self._build_list()
        if self.posts:
            self._show_post(0)

    def _build_list(self):
        for w in self.list_inner.winfo_children():
            w.destroy()

        if not self.posts:
            tk.Label(self.list_inner, text="No posts found.",
                     bg=BG_MID, fg=FG_MUTED, font=FONT_SMALL,
                     padx=14, pady=10).pack(anchor="w")
            return

        self._post_btns = []
        for i, post in enumerate(self.posts):
            f = tk.Frame(self.list_inner, bg=BG_MID,
                         highlightbackground=BORDER, highlightthickness=1)
            f.pack(fill="x", pady=1)

            # Sticky indicator
            if post.get("sticky"):
                tk.Frame(f, bg=ACCENT, width=3).pack(side="left", fill="y")

            inner = tk.Frame(f, bg=BG_MID)
            inner.pack(side="left", fill="both", expand=True)

            title_lbl = tk.Label(inner,
                                  text=post["title"][:36] + ("…" if len(post["title"])>36 else ""),
                                  bg=BG_MID, fg=FG_PRIMARY,
                                  font=("TkDefaultFont", 10, "bold"),
                                  anchor="w", padx=10, pady=6,
                                  cursor="hand2", wraplength=220)
            title_lbl.pack(fill="x")

            date_lbl = tk.Label(inner,
                                 text=post.get("date",""),
                                 bg=BG_MID, fg=FG_MUTED,
                                 font=FONT_SMALL, anchor="w", padx=10, pady=3)
            date_lbl.pack(fill="x")

            for w in [f, inner, title_lbl, date_lbl]:
                w.bind("<Button-1>", lambda e, idx=i: self._show_post(idx))
                w.bind("<Enter>",    lambda e, ff=f: ff.configure(bg=BG_LIGHT))
                w.bind("<Leave>",    lambda e, ff=f, idx=i:
                       ff.configure(bg=ACCENT if self.selected_post==idx else BG_MID))

            self._post_btns.append(f)
            tk.Frame(self.list_inner, bg=BORDER, height=1).pack(fill="x")

    def _show_post(self, idx):
        self.selected_post = idx

        # Update list highlights
        for i, btn in enumerate(self._post_btns):
            btn.configure(bg=ACCENT if i==idx else BG_MID)
            for child in btn.winfo_children():
                self._update_widget_bg(child, ACCENT if i==idx else BG_MID)

        for w in self.content_area.winfo_children():
            w.destroy()

        if not self.posts:
            return
        post = self.posts[idx]
        self._render_post(post)

    def _update_widget_bg(self, widget, bg):
        try:
            widget.configure(bg=bg)
            fg = BG_DARK if bg == ACCENT else (FG_PRIMARY if "bold" in str(widget.cget("font")) else FG_MUTED)
            widget.configure(fg=fg)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._update_widget_bg(child, bg)

    def _render_post(self, post: dict):
        """Render a post with rich formatting matching mySBC style."""
        area = self.content_area

        # Post title
        title_frame = tk.Frame(area, bg=BG_MID)
        title_frame.pack(fill="x")
        tk.Frame(title_frame, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(title_frame, text=post["title"],
                 bg=BG_MID, fg=FG_PRIMARY,
                 font=("Georgia", 16, "bold"),
                 anchor="w", padx=20, pady=14,
                 wraplength=700, justify="left").pack(fill="x")

        # Meta: author + date
        meta = tk.Frame(area, bg=BG_CARD)
        meta.pack(fill="x")
        mf = tk.Frame(meta, bg=BG_CARD)
        mf.pack(fill="x", padx=20, pady=8)
        if post.get("author"):
            tk.Label(mf, text=f"👤  {post['author']}",
                     bg=BG_CARD, fg=FG_SEC,
                     font=("TkDefaultFont", 10)).pack(side="left", padx=(0,20))
        if post.get("date"):
            tk.Label(mf, text=f"📅  {post['date']}",
                     bg=BG_CARD, fg=FG_SEC,
                     font=("TkDefaultFont", 10)).pack(side="left")

        tk.Frame(area, bg=BORDER, height=1).pack(fill="x")

        # Body content
        body_frame = tk.Frame(area, bg=BG_DARK)
        body_frame.pack(fill="x", padx=20, pady=16)

        sections = _parse_sections(post.get("body_html",""))

        for sec_type, content in sections:
            if sec_type == 'h1':
                tk.Label(body_frame, text=content,
                         bg=BG_DARK, fg=FG_PRIMARY,
                         font=("Georgia", 15, "bold"),
                         anchor="w", wraplength=720,
                         pady=8).pack(fill="x")
                tk.Frame(body_frame, bg=ACCENT, height=2).pack(fill="x", pady=8)

            elif sec_type in ('h2','h3'):
                tk.Label(body_frame, text=content,
                         bg=BG_DARK, fg=ACCENT,
                         font=("Georgia", 13, "bold"),
                         anchor="w", wraplength=720,
                         pady=4).pack(fill="x")

            elif sec_type == 'h4':
                tk.Label(body_frame, text=content,
                         bg=BG_DARK, fg=FG_PRIMARY,
                         font=("TkDefaultFont", 11, "bold"),
                         anchor="w", wraplength=720).pack(fill="x", pady=2)

            elif sec_type == 'bold':
                tk.Label(body_frame, text=content,
                         bg=BG_DARK, fg=FG_PRIMARY,
                         font=("TkDefaultFont", 11, "bold"),
                         anchor="w", wraplength=720).pack(fill="x", pady=2)

            elif sec_type == 'p':
                tk.Label(body_frame, text=content,
                         bg=BG_DARK, fg=FG_SEC,
                         font=("TkDefaultFont", 11),
                         anchor="w", wraplength=720,
                         justify="left").pack(fill="x", pady=2)

            elif sec_type == 'li':
                row = tk.Frame(body_frame, bg=BG_DARK)
                row.pack(fill="x", pady=1)
                tk.Label(row, text="•",
                         bg=BG_DARK, fg=ACCENT,
                         font=("TkDefaultFont", 11),
                         width=2).pack(side="left", anchor="n", pady=2)
                tk.Label(row, text=content,
                         bg=BG_DARK, fg=FG_SEC,
                         font=("TkDefaultFont", 11),
                         anchor="w", wraplength=690,
                         justify="left").pack(side="left", fill="x", expand=True)

            elif sec_type == 'divider':
                tk.Frame(body_frame, bg=BORDER, height=1).pack(fill="x", pady=8)
