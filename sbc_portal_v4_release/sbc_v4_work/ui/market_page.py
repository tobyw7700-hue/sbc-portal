"""
Market page — refreshes every 15 minutes on the hour.
Items are deterministic based on the current time slot so all users see the same market.
"""
import tkinter as tk
import datetime, hashlib, random
from ui.theme import *
from ui.widgets import ScrollableFrame
from data.pet_models import (CLOTHING, PET_SPECIES, RARITY_COLOURS,
                               load_pet, save_pet, load_crate_counts, save_crate_counts)

# Market costs (in "coins" earned by opening crates = 1 coin each opened)
RARITY_COST = {
    "common":    8,
    "uncommon":  20,
    "rare":      55,
    "epic":      130,
    "legendary": 300,
    "mythic":    700,
    "divine":    1500,
}

MARKET_SIZE = 12   # items shown per slot

def _market_seed() -> str:
    """Deterministic seed based on 15-minute slot — same for all users."""
    now  = datetime.datetime.now()
    slot = (now.hour * 60 + now.minute) // 15
    day  = now.strftime("%Y%m%d")
    return f"sbc_market_{day}_{slot}"

def _get_market_items() -> list:
    """Generate deterministic market items for the current 15-minute slot."""
    seed = _market_seed()
    rng  = random.Random(int(hashlib.md5(seed.encode()).hexdigest(), 16))

    # Weight by rarity — rarer items appear less often
    all_items = []
    rarity_weights = {"common":30,"uncommon":25,"rare":20,"epic":12,"legendary":8,"mythic":4,"divine":1}
    for k, v in CLOTHING.items():
        all_items.append(("clothing", k, v))
    for k, v in PET_SPECIES.items():
        if v["unlock"] != "default":
            all_items.append(("pet", k, v))

    weights = []
    for t, k, v in all_items:
        r = v.get("rarity") or v.get("unlock", "common")
        weights.append(rarity_weights.get(r, 1))

    chosen = rng.choices(all_items, weights=weights, k=MARKET_SIZE)
    result = []
    seen = set()
    for t, k, v in chosen:
        if k in seen:
            continue
        seen.add(k)
        rarity = v.get("rarity") or v.get("unlock","common")
        result.append({
            "type":   t,
            "key":    k,
            "name":   v.get("name",""),
            "emoji":  v.get("emoji_base") or v.get("emoji","?"),
            "rarity": rarity,
            "cost":   RARITY_COST.get(rarity, 5),
        })
    return result

def _time_until_refresh() -> str:
    now = datetime.datetime.now()
    minutes_past = now.minute % 15
    seconds_past = now.second
    remaining = (14 - minutes_past) * 60 + (60 - seconds_past)
    m = remaining // 60
    s = remaining % 60
    return f"{m:02d}:{s:02d}"


