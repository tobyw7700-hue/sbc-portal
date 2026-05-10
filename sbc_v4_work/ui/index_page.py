"""
Collection Index — browse every pet and accessory sorted by rarity and kind.
"""
import tkinter as tk
from tkinter import ttk

from ui.theme import *
from ui.widgets import ScrollableFrame
from data.pet_models import (CLOTHING, PET_SPECIES, RARITY_COLOURS,
                              RARITIES, load_pet)

# Reverse so Divine shows first
RARITY_ORDER = list(reversed(RARITIES))  # divine → common


class IndexPage(tk.Frame):

    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.username = data.profile.username if data and data.profile else "default"
        self.pet      = load_pet(self.username)
        self._view    = tk.StringVar(value="accessories")
        self._search  = tk.StringVar()
        self._filter  = tk.StringVar(value="all")
        self._search.trace_add("write", lambda *a: self._refresh())
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_MID)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(hdr, text="📖  Collection Index",
                 bg=BG_MID, fg=FG_PRIMARY,
                 font=("Georgia", 18, "bold"),
                 padx=20, pady=10).pack(anchor="w")

        # Controls bar
        ctrl = tk.Frame(self, bg=BG_MID)
        ctrl.pack(fill="x", padx=0)
        tk.Frame(ctrl, bg=BORDER, height=1).pack(fill="x")
        inner = tk.Frame(ctrl, bg=BG_MID)
        inner.pack(fill="x", padx=16, pady=8)

        # Tab buttons
        for key, label in [("accessories", "🎽 Accessories"), ("pets", "🐾 Pets")]:
            btn = tk.Label(inner, text=label,
                           bg=ACCENT if self._view.get()==key else BG_CARD,
                           fg=BG_DARK if self._view.get()==key else FG_SEC,
                           font=("TkDefaultFont", 10, "bold"),
                           padx=16, pady=6, cursor="hand2",
                           highlightbackground=BORDER, highlightthickness=1)
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, k=key: self._switch(k))
            setattr(self, f"_tab_{key}", btn)

        # Rarity filter
        tk.Label(inner, text="Rarity:", bg=BG_MID, fg=FG_MUTED,
                 font=FONT_SMALL).pack(side="left", padx=(20, 4))
        rarity_opts = ["all"] + RARITY_ORDER
        fmenu = ttk.Combobox(inner, textvariable=self._filter,
                              values=rarity_opts, state="readonly", width=12)
        fmenu.pack(side="left")
        self._filter.trace_add("write", lambda *a: self._refresh())

        # Search
        tk.Label(inner, text="Search:", bg=BG_MID, fg=FG_MUTED,
                 font=FONT_SMALL).pack(side="left", padx=(20, 4))
        tk.Entry(inner, textvariable=self._search,
                 bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY,
                 relief="flat", font=FONT_BODY, width=18).pack(side="left", ipady=4)

        # Stats
        self._stats_var = tk.StringVar()
        tk.Label(inner, textvariable=self._stats_var,
                 bg=BG_MID, fg=FG_MUTED, font=FONT_SMALL).pack(side="right", padx=8)

        # Content
        self._scroll = ScrollableFrame(self, bg=BG_DARK)
        self._scroll.pack(fill="both", expand=True)

        self._refresh()

    def _switch(self, key):
        self._view.set(key)
        for k in ("accessories", "pets"):
            btn = getattr(self, f"_tab_{k}", None)
            if btn:
                btn.configure(
                    bg=ACCENT if k==key else BG_CARD,
                    fg=BG_DARK if k==key else FG_SEC)
        self._refresh()

    # ── Refresh content ───────────────────────────────────────────────────────

    def _refresh(self):
        area = self._scroll.inner
        for w in area.winfo_children():
            w.destroy()

        view   = self._view.get()
        flt    = self._filter.get()
        query  = self._search.get().strip().lower()
        owned_clothes = set(self.pet.inventory)
        owned_pets    = set(self.pet.unlocked_pets)

        total_shown = 0

        if view == "accessories":
            for rarity in RARITY_ORDER:
                if flt != "all" and flt != rarity:
                    continue
                items = [(k, v) for k, v in CLOTHING.items()
                         if v["rarity"] == rarity
                         and (not query or query in v["name"].lower() or query in rarity)]
                if not items:
                    continue
                total_shown += len(items)
                self._rarity_section(area, rarity, len(items))
                grid = tk.Frame(area, bg=BG_DARK)
                grid.pack(fill="x", padx=16, pady=4)
                for col in range(5):
                    grid.columnconfigure(col, weight=1)
                for i, (key, val) in enumerate(items):
                    owned = key in owned_clothes
                    self._accessory_card(grid, key, val, owned, i // 5, i % 5)

        else:  # pets
            for rarity in RARITY_ORDER:
                if flt != "all" and flt != rarity:
                    continue
                pets = [(k, v) for k, v in PET_SPECIES.items()
                        if v["unlock"] == rarity
                        and (not query or query in v["name"].lower() or query in rarity)]
                if not pets:
                    continue
                total_shown += len(pets)
                self._rarity_section(area, rarity, len(pets))
                grid = tk.Frame(area, bg=BG_DARK)
                grid.pack(fill="x", padx=16, pady=4)
                for col in range(5):
                    grid.columnconfigure(col, weight=1)
                for i, (key, val) in enumerate(pets):
                    owned = key in owned_pets
                    self._pet_card(grid, key, val, owned, i // 5, i % 5)

        label = "accessories" if view == "accessories" else "pets"
        self._stats_var.set(f"{total_shown} {label} shown")

        if total_shown == 0:
            tk.Label(area, text="Nothing found.",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=FONT_BODY, pady=40).pack()

    # ── Section header ────────────────────────────────────────────────────────

    def _rarity_section(self, parent, rarity: str, count: int):
        r_col = RARITY_COLOURS.get(rarity, FG_MUTED)
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(fill="x", padx=16, pady=(12, 2))

        # Coloured bar
        tk.Frame(frame, bg=r_col, height=3).pack(fill="x")

        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x", pady=4)

        # Rarity name with coloured dot
        tk.Label(row, text="●", bg=BG_DARK, fg=r_col,
                 font=("TkDefaultFont", 14)).pack(side="left")
        tk.Label(row, text=f"  {rarity.upper()}",
                 bg=BG_DARK, fg=r_col,
                 font=("Georgia", 13, "bold")).pack(side="left")
        tk.Label(row, text=f"  —  {count} item{'s' if count != 1 else ''}",
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("TkDefaultFont", 10)).pack(side="left")

        # Rarity description
        descriptions = {
            "divine":    "Extremely rare · Almost impossible to get · Only from Divine Chests",
            "mythic":    "Very rare · Found in Mythic & Divine Chests and A+ crates",
            "legendary": "Rare · Available from A+ and A crates",
            "epic":      "Uncommon · Found in A+, A, and B crates",
            "rare":      "Somewhat common · Available from most crates",
            "uncommon":  "Common · Drops frequently from all crates",
            "common":    "Very common · Drops from every crate type",
        }
        desc = descriptions.get(rarity, "")
        if desc:
            tk.Label(row, text=desc, bg=BG_DARK, fg=FG_MUTED,
                     font=FONT_SMALL).pack(side="right", padx=8)

    # ── Accessory card ────────────────────────────────────────────────────────

    def _accessory_card(self, parent, key, val, owned, row, col):
        rarity  = val["rarity"]
        r_col   = RARITY_COLOURS.get(rarity, FG_MUTED)
        bg      = BG_CARD if owned else BG_MID
        border  = r_col if owned else BORDER

        card = tk.Frame(parent, bg=bg,
                        highlightbackground=border,
                        highlightthickness=2 if owned else 1)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Pet preview with item equipped
        try:
            from ui.pet_canvas import PetWidget
            pw = PetWidget(card, species=self.pet.species,
                           level=self.pet.level,
                           equipped_item=key,
                           size=75, bg=bg)
            pw.pack(pady=(8, 2))
        except Exception:
            tk.Label(card, text=val["emoji"], bg=bg,
                     font=("TkDefaultFont", 32), pady=8).pack()

        tk.Label(card, text=val["name"], bg=bg, fg=FG_PRIMARY if owned else FG_MUTED,
                 font=("TkDefaultFont", 9, "bold"),
                 wraplength=110).pack(padx=4)

        # Owned badge or lock
        if owned:
            equip_label = "✓ Equipped" if self.pet.equipped_item == key else "Owned"
            col_lbl     = SUCCESS if equip_label == "✓ Equipped" else ACCENT
            tk.Label(card, text=equip_label, bg=bg, fg=col_lbl,
                     font=FONT_SMALL, pady=4).pack()
        else:
            tk.Label(card, text="🔒 Locked", bg=bg, fg=FG_MUTED,
                     font=FONT_SMALL, pady=4).pack()

    # ── Pet card ──────────────────────────────────────────────────────────────

    def _pet_card(self, parent, key, val, owned, row, col):
        rarity  = val["unlock"]
        r_col   = RARITY_COLOURS.get(rarity, FG_MUTED)
        bg      = BG_CARD if owned else BG_MID
        border  = r_col if owned else BORDER

        card = tk.Frame(parent, bg=bg,
                        highlightbackground=border,
                        highlightthickness=2 if owned else 1)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Pet preview at different evolution tiers
        if owned:
            try:
                from ui.pet_canvas import PetWidget
                pw = PetWidget(card, species=key,
                               level=1, equipped_item="",
                               size=75, bg=bg)
                pw.pack(pady=(8, 2))
            except Exception:
                tk.Label(card, text=val["emoji_base"], bg=bg,
                         font=("TkDefaultFont", 36), pady=8).pack()
        else:
            tk.Label(card, text="🔒", bg=bg,
                     font=("TkDefaultFont", 36), pady=8).pack()

        tk.Label(card, text=val["name"], bg=bg,
                 fg=FG_PRIMARY if owned else FG_MUTED,
                 font=("TkDefaultFont", 9, "bold"),
                 wraplength=110).pack(padx=4)

        # Evolution preview row (5 tiers)
        if owned:
            from data.pet_models import get_pet_emoji
            evo_row = tk.Frame(card, bg=bg)
            evo_row.pack(pady=2)
            for lvl in [0, 10, 20, 30, 40]:
                tk.Label(evo_row, text=get_pet_emoji(key, lvl),
                         bg=bg, font=("TkDefaultFont", 10)).pack(side="left")
            tk.Label(card, text="Owned", bg=bg, fg=ACCENT,
                     font=FONT_SMALL, pady=2).pack()
        else:
            unlock_text = f"Unlock: {rarity.title()} crate"
            tk.Label(card, text=unlock_text, bg=bg, fg=FG_MUTED,
                     font=FONT_SMALL, pady=4).pack()
