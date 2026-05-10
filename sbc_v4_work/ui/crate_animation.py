"""
Crate animation — smooth lootbox roller with rarity-specific particle effects.
NO flashing colours. Smooth animations only (epilepsy-safe).
  Divine  → black hole vortex sucking in particles then exploding outward
  Mythic  → swirling fire particles rising from bottom
  Legendary → golden starburst particles radiating outward
  Epic    → purple sparkle particles floating upward
  Rare+   → simple confetti
"""
import tkinter as tk
import random, math
from data.pet_models import (CLOTHING, PET_SPECIES, CRATE_TYPES,
                              RARITY_COLOURS, RARITIES)
from ui.theme import (BG_DARK, BG_CARD, BG_MID, ACCENT, FG_PRIMARY,
                      FG_SEC, FG_MUTED, BORDER)

RARITY_BG = {
    "divine":    "#080018",
    "mythic":    "#1a0800",
    "legendary": "#1a1200",
    "epic":      "#120020",
    "rare":      "#001020",
    "uncommon":  "#001408",
    "common":    "#0a0e18",
}
RARITY_BORDER = {
    "divine":    "#e8e0ff",
    "mythic":    "#ff6b35",
    "legendary": "#f0c040",
    "epic":      "#c77dff",
    "rare":      "#4a90d9",
    "uncommon":  "#22c55e",
    "common":    "#8da4cc",
}


def _pick_reward(crate_key: str) -> dict:
    ct = CRATE_TYPES.get(crate_key, {})
    weights = ct.get("weights", {})
    if not weights:
        return {"type": "none", "rarity": "common"}
    import random as _r
    total = sum(weights.values())
    r = _r.uniform(0, total)
    rarity = "common"
    for rar, w in weights.items():
        r -= w
        if r <= 0:
            rarity = rar
            break
    pets    = [p for p in ct.get("pets", [])    if PET_SPECIES.get(p, {}).get("unlock") == rarity]
    clothes = [c for c in ct.get("clothes", []) if CLOTHING.get(c, {}).get("rarity") == rarity]
    if pets and clothes:
        pool_type = "pet" if random.random() < 0.3 else "clothing"
    elif pets:
        pool_type = "pet"
    elif clothes:
        pool_type = "clothing"
    else:
        all_c = ct.get("clothes", [])
        if all_c:
            k = random.choice(all_c)
            v = CLOTHING[k]
            return {"type":"clothing","key":k,"name":v["name"],"emoji":v["emoji"],"rarity":v["rarity"]}
        return {"type":"none","rarity":"common"}
    if pool_type == "pet":
        k = random.choice(pets)
        s = PET_SPECIES[k]
        return {"type":"pet","key":k,"name":s["name"],"emoji":s["emoji_base"],"rarity":rarity}
    else:
        k = random.choice(clothes)
        v = CLOTHING[k]
        return {"type":"clothing","key":k,"name":v["name"],"emoji":v["emoji"],"rarity":rarity}


def _build_strip(crate_key: str, reward: dict) -> tuple:
    ct = CRATE_TYPES.get(crate_key, {})
    pool = []
    for k, v in CLOTHING.items():
        if k in ct.get("clothes", []):
            pool.append({"key":k,"name":v["name"],"emoji":v["emoji"],"rarity":v["rarity"]})
    for k in ct.get("pets", []):
        s = PET_SPECIES[k]
        pool.append({"key":k,"name":s["name"],"emoji":s["emoji_base"],"rarity":s["unlock"]})
    if not pool:
        pool = [{"key":"collar","name":"Collar","emoji":"🔵","rarity":"common"}]

    N = 52
    strip = [random.choice(pool) for _ in range(N)]
    reward_pos = N - 8

    # Buff surrounding slots for high rarities
    HIGH = {"divine","mythic","legendary"}
    reward_rarity = reward.get("rarity","common")
    if reward_rarity in HIGH:
        ri = RARITIES.index(reward_rarity)
        hype_pool = [i for i in pool if RARITIES.index(i["rarity"]) >= max(0, ri - 2)]
        if hype_pool:
            for off in [-3,-2,-1,1,2,3]:
                p = reward_pos + off
                if 0 <= p < N:
                    strip[p] = random.choice(hype_pool)
    strip[reward_pos] = reward
    return strip, reward_pos


