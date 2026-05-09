"""
Index page — browse and sort all pets and accessories.
"""
import tkinter as tk
from ui.theme import *
from ui.widgets import ScrollableFrame
from data.pet_models import CLOTHING, PET_SPECIES, RARITY_COLOURS, RARITIES, load_pet

class IndexPage(tk.Frame):

    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.username = data.profile.username if data and data.profile else "default"
        self.pet = load_pet(self.username)
        self._tab    = tk.StringVar(value="accessories")
        self._sort   = tk.StringVar(value="rarity")
        self._filter = tk.StringVar(value="all")
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_MID)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(hdr, text="📖  Collection Index", bg=BG_MID, fg=FG_PRIMARY,
                 font=FONT_HEADING, padx=20, pady=10).pack(anchor="w")

        # Tab bar
        tabs = tk.Frame(self, bg=BG_DARK)
        tabs.pack(fill="x", padx=16, pady=8)
        for key, label in [("accessories","🎽 Accessories"), ("pets","🐾 Pets")]:
            btn = tk.Label(tabs, text=label, bg=BG_CARD, fg=FG_SEC,
                           font=FONT_LABEL, padx=20, pady=8, cursor="hand2",
                           highlightbackground=BORDER, highlightthickness=1)
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, k=key, b=btn: self._switch_tab(k))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=FG_PRIMARY))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=FG_SEC))
            setattr(self, f"_tab_btn_{key}", btn)

        # Controls
        ctrl = tk.Frame(self, bg=BG_DARK)
        ctrl.pack(fill="x", padx=16, pady=4)
        tk.Label(ctrl, text="Sort:", bg=BG_DARK, fg=FG_SEC, font=FONT_SMALL).pack(side="left")
        for val, label in [("rarity","Rarity"),("name","Name"),("owned","Owned First")]:
            rb = tk.Radiobutton(ctrl, text=label, variable=self._sort, value=val,
                                bg=BG_DARK, fg=FG_SEC, selectcolor=BG_MID,
                                activebackground=BG_DARK, font=FONT_SMALL,
                                command=self._refresh)
            rb.pack(side="left", padx=8)

        tk.Label(ctrl, text="  Filter:", bg=BG_DARK, fg=FG_SEC, font=FONT_SMALL).pack(side="left")
        rarity_opts = ["all"] + RARITIES[::-1]
        self._filter_menu = tk.OptionMenu(ctrl, self._filter, *rarity_opts,
                                           command=lambda _: self._refresh())
        self._filter_menu.configure(bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SMALL,
                                     activebackground=BG_LIGHT, highlightthickness=0)
        self._filter_menu["menu"].configure(bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SMALL)
        self._filter_menu.pack(side="left", padx=8)

        # Content
        self._scroll = ScrollableFrame(self, bg=BG_DARK)
        self._scroll.pack(fill="both", expand=True)
        self._switch_tab("accessories")

    def _switch_tab(self, tab):
        self._tab.set(tab)
        for key in ("accessories","pets"):
            btn = getattr(self, f"_tab_btn_{key}", None)
            if btn:
                btn.configure(bg=ACCENT if key==tab else BG_CARD,
                               fg=BG_DARK if key==tab else FG_SEC)
        self._refresh()

    def _refresh(self):
        area = self._scroll.inner
        for w in area.winfo_children():
            w.destroy()

        tab     = self._tab.get()
        sort_by = self._sort.get()
        flt     = self._filter.get()

        if tab == "accessories":
            items = list(CLOTHING.items())
            if flt != "all":
                items = [(k,v) for k,v in items if v["rarity"] == flt]
            if sort_by == "rarity":
                items.sort(key=lambda x: RARITIES.index(x[1]["rarity"]), reverse=True)
            elif sort_by == "name":
                items.sort(key=lambda x: x[1]["name"])
            elif sort_by == "owned":
                owned = set(self.pet.inventory)
                items.sort(key=lambda x: (0 if x[0] in owned else 1,
                                           RARITIES.index(x[1]["rarity"])), reverse=False)
                items.sort(key=lambda x: x[0] not in owned)

            cols = 5
            for i, (key, val) in enumerate(items):
                ri, ci = divmod(i, cols)
                owned = key in self.pet.inventory
                self._item_card(area, val["emoji"], val["name"], val["rarity"],
                                 owned, ri, ci)
            for c in range(cols):
                area.columnconfigure(c, weight=1)

        else:  # pets
            pets = list(PET_SPECIES.items())
            if flt != "all":
                pets = [(k,v) for k,v in pets if v["unlock"] == flt]
            if sort_by == "rarity":
                pets.sort(key=lambda x: RARITIES.index(x[1]["unlock"]) if x[1]["unlock"] in RARITIES else 0, reverse=True)
            elif sort_by == "name":
                pets.sort(key=lambda x: x[1]["name"])
            elif sort_by == "owned":
                owned = set(self.pet.unlocked_pets)
                pets.sort(key=lambda x: x[0] not in owned)

            cols = 5
            for i, (key, val) in enumerate(pets):
                ri, ci = divmod(i, cols)
                owned = key in self.pet.unlocked_pets
                self._item_card(area, val["emoji_base"], val["name"], val["unlock"],
                                 owned, ri, ci)
            for c in range(cols):
                area.columnconfigure(c, weight=1)

    def _item_card(self, parent, emoji, name, rarity, owned, row, col):
        r_col = RARITY_COLOURS.get(rarity, BORDER)
        bg    = BG_CARD if owned else BG_MID
        alpha = "" if owned else " (Locked)"

        card = tk.Frame(parent, bg=bg,
                        highlightbackground=r_col if owned else BORDER,
                        highlightthickness=2)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        tk.Label(card, text=emoji if owned else "🔒",
                 bg=bg, font=("TkDefaultFont", 30), pady=6).pack()
        tk.Label(card, text=name + alpha, bg=bg, fg=FG_PRIMARY if owned else FG_MUTED,
                 font=("TkDefaultFont", 9, "bold"), wraplength=100).pack()
        tk.Label(card, text=rarity.upper(), bg=bg, fg=r_col,
                 font=("TkDefaultFont", 8)).pack(pady=2)
        if owned:
            tk.Label(card, text="✓ Owned", bg=bg, fg=SUCCESS,
                     font=("TkDefaultFont", 8)).pack(pady=2)
