"""
Lootbox opening animation — slot machine style.
- Predetermined result before animation starts
- Rolls fast then decelerates smoothly
- Result item centred, rare items flanking it
- Legendary items very rare
"""
import tkinter as tk
import random
import math
from ui.theme import *
from data.pet_models import CRATE_TYPES, CLOTHING, PET_SPECIES, RARITY_COLOURS

ITEM_W = 90   # width of each slot item
ITEM_H = 90   # height of slot area


def _pick_reward(grade_label: str) -> dict:
    """
    Predetermined reward selection with rarity weighting.
    Called BEFORE animation so result is fixed.
    """
    crate = CRATE_TYPES.get(grade_label, {})

    # Rarity weights per crate tier
    # A+ CAN still get common/uncommon items — variety is more satisfying
    rarity_weights = {
        "A+": {"legendary": 8,  "epic": 15, "rare": 30, "uncommon": 28, "common": 19},
        "A":  {"legendary": 2,  "epic": 8,  "rare": 25, "uncommon": 38, "common": 27},
        "B":  {"legendary": 0,  "epic": 3,  "rare": 18, "uncommon": 42, "common": 37},
        "C":  {"legendary": 0,  "epic": 1,  "rare": 8,  "uncommon": 33, "common": 58},
        "D":  {"legendary": 0,  "epic": 0,  "rare": 3,  "uncommon": 22, "common": 75},
    }
    weights = rarity_weights.get(grade_label, rarity_weights["D"])

    # Build pool from crate's available items with rarity filter
    pool = []
    for item_key in crate.get("clothes", []):
        if item_key in CLOTHING:
            r = CLOTHING[item_key]["rarity"]
            w = weights.get(r, 1)
            pool.extend([("clothing", item_key)] * w)

    # Pet chance
    pet_chance = {"A+": 20, "A": 8, "B": 3, "C": 1, "D": 0}.get(grade_label, 0)
    for sp in crate.get("pets", []):
        pool.extend([("pet", sp)] * pet_chance)

    if not pool:
        pool = [("clothing", "collar")]

    rtype, key = random.choice(pool)
    return {"type": rtype, "key": key}


def _build_strip(reward: dict, length: int = 40) -> list:
    """
    Build a strip of items for the rolling display.
    The reward is placed at a fixed position near the end.
    Surrounding items are contextually chosen (rarer items flank the result).
    """
    all_items = list(CLOTHING.keys()) + list(PET_SPECIES.keys())
    
    # Rarity of the reward
    if reward["type"] == "clothing":
        result_rarity = CLOTHING.get(reward["key"], {}).get("rarity", "common")
    else:
        result_rarity = "epic"

    # Build a varied strip — mostly common/uncommon items
    common_pool    = [k for k,v in CLOTHING.items() if v["rarity"] in ("common","uncommon")]
    rare_pool      = [k for k,v in CLOTHING.items() if v["rarity"] in ("rare","epic","legendary")]
    
    strip = []
    for i in range(length):
        # Mostly common filler
        if random.random() < 0.15 and rare_pool:
            strip.append(("clothing", random.choice(rare_pool)))
        elif common_pool:
            strip.append(("clothing", random.choice(common_pool)))
        else:
            strip.append(("clothing", random.choice(all_items)))

    # Place the result at a fixed near-end position
    result_pos = length - 5
    strip[result_pos] = (reward["type"], reward["key"])

    # Place 1-2 items of same or higher rarity just before/after (for drama)
    if result_rarity in ("legendary", "epic") and rare_pool:
        if result_pos > 2:
            strip[result_pos - 2] = ("clothing", random.choice(rare_pool))
        if result_pos < length - 2:
            strip[result_pos + 1] = ("clothing", random.choice(rare_pool))

    return strip, result_pos


def _item_display(key: str, itype: str = "clothing"):
    """Returns (label, colour, rarity_label) for display."""
    if itype == "pet" and key in PET_SPECIES:
        info = PET_SPECIES[key]
        return info["emoji_base"], info["name"], "#22c55e", "Pet"
    if key in CLOTHING:
        item = CLOTHING[key]
        col  = RARITY_COLOURS.get(item["rarity"], FG_PRIMARY)
        return item["emoji"], item["name"], col, item["rarity"].title()
    return "❓", key, FG_MUTED, ""