class MarketPage(tk.Frame):

    def __init__(self, parent, data=None, session=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.data     = data
        self.username = data.profile.username if data and data.profile else "default"
        self.pet      = load_pet(self.username)
        self.crates   = load_crate_counts(self.username)
        from data.pet_models import compute_grade_coins, CRATE_OPEN_COINS
        grade_coins = compute_grade_coins(data)
        crate_coins = self.pet.crates_opened * CRATE_OPEN_COINS
        self.coins  = grade_coins + crate_coins
        self._build()
        self._tick()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_MID)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")
        row = tk.Frame(hdr, bg=BG_MID)
        row.pack(fill="x", padx=20, pady=10)
        tk.Label(row, text="🏪  Market", bg=BG_MID, fg=FG_PRIMARY,
                 font=FONT_HEADING).pack(side="left")
        self._timer_var = tk.StringVar(value="Refreshes in --:--")
        tk.Label(row, textvariable=self._timer_var, bg=BG_MID,
                 fg=ACCENT, font=FONT_SMALL).pack(side="right", padx=10)
        self._coins_var = tk.StringVar(value=f"🪙 {self.coins} coins")
        tk.Label(row, textvariable=self._coins_var, bg=BG_MID,
                 fg=FG_SEC, font=FONT_BODY).pack(side="right", padx=20)
        tk.Label(hdr, text="Earn coins: A+=20 · A=14 · B=9 · C=5 · D=2 · +3 per crate opened",
                 bg=BG_MID, fg=FG_MUTED, font=FONT_SMALL, padx=20, pady=4).pack(anchor="w")

        tk.Label(self, text="Market refreshes every 15 minutes · Same items for all users · Rare items still respect rarity chances",
                 bg=BG_DARK, fg=FG_MUTED, font=FONT_SMALL).pack(anchor="w", padx=20, pady=6)

        # Items grid
        self._content_frame = tk.Frame(self, bg=BG_DARK)
        self._content_frame.pack(fill="both", expand=True, padx=16, pady=12)
        self._refresh_items()

    def _refresh_items(self):
        for w in self._content_frame.winfo_children():
            w.destroy()

        items = _get_market_items()
        cols  = 4
        for i, item in enumerate(items):
            row_idx, col_idx = divmod(i, cols)
            card = self._make_card(self._content_frame, item)
            card.grid(row=row_idx, column=col_idx, padx=8, pady=8, sticky="nsew")
        for c in range(cols):
            self._content_frame.columnconfigure(c, weight=1)

        self._last_seed = _market_seed()

    def _make_card(self, parent, item):
        rarity = item["rarity"]
        r_col  = RARITY_COLOURS.get(rarity, BORDER)
        owned  = item["key"] in (self.pet.inventory + self.pet.unlocked_pets)
        can_buy= self.coins >= item["cost"] and not owned

        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=r_col, highlightthickness=2)

        tk.Label(card, text=item["emoji"], bg=BG_CARD,
                 font=("TkDefaultFont", 36), pady=8).pack()
        tk.Label(card, text=item["name"], bg=BG_CARD, fg=FG_PRIMARY,
                 font=("TkDefaultFont", 10, "bold"), wraplength=110).pack()
        tk.Label(card, text=rarity.upper(), bg=BG_CARD,
                 fg=r_col, font=FONT_SMALL).pack()
        tk.Label(card, text=f"🪙 {item['cost']}", bg=BG_CARD,
                 fg=ACCENT, font=FONT_LABEL).pack(pady=4)

        if owned:
            tk.Label(card, text="✓ Owned", bg=BG_CARD, fg=SUCCESS,
                     font=FONT_SMALL).pack(pady=4)
        else:
            btn_col = ACCENT if can_buy else FG_MUTED
            btn = tk.Label(card, text="Buy", bg=btn_col if can_buy else BG_MID,
                           fg=BG_DARK if can_buy else FG_MUTED,
                           font=FONT_LABEL, padx=16, pady=6,
                           cursor="hand2" if can_buy else "")
            btn.pack(pady=6)
            if can_buy:
                btn.bind("<Button-1>", lambda e, it=item, b=btn: self._buy(it, b))
        return card

    def _buy(self, item, btn):
        if self.coins < item["cost"]:
            return
        if item["key"] in (self.pet.inventory + self.pet.unlocked_pets):
            return
        self.coins -= item["cost"]
        self.pet.crates_opened = max(0, self.pet.crates_opened - item["cost"])
        if item["type"] == "pet":
            self.pet.unlocked_pets.append(item["key"])
        else:
            self.pet.inventory.append(item["key"])
        save_pet(self.pet, self.username)
        self._coins_var.set(f"🪙 {self.coins} coins")
        btn.configure(text="✓ Purchased", bg=SUCCESS, fg=BG_DARK, cursor="")
        btn.unbind("<Button-1>")

    def _tick(self):
        self._timer_var.set(f"Refreshes in {_time_until_refresh()}")
        # Check if slot changed
        if _market_seed() != getattr(self, "_last_seed", ""):
            self._refresh_items()
        try:
            self.after(1000, self._tick)
        except Exception:
            pass
