"""
Pet & Achievements tab.
"""
import tkinter as tk
from tkinter import ttk, simpledialog
import random, threading

from ui.theme import *
from ui.widgets import ScrollableFrame, PageHeader, GoldDivider
from ui.pet_canvas import PetWidget
from data.pet_models import (PetData, CRATE_TYPES, CLOTHING, RARITY_COLOURS,
                              PET_SPECIES, load_pet, save_pet, xp_for_level,
                              count_crates, load_crate_counts)
from data.achievements import ALL_ACHIEVEMENTS, detect_achievements


def _btn(parent, text, bg, fg, cmd, font=None, padx=12, pady=6):
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg,
                   font=font or ("TkDefaultFont",10,"bold"),
                   cursor="hand2", padx=padx, pady=pady)
    lbl.bind("<Button-1>", lambda e: cmd())
    def dk(h):
        try:
            h=h.lstrip("#"); r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
            return f"#{max(0,r-20):02x}{max(0,g-20):02x}{max(0,b-20):02x}"
        except: return bg
    lbl.bind("<Enter>", lambda e: lbl.configure(bg=dk(bg)))
    lbl.bind("<Leave>", lambda e: lbl.configure(bg=bg))
    return lbl


class PetPage(tk.Frame):

    def __init__(self, parent, data=None, session=None, settings=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data     = data
        self.session  = session
        self.settings = settings or {}
        self.username = (data.profile.username if data and data.profile else "default")
        self.pet      = load_pet(self.username)
        # Load saved crate counts (HMAC verified) then recompute from grades
        # Saved file is the source of truth for remaining crates
        self.crate_counts = self._load_crate_counts_init(data)
        self._claimable = []          # populated by _check_achievements below
        self._build()
        self._check_achievements()

    def _save(self):
        save_pet(self.pet, self.username)

    def _get_hmac_key(self) -> bytes:
        """Machine-specific key using username + a fixed app secret."""
        import hashlib
        secret = f"sbc_portal_v2_{self.username}_crates_integrity"
        return hashlib.sha256(secret.encode()).digest()

    def _save_crate_counts(self):
        """Save crate counts with HMAC integrity check."""
        import json, hmac, hashlib, os
        path = os.path.expanduser(f"~/.sbc_portal/crates_{self.username}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = json.dumps(self.crate_counts, sort_keys=True)
        sig  = hmac.new(self._get_hmac_key(), data.encode(), hashlib.sha256).hexdigest()
        with open(path, "w") as f:
            json.dump({"data": self.crate_counts, "sig": sig}, f)

    def _load_crate_counts(self) -> dict:
        """Load crate counts, verifying HMAC. Returns zeros if tampered."""
        import json, hmac, hashlib, os
        path = os.path.expanduser(f"~/.sbc_portal/crates_{self.username}.json")
        empty = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0}
        if not os.path.exists(path):
            return empty
        try:
            with open(path) as f:
                stored = json.load(f)
            # Handle legacy format (plain dict)
            if "data" not in stored:
                return stored if isinstance(stored, dict) else empty
            counts = stored["data"]
            stored_sig = stored.get("sig", "")
            # Verify
            data = json.dumps(counts, sort_keys=True)
            expected = hmac.new(self._get_hmac_key(), data.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(stored_sig, expected):
                import logging
                logging.getLogger("sbc.pet").warning(
                    "Crate count file tampered! Resetting to zero.")
                return empty
            return counts
        except Exception:
            return empty

    def _check_achievements(self):
        """Detect newly earned achievements but don't claim them — store as claimable."""
        new = detect_achievements(self.data, self.pet, self.username)
        # claimable = earned but not yet claimed (not in pet.achievements)
        self._claimable = [a for a in new if a.id not in self.pet.achievements]

    def _load_crate_counts_init(self, data) -> dict:
        """
        On first open: compute from grades.
        On subsequent opens: load from secure file.
        If grades have new assignments since last save, add the difference.
        """
        import json, hmac, hashlib, os
        path = os.path.expanduser(f"~/.sbc_portal/crates_{self.username}.json")
        
        # Compute fresh counts from grades
        fresh = count_crates(data, "") if data else {"A+":0,"A":0,"B":0,"C":0,"D":0}
        
        if not os.path.exists(path):
            # First time — save fresh counts securely
            self.crate_counts = fresh
            self._save_crate_counts_direct(fresh)
            return fresh

        # Load secure file
        empty = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0}
        try:
            with open(path) as f:
                stored = json.load(f)
            if "data" not in stored:
                saved = stored if isinstance(stored, dict) else empty
            else:
                counts = stored["data"]
                saved_sig = stored.get("sig", "")
                check_data = json.dumps(counts, sort_keys=True)
                key = self._get_hmac_key()
                expected = hmac.new(key, check_data.encode(), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(saved_sig, expected):
                    import logging
                    logging.getLogger("sbc.pet").warning("Crate file tampered — resetting")
                    self._save_crate_counts_direct(fresh)
                    return fresh
                saved = counts
        except Exception:
            saved = empty

        # The saved file represents REMAINING crates (after openings).
        # If grades have grown, the difference is new crates to add.
        # We track "total earned" = fresh counts (from all grades).
        # Remaining = fresh - opened. But we don't want to reset openings.
        # Strategy: if saved[grade] < fresh[grade], user earned more — keep saved
        # (already accounts for openings). If saved > fresh somehow, cap at fresh.
        result = {}
        for grade in ["A+","A","B","C","D"]:
            result[grade] = min(saved.get(grade, 0), fresh.get(grade, 0))
            # If fresh earned more than what was originally saved, add new ones
            # (can't know exact delta without history, so use max of both)
            if fresh.get(grade, 0) > saved.get(grade, 0) + self.pet.crates_opened:
                result[grade] = fresh.get(grade, 0)
        return result

    def _save_crate_counts_direct(self, counts):
        """Save without going through self.crate_counts."""
        import json, hmac, hashlib, os
        path = os.path.expanduser(f"~/.sbc_portal/crates_{self.username}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = json.dumps(counts, sort_keys=True)
        key = self._get_hmac_key()
        sig = hmac.new(key, data.encode(), hashlib.sha256).hexdigest()
        with open(path, "w") as f:
            json.dump({"data": counts, "sig": sig}, f)

    def _build(self):
        hdr = PageHeader(self, "🐾 My Pet", subtitle="Gamification & Achievements")
        hdr.pack(fill="x")

        tab_bar = tk.Frame(self, bg=BG_MID)
        tab_bar.pack(fill="x")
        self._tab_btns = {}

        total_crates = sum(self.crate_counts.values())
        crate_badge = f"  ({total_crates})" if total_crates else ""
        claimable_count = len(self._claimable)
        ach_badge = f"  🔔{claimable_count}" if claimable_count else ""

        for key, label in [("pet","🐾 My Pet"),
                            ("crates", f"📦 Crates{crate_badge}"),
                            ("wardrobe","👗 Wardrobe"),
                            ("achievements", f"🏆 Achievements{ach_badge}")]:
            btn = tk.Label(tab_bar, text=label,
                           bg=ACCENT if key=="pet" else BG_MID,
                           fg=BG_DARK if key=="pet" else FG_SEC,
                           font=("TkDefaultFont",10,"bold"),
                           padx=16, pady=8, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn

        GoldDivider(self).pack(fill="x")
        self.tab_content = tk.Frame(self, bg=BG_DARK)
        self.tab_content.pack(fill="both", expand=True)
        self._switch_tab("pet")

    def _switch_tab(self, key):
        for k, btn in self._tab_btns.items():
            btn.configure(bg=ACCENT if k==key else BG_MID,
                          fg=BG_DARK if k==key else FG_SEC)
        for w in self.tab_content.winfo_children():
            w.destroy()
        {"pet": self._build_pet, "crates": self._build_crates,
         "wardrobe": self._build_wardrobe,
         "achievements": self._build_achievements}[key]()

    # ── Pet Tab ───────────────────────────────────────────────────────────────
    def _build_pet(self):
        scroll = ScrollableFrame(self.tab_content, bg=BG_DARK)
        scroll.pack(fill="both", expand=True)
        area = scroll.inner

        # Card
        card = tk.Frame(area, bg=BG_CARD,
                        highlightbackground=ACCENT, highlightthickness=2)
        card.pack(padx=40, pady=20)

        top = tk.Frame(card, bg=BG_CARD)
        top.pack(padx=20, pady=16)

        # Canvas pet widget
        self._pet_widget = PetWidget(top,
                                      species=self.pet.species,
                                      level=self.pet.level,
                                      equipped_item=self.pet.equipped_item,
                                      size=140, bg=BG_CARD)
        self._pet_widget.pack(side="left", padx=(0,20))

        # Info right of pet
        info = tk.Frame(top, bg=BG_CARD)
        info.pack(side="left", anchor="n")

        name_row = tk.Frame(info, bg=BG_CARD)
        name_row.pack(anchor="w")
        tk.Label(name_row, text=self.pet.name, bg=BG_CARD, fg=FG_PRIMARY,
                 font=("Georgia", 18, "bold")).pack(side="left")
        edit = tk.Label(name_row, text=" ✏", bg=BG_CARD, fg=FG_MUTED,
                        font=("TkDefaultFont",14), cursor="hand2")
        edit.pack(side="left")
        edit.bind("<Button-1>", lambda e: self._rename_pet())

        species_info = PET_SPECIES.get(self.pet.species, {})
        tk.Label(info, text=species_info.get("name",""), bg=BG_CARD, fg=FG_MUTED,
                 font=FONT_SMALL).pack(anchor="w")

        # Level + XP
        lv_row = tk.Frame(info, bg=BG_CARD)
        lv_row.pack(anchor="w", pady=(10,2))
        tk.Label(lv_row, text=f"Level {self.pet.level}",
                 bg=BG_CARD, fg=ACCENT,
                 font=("Georgia",16,"bold")).pack(side="left", padx=(0,8))
        if self.pet.level < 99:
            needed = xp_for_level(self.pet.level)
            tk.Label(lv_row, text=f"{self.pet.xp}/{needed} XP",
                     bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL).pack(side="left")

        bar_bg = tk.Frame(info, bg=BORDER, height=10, width=200)
        bar_bg.pack(anchor="w", pady=(0,8))
        bar_bg.pack_propagate(False)
        bar_fill = tk.Frame(bar_bg, bg=ACCENT, height=10)
        bar_fill.place(relwidth=self.pet.xp_progress(), relheight=1)

        if self.pet.equipped_item and self.pet.equipped_item in CLOTHING:
            item = CLOTHING[self.pet.equipped_item]
            eq_row = tk.Frame(info, bg=BG_CARD)
            eq_row.pack(anchor="w")
            tk.Label(eq_row, text=f"Wearing: {item['emoji']} {item['name']}",
                     bg=BG_CARD, fg=FG_SEC, font=FONT_BODY).pack(side="left")
            _btn(eq_row, "Remove", BG_LIGHT, FG_PRIMARY,
                 self._remove_clothing, padx=8, pady=2).pack(side="left", padx=8)
        else:
            tk.Label(info, text="No outfit — visit Wardrobe!",
                     bg=BG_CARD, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w")

        # Stats row
        stats = tk.Frame(area, bg=BG_DARK)
        stats.pack(fill="x", padx=20, pady=8)
        for i, (lbl, val, col) in enumerate([
            ("Level", str(self.pet.level), ACCENT),
            ("Crates", str(self.pet.crates_opened), "#4a90d9"),
            ("Items", str(len(self.pet.inventory)), "#22c55e"),
            ("Achievements", str(len(self.pet.achievements)), "#f0c040"),
        ]):
            f = tk.Frame(stats, bg=BG_CARD,
                         highlightbackground=BORDER, highlightthickness=1)
            f.grid(row=0, column=i, padx=4, sticky="nsew")
            stats.columnconfigure(i, weight=1)
            tk.Label(f, text=val, bg=BG_CARD, fg=col,
                     font=("Georgia",18,"bold"), pady=8).pack()
            tk.Label(f, text=lbl, bg=BG_CARD, fg=FG_MUTED,
                     font=FONT_SMALL, pady=4).pack()

        # Pet switcher
        if len(self.pet.unlocked_pets) > 1:
            tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
            tk.Label(area, text="Switch Pet", bg=BG_DARK, fg=ACCENT,
                     font=("Georgia",13,"bold"), padx=20).pack(anchor="w")
            row = tk.Frame(area, bg=BG_DARK)
            row.pack(fill="x", padx=20, pady=8)
            for sp in self.pet.unlocked_pets:
                info2 = PET_SPECIES.get(sp, {})
                active = sp == self.pet.species
                f = tk.Frame(row, bg=ACCENT if active else BG_CARD,
                             highlightbackground=ACCENT if active else BORDER,
                             highlightthickness=2)
                f.pack(side="left", padx=4)
                pw = PetWidget(f, species=sp, level=self.pet.level,
                               size=60, bg=ACCENT if active else BG_CARD)
                pw.pack(padx=6, pady=6)
                tk.Label(f, text=info2.get("name",sp),
                         bg=ACCENT if active else BG_CARD,
                         fg=BG_DARK if active else FG_PRIMARY,
                         font=FONT_SMALL, pady=4).pack()
                for w in [f, pw, pw.canvas]:
                    w.bind("<Button-1>", lambda e, s=sp: self._switch_pet(s))

    def _rename_pet(self):
        name = simpledialog.askstring("Rename", f"New name:",
                                       initialvalue=self.pet.name, parent=self)
        if name and name.strip():
            self.pet.name = name.strip()[:20]
            self._save()
            self._switch_tab("pet")

    def _switch_pet(self, species):
        self.pet.species = species
        self._save()
        self._switch_tab("pet")

    def _remove_clothing(self):
        self.pet.equipped_item = ""
        self._save()
        self._switch_tab("pet")

    # ── Crates Tab ────────────────────────────────────────────────────────────
    def _build_crates(self):
        scroll = ScrollableFrame(self.tab_content, bg=BG_DARK)
        scroll.pack(fill="both", expand=True)
        area = scroll.inner

        tk.Label(area, text="Your Crates",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=("Georgia",16,"bold"),
                 padx=20, pady=12).pack(anchor="w")
        tk.Label(area,
                 text="Each graded assessment earns you a crate. "
                      "Better grades = rarer crates with better rewards!",
                 bg=BG_DARK, fg=FG_SEC, font=FONT_BODY,
                 padx=20, wraplength=700, justify="left").pack(anchor="w")

        # Crate inventory grid
        grid = tk.Frame(area, bg=BG_DARK)
        grid.pack(fill="x", padx=20, pady=16)
        col = 0
        for grade, crate in CRATE_TYPES.items():
            if not crate.get("name"): continue
            count = self.crate_counts.get(grade, 0)
            if count == 0: continue
            col_frame = tk.Frame(grid, bg=BG_CARD,
                                  highlightbackground=crate["colour"],
                                  highlightthickness=2)
            col_frame.grid(row=0, column=col, padx=8, pady=4, sticky="nsew")
            grid.columnconfigure(col, weight=1)
            col += 1

            tk.Label(col_frame, text="📦",
                     bg=BG_CARD, font=("TkDefaultFont",40), pady=8).pack()
            tk.Label(col_frame, text=crate["name"],
                     bg=BG_CARD, fg=crate["colour"],
                     font=("Georgia",12,"bold")).pack()
            tk.Label(col_frame, text=f"x{count}",
                     bg=BG_CARD, fg=FG_PRIMARY,
                     font=("Georgia",20,"bold")).pack()
            _btn(col_frame, f"Open {grade} Crate",
                 crate["colour"], BG_DARK,
                 lambda g=grade: self._open_crate(g),
                 padx=0, pady=8).pack(fill="x", padx=8, pady=8)

        if col == 0:
            tk.Label(area,
                     text="No crates available yet.\nGet graded assignments to earn crates!",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY,
                     justify="center", pady=30).pack()

        # Crate guide
        tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=12)
        tk.Label(area, text="Crate Guide",
                 bg=BG_DARK, fg=ACCENT,
                 font=("TkDefaultFont",11,"bold"), padx=20).pack(anchor="w", pady=4)
        for grade, crate in CRATE_TYPES.items():
            if not crate.get("name"): continue
            row = tk.Frame(area, bg=BG_CARD,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", padx=20, pady=2)
            tk.Frame(row, bg=crate["colour"], width=6).pack(side="left", fill="y")
            tk.Label(row, text=f"  {grade}  ",
                     bg=BG_CARD, fg=crate["colour"],
                     font=("Georgia",12,"bold"), padx=6, pady=8).pack(side="left")
            tk.Label(row, text=crate["name"],
                     bg=BG_CARD, fg=FG_PRIMARY,
                     font=("TkDefaultFont",11,"bold")).pack(side="left")
            pets = ", ".join(PET_SPECIES[p]["name"] for p in crate["pets"] if p in PET_SPECIES)
            clothes = ", ".join(CLOTHING[c]["name"] for c in crate["clothes"][:3] if c in CLOTHING)
            detail = []
            if pets: detail.append(f"Pets: {pets}")
            if clothes: detail.append(f"Items: {clothes}...")
            if detail:
                tk.Label(row, text="  ·  ".join(detail),
                         bg=BG_CARD, fg=FG_MUTED,
                         font=FONT_SMALL, padx=8).pack(side="left")

    def _open_crate(self, grade_label: str):
        crate = CRATE_TYPES.get(grade_label, {})
        if not crate.get("name"): return
        if self.crate_counts.get(grade_label, 0) <= 0: return

        # reward_meta is filled in by CrateAnimation (predetermined result)
        reward_meta = {"xp": 0}

        def on_anim_close():
            # Apply the predetermined reward after animation
            itype    = reward_meta.get("type", "clothing")
            item_key = reward_meta.get("item_key", "")
            if itype == "pet" and item_key and item_key not in self.pet.unlocked_pets:
                self.pet.unlocked_pets.append(item_key)
            elif itype == "clothing" and item_key:
                if item_key not in self.pet.inventory:
                    self.pet.inventory.append(item_key)

            # No XP from crates — XP comes from achievements only
            reward_meta["xp"] = 0

            # Consume crate and save immediately to prevent tab-switch refresh bug
            self.crate_counts[grade_label] = max(0, self.crate_counts.get(grade_label, 1) - 1)
            reward_meta["remaining"] = self.crate_counts.get(grade_label, 0)
            self.pet.crates_opened += 1
            self.pet.crates_by_type[grade_label] =                 self.pet.crates_by_type.get(grade_label, 0) + 1

            if grade_label == "A+" and "golden_crate" not in self.pet.achievements:
                self.pet.achievements.append("golden_crate")

            # Save crate counts to disk immediately
            self._save_crate_counts()
            self._save()
            self._check_achievements()
            self._switch_tab("crates")

        from ui.crate_animation import CrateAnimation
        CrateAnimation(self, grade_label, reward_meta, on_close=on_anim_close)

    # ── Wardrobe Tab ──────────────────────────────────────────────────────────
    def _build_wardrobe(self):
        scroll = ScrollableFrame(self.tab_content, bg=BG_DARK)
        scroll.pack(fill="both", expand=True)
        area = scroll.inner

        tk.Label(area, text="Wardrobe",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=("Georgia",16,"bold"),
                 padx=20, pady=12).pack(anchor="w")

        if not self.pet.inventory:
            tk.Label(area, text="No items yet! Open crates to earn clothing.",
                     bg=BG_DARK, fg=FG_MUTED, font=FONT_BODY,
                     padx=20, pady=40).pack(anchor="w")
            return

        grid = tk.Frame(area, bg=BG_DARK)
        grid.pack(fill="x", padx=16, pady=8)
        for col in range(4):
            grid.columnconfigure(col, weight=1)

        for i, item_key in enumerate(self.pet.inventory):
            if item_key not in CLOTHING: continue
            item      = CLOTHING[item_key]
            is_eq     = self.pet.equipped_item == item_key
            rar_col   = RARITY_COLOURS.get(item["rarity"], FG_MUTED)

            card = tk.Frame(grid, bg=BG_CARD,
                            highlightbackground=rar_col if is_eq else BORDER,
                            highlightthickness=2 if is_eq else 1)
            card.grid(row=i//4, column=i%4, padx=6, pady=6, sticky="nsew")

            # Preview pet with this item
            pw = PetWidget(card, species=self.pet.species,
                           level=self.pet.level,
                           equipped_item=item_key,
                           size=80, bg=BG_CARD)
            pw.pack(pady=8)

            tk.Label(card, text=item["name"],
                     bg=BG_CARD, fg=FG_PRIMARY,
                     font=("TkDefaultFont",10,"bold")).pack()
            tk.Label(card, text=item["rarity"].title(),
                     bg=BG_CARD, fg=rar_col,
                     font=FONT_SMALL, pady=2).pack()

            if is_eq:
                tk.Label(card, text="✓ Equipped",
                         bg=BG_CARD, fg=SUCCESS,
                         font=FONT_SMALL, pady=4).pack()
            else:
                _btn(card, "Equip", ACCENT, BG_DARK,
                     lambda k=item_key: self._equip(k),
                     padx=0, pady=5).pack(fill="x", padx=8, pady=8)

    def _equip(self, item_key: str):
        self.pet.equipped_item = item_key
        if "dressed_up" not in self.pet.achievements:
            self.pet.achievements.append("dressed_up")
        self._save()
        self._switch_tab("wardrobe")

    # ── Achievements Tab ──────────────────────────────────────────────────────
    def _build_achievements(self):
        scroll = ScrollableFrame(self.tab_content, bg=BG_DARK)
        scroll.pack(fill="both", expand=True)
        area = scroll.inner

        earned = set(self.pet.achievements)
        total  = len(ALL_ACHIEVEMENTS)
        done   = len([a for a in ALL_ACHIEVEMENTS if a.id in earned])

        tk.Label(area, text=f"Achievements  —  {done}/{total}",
                 bg=BG_DARK, fg=FG_PRIMARY,
                 font=("Georgia",16,"bold"),
                 padx=20, pady=12).pack(anchor="w")

        bar_bg = tk.Frame(area, bg=BORDER, height=10)
        bar_bg.pack(fill="x", padx=20, pady=4)
        bar_fill = tk.Frame(bar_bg, bg=ACCENT, height=10)
        bar_fill.place(relwidth=done/total if total else 0, relheight=1)

        # ── Claimable section ─────────────────────────────────────────────
        if self._claimable:
            tk.Frame(area, bg=ACCENT, height=2).pack(fill="x", padx=20, pady=8)
            tk.Label(area, text=f"🔔  Ready to Claim  ({len(self._claimable)})",
                     bg=BG_DARK, fg=ACCENT,
                     font=("TkDefaultFont",12,"bold"),
                     padx=20).pack(anchor="w", pady=4)
            for ach in self._claimable:
                self._ach_row(area, ach, earned=False, claimable=True)

        # ── Earned ────────────────────────────────────────────────────────
        earned_list = [a for a in ALL_ACHIEVEMENTS if a.id in earned]
        locked_list = [a for a in ALL_ACHIEVEMENTS
                       if a.id not in earned and a not in self._claimable]

        if earned_list:
            tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
            tk.Label(area, text="Earned",
                     bg=BG_DARK, fg=SUCCESS,
                     font=("TkDefaultFont",11,"bold"),
                     padx=20).pack(anchor="w", pady=4)
            for ach in earned_list:
                self._ach_row(area, ach, earned=True)

        if locked_list:
            tk.Frame(area, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)
            tk.Label(area, text="Locked",
                     bg=BG_DARK, fg=FG_MUTED,
                     font=("TkDefaultFont",11,"bold"),
                     padx=20).pack(anchor="w", pady=4)
            for ach in locked_list:
                self._ach_row(area, ach, earned=False)

    def _ach_row(self, parent, ach, earned: bool, claimable: bool = False):
        bg = BG_CARD if (earned or claimable) else BG_MID
        border = ACCENT if claimable else (SUCCESS if earned else BORDER)
        row = tk.Frame(parent, bg=bg,
                       highlightbackground=border, highlightthickness=1)
        row.pack(fill="x", padx=20, pady=2)
        tk.Label(row, text=ach.emoji if (earned or claimable) else "🔒",
                 bg=bg, font=("TkDefaultFont",20),
                 padx=12, pady=10, width=3).pack(side="left")
        info = tk.Frame(row, bg=bg)
        info.pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(info, text=ach.title, bg=bg,
                 fg=FG_PRIMARY if (earned or claimable) else FG_MUTED,
                 font=("TkDefaultFont",11,"bold"), anchor="w").pack(anchor="w")
        tk.Label(info, text=ach.description, bg=bg,
                 fg=FG_SEC if (earned or claimable) else FG_MUTED,
                 font=FONT_SMALL, anchor="w").pack(anchor="w")

        right = tk.Frame(row, bg=bg)
        right.pack(side="right", padx=12)

        if ach.xp_reward:
            tk.Label(right, text=f"+{ach.xp_reward} XP", bg=bg,
                     fg=ACCENT if (earned or claimable) else FG_MUTED,
                     font=("TkDefaultFont",10,"bold")).pack()

        if claimable:
            claim_btn = tk.Label(right, text=" ✦ Claim ", bg=ACCENT, fg=BG_DARK,
                                 font=("TkDefaultFont",10,"bold"),
                                 cursor="hand2", padx=8, pady=4)
            claim_btn.pack(pady=4)
            claim_btn.bind("<Button-1>", lambda e, a=ach, r=row: self._claim_achievement(a, r))
            claim_btn.bind("<Enter>", lambda e, b=claim_btn: b.configure(bg="#f0c040"))
            claim_btn.bind("<Leave>", lambda e, b=claim_btn: b.configure(bg=ACCENT))

    def _claim_achievement(self, ach, row_widget):
        """Claim one achievement: play confetti + XP animation, then level-up if applicable."""
        if ach.id in self.pet.achievements:
            return  # already claimed
        # Mark claimed
        self.pet.achievements.append(ach.id)
        if ach in self._claimable:
            self._claimable.remove(ach)
        old_level = self.pet.level
        level_msgs = self.pet.add_xp(ach.xp_reward)
        self._save()

        # Update tab badge
        claimable_count = len(self._claimable)
        new_label = f"🏆 Achievements" + (f"  🔔{claimable_count}" if claimable_count else "")
        if "achievements" in self._tab_btns:
            self._tab_btns["achievements"].configure(text=new_label)

        # Launch overlay animation
        self._play_claim_animation(ach, old_level, self.pet.level, level_msgs, row_widget)

    def _play_claim_animation(self, ach, old_level, new_level, level_msgs, row_widget):
        """Full-screen overlay: confetti + XP rise + optional level-up / evolution."""
        overlay = tk.Toplevel(self.winfo_toplevel())
        overlay.overrideredirect(True)
        # Position over the main window
        root = self.winfo_toplevel()
        x, y = root.winfo_x(), root.winfo_y()
        w, h = root.winfo_width(), root.winfo_height()
        overlay.geometry(f"{w}x{h}+{x}+{y}")
        overlay.configure(bg=BG_DARK)
        overlay.attributes("-alpha", 0.0)
        overlay.lift()

        canvas = tk.Canvas(overlay, bg=BG_DARK, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # ── Confetti particles ────────────────────────────────────────────
        import random, math
        COLOURS = [ACCENT, SUCCESS, "#ff6b6b", "#4ecdc4", "#a855f7", "#3b82f6", "#f97316"]
        particles = []
        for _ in range(80):
            px = random.randint(0, w)
            py = random.randint(-60, 0)
            particles.append({
                "x": px, "y": py,
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(3, 8),
                "col": random.choice(COLOURS),
                "size": random.randint(6, 14),
                "rot": random.uniform(0, 360),
                "vrot": random.uniform(-6, 6),
                "shape": random.choice(["rect", "circle"]),
                "id": None,
            })

        # ── Central content ───────────────────────────────────────────────
        cx, cy = w // 2, h // 2

        # Achievement card
        card_id = canvas.create_rectangle(cx-220, cy-130, cx+220, cy+160,
                                          fill=BG_CARD, outline=ACCENT, width=3)
        canvas.create_text(cx, cy-95, text=ach.emoji,
                           font=("TkDefaultFont", 52), fill=FG_PRIMARY)
        canvas.create_text(cx, cy-28, text=ach.title,
                           font=("Georgia", 16, "bold"), fill=FG_PRIMARY)
        canvas.create_text(cx, cy+2, text=ach.description,
                           font=("TkDefaultFont", 10), fill=FG_SEC, width=380)

        # XP counter (animates up)
        xp_var = [0]
        xp_text = canvas.create_text(cx, cy+50,
                                     text=f"+0 XP",
                                     font=("Georgia", 22, "bold"), fill=ACCENT)

        # Level display
        lvl_text = canvas.create_text(cx, cy+90,
                                      text=f"Level {old_level}  →  {new_level}" if new_level > old_level else f"Level {new_level}",
                                      font=("TkDefaultFont", 13, "bold"),
                                      fill=ACCENT if new_level > old_level else FG_MUTED)

        # Evolution notice
        levelled_up = new_level > old_level
        evolved = any(m for m in level_msgs if "evolved" in m)
        if evolved:
            canvas.create_text(cx, cy+120,
                               text="✨  PET EVOLVED!  ✨",
                               font=("Georgia", 15, "bold"), fill="#a855f7")
            # Show pet widget below if evolved
            from ui.pet_canvas import PetWidget
            pet_frame = tk.Frame(overlay, bg=BG_DARK)
            pet_frame.place(x=cx+230, y=cy-80)
            tk.Label(pet_frame, text="Before", bg=BG_DARK, fg=FG_MUTED,
                     font=FONT_SMALL).pack()
            PetWidget(pet_frame, species=self.pet.species, level=old_level,
                      equipped_item="", size=70, bg=BG_DARK).pack()
            tk.Label(pet_frame, text="→", bg=BG_DARK, fg=ACCENT,
                     font=("Georgia", 20, "bold")).pack()
            PetWidget(pet_frame, species=self.pet.species, level=new_level,
                      equipped_item=self.pet.equipped_item, size=70, bg=BG_DARK).pack()
            tk.Label(pet_frame, text="After", bg=BG_DARK, fg=ACCENT,
                     font=FONT_SMALL).pack()

        # Close button
        close_btn = canvas.create_text(cx, cy+148,
                                       text="✕  Tap to close",
                                       font=("TkDefaultFont", 10), fill=FG_MUTED)

        def close_overlay(event=None):
            try:
                overlay.destroy()
            except Exception:
                pass
            # Refresh the achievements tab
            self._switch_tab("achievements")

        canvas.bind("<Button-1>", close_overlay)
        overlay.bind("<Escape>", close_overlay)

        # ── Animation loop ─────────────────────────────────────────────────
        frame_count = [0]
        xp_target = ach.xp_reward
        TOTAL_FRAMES = 80

        def animate():
            try:
                f = frame_count[0]
                frame_count[0] += 1

                # Fade in
                alpha = min(1.0, f / 12)
                overlay.attributes("-alpha", alpha)

                # Confetti
                canvas.delete("confetti")
                for p in particles:
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["rot"] += p["vrot"]
                    p["vy"] += 0.15  # gravity
                    if p["y"] > h + 20:
                        p["y"] = random.randint(-40, -10)
                        p["x"] = random.randint(0, w)
                    if p["shape"] == "circle":
                        r = p["size"] // 2
                        canvas.create_oval(p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r,
                                           fill=p["col"], outline="", tags="confetti")
                    else:
                        s = p["size"]
                        canvas.create_rectangle(p["x"], p["y"], p["x"]+s, p["y"]+s//2,
                                                fill=p["col"], outline="", tags="confetti")

                # Animate XP counter
                if f < TOTAL_FRAMES:
                    shown = int(xp_target * min(1.0, f / 40))
                    canvas.itemconfigure(xp_text, text=f"+{shown} XP")

                if f < TOTAL_FRAMES + 40:
                    overlay.after(16, animate)
            except tk.TclError:
                pass

        animate()