class CrateAnimation(tk.Toplevel):

    def __init__(self, parent, grade_label: str, reward_meta: dict, on_close=None):
        super().__init__(parent)
        self.title("Opening Crate!")
        self.configure(bg=BG_DARK)
        self.geometry("520x480")
        self.resizable(False, False)
        self.grab_set()

        crate = CRATE_TYPES.get(grade_label, {})
        self.grade_label = grade_label
        self.crate_col   = crate.get("colour", ACCENT)
        self.on_close    = on_close

        # Predetermined reward
        self.reward = _pick_reward(grade_label)
        # Pass result back to caller (pet page uses this)
        reward_meta["type"]    = self.reward["type"]
        reward_meta["item_key"] = self.reward["key"]

        # Build strip
        self.strip, self.result_pos = _build_strip(self.reward)

        # Animation state
        self._pixel_offset = 0.0   # sub-pixel scroll position
        self._speed        = 0.0   # pixels per frame
        self._target_px    = 0.0   # total pixels to travel
        self._frame        = 0
        self._total_frames = 120
        self._done         = False
        self._revealed     = False

        self._build_ui(grade_label, crate)
        self.after(400, self._start)

    def _build_ui(self, grade_label, crate):
        # Top bar
        tk.Frame(self, bg=self.crate_col, height=5).pack(fill="x")

        tk.Label(self, text="📦  Opening Crate",
                 bg=BG_DARK, fg=self.crate_col,
                 font=("Georgia", 20, "bold"),
                 pady=10).pack()
        tk.Label(self, text=crate.get("name",""),
                 bg=BG_DARK, fg=FG_MUTED,
                 font=("TkDefaultFont", 10)).pack()

        # Slot machine frame
        slot_outer = tk.Frame(self, bg=self.crate_col, padx=3, pady=3)
        slot_outer.pack(fill="x", padx=24, pady=14)

        slot_inner = tk.Frame(slot_outer, bg=BG_MID)
        slot_inner.pack(fill="x")

        # Top/bottom arrows
        tk.Label(slot_inner, text="▼  ▼  ▼",
                 bg=BG_MID, fg=self.crate_col,
                 font=("TkDefaultFont", 12), pady=2).pack()

        # Rolling canvas
        self.canvas = tk.Canvas(slot_inner, bg=BG_MID,
                                height=ITEM_H, highlightthickness=0)
        self.canvas.pack(fill="x")

        tk.Label(slot_inner, text="▲  ▲  ▲",
                 bg=BG_MID, fg=self.crate_col,
                 font=("TkDefaultFont", 12), pady=2).pack()

        # Result area
        self.result_frame = tk.Frame(self, bg=BG_DARK)
        self.result_frame.pack(fill="x", padx=24, pady=4)

        self.result_lbl = tk.Label(self.result_frame, text=" " * 40,
                                    bg=BG_DARK, fg=FG_PRIMARY,
                                    font=("Georgia", 15, "bold"),
                                    pady=4)
        self.result_lbl.pack()

        self.rarity_lbl = tk.Label(self.result_frame, text="",
                                    bg=BG_DARK, fg=FG_MUTED,
                                    font=("TkDefaultFont", 11))
        self.rarity_lbl.pack()

        self.xp_lbl = tk.Label(self.result_frame, text="",
                                bg=BG_DARK, fg=ACCENT,
                                font=("TkDefaultFont", 11, "bold"))
        self.xp_lbl.pack()

        # Close button (hidden until done)
        self.close_btn = tk.Label(self, text="",
                                   bg=self.crate_col, fg=BG_DARK,
                                   font=("Georgia", 13, "bold"),
                                   padx=24, pady=9, cursor="hand2")
        self.close_btn.pack(pady=8)
        self.close_btn.bind("<Button-1>", lambda e: self._close())

    def _start(self):
        w = self.canvas.winfo_width() or 474
        # Total pixels = result_pos * ITEM_W, aligned so result_pos is centred
        centre_x = w // 2
        self._start_offset = -ITEM_W * 3  # start a few items before strip start
        target_item_left   = self.result_pos * ITEM_W
        target_centre      = target_item_left + ITEM_W // 2
        self._target_px    = target_centre - centre_x - self._start_offset
        self._pixel_offset = 0.0
        self._frame        = 0
        self._speed        = 80.0  # start fast (pixels per frame at 16ms = ~5000px/s)
        self._animate()

    def _animate(self):
        if self._done:
            return

        self._frame += 1
        progress = self._frame / self._total_frames

        # Ease-out cubic: fast start, smooth deceleration
        # Speed follows derivative of ease curve
        remaining = self._target_px - self._pixel_offset
        if remaining <= 0:
            self._pixel_offset = self._target_px
            self._done = True
            self._draw()
            self.after(180, self._shake)
            return

        # Easing: lerp speed toward a minimum, faster when far away
        ease = 1.0 - (progress ** 0.4)  # decelerates over time
        min_speed = 1.5
        self._speed = max(min_speed, remaining * 0.18 * ease + min_speed)

        self._pixel_offset += self._speed
        if self._pixel_offset >= self._target_px:
            self._pixel_offset = self._target_px
            self._done = True

        self._draw()

        # Frame rate: 16ms (60fps) when fast, slow to 32ms near end
        delay = 16 if self._speed > 8 else 22 if self._speed > 3 else 32
        if not self._done:
            self.after(delay, self._animate)
        else:
            self.after(180, self._shake)

    def _draw(self):
        c  = self.canvas
        w  = c.winfo_width() or 474
        c.delete("all")

        total_offset = self._start_offset + self._pixel_offset
        centre_x     = w // 2

        # Highlight centre selection box
        c.create_rectangle(centre_x - ITEM_W//2 - 2, 0,
                           centre_x + ITEM_W//2 + 2, ITEM_H,
                           fill=self.crate_col,
                           stipple="gray25",
                           outline=self.crate_col, width=3)

        # Draw visible items
        # Rarity background colours (dark tinted versions)
        RARITY_BG = {
            "Legendary": "#3a2e00",
            "Epic":      "#2a1040",
            "Rare":      "#0a1a30",
            "Uncommon":  "#0a2010",
            "Common":    "#1a1a2a",
            "Pet":       "#0a2a10",
        }

        for idx in range(len(self.strip)):
            item_centre_x = int(idx * ITEM_W + ITEM_W//2 - total_offset)
            if item_centre_x < -ITEM_W or item_centre_x > w + ITEM_W:
                continue

            itype, key = self.strip[idx]
            emoji, name, col, rarity = _item_display(key, itype)

            dist     = abs(item_centre_x - centre_x)
            is_focus = dist < ITEM_W // 2

            # Rarity-coloured background for every item
            bg_col = RARITY_BG.get(rarity, "#1a1a2a")
            c.create_rectangle(item_centre_x - ITEM_W//2 + 1, 1,
                               item_centre_x + ITEM_W//2 - 1, ITEM_H - 1,
                               fill=bg_col, outline="", width=0)

            # Rarity border — brighter on focused item
            if is_focus:
                c.create_rectangle(item_centre_x - ITEM_W//2 + 1, 1,
                                   item_centre_x + ITEM_W//2 - 1, ITEM_H - 1,
                                   fill="", outline=col, width=2)
            else:
                # Subtle border for non-focused
                c.create_rectangle(item_centre_x - ITEM_W//2 + 1, 1,
                                   item_centre_x + ITEM_W//2 - 1, ITEM_H - 1,
                                   fill="", outline=col, width=1)

            text_col = col if is_focus else col  # always use rarity colour
            font_size = 30 if is_focus else 22
            c.create_text(item_centre_x, 30,
                          text=emoji,
                          font=("TkDefaultFont", font_size),
                          fill=text_col)
            c.create_text(item_centre_x, 64,
                          text=name[:9],
                          font=("TkDefaultFont", 9 if is_focus else 8),
                          fill=text_col)
            if rarity:
                c.create_text(item_centre_x, 80,
                              text=rarity.upper(),
                              font=("TkDefaultFont", 7, "bold"),
                              fill=col)

    def _shake(self):
        ox, oy = self.winfo_x(), self.winfo_y()
        seq = [5, -5, 4, -4, 3, -3, 2, -2, 1, 0]

        def step(i):
            if i >= len(seq):
                self.geometry(f"+{ox}+{oy}")
                self.after(80, self._reveal)
                return
            self.geometry(f"+{ox + seq[i]}+{oy}")
            self.after(35, lambda: step(i + 1))

        step(0)

    def _reveal(self):
        itype, key = self.reward["type"], self.reward["key"]
        emoji, name, col, rarity = _item_display(key, itype)

        if itype == "pet":
            title = f"🎉  New Pet: {emoji} {name}!"
        else:
            title = f"{emoji}  {name}"

        self.result_lbl.configure(text=title, fg=col)

        if rarity:
            self.rarity_lbl.configure(text=rarity, fg=col)

        self.xp_lbl.configure(
            text=f"+{self.reward.get('xp', 0)} XP  ·  Crates remaining: {self.reward.get('remaining', 0)}")

        self.close_btn.configure(text="  Claim Reward! 🎉  ")

        # Flash effect for legendary/epic
        if rarity in ("Legendary", "Epic"):
            self._flash(col, 0)

    def _flash(self, col, n):
        if n >= 6:
            self.configure(bg=BG_DARK)
            return
        self.configure(bg=col if n % 2 == 0 else BG_DARK)
        self.after(80, lambda: self._flash(col, n + 1))

    def _close(self):
        if not self._revealed and not self._done:
            return  # don't allow closing mid-animation
        self.grab_release()
        self.destroy()
        if self.on_close:
            self.on_close()

    def show(self):
        self._revealed = True