# ── Particle systems (epilepsy-safe — no sudden colour changes) ───────────────

class _Particle:
    __slots__ = ["x","y","vx","vy","life","max_life","col","size","angle","speed"]
    def __init__(self, x, y, vx, vy, col, size, life):
        self.x=x; self.y=y; self.vx=vx; self.vy=vy
        self.col=col; self.size=size; self.life=life; self.max_life=life


def _make_vortex(w, h, colour) -> list:
    """Particles slowly spiraling inward toward centre — black hole effect."""
    cx, cy = w//2, h//2
    pts = []
    for _ in range(80):
        angle = random.uniform(0, 2*math.pi)
        dist  = random.uniform(80, min(w,h)//2)
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        pts.append(_Particle(px, py, 0, 0, colour,
                              random.randint(3,8), random.randint(60,120)))
    return pts


def _make_starburst(cx, cy, colour, n=60) -> list:
    """Particles shooting outward from centre in all directions."""
    pts = []
    for i in range(n):
        angle = (i / n) * 2 * math.pi + random.uniform(-0.1, 0.1)
        speed = random.uniform(3, 10)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        pts.append(_Particle(cx, cy, vx, vy, colour,
                              random.randint(5,12), random.randint(60,110)))
    return pts


def _make_fire(w, h, colour) -> list:
    """Particles rising from the bottom like flames."""
    pts = []
    for _ in range(100):
        px = random.uniform(w*0.2, w*0.8)
        py = random.uniform(h*0.7, h)
        vx = random.uniform(-1.5, 1.5)
        vy = random.uniform(-6, -2)
        pts.append(_Particle(px, py, vx, vy, colour,
                              random.randint(6,14), random.randint(50,90)))
    return pts


def _make_sparkles(w, h, colour) -> list:
    """Small sparkle particles floating upward gently."""
    pts = []
    for _ in range(50):
        px = random.uniform(50, w-50)
        py = random.uniform(50, h-50)
        vx = random.uniform(-0.5, 0.5)
        vy = random.uniform(-1.5, -0.3)
        pts.append(_Particle(px, py, vx, vy, colour,
                              random.randint(2,6), random.randint(60,100)))
    return pts


def _make_confetti(w, h) -> list:
    COLS = [ACCENT,"#4a90d9","#22c55e","#c77dff","#ff6b35"]
    pts = []
    for _ in range(50):
        px = random.uniform(0, w)
        py = random.uniform(-40, 0)
        vx = random.uniform(-1.5, 1.5)
        vy = random.uniform(2, 5)
        pts.append(_Particle(px, py, vx, vy, random.choice(COLS),
                              random.randint(5,10), 120))
    return pts


class CrateAnimationWindow:
    """Full-screen lootbox roller — epilepsy safe, smooth animations only."""

    def __init__(self, parent_root, crate_key: str, on_complete):
        self.root        = parent_root
        self.crate_key   = crate_key
        self.on_complete = on_complete
        self.reward      = _pick_reward(crate_key)
        self.strip, self.reward_pos = _build_strip(crate_key, self.reward)

        ct = CRATE_TYPES.get(crate_key, {})
        self.crate_name   = ct.get("name","Crate")
        self.crate_colour = ct.get("colour", ACCENT)

        self._particles   = []
        self._phase       = "roll"   # roll → effect → result
        self._anim_job    = None

        self._build_overlay()
        self._fade_in(0)

    def _build_overlay(self):
        root = self.root
        x, y = root.winfo_x(), root.winfo_y()
        w, h = root.winfo_width(), root.winfo_height()
        self.W, self.H = w, h

        self.overlay = tk.Toplevel(root)
        self.overlay.overrideredirect(True)
        self.overlay.geometry(f"{w}x{h}+{x}+{y}")
        self.overlay.configure(bg=BG_DARK)
        self.overlay.attributes("-alpha", 0.0)
        self.overlay.lift()

        self.canvas = tk.Canvas(self.overlay, bg=BG_DARK, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Title
        self.canvas.create_text(w//2, 55, text=f"Opening  {self.crate_name}",
                                 font=("Georgia",20,"bold"),
                                 fill=self.crate_colour, tags="title")
        # Track
        ty1 = h//2 - 55
        ty2 = h//2 + 55
        self.canvas.create_rectangle(0, ty1, w, ty2, fill=BG_MID, outline=BORDER, width=2)
        cx = w // 2
        self.canvas.create_line(cx, ty1-8, cx, ty2+8, fill=self.crate_colour, width=3)
        self.canvas.create_polygon(cx-10,ty1-14,cx+10,ty1-14,cx,ty1-2,
                                    fill=self.crate_colour, outline="")
        self.canvas.create_polygon(cx-10,ty2+14,cx+10,ty2+14,cx,ty2+2,
                                    fill=self.crate_colour, outline="")
        self.track_y  = (ty1+ty2)//2
        self.track_y1 = ty1
        self.track_y2 = ty2
        self.item_w   = 112
        self.current_px = [0.0]
        self.frame_n    = [0]

        self._close_text = self.canvas.create_text(
            w//2, h-38, text="", font=("TkDefaultFont",11), fill=FG_MUTED)

    def _fade_in(self, step):
        alpha = min(0.96, step * 0.09)
        try:
            self.overlay.attributes("-alpha", alpha)
        except Exception:
            return
        if alpha < 0.96:
            self.overlay.after(18, lambda: self._fade_in(step+1))
        else:
            self._start_roll()

    def _start_roll(self):
        total_px = self.reward_pos * self.item_w
        FRAMES   = 110

        def animate():
            f = self.frame_n[0]
            self.frame_n[0] += 1
            progress = min(1.0, f / FRAMES)
            eased    = 1 - (1 - progress) ** 3      # cubic ease-out
            self.current_px[0] = eased * total_px
            self._draw_strip()
            if progress < 1.0:
                delay = 8 if progress < 0.45 else 16 if progress < 0.82 else 33
                self.overlay.after(delay, animate)
            else:
                self.current_px[0] = total_px
                self._draw_strip()
                self.overlay.after(180, self._start_effect)

        self.overlay.after(100, animate)

    def _draw_strip(self):
        c = self.canvas
        c.delete("strip")
        w, h = self.W, self.H
        cx     = w // 2
        scroll = self.current_px[0]
        for i, item in enumerate(self.strip):
            item_cx = cx + (i * self.item_w) - scroll
            if item_cx < -self.item_w or item_cx > w + self.item_w:
                continue
            rarity = item.get("rarity","common")
            bg     = RARITY_BG.get(rarity, BG_MID)
            border = RARITY_BORDER.get(rarity, BORDER)
            bw = 3 if rarity in ("divine","mythic","legendary") else 2
            c.create_rectangle(item_cx-50, self.track_y1+4,
                                item_cx+50, self.track_y2-4,
                                fill=bg, outline=border, width=bw, tags="strip")
            c.create_text(item_cx, self.track_y-10, text=item.get("emoji","?"),
                          font=("TkDefaultFont",28), fill=FG_PRIMARY, tags="strip")
            nm = item.get("name","")
            if len(nm) > 11: nm = nm[:10]+"…"
            c.create_text(item_cx, self.track_y+28, text=nm,
                          font=("TkDefaultFont",8), fill=FG_SEC, tags="strip")
            rc = RARITY_BORDER.get(rarity, BORDER)
            c.create_oval(item_cx-5, self.track_y2-18, item_cx+5, self.track_y2-8,
                          fill=rc, outline="", tags="strip")

    # ── Effect dispatch ───────────────────────────────────────────────────────

    def _start_effect(self):
        rarity = self.reward.get("rarity","common")
        if rarity == "divine":
            self._play_black_hole()
        elif rarity == "mythic":
            self._play_fire_vortex()
        elif rarity == "legendary":
            self._play_starburst()
        elif rarity == "epic":
            self._play_sparkles_effect()
        else:
            self._particles = _make_confetti(self.W, self.H)
            self._run_particles(0, on_done=self._show_result)

    # ── Black hole effect (Divine) ────────────────────────────────────────────
    def _play_black_hole(self):
        """
        Particles spiral inward toward centre over ~2 seconds,
        then a ring expands outward. No flashing — smooth glow only.
        """
        w, h = self.W, self.H
        cx, cy = w//2, h//2
        colour = RARITY_BORDER["divine"]
        self._bh_particles = []
        for _ in range(140):
            angle = random.uniform(0, 2*math.pi)
            dist  = random.uniform(60, min(w,h)//2)
            self._bh_particles.append({
                "angle": angle, "dist": dist,
                "speed": random.uniform(0.04, 0.10),  # angular speed
                "inward": random.uniform(1.8, 3.5),   # pixels per frame toward centre
                "col": colour,
                "size": random.randint(3,7),
                "alive": True,
            })
        self._bh_ring_r  = [0]
        self._bh_phase   = "in"   # in → ring
        self._bh_frame   = [0]
        self._bh_cx      = cx
        self._bh_cy      = cy
        self._animate_bh()

    def _animate_bh(self):
        try:
            c = self.canvas
        except Exception:
            return
        c.delete("effect")
        w, h = self.W, self.H
        cx, cy = self._bh_cx, self._bh_cy
        f = self._bh_frame[0]
        self._bh_frame[0] += 1
        colour = RARITY_BORDER["divine"]

        if self._bh_phase == "in":
            # Draw dark centre disc growing slightly
            disc_r = min(40, f * 0.5)
            c.create_oval(cx-disc_r, cy-disc_r, cx+disc_r, cy+disc_r,
                          fill="#000000", outline=colour, width=2, tags="effect")

            all_dead = True
            for p in self._bh_particles:
                if not p["alive"]:
                    continue
                all_dead = False
                p["angle"] += p["speed"]
                p["dist"]  -= p["inward"]
                if p["dist"] < 8:
                    p["alive"] = False
                    continue
                px = cx + math.cos(p["angle"]) * p["dist"]
                py = cy + math.sin(p["angle"]) * p["dist"]
                s  = max(1, int(p["size"] * p["dist"] / 200))
                c.create_oval(px-s, py-s, px+s, py+s,
                              fill=p["col"], outline="", tags="effect")

            if all_dead or f > 130:
                self._bh_phase = "ring"
                self._bh_ring_r[0] = 0

            self.overlay.after(16, self._animate_bh)

        elif self._bh_phase == "ring":
            # Ring expands smoothly outward
            r = self._bh_ring_r[0]
            self._bh_ring_r[0] += 12
            max_r = max(w, h)
            # Draw dark centre still
            c.create_oval(cx-50, cy-50, cx+50, cy+50,
                          fill="#000000", outline="", tags="effect")
            if r < max_r:
                # Outer glow ring — 3 concentric rings with fading opacity
                for dr, alpha_tag in [(0,""), (8,""), (16,"")]:
                    rr = r + dr
                    if rr > 0:
                        c.create_oval(cx-rr, cy-rr, cx+rr, cy+rr,
                                      fill="", outline=colour,
                                      width=max(1, 3-dr//8), tags="effect")
                self.overlay.after(16, self._animate_bh)
            else:
                c.delete("effect")
                self.overlay.after(100, self._show_result)

    # ── Fire vortex (Mythic) ──────────────────────────────────────────────────
    def _play_fire_vortex(self):
        """Fire particles swirling upward in a vortex — warm orange glow."""
        self._particles = _make_fire(self.W, self.H, RARITY_BORDER["mythic"])
        # Add extra particles in a spiral
        cx, cy = self.W//2, self.H
        for i in range(40):
            angle = (i/40) * 4 * math.pi
            dist  = i * 3
            px    = cx + math.cos(angle) * dist
            py    = cy - i * 2
            self._particles.append(_Particle(
                px, py, math.cos(angle)*0.5, -random.uniform(2,5),
                RARITY_BORDER["mythic"], random.randint(4,9), random.randint(50,80)
            ))
        self._run_particles(0, gravity=-0.05, on_done=self._show_result)

    # ── Starburst (Legendary) ─────────────────────────────────────────────────
    def _play_starburst(self):
        """Gold particles burst from centre then drift outward with gravity."""
        cx, cy = self.W//2, self.H//2
        self._particles = _make_starburst(cx, cy, RARITY_BORDER["legendary"], n=120)
        self._run_particles(0, gravity=0.12, on_done=self._show_result)

    # ── Sparkles (Epic) ───────────────────────────────────────────────────────
    def _play_sparkles_effect(self):
        self._particles = _make_sparkles(self.W, self.H, RARITY_BORDER["epic"])
        self._run_particles(0, gravity=0.0, on_done=self._show_result)

    # ── Generic particle runner ───────────────────────────────────────────────
    def _run_particles(self, frame, gravity=0.08, on_done=None):
        try:
            c = self.canvas
        except Exception:
            return
        c.delete("effect")
        alive = False
        for p in self._particles:
            p.life -= 1
            if p.life <= 0:
                continue
            alive = True
            p.x += p.vx; p.y += p.vy; p.vy += gravity
            alpha_frac = p.life / p.max_life
            s = max(1, int(p.size * alpha_frac))
            # Fade colour toward background by adjusting size only (no colour change)
            c.create_oval(p.x-s, p.y-s, p.x+s, p.y+s,
                          fill=p.col, outline="", tags="effect")

        if alive and frame < 160:
            self.overlay.after(16, lambda: self._run_particles(frame+1, gravity, on_done))
        else:
            c.delete("effect")
            if on_done:
                self.overlay.after(80, on_done)

    # ── Result screen ─────────────────────────────────────────────────────────
    def _show_result(self):
        c = self.canvas
        w, h = self.W, self.H
        rarity = self.reward.get("rarity","common")
        r_col  = RARITY_BORDER.get(rarity, BORDER)
        r_bg   = RARITY_BG.get(rarity, BG_MID)
        cx, cy = w//2, h//2 + 50

        # Glow behind card (soft concentric ovals — not flashing)
        for radius, alpha in [(180,1),(150,1),(120,1)]:
            c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                          fill="", outline=r_col, width=1, tags="result_glow")

        # Result card
        c.create_rectangle(cx-240, cy-150, cx+240, cy+150,
                            fill=r_bg, outline=r_col, width=4, tags="result")
        c.create_text(cx, cy-82, text=self.reward.get("emoji","?"),
                      font=("TkDefaultFont",64), fill=FG_PRIMARY, tags="result")
        c.create_text(cx, cy-5,  text=self.reward.get("name",""),
                      font=("Georgia",18,"bold"), fill=FG_PRIMARY, tags="result")
        c.create_text(cx, cy+30, text=rarity.upper(),
                      font=("TkDefaultFont",12,"bold"), fill=r_col, tags="result")
        type_label = "Pet Unlocked!" if self.reward.get("type")=="pet" else "Accessory Unlocked!"
        c.create_text(cx, cy+58, text=type_label,
                      font=("TkDefaultFont",10), fill=FG_SEC, tags="result")

        # Gentle ambient sparkles for high rarities (no flashing)
        if rarity in ("divine","mythic","legendary","epic"):
            self._ambient = _make_sparkles(w, h, r_col)
            self._run_ambient(0)

        c.itemconfigure(self._close_text, text="✕  Click anywhere to close")
        c.bind("<Button-1>", self._close)
        self.overlay.bind("<Escape>", self._close)

    def _run_ambient(self, frame):
        """Gentle ambient sparkles on result screen — slow, no flashing."""
        try:
            c = self.canvas
        except Exception:
            return
        c.delete("ambient")
        for p in self._ambient:
            p.life -= 0.4   # much slower fade
            if p.life <= 0:
                p.life = p.max_life   # respawn
                p.x = random.uniform(50, self.W-50)
                p.y = random.uniform(50, self.H-50)
            p.x += p.vx; p.y += p.vy
            s = max(1, int(p.size * (p.life / p.max_life)))
            c.create_oval(p.x-s, p.y-s, p.x+s, p.y+s,
                          fill=p.col, outline="", tags="ambient")
        if frame < 600:   # runs until closed
            self.overlay.after(24, lambda: self._run_ambient(frame+1))

    def _close(self, event=None):
        try:
            self.overlay.destroy()
        except Exception:
            pass
        self.on_complete(self.reward)
