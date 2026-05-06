"""
Pet canvas renderer — draws pets and clothing as vector art on tkinter Canvas.
Supports layered clothing overlays. No emojis.
"""
import tkinter as tk
import math


SPECIES_COLOURS = {
    "cat":      {"body": "#e8c080", "inner": "#f5e0c0", "accent": "#c8a060", "eye": "#2d5a8c", "nose": "#e87070", "pupil": "#1a1a2e"},
    "dog":      {"body": "#c8a070", "inner": "#e8c890", "accent": "#a07050", "eye": "#3d2010", "nose": "#201008", "pupil": "#100808"},
    "fox":      {"body": "#e86030", "inner": "#f0d0a0", "accent": "#c04020", "eye": "#3d2010", "nose": "#201008", "pupil": "#100808"},
    "dragon":   {"body": "#60c060", "inner": "#90e890", "accent": "#409040", "eye": "#e8d020", "nose": "#e06040", "pupil": "#202020"},
    "bunny":    {"body": "#f0e0e8", "inner": "#ffffff", "accent": "#e0b0c0", "eye": "#e04060", "nose": "#e04060", "pupil": "#201020"},
    "bear":     {"body": "#805030", "inner": "#c09060", "accent": "#604020", "eye": "#201008", "nose": "#100808", "pupil": "#080400"},
    "wolf":     {"body": "#808090", "inner": "#c0c0d0", "accent": "#505060", "eye": "#f0d020", "nose": "#202020", "pupil": "#101010"},
    "penguin":  {"body": "#202030", "inner": "#f0f0f0", "accent": "#101020", "eye": "#f0f0f0", "nose": "#e08030", "pupil": "#101010"},
    "owl":      {"body": "#805020", "inner": "#e8d090", "accent": "#503010", "eye": "#f0c820", "nose": "#e07030", "pupil": "#202020"},
    "tiger":    {"body": "#e88030", "inner": "#f8e0b0", "accent": "#202020", "eye": "#60a020", "nose": "#e04040", "pupil": "#101010"},
    "panda":    {"body": "#f0f0f0", "inner": "#f0f0f0", "accent": "#202020", "eye": "#202020", "nose": "#202020", "pupil": "#101010"},
    "unicorn":  {"body": "#f8d0f0", "inner": "#ffffff", "accent": "#e090e0", "eye": "#6040d0", "nose": "#f090b0", "pupil": "#301060"},
    "phoenix":  {"body": "#e84020", "inner": "#f8c040", "accent": "#c02010", "eye": "#f0d020", "nose": "#e06020", "pupil": "#202020"},
    "frog":     {"body": "#40b840", "inner": "#c0f0a0", "accent": "#208020", "eye": "#f0d020", "nose": "#208020", "pupil": "#101010"},
    "axolotl":  {"body": "#f090b0", "inner": "#ffe0e8", "accent": "#d06080", "eye": "#201030", "nose": "#c05070", "pupil": "#100820"},
    "deer":     {"body": "#c08040", "inner": "#e8c080", "accent": "#906030", "eye": "#3d2010", "nose": "#201008", "pupil": "#100808"},
    "koala":    {"body": "#909090", "inner": "#d0d0d0", "accent": "#606060", "eye": "#201008", "nose": "#401010", "pupil": "#100808"},
    "shark":    {"body": "#507090", "inner": "#e0e8f0", "accent": "#304060", "eye": "#101020", "nose": "#304060", "pupil": "#080810"},
    "capybara": {"body": "#b09060", "inner": "#d4b080", "accent": "#806040", "eye": "#201008", "nose": "#401010", "pupil": "#100808"},
    "dino":     {"body": "#508050", "inner": "#90d090", "accent": "#306030", "eye": "#f0d020", "nose": "#306030", "pupil": "#101010"},
}

def _oval(c, x, y, rx, ry, fill, outline="", width=1):
    return c.create_oval(x-rx, y-ry, x+rx, y+ry, fill=fill, outline=outline, width=width)

def _rect(c, x1, y1, x2, y2, fill, outline="", width=1):
    return c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)

def _poly(c, points, fill, outline="", width=1):
    return c.create_polygon(points, fill=fill, outline=outline, width=width, smooth=False)

def draw_pet(canvas: tk.Canvas, species: str, level: int, cx: int, cy: int, size: int = 100):
    """Draw a pet centred at (cx, cy) with given size."""
    cols = SPECIES_COLOURS.get(species, SPECIES_COLOURS["cat"])
    tier = min(level // 20, 4)
    s = size / 100  # scale factor

    dispatch = {
        "cat":      _draw_cat,    "dog":      _draw_dog,
        "fox":      _draw_fox,    "dragon":   _draw_dragon,
        "bunny":    _draw_bunny,  "bear":     _draw_bear,
        "wolf":     _draw_wolf,   "penguin":  _draw_penguin,
        "owl":      _draw_owl,    "tiger":    _draw_tiger,
        "panda":    _draw_panda,  "unicorn":  _draw_unicorn,
        "phoenix":  _draw_phoenix,"frog":     _draw_frog,
        "axolotl":  _draw_axolotl,"deer":     _draw_deer,
        "koala":    _draw_koala,  "shark":    _draw_shark,
        "capybara": _draw_capybara,"dino":    _draw_dino,
    }
    fn = dispatch.get(species, _draw_cat)
    fn(canvas, cols, cx, cy, s, tier)

def _cloth_dragon_wings(c, cx, cy, s):
    for side, sign in [(-1,-1),(1,1)]:
        pts = [cx+sign*25*s,cy-10*s, cx+sign*70*s,cy-50*s,
               cx+sign*75*s,cy+10*s, cx+sign*50*s,cy+30*s, cx+sign*25*s,cy+20*s]
        _poly(c, pts, "#409040", "#206020", 2)
        for vx,vy in [(sign*40*s,-20*s),(sign*55*s,-5*s),(sign*35*s,10*s)]:
            c.create_line(cx+sign*25*s,cy+5*s, cx+vx,cy+vy, fill="#206020", width=max(1,int(2*s)))

def _cloth_phoenix_feather(c, cx, cy, s):
    for i, (dx, dy) in enumerate([(-8,0),(0,-5),(8,0),(-4,-12),(4,-12)]):
        col = ["#e84020","#f0a020","#f0f020","#e84020","#f0a020"][i]
        _poly(c, [cx+dx*s,cy+dy*s, cx+(dx-4)*s,cy+(dy-18)*s, cx+(dx+4)*s,cy+(dy-18)*s], col, "", 0)

def _cloth_unicorn_horn(c, cx, cy, s):
    hy = cy - 46*s
    _poly(c, [cx-5*s,hy, cx+5*s,hy, cx+2*s,hy-28*s, cx-2*s,hy-28*s], "#f0c040", "#c09020", 2)
    for y in [hy-6, hy-12, hy-18, hy-24]:
        c.create_line(cx-4*s, y*s, cx+4*s, y*s, fill="#e0a0e0", width=max(1,int(s)))

def _cloth_samurai_helm(c, cx, cy, s):
    hy = cy - 40*s
    _oval(c, cx, hy, 28*s, 22*s, "#cc2020", "#881010", 2)
    _rect(c, cx-24*s, hy+10*s, cx+24*s, hy+18*s, "#cc2020", "#881010", 2)
    _poly(c, [cx-28*s,hy-12*s, cx-38*s,hy-22*s, cx-18*s,hy-12*s], "#f0c040", "#c09020", 1)
    _poly(c, [cx+28*s,hy-12*s, cx+38*s,hy-22*s, cx+18*s,hy-12*s], "#f0c040", "#c09020", 1)
    _rect(c, cx-16*s, hy+2*s, cx+16*s, hy+8*s, "#401010", "", 0)
    for ix in [-8, -2, 4, 10]:
        c.create_line(cx+ix*s, hy+2*s, cx+ix*s, hy+8*s, fill="#cc2020", width=max(1,int(s)))

def _cloth_space_helmet(c, cx, cy, s):
    hy = cy - 38*s
    _oval(c, cx, hy, 34*s, 32*s, "#d0d8e0", "#9098a0", 3)
    _oval(c, cx-4*s, hy-2*s, 22*s, 20*s, "#90c8f0", "#70a8d0", 1)
    _oval(c, cx-8*s, hy-8*s, 8*s, 5*s, "#ffffff", "", 0)
    _oval(c, cx-26*s, hy+8*s, 6*s, 8*s, "#f0c040", "#c09020", 2)
    _oval(c, cx+26*s, hy+8*s, 6*s, 8*s, "#f0c040", "#c09020", 2)

def _cloth_jester_hat(c, cx, cy, s):
    hy = cy - 42*s
    _poly(c, [cx-24*s,hy+4*s, cx,hy+4*s, cx-16*s,hy-30*s], "#e03020", "#a01010", 2)
    _poly(c, [cx+24*s,hy+4*s, cx,hy+4*s, cx+16*s,hy-30*s], "#4040e0", "#2020a0", 2)
    _poly(c, [cx-4*s,hy+4*s, cx+4*s,hy+4*s, cx,hy-32*s], "#f0c040", "#c09020", 2)
    _oval(c, cx-18*s, hy-32*s, 6*s, 6*s, "#f0f040", "", 0)
    _oval(c, cx+18*s, hy-32*s, 6*s, 6*s, "#f0f040", "", 0)
    _oval(c, cx, hy-34*s, 6*s, 6*s, "#f0f040", "", 0)

def _cloth_viking_helm(c, cx, cy, s):
    hy = cy - 40*s
    _oval(c, cx, hy, 28*s, 16*s, "#888888", "#555555", 2)
    _oval(c, cx, hy-12*s, 20*s, 14*s, "#888888", "#555555", 2)
    c.create_line(cx-20*s, hy+6*s, cx+20*s, hy+6*s, fill="#555555", width=max(2,int(3*s)))
    _poly(c, [cx-26*s,hy+4*s, cx-42*s,hy-4*s, cx-36*s,hy+10*s], "#d0d0b0", "#a0a080", 2)
    _poly(c, [cx+26*s,hy+4*s, cx+42*s,hy-4*s, cx+36*s,hy+10*s], "#d0d0b0", "#a0a080", 2)

def _cloth_detective_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 26*s, 6*s, "#3d2d1d", "#201808", 2)
    _rect(c, cx-16*s, hy-30*s, cx+16*s, hy, "#3d2d1d", "#201808", 2)
    _rect(c, cx+16*s, hy-12*s, cx+32*s, hy-6*s, "#3d2d1d", "#201808", 1)
    _oval(c, cx, hy-15*s, 14*s, 6*s, "#4d3d2d", "", 0)

def _cloth_cowboy_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 34*s, 8*s, "#8b5e3c", "#5d3a20", 2)
    _poly(c, [cx-18*s,hy, cx+18*s,hy, cx+14*s,hy-28*s, cx-14*s,hy-28*s], "#8b5e3c", "#5d3a20", 2)
    c.create_arc(cx-18*s, hy-18*s, cx+18*s, hy-8*s, start=180, extent=180, style="arc",
                 outline="#5d3a20", width=max(2,int(3*s)))
    _rect(c, cx-14*s, hy-6*s, cx+14*s, hy-3*s, "#f0c040", "", 0)

def _cloth_chef_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 22*s, 8*s, "#f0f0f0", "#cccccc", 2)
    _oval(c, cx, hy-22*s, 18*s, 22*s, "#f0f0f0", "#cccccc", 2)
    _rect(c, cx-22*s, hy-4*s, cx+22*s, hy+2*s, "#f0f0f0", "#cccccc", 1)

def _cloth_ninja_mask(c, cx, cy, s):
    fy = cy - 15*s
    _rect(c, cx-24*s, fy-8*s, cx+24*s, fy+4*s, "#1a1a2e", "#000010", 0)
    _oval(c, cx, fy-2*s, 24*s, 14*s, "#1a1a2e", "#000010", 2)
    _oval(c, cx-11*s, cy-22*s, 8*s, 5*s, "#1a1a2e", "", 0)
    _oval(c, cx+11*s, cy-22*s, 8*s, 5*s, "#1a1a2e", "", 0)
    c.create_line(cx-24*s, fy-2*s, cx+24*s, fy-2*s, fill="#2a2a4e", width=max(1,int(s)))

def _cloth_pirate_hat(c, cx, cy, s):
    hy = cy - 42*s
    _poly(c, [cx-28*s,hy+6*s, cx+28*s,hy+6*s, cx+20*s,hy-20*s, cx-20*s,hy-20*s],
          "#1a1a2e", "#000010", 2)
    _oval(c, cx-26*s, hy+8*s, 8*s, 6*s, "#1a1a2e", "", 0)
    _oval(c, cx+26*s, hy+8*s, 8*s, 6*s, "#1a1a2e", "", 0)
    _oval(c, cx, hy-4*s, 12*s, 10*s, "#f0f0f0", "#cccccc", 2)
    c.create_line(cx-8*s, hy-4*s, cx+8*s, hy-4*s, fill="#1a1a2e", width=max(2,int(3*s)))
    c.create_line(cx, hy-12*s, cx, hy+4*s, fill="#1a1a2e", width=max(2,int(3*s)))

def _cloth_witch_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 30*s, 8*s, "#2a0a4a", "#180628", 2)
    _poly(c, [cx-22*s,hy, cx+22*s,hy, cx+6*s,hy-50*s, cx-6*s,hy-50*s],
          "#2a0a4a", "#180628", 2)
    _rect(c, cx-22*s, hy-4*s, cx+22*s, hy, "#e03090", "", 0)
    _draw_star(c, cx+8*s, hy-20*s, 5*s, "#f0c040")
    _draw_star(c, cx-6*s, hy-35*s, 4*s, "#f0c040")

def _cloth_santa_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy+6*s, 28*s, 8*s, "#f0f0f0", "#cccccc", 2)
    _poly(c, [cx-22*s,hy+4*s, cx+22*s,hy+4*s, cx+8*s,hy-36*s, cx-8*s,hy-36*s],
          "#e03020", "#a01010", 2)
    _oval(c, cx+6*s, hy-38*s, 7*s, 7*s, "#f0f0f0", "#cccccc", 1)

def _cloth_elf_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy+4*s, 24*s, 7*s, "#e03020", "#a01010", 2)
    _poly(c, [cx-20*s,hy+2*s, cx+20*s,hy+2*s, cx+4*s,hy-38*s, cx-4*s,hy-38*s],
          "#20a020", "#106010", 2)
    _oval(c, cx+2*s, hy-40*s, 5*s, 5*s, "#f0c040", "", 0)
    for i in range(3):
        y = hy - 10 - i*10
        _oval(c, cx+18*s-i*5*s, y*s, 3*s, 3*s, "#f0c040", "", 0)

def _cloth_rainbow_hat(c, cx, cy, s):
    hy = cy - 42*s
    colours = ["#e03020","#f08020","#f0f020","#20c040","#2060f0","#8020c0"]
    for i, col in enumerate(colours):
        _poly(c, [cx-(18-i*2)*s, hy+4*s, cx+(18-i*2)*s, hy+4*s,
                  cx+(10-i*1.5)*s, hy-20*s, cx-(10-i*1.5)*s, hy-20*s], col, "", 0)
    _oval(c, cx, hy-22*s, 8*s, 8*s, "#f0f0f0", "", 0)

def _cloth_angel_wings(c, cx, cy, s):
    for sign in [-1, 1]:
        _poly(c, [cx+sign*20*s,cy-15*s, cx+sign*60*s,cy-45*s,
                  cx+sign*65*s,cy+5*s, cx+sign*40*s,cy+25*s, cx+sign*20*s,cy+10*s],
              "#f0f0f8", "#d0d0e8", 2)
        _poly(c, [cx+sign*20*s,cy-5*s, cx+sign*50*s,cy-30*s,
                  cx+sign*55*s,cy+10*s, cx+sign*30*s,cy+20*s],
              "#ffffff", "#e0e0f0", 1)

def _cloth_devil_horns(c, cx, cy, s):
    for sx, sign in [(-16,-1),(16,1)]:
        hy = cy - 46*s
        _poly(c, [cx+sx*s-6*s,hy, cx+sx*s+6*s,hy, cx+(sx+sign*4)*s,hy-24*s],
              "#e03020", "#a01010", 2)

def _cloth_tiara(c, cx, cy, s):
    hy = cy - 48*s
    c.create_arc(cx-28*s, hy-10*s, cx+28*s, hy+10*s, start=0, extent=180, style="arc",
                 outline="#f0c040", width=max(3,int(4*s)))
    for dx, h in [(-20,8),(-10,12),(0,16),(10,12),(20,8)]:
        c.create_line(cx+dx*s, hy, cx+dx*s, hy-h*s, fill="#f0c040", width=max(2,int(2*s)))
        _oval(c, cx+dx*s, hy-h*s, 3*s, 3*s, "#e040a0", "", 0)

def _cloth_mushroom_hat(c, cx, cy, s):
    hy = cy - 38*s
    _oval(c, cx, hy, 28*s, 12*s, "#f0f0f0", "#cccccc", 2)
    _oval(c, cx, hy-16*s, 24*s, 20*s, "#e03020", "#a01010", 2)
    for dx, dy in [(-8,-20),(0,-26),(10,-18),(-14,-12),(12,-10)]:
        _oval(c, cx+dx*s, hy+dy*s, 4*s, 4*s, "#f0f0f0", "", 0)

def _cloth_shark_fin(c, cx, cy, s):
    fx = cx + 0
    fy = cy - 50*s
    _poly(c, [fx-6*s,fy+20*s, fx+6*s,fy+20*s, fx+4*s,fy-10*s, fx-4*s,fy-10*s],
          "#507090", "#304060", 2)
    _poly(c, [fx-6*s,fy+20*s, fx-20*s,fy+20*s, fx-6*s,fy-10*s], "#507090", "#304060", 1)

def _cloth_pirate_eyepatch(c, cx, cy, s):
    ey = cy - 22*s
    _oval(c, cx-13*s, ey, 10*s, 9*s, "#1a1a2e", "#000010", 2)
    c.create_line(cx-3*s, ey-8*s, cx+8*s, ey-8*s, fill="#1a1a2e", width=max(2,int(2*s)))
    c.create_line(cx-3*s, ey+6*s, cx+5*s, ey+10*s, fill="#1a1a2e", width=max(2,int(2*s)))

def _cloth_mortarboard(c, cx, cy, s):
    hy = cy - 44*s
    _oval(c, cx, hy, 22*s, 9*s, "#1a1a2e", "#000010", 1)
    _poly(c, [cx-28*s,hy-6*s, cx+28*s,hy-6*s, cx+32*s,hy-14*s, cx-32*s,hy-14*s],
          "#1a1a2e", "#000010", 2)
    c.create_line(cx+28*s, hy-12*s, cx+28*s, hy+8*s, fill="#f0c040", width=max(2,int(3*s)))
    _oval(c, cx+28*s, hy+10*s, 5*s, 5*s, "#f0c040", "", 0)

def _cloth_astronaut_helm(c, cx, cy, s):
    hy = cy - 36*s
    _oval(c, cx, hy, 36*s, 34*s, "#e0e8f0", "#a0b0c0", 3)
    _oval(c, cx-2*s, hy-2*s, 24*s, 22*s, "#90c8f0", "#70a8d0", 2)
    _oval(c, cx-12*s, hy-12*s, 8*s, 5*s, "#ffffff", "", 0)
    _rect(c, cx-28*s, hy+18*s, cx+28*s, hy+26*s, "#c0c8d0", "#9098a0", 2)
    _oval(c, cx-20*s, hy+22*s, 5*s, 4*s, "#e03020", "", 0)
    _oval(c, cx+20*s, hy+22*s, 5*s, 4*s, "#20a020", "", 0)

def _cloth_fez(c, cx, cy, s):
    hy = cy - 40*s
    _poly(c, [cx-20*s,hy+4*s, cx+20*s,hy+4*s, cx+14*s,hy-24*s, cx-14*s,hy-24*s],
          "#c02020", "#801010", 2)
    _oval(c, cx, hy+4*s, 20*s, 6*s, "#a01010", "", 0)
    c.create_line(cx+12*s, hy-22*s, cx+12*s, hy-40*s, fill="#1a1a2e", width=max(2,int(2*s)))
    _oval(c, cx+12*s, hy-42*s, 4*s, 4*s, "#f0c040", "", 0)

def _cloth_reindeer_antlers(c, cx, cy, s):
    for side, sign in [(-1,-1),(1,1)]:
        bx = cx + sign*18*s
        c.create_line(bx, cy-44*s, bx+sign*10*s, cy-62*s, fill="#8b5e3c", width=max(3,int(5*s)))
        c.create_line(bx+sign*10*s, cy-62*s, bx+sign*16*s, cy-52*s, fill="#8b5e3c", width=max(2,int(3*s)))
        c.create_line(bx+sign*10*s, cy-62*s, bx+sign*6*s, cy-70*s, fill="#8b5e3c", width=max(2,int(3*s)))
        c.create_line(bx+sign*10*s, cy-62*s, bx+sign*18*s, cy-62*s, fill="#8b5e3c", width=max(2,int(3*s)))

def _cloth_bunny_ears(c, cx, cy, s):
    for sx, col in [(-16,"#f0e0e8"),(16,"#f0e0e8")]:
        _oval(c, cx+sx*s, cy-62*s, 9*s, 22*s, col, "#e0b0c0", 2)
        _oval(c, cx+sx*s, cy-62*s, 5*s, 17*s, "#e04060", "", 0)

def _cloth_cat_ears(c, cx, cy, s):
    for sx in [-18, 18]:
        _poly(c, [cx+sx*s-8*s,cy-42*s, cx+sx*s+8*s,cy-42*s, cx+sx*s,cy-60*s],
              "#e8c080", "#c8a060", 2)
        _poly(c, [cx+sx*s-5*s,cy-44*s, cx+sx*s+5*s,cy-44*s, cx+sx*s,cy-56*s],
              "#e87070", "", 0)

def _cloth_swim_goggles(c, cx, cy, s):
    ey = cy - 22*s
    _oval(c, cx-13*s, ey, 10*s, 8*s, "#40a0e0", "#2080c0", 2)
    _oval(c, cx+13*s, ey, 10*s, 8*s, "#40a0e0", "#2080c0", 2)
    c.create_line(cx-3*s, ey, cx+3*s, ey, fill="#f0c040", width=max(3,int(3*s)))
    c.create_line(cx-23*s, ey, cx-32*s, ey+3*s, fill="#f0c040", width=max(2,int(2*s)))
    c.create_line(cx+23*s, ey, cx+32*s, ey+3*s, fill="#f0c040", width=max(2,int(2*s)))

def _cloth_superhero_mask(c, cx, cy, s):
    ey = cy - 20*s
    _poly(c, [cx-26*s,ey-8*s, cx-8*s,ey-8*s, cx-2*s,ey+6*s,
              cx+2*s,ey+6*s, cx+8*s,ey-8*s, cx+26*s,ey-8*s,
              cx+26*s,ey+8*s, cx+8*s,ey+8*s, cx+2*s,ey-2*s,
              cx-2*s,ey-2*s, cx-8*s,ey+8*s, cx-26*s,ey+8*s],
          "#e03020", "#a01010", 2)

def _cloth_propeller_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 22*s, 8*s, "#4060e0", "#2040c0", 2)
    _oval(c, cx, hy-10*s, 14*s, 8*s, "#4060e0", "#2040c0", 2)
    _oval(c, cx, hy-18*s, 3*s, 3*s, "#c0c0c0", "", 0)
    _poly(c, [cx,hy-18*s, cx-16*s,hy-26*s, cx-14*s,hy-14*s], "#e03020", "#a01010", 1)
    _poly(c, [cx,hy-18*s, cx+16*s,hy-10*s, cx+14*s,hy-22*s], "#20a020", "#106010", 1)

def _cloth_laurel_wreath(c, cx, cy, s):
    hy = cy - 48*s
    import math
    for ang in range(0, 360, 20):
        rx = cx + 28*s * math.cos(math.radians(ang))
        ry = hy + 8*s * math.sin(math.radians(ang))
        _poly(c, [rx,ry, rx+5*s,ry-8*s, rx-5*s,ry-8*s], "#40a040", "", 0)

def _cloth_thunder_crown(c, cx, cy, s):
    base_y = cy - 48*s
    _rect(c, cx-20*s, base_y, cx+20*s, base_y-10*s, "#6060e0", "#4040c0", 2)
    for xi, col in [(-16,"#f0c040"),(-5,"#80c0f0"),(6,"#f0c040"),(17,"#80c0f0")]:
        _poly(c, [cx+xi*s,base_y, cx+(xi+5)*s,base_y-22*s, cx+(xi+10)*s,base_y],
              col, "#a0a080", 1)
    for dx in [-10, 0, 10]:
        _draw_star(c, cx+dx*s, base_y-5*s, 3*s, "#f0f040")

def _cloth_ice_crown(c, cx, cy, s):
    base_y = cy - 48*s
    _rect(c, cx-20*s, base_y, cx+20*s, base_y-8*s, "#a0d0f0", "#80b0d0", 2)
    for xi in [-18, -8, 2, 12]:
        _poly(c, [cx+xi*s,base_y, cx+(xi+4)*s,base_y-20*s, cx+(xi+8)*s,base_y],
              "#c0e8ff", "#80b0d0", 1)
    for dx in [-14, -4, 6, 16]:
        _oval(c, cx+dx*s, base_y-5*s, 3*s, 3*s, "#ffffff", "#80b0d0", 1)

def _cloth_black_cape(c, cx, cy, s):
    _poly(c, [cx-15*s,cy-25*s, cx-50*s,cy+5*s, cx-45*s,cy+55*s,
              cx+45*s,cy+55*s, cx+50*s,cy+5*s, cx+15*s,cy-25*s],
          "#1a1a2e", "#000010", 2)
    _poly(c, [cx-15*s,cy-25*s, cx,cy-30*s, cx+15*s,cy-25*s,
              cx+12*s,cy-15*s, cx,cy-18*s, cx-12*s,cy-15*s],
          "#e0c060", "#c0a040", 1)
    _oval(c, cx, cy-20*s, 5*s, 5*s, "#c0a040", "#a08020", 2)

def _cloth_graduation_sash(c, cx, cy, s):
    _poly(c, [cx-6*s,cy-30*s, cx+6*s,cy-30*s, cx+20*s,cy+30*s, cx+8*s,cy+30*s],
          "#4060c0", "#2040a0", 2)
    _draw_star(c, cx+14*s, cy, 5*s, "#f0c040")

def _cloth_knitted_hat(c, cx, cy, s):
    hy = cy - 40*s
    _oval(c, cx, hy, 26*s, 16*s, "#c06040", "#904020", 2)
    for y_off in [0, 6, 12]:
        c.create_arc(cx-26*s, hy-8*s+y_off*s, cx+26*s, hy+8*s+y_off*s,
                     start=0, extent=180, style="arc",
                     outline="#804020", width=max(1,int(s)))
    _oval(c, cx, hy-18*s, 10*s, 10*s, "#e08060", "#c06040", 1)

def _cloth_paper_crown(c, cx, cy, s):
    base_y = cy - 46*s
    _rect(c, cx-20*s, base_y, cx+20*s, base_y-6*s, "#f0f0d0", "#c0c0a0", 2)
    for xi in [-16, -6, 4, 14]:
        _poly(c, [cx+xi*s,base_y, cx+(xi+5)*s,base_y-18*s, cx+(xi+10)*s,base_y],
              "#f0f0d0", "#c0c0a0", 1)

def _cloth_sweatband(c, cx, cy, s):
    hy = cy - 44*s
    _rect(c, cx-28*s, hy, cx+28*s, hy+10*s, "#e03020", "#a01010", 0)
    c.create_arc(cx-28*s, hy-5*s, cx+28*s, hy+5*s,
                 start=0, extent=180, style="arc",
                 fill="#e03020", outline="#a01010", width=2)
    c.create_arc(cx-28*s, hy+5*s, cx+28*s, hy+15*s,
                 start=180, extent=180, style="arc",
                 fill="#e03020", outline="#a01010", width=2)

def _cloth_detective_glass(c, cx, cy, s):
    _oval(c, cx+10*s, cy-18*s, 14*s, 14*s, "", "#3d2d1d", 2)
    c.create_line(cx+24*s, cy-18*s, cx+36*s, cy-10*s, fill="#3d2d1d", width=max(3,int(4*s)))
    _oval(c, cx+36*s, cy-10*s, 5*s, 5*s, "#3d2d1d", "#201008", 2)

def _cloth_bandaid(c, cx, cy, s):
    bx, by = cx+12*s, cy-32*s
    _poly(c, [bx-8*s,by-3*s, bx+8*s,by-3*s, bx+8*s,by+3*s, bx-8*s,by+3*s], "#f0c0a0","#d09080",2)
    _rect(c, bx-3*s, by-3*s, bx+3*s, by+3*s, "#ffffff", "", 0)
    c.create_line(bx-1*s, by, bx+1*s, by, fill="#d09080", width=max(1,int(s)))

def _cloth_safety_glasses(c, cx, cy, s):
    ey = cy - 22*s
    _oval(c, cx-13*s, ey, 10*s, 8*s, "#90d090", "#60b060", 2)
    _oval(c, cx+13*s, ey, 10*s, 8*s, "#90d090", "#60b060", 2)
    c.create_line(cx-3*s, ey, cx+3*s, ey, fill="#f0c040", width=max(3,int(3*s)))
    _rect(c, cx-23*s, ey-8*s, cx-3*s, ey+8*s, "#90d090", "#60b060", 1)
    _rect(c, cx+3*s, ey-8*s, cx+23*s, ey+8*s, "#90d090", "#60b060", 1)

def _cloth_3d_glasses(c, cx, cy, s):
    ey = cy - 22*s
    _oval(c, cx-13*s, ey, 10*s, 8*s, "#e04040", "#c02020", 2)
    _oval(c, cx+13*s, ey, 10*s, 8*s, "#4040e0", "#2020c0", 2)
    c.create_line(cx-3*s, ey, cx+3*s, ey, fill="#1a1a2e", width=max(2,int(2*s)))
    c.create_line(cx-23*s, ey, cx-32*s, ey+4*s, fill="#1a1a2e", width=max(2,int(2*s)))
    c.create_line(cx+23*s, ey, cx+32*s, ey+4*s, fill="#1a1a2e", width=max(2,int(2*s)))


def _draw_wolf(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+20*s, 38*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-18*s, 34*s, 30*s, cols["body"], cols["accent"], 2)
    _poly(c, [cx-22*s,cy-42*s, cx-30*s,cy-62*s, cx-8*s,cy-42*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx+22*s,cy-42*s, cx+30*s,cy-62*s, cx+8*s,cy-42*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx-22*s,cy-44*s, cx-26*s,cy-58*s, cx-10*s,cy-44*s], cols["inner"], "", 0)
    _poly(c, [cx+22*s,cy-44*s, cx+26*s,cy-58*s, cx+10*s,cy-44*s], cols["inner"], "", 0)
    _oval(c, cx, cy-14*s, 20*s, 18*s, cols["inner"], "", 0)
    _oval(c, cx-12*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+12*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-12*s, cy-24*s, 4*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx+12*s, cy-24*s, 4*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx-11*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+11*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-8*s, 6*s, 5*s, cols["nose"], "", 0)
    c.create_line(cx, cy-3*s, cx-5*s, cy+1*s, fill=cols["accent"], width=max(1,int(2*s)))
    c.create_line(cx, cy-3*s, cx+5*s, cy+1*s, fill=cols["accent"], width=max(1,int(2*s)))
    _oval(c, cx-22*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+22*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    if tier >= 1:
        c.create_arc(cx+20*s, cy+8*s, cx+58*s, cy+48*s, start=90, extent=200, style="arc",
                     outline=cols["body"], width=max(3,int(6*s)))

def _draw_penguin(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+20*s, 34*s, 32*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-16*s, 28*s, 28*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy+8*s, 20*s, 28*s, cols["inner"], "", 0)
    _oval(c, cx, cy-14*s, 18*s, 20*s, cols["inner"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-11*s, cy-23*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+11*s, cy-23*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _poly(c, [cx-6*s,cy-10*s, cx+6*s,cy-10*s, cx,cy-4*s], cols["nose"], "", 0)
    _poly(c, [cx-28*s,cy-4*s, cx-20*s,cy+20*s, cx-14*s,cy+20*s, cx-20*s,cy-4*s], cols["body"], cols["accent"], 1)
    _poly(c, [cx+28*s,cy-4*s, cx+20*s,cy+20*s, cx+14*s,cy+20*s, cx+20*s,cy-4*s], cols["body"], cols["accent"], 1)
    _oval(c, cx-16*s, cy+50*s, 12*s, 7*s, cols["nose"], cols["accent"], 1)
    _oval(c, cx+16*s, cy+50*s, 12*s, 7*s, cols["nose"], cols["accent"], 1)

def _draw_owl(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+20*s, 36*s, 32*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-14*s, 32*s, 30*s, cols["body"], cols["accent"], 2)
    _poly(c, [cx-22*s,cy-38*s, cx-14*s,cy-52*s, cx-6*s,cy-38*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx+22*s,cy-38*s, cx+14*s,cy-52*s, cx+6*s,cy-38*s], cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-10*s, 22*s, 24*s, cols["inner"], "", 0)
    _oval(c, cx-13*s, cy-20*s, 10*s, 10*s, "#f0f0d0", cols["accent"], 2)
    _oval(c, cx+13*s, cy-20*s, 10*s, 10*s, "#f0f0d0", cols["accent"], 2)
    _oval(c, cx-13*s, cy-20*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+13*s, cy-20*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-13*s, cy-20*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+13*s, cy-20*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+12*s, cy-22*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _poly(c, [cx-4*s,cy-8*s, cx+4*s,cy-8*s, cx,cy-3*s], cols["nose"], "", 0)
    _oval(c, cx-20*s, cy+50*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+20*s, cy+50*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    if tier >= 1:
        _poly(c, [cx-28*s,cy-8*s, cx-55*s,cy+10*s, cx-45*s,cy+30*s, cx-28*s,cy+20*s],
              cols["inner"], cols["accent"], 1)
        _poly(c, [cx+28*s,cy-8*s, cx+55*s,cy+10*s, cx+45*s,cy+30*s, cx+28*s,cy+20*s],
              cols["inner"], cols["accent"], 1)

def _draw_tiger(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+20*s, 40*s, 32*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-18*s, 36*s, 32*s, cols["body"], cols["accent"], 2)
    _poly(c, [cx-24*s,cy-42*s, cx-30*s,cy-58*s, cx-8*s,cy-42*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx+24*s,cy-42*s, cx+30*s,cy-58*s, cx+8*s,cy-42*s], cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-12*s, 24*s, 22*s, cols["inner"], "", 0)
    for sx, sy, sw in [(-18,-30,3),(-8,-35,3),(8,-35,3),(18,-30,3),(0,-12,3)]:
        c.create_line(cx+sx*s,cy+sy*s, cx+(sx+4)*s,cy+(sy-8)*s, fill=cols["accent"], width=max(1,int(sw*s)))
    _oval(c, cx-14*s, cy-22*s, 8*s, 8*s, cols["eye"], "", 0)
    _oval(c, cx+14*s, cy-22*s, 8*s, 8*s, cols["eye"], "", 0)
    _oval(c, cx-14*s, cy-22*s, 5*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx+14*s, cy-22*s, 5*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx-13*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+13*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-5*s, 8*s, 6*s, cols["inner"], cols["accent"], 1)
    _oval(c, cx, cy-7*s, 5*s, 4*s, cols["nose"], "", 0)
    _oval(c, cx-24*s, cy+50*s, 14*s, 9*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+24*s, cy+50*s, 14*s, 9*s, cols["body"], cols["accent"], 1)

def _draw_panda(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+22*s, 40*s, 34*s, cols["body"], "#888", 2)
    _oval(c, cx, cy-14*s, 36*s, 32*s, cols["body"], "#888", 2)
    _oval(c, cx-26*s, cy-38*s, 12*s, 12*s, cols["accent"], cols["accent"], 2)
    _oval(c, cx+26*s, cy-38*s, 12*s, 12*s, cols["accent"], cols["accent"], 2)
    _oval(c, cx, cy+10*s, 22*s, 28*s, cols["body"], "", 0)
    _oval(c, cx-14*s, cy-20*s, 10*s, 10*s, cols["accent"], "", 0)
    _oval(c, cx+14*s, cy-20*s, 10*s, 10*s, cols["accent"], "", 0)
    _oval(c, cx-14*s, cy-20*s, 6*s, 6*s, "#ffffff", "", 0)
    _oval(c, cx+14*s, cy-20*s, 6*s, 6*s, "#ffffff", "", 0)
    _oval(c, cx-14*s, cy-20*s, 3*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+14*s, cy-20*s, 3*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-13*s, cy-22*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+13*s, cy-22*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-5*s, 16*s, 12*s, "#ffffff", "#888", 1)
    _oval(c, cx, cy-7*s, 6*s, 5*s, cols["nose"], "", 0)
    _oval(c, cx-24*s, cy+50*s, 15*s, 10*s, cols["body"], "#888", 1)
    _oval(c, cx+24*s, cy+50*s, 15*s, 10*s, cols["body"], "#888", 1)

def _draw_unicorn(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+20*s, 38*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-18*s, 34*s, 30*s, cols["body"], cols["accent"], 2)
    _poly(c, [cx-24*s,cy-40*s, cx-32*s,cy-58*s, cx-8*s,cy-40*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx+24*s,cy-40*s, cx+32*s,cy-58*s, cx+8*s,cy-40*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx-6*s,cy-46*s, cx+6*s,cy-46*s, cx,cy-72*s], "#f0c040", "#c09020", 2)
    c.create_line(cx, cy-46*s, cx-3*s, cy-60*s, fill="#e080d0", width=max(2,int(3*s)))
    c.create_line(cx, cy-46*s, cx+3*s, cy-58*s, fill="#80d0f0", width=max(2,int(3*s)))
    _oval(c, cx, cy-12*s, 22*s, 20*s, cols["inner"], "", 0)
    _oval(c, cx-13*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+13*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-13*s, cy-24*s, 4*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx+13*s, cy-24*s, 4*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx-12*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+12*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-8*s, 5*s, 4*s, cols["nose"], "", 0)
    _oval(c, cx-20*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+20*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)

def _draw_phoenix(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+22*s, 36*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-16*s, 30*s, 28*s, cols["body"], cols["accent"], 2)
    _poly(c, [cx-18*s,cy-40*s, cx-28*s,cy-62*s, cx-6*s,cy-40*s], cols["inner"], cols["accent"], 2)
    _poly(c, [cx+18*s,cy-40*s, cx+28*s,cy-62*s, cx+6*s,cy-40*s], cols["inner"], cols["accent"], 2)
    _oval(c, cx, cy-10*s, 20*s, 22*s, cols["inner"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-11*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+11*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _poly(c, [cx-5*s,cy-8*s, cx+5*s,cy-8*s, cx,cy-3*s], cols["nose"], "", 0)
    for pts in [
        [cx-28*s,cy-10*s, cx-65*s,cy-35*s, cx-60*s,cy+5*s, cx-28*s,cy+15*s],
        [cx+28*s,cy-10*s, cx+65*s,cy-35*s, cx+60*s,cy+5*s, cx+28*s,cy+15*s],
    ]:
        _poly(c, pts, cols["inner"], cols["accent"], 1)
    _oval(c, cx-20*s, cy+48*s, 13*s, 9*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+20*s, cy+48*s, 13*s, 9*s, cols["body"], cols["accent"], 1)

def _draw_frog(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+24*s, 38*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-12*s, 32*s, 28*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-18*s, cy-36*s, 10*s, 10*s, cols["body"], cols["accent"], 2)
    _oval(c, cx+18*s, cy-36*s, 10*s, 10*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-6*s, 26*s, 20*s, cols["inner"], "", 0)
    _oval(c, cx-18*s, cy-36*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+18*s, cy-36*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-18*s, cy-36*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+18*s, cy-36*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-17*s, cy-38*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+17*s, cy-38*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx-8*s, cy-12*s, 4*s, 3*s, cols["accent"], "", 0)
    _oval(c, cx+8*s, cy-12*s, 4*s, 3*s, cols["accent"], "", 0)
    c.create_arc(cx-16*s, cy-2*s, cx+16*s, cy+12*s, start=0, extent=-180, style="arc",
                 outline=cols["accent"], width=max(2,int(3*s)))
    _oval(c, cx-22*s, cy+52*s, 14*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+22*s, cy+52*s, 14*s, 8*s, cols["body"], cols["accent"], 1)

def _draw_axolotl(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+24*s, 40*s, 26*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-10*s, 34*s, 26*s, cols["body"], cols["accent"], 2)
    for dx, angle in [(-20, -30), (-8, -15), (8, -15), (20, -30)]:
        c.create_line(cx+dx*s, cy-28*s, cx+(dx-6)*s, cy-48*s, fill="#d06080", width=max(3,int(5*s)))
        _oval(c, cx+(dx-6)*s, cy-50*s, 5*s, 8*s, "#d06080", "", 0)
    _oval(c, cx, cy-6*s, 24*s, 20*s, cols["inner"], "", 0)
    _oval(c, cx-13*s, cy-16*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+13*s, cy-16*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-13*s, cy-16*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+13*s, cy-16*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-12*s, cy-18*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+12*s, cy-18*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-4*s, 5*s, 4*s, cols["nose"], "", 0)
    c.create_arc(cx-12*s, cy+2*s, cx+12*s, cy+12*s, start=0, extent=-180, style="arc",
                 outline=cols["accent"], width=max(2,int(3*s)))
    _oval(c, cx-26*s, cy+46*s, 14*s, 7*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+26*s, cy+46*s, 14*s, 7*s, cols["body"], cols["accent"], 1)

def _draw_deer(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+22*s, 36*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-18*s, 30*s, 28*s, cols["body"], cols["accent"], 2)
    # Antlers
    for side in [-1, 1]:
        bx = cx + side*18*s
        c.create_line(bx, cy-40*s, bx+side*8*s, cy-60*s, fill=cols["accent"], width=max(3,int(4*s)))
        c.create_line(bx+side*8*s, cy-60*s, bx+side*14*s, cy-52*s, fill=cols["accent"], width=max(2,int(3*s)))
        c.create_line(bx+side*8*s, cy-60*s, bx+side*4*s, cy-70*s, fill=cols["accent"], width=max(2,int(3*s)))
    _oval(c, cx, cy-12*s, 22*s, 20*s, cols["inner"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 6*s, 6*s, cols["eye"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 6*s, 6*s, cols["eye"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 3.5*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 3.5*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-11*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+11*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-8*s, 8*s, 6*s, cols["inner"], cols["accent"], 1)
    _oval(c, cx, cy-8*s, 5*s, 4*s, cols["nose"], "", 0)
    _oval(c, cx-20*s, cy+50*s, 10*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+20*s, cy+50*s, 10*s, 8*s, cols["body"], cols["accent"], 1)

def _draw_koala(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+22*s, 38*s, 32*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-14*s, 34*s, 32*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-28*s, cy-34*s, 16*s, 14*s, cols["body"], cols["accent"], 2)
    _oval(c, cx+28*s, cy-34*s, 16*s, 14*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-28*s, cy-34*s, 10*s, 9*s, cols["accent"], "", 0)
    _oval(c, cx+28*s, cy-34*s, 10*s, 9*s, cols["accent"], "", 0)
    _oval(c, cx, cy+4*s, 24*s, 28*s, cols["inner"], "", 0)
    _oval(c, cx-13*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+13*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-13*s, cy-22*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+13*s, cy-22*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-12*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+12*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-8*s, 10*s, 8*s, cols["nose"], cols["accent"], 2)
    _oval(c, cx-22*s, cy+50*s, 13*s, 9*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+22*s, cy+50*s, 13*s, 9*s, cols["body"], cols["accent"], 1)

def _draw_shark(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+20*s, 42*s, 28*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-14*s, 34*s, 26*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy+8*s, 28*s, 22*s, cols["inner"], "", 0)
    _poly(c, [cx-6*s,cy-36*s, cx+6*s,cy-36*s, cx,cy-60*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx+28*s,cy+5*s, cx+50*s,cy-10*s, cx+50*s,cy+20*s], cols["body"], cols["accent"], 2)
    _oval(c, cx-14*s, cy-18*s, 6*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+14*s, cy-18*s, 6*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-14*s, cy-18*s, 3.5*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+14*s, cy-18*s, 3.5*s, 4*s, cols["pupil"], "", 0)
    c.create_arc(cx-18*s, cy-2*s, cx+18*s, cy+12*s, start=200, extent=140, style="arc",
                 outline="#ffffff", width=max(2,int(3*s)))
    for tx in [-10, -4, 2, 8]:
        c.create_line(cx+tx*s, cy+6*s, cx+(tx+3)*s, cy+12*s, fill="#ffffff", width=max(1,int(2*s)))
    _oval(c, cx-22*s, cy+46*s, 14*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+22*s, cy+46*s, 14*s, 8*s, cols["body"], cols["accent"], 1)

def _draw_capybara(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+24*s, 42*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-10*s, 36*s, 28*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-4*s, 28*s, 22*s, cols["inner"], "", 0)
    _oval(c, cx-14*s, cy-20*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+14*s, cy-20*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-14*s, cy-20*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+14*s, cy-20*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-13*s, cy-22*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+13*s, cy-22*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-4*s, 14*s, 10*s, cols["inner"], cols["accent"], 1)
    _oval(c, cx-5*s, cy-6*s, 4*s, 3*s, cols["nose"], "", 0)
    _oval(c, cx+5*s, cy-6*s, 4*s, 3*s, cols["nose"], "", 0)
    _oval(c, cx-10*s, cy-30*s, 6*s, 5*s, cols["body"], cols["accent"], 2)
    _oval(c, cx+10*s, cy-30*s, 6*s, 5*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-26*s, cy+52*s, 14*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+26*s, cy+52*s, 14*s, 8*s, cols["body"], cols["accent"], 1)

def _draw_dino(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+24*s, 36*s, 28*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-8*s, cy-12*s, 28*s, 24*s, cols["body"], cols["accent"], 2)
    # Spines on back
    for i, sx in enumerate(range(-12, 18, 6)):
        h = 10 + (i % 3) * 4
        _poly(c, [cx+sx*s,cy+4*s, cx+(sx+5)*s,cy+4*s, cx+(sx+2.5)*s,cy+(4-h)*s],
              cols["accent"], cols["accent"], 1)
    _oval(c, cx-8*s, cy-8*s, 20*s, 18*s, cols["inner"], "", 0)
    _oval(c, cx-18*s, cy-18*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+2*s, cy-18*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-18*s, cy-18*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+2*s, cy-18*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-17*s, cy-20*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+1*s, cy-20*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx-10*s, cy-6*s, 9*s, 7*s, cols["inner"], cols["accent"], 1)
    _oval(c, cx-10*s, cy-8*s, 6*s, 4*s, cols["nose"], "", 0)
    _oval(c, cx+30*s, cy+10*s, 18*s, 8*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-22*s, cy+50*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+10*s, cy+50*s, 12*s, 8*s, cols["body"], cols["accent"], 1)


def draw_clothing(canvas: tk.Canvas, item_key: str, cx: int, cy: int, size: int = 100):
    """Draw clothing item over the pet."""
    s = size / 100
    fns = {
        "crown":          _cloth_crown,
        "wizard_hat":     _cloth_wizard_hat,
        "cape":           _cloth_cape,
        "graduation_cap": _cloth_grad_cap,
        "sunglasses":     _cloth_sunglasses,
        "bow":            _cloth_bow,
        "hat":            _cloth_hat,
        "scarf":          _cloth_scarf,
        "glasses":        _cloth_glasses,
        "bandana":        _cloth_bandana,
        "collar":         _cloth_collar,
        "party_hat":      _cloth_party_hat,
        "monocle":        _cloth_monocle,
        "beret":          _cloth_beret,
        "headphones":     _cloth_headphones,
        "flower_crown":   _cloth_flower_crown,
        "lei":            _cloth_lei,
        "bow_tie":        _cloth_bow_tie,
        "pilot_cap":      _cloth_pilot_cap,
        "beanie":         _cloth_beanie,
        "sports_cap":     _cloth_sports_cap,
        "top_hat":        _cloth_top_hat,
        "halo":           _cloth_halo,
        "knight_helm":    _cloth_knight_helm,
        "galaxy_scarf":   _cloth_galaxy_scarf,
        "sombrero":       _cloth_sombrero,
        "dragon_wings":   _cloth_dragon_wings,
        "phoenix_feather":_cloth_phoenix_feather,
        "unicorn_horn":   _cloth_unicorn_horn,
        "samurai_helm":   _cloth_samurai_helm,
        "space_helmet":   _cloth_space_helmet,
        "jester_hat":     _cloth_jester_hat,
        "viking_helm":    _cloth_viking_helm,
        "detective_hat":  _cloth_detective_hat,
        "cowboy_hat":     _cloth_cowboy_hat,
        "chef_hat":       _cloth_chef_hat,
        "ninja_mask":     _cloth_ninja_mask,
        "pirate_hat":     _cloth_pirate_hat,
        "witch_hat":      _cloth_witch_hat,
        "santa_hat":      _cloth_santa_hat,
        "elf_hat":        _cloth_elf_hat,
        "rainbow_hat":    _cloth_rainbow_hat,
        "angel_wings":    _cloth_angel_wings,
        "devil_horns":    _cloth_devil_horns,
        "tiara":          _cloth_tiara,
        "mushroom_hat":   _cloth_mushroom_hat,
        "shark_fin":      _cloth_shark_fin,
        "pirate_eyepatch":_cloth_pirate_eyepatch,
        "mortarboard":    _cloth_mortarboard,
        "astronaut_helm": _cloth_astronaut_helm,
        "fez":            _cloth_fez,
        "reindeer_antlers":_cloth_reindeer_antlers,
        "bunny_ears":     _cloth_bunny_ears,
        "cat_ears":       _cloth_cat_ears,
        "swim_goggles":   _cloth_swim_goggles,
        "superhero_mask": _cloth_superhero_mask,
        "propeller_hat":  _cloth_propeller_hat,
        "laurel_wreath":  _cloth_laurel_wreath,
        "thunder_crown":  _cloth_thunder_crown,
        "ice_crown":      _cloth_ice_crown,
        "black_cape":     _cloth_black_cape,
        "graduation_sash":_cloth_graduation_sash,
        "knitted_hat":    _cloth_knitted_hat,
        "paper_crown":    _cloth_paper_crown,
        "sweatband":      _cloth_sweatband,
        "detective_glass":_cloth_detective_glass,
        "bandaid":        _cloth_bandaid,
        "safety_glasses": _cloth_safety_glasses,
        "3d_glasses":     _cloth_3d_glasses,
        # simple items (emoji only, no complex draw needed)
        "lei_simple":     lambda c,cx,cy,s: _cloth_lei(c,cx,cy,s),
        "cap_backwards":  lambda c,cx,cy,s: _cloth_sports_cap(c,cx,cy,s),
        "crown_flowers":  lambda c,cx,cy,s: _cloth_flower_crown(c,cx,cy,s),
        "hair_bow":       lambda c,cx,cy,s: _cloth_bow(c,cx,cy,s),
        "hair_clip":      lambda c,cx,cy,s: _cloth_bow(c,cx,cy,s),
        "crown_gold":     lambda c,cx,cy,s: _cloth_crown(c,cx,cy,s),
        "viking_horns":   lambda c,cx,cy,s: _cloth_reindeer_antlers(c,cx,cy,s),
        "tiny_crown":     lambda c,cx,cy,s: _cloth_paper_crown(c,cx,cy,s),
        "nurse_cap":      lambda c,cx,cy,s: _cloth_chef_hat(c,cx,cy,s),
        "construction_hat":lambda c,cx,cy,s: _cloth_hat(c,cx,cy,s),
        "3d_glasses":     _cloth_3d_glasses,
    }
    fn = fns.get(item_key)
    if fn:
        fn(canvas, cx, cy, s)

# ── Pet drawing functions ─────────────────────────────────────────────────────

def _draw_cat(c, cols, cx, cy, s, tier):
    # Body
    _oval(c, cx, cy+20*s, 38*s, 32*s, cols["body"], cols["accent"], 2)
    # Head
    _oval(c, cx, cy-20*s, 35*s, 30*s, cols["body"], cols["accent"], 2)
    # Ears
    _poly(c, [cx-25*s, cy-40*s, cx-10*s, cy-55*s, cx-5*s, cy-35*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx+25*s, cy-40*s, cx+10*s, cy-55*s, cx+5*s, cy-35*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx-22*s, cy-43*s, cx-12*s, cy-52*s, cx-8*s, cy-38*s], cols["nose"], "", 0)
    _poly(c, [cx+22*s, cy-43*s, cx+12*s, cy-52*s, cx+8*s, cy-38*s], cols["nose"], "", 0)
    # Face
    _oval(c, cx, cy-18*s, 25*s, 20*s, cols["inner"], "", 0)
    # Eyes
    _oval(c, cx-12*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-12*s, cy-22*s, 4*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx+12*s, cy-22*s, 4*s, 5*s, cols["pupil"], "", 0)
    _oval(c, cx-11*s, cy-23*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+11*s, cy-23*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    # Nose
    _poly(c, [cx, cy-12*s, cx-4*s, cy-8*s, cx+4*s, cy-8*s], cols["nose"], "", 0)
    # Mouth
    c.create_line(cx, cy-8*s, cx-6*s, cy-4*s, fill=cols["accent"], width=max(1,int(2*s)))
    c.create_line(cx, cy-8*s, cx+6*s, cy-4*s, fill=cols["accent"], width=max(1,int(2*s)))
    # Whiskers
    for dx, dir_ in [(-1, -1), (1, 1)]:
        for wy in [-10, -8, -6]:
            c.create_line(cx+dx*8*s, cy+wy*s, cx+dx*28*s, cy+(wy-2)*s,
                          fill=cols["accent"], width=1)
    # Tail
    if tier >= 1:
        c.create_arc(cx+20*s, cy+10*s, cx+60*s, cy+50*s,
                     start=90, extent=180, style="arc",
                     outline=cols["accent"], width=max(2,int(4*s)))
    # Paws
    _oval(c, cx-22*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+22*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)

def _draw_dog(c, cols, cx, cy, s, tier):
    # Body
    _oval(c, cx, cy+20*s, 38*s, 32*s, cols["body"], cols["accent"], 2)
    # Head (rounder than cat)
    _oval(c, cx, cy-18*s, 36*s, 34*s, cols["body"], cols["accent"], 2)
    # Floppy ears
    _poly(c, [cx-28*s, cy-35*s, cx-42*s, cy-15*s, cx-38*s, cy+5*s, cx-22*s, cy-10*s], 
          cols["accent"], cols["accent"], 1)
    _poly(c, [cx+28*s, cy-35*s, cx+42*s, cy-15*s, cx+38*s, cy+5*s, cx+22*s, cy-10*s], 
          cols["accent"], cols["accent"], 1)
    # Face patch
    _oval(c, cx, cy-12*s, 26*s, 22*s, cols["inner"], "", 0)
    # Snout
    _oval(c, cx, cy-5*s, 16*s, 12*s, cols["inner"], cols["accent"], 1)
    # Eyes
    _oval(c, cx-13*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+13*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-13*s, cy-24*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+13*s, cy-24*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-12*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+12*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    # Nose
    _oval(c, cx, cy-7*s, 7*s, 5*s, cols["nose"], "", 0)
    # Paws
    _oval(c, cx-22*s, cy+48*s, 14*s, 9*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+22*s, cy+48*s, 14*s, 9*s, cols["body"], cols["accent"], 1)
    if tier >= 1:
        # Tail (wagging)
        c.create_arc(cx+22*s, cy, cx+55*s, cy+40*s,
                     start=120, extent=150, style="arc",
                     outline=cols["body"], width=max(3,int(6*s)))

def _draw_fox(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+20*s, 36*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-20*s, 34*s, 30*s, cols["body"], cols["accent"], 2)
    # Pointy ears
    _poly(c, [cx-20*s, cy-42*s, cx-32*s, cy-62*s, cx-5*s, cy-42*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx+20*s, cy-42*s, cx+32*s, cy-62*s, cx+5*s, cy-42*s], cols["body"], cols["accent"], 2)
    _poly(c, [cx-20*s, cy-44*s, cx-28*s, cy-58*s, cx-8*s, cy-44*s], cols["inner"], "", 0)
    _poly(c, [cx+20*s, cy-44*s, cx+28*s, cy-58*s, cx+8*s, cy-44*s], cols["inner"], "", 0)
    # White face mask
    _oval(c, cx, cy-16*s, 22*s, 22*s, cols["inner"], "", 0)
    # Pointed snout
    _poly(c, [cx-14*s, cy-10*s, cx+14*s, cy-10*s, cx, cy+5*s], cols["inner"], cols["accent"], 1)
    # Eyes
    _oval(c, cx-12*s, cy-24*s, 6*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+12*s, cy-24*s, 6*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-12*s, cy-24*s, 3.5*s, 4.5*s, cols["pupil"], "", 0)
    _oval(c, cx+12*s, cy-24*s, 3.5*s, 4.5*s, cols["pupil"], "", 0)
    _oval(c, cx-11*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+11*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-4*s, 5*s, 4*s, cols["nose"], "", 0)
    _oval(c, cx-22*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+22*s, cy+48*s, 12*s, 8*s, cols["body"], cols["accent"], 1)
    if tier >= 1:
        c.create_arc(cx+18*s, cy+5*s, cx+62*s, cy+50*s,
                     start=90, extent=200, style="arc",
                     outline=cols["body"], width=max(4,int(8*s)))

def _draw_dragon(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+22*s, 36*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-18*s, 32*s, 28*s, cols["body"], cols["accent"], 2)
    # Horns
    _poly(c, [cx-15*s, cy-40*s, cx-22*s, cy-65*s, cx-8*s, cy-40*s], cols["accent"], cols["accent"], 1)
    _poly(c, [cx+15*s, cy-40*s, cx+22*s, cy-65*s, cx+8*s, cy-40*s], cols["accent"], cols["accent"], 1)
    # Belly
    _oval(c, cx, cy+5*s, 22*s, 30*s, cols["inner"], "", 0)
    # Eyes (slitted)
    _oval(c, cx-13*s, cy-22*s, 8*s, 8*s, cols["eye"], "", 0)
    _oval(c, cx+13*s, cy-22*s, 8*s, 8*s, cols["eye"], "", 0)
    _oval(c, cx-13*s, cy-22*s, 3*s, 6*s, cols["pupil"], "", 0)
    _oval(c, cx+13*s, cy-22*s, 3*s, 6*s, cols["pupil"], "", 0)
    _oval(c, cx-12*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+12*s, cy-24*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-8*s, 5*s, 4*s, cols["nose"], "", 0)
    # Wings
    if tier >= 1:
        _poly(c, [cx-30*s, cy, cx-65*s, cy-30*s, cx-55*s, cy+10*s, cx-30*s, cy+15*s],
              cols["inner"], cols["accent"], 1)
        _poly(c, [cx+30*s, cy, cx+65*s, cy-30*s, cx+55*s, cy+10*s, cx+30*s, cy+15*s],
              cols["inner"], cols["accent"], 1)
    _oval(c, cx-20*s, cy+48*s, 13*s, 9*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+20*s, cy+48*s, 13*s, 9*s, cols["body"], cols["accent"], 1)

def _draw_bunny(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+22*s, 36*s, 30*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-16*s, 30*s, 28*s, cols["body"], cols["accent"], 2)
    # Long ears
    _oval(c, cx-16*s, cy-55*s, 9*s, 25*s, cols["body"], cols["accent"], 2)
    _oval(c, cx+16*s, cy-55*s, 9*s, 25*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-16*s, cy-55*s, 5*s, 20*s, cols["nose"], "", 0)
    _oval(c, cx+16*s, cy-55*s, 5*s, 20*s, cols["nose"], "", 0)
    _oval(c, cx, cy-12*s, 20*s, 18*s, cols["inner"], "", 0)
    # Eyes
    _oval(c, cx-11*s, cy-20*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+11*s, cy-20*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-11*s, cy-20*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+11*s, cy-20*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-10*s, cy-21*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+10*s, cy-21*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-8*s, 5*s, 4*s, cols["nose"], "", 0)
    _oval(c, cx-20*s, cy+48*s, 14*s, 9*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+20*s, cy+48*s, 14*s, 9*s, cols["body"], cols["accent"], 1)

def _draw_bear(c, cols, cx, cy, s, tier):
    _oval(c, cx, cy+22*s, 40*s, 34*s, cols["body"], cols["accent"], 2)
    _oval(c, cx, cy-16*s, 36*s, 34*s, cols["body"], cols["accent"], 2)
    # Round ears
    _oval(c, cx-26*s, cy-42*s, 12*s, 12*s, cols["body"], cols["accent"], 2)
    _oval(c, cx+26*s, cy-42*s, 12*s, 12*s, cols["body"], cols["accent"], 2)
    _oval(c, cx-26*s, cy-42*s, 7*s, 7*s, cols["accent"], "", 0)
    _oval(c, cx+26*s, cy-42*s, 7*s, 7*s, cols["accent"], "", 0)
    # Belly
    _oval(c, cx, cy+8*s, 24*s, 28*s, cols["inner"], "", 0)
    # Snout
    _oval(c, cx, cy-5*s, 18*s, 14*s, cols["inner"], cols["accent"], 1)
    # Eyes
    _oval(c, cx-14*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx+14*s, cy-24*s, 7*s, 7*s, cols["eye"], "", 0)
    _oval(c, cx-14*s, cy-24*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx+14*s, cy-24*s, 4*s, 4*s, cols["pupil"], "", 0)
    _oval(c, cx-13*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx+13*s, cy-25*s, 1.5*s, 1.5*s, "#ffffff", "", 0)
    _oval(c, cx, cy-6*s, 6*s, 5*s, cols["nose"], "", 0)
    _oval(c, cx-24*s, cy+50*s, 15*s, 10*s, cols["body"], cols["accent"], 1)
    _oval(c, cx+24*s, cy+50*s, 15*s, 10*s, cols["body"], cols["accent"], 1)

# ── Clothing drawing functions ────────────────────────────────────────────────

def _cloth_crown(c, cx, cy, s):
    base_y = cy - 48*s
    # Crown base
    _rect(c, cx-20*s, base_y, cx+20*s, base_y-10*s, "#f0c040", "#c89820", 2)
    # Crown points
    for xi in [-16, -5, 6, 17]:
        _poly(c, [cx+xi*s, base_y, cx+(xi+5)*s, base_y-20*s, cx+(xi+10)*s, base_y],
              "#f0c040", "#c89820", 1)
    # Jewels
    _oval(c, cx-10*s, base_y-6*s, 3*s, 3*s, "#e04040", "", 0)
    _oval(c, cx, base_y-6*s, 3*s, 3*s, "#4040e0", "", 0)
    _oval(c, cx+10*s, base_y-6*s, 3*s, 3*s, "#e04040", "", 0)

def _cloth_wizard_hat(c, cx, cy, s):
    brim_y = cy - 42*s
    # Brim
    _oval(c, cx, brim_y, 30*s, 8*s, "#4a1a8a", "#2a0a5a", 2)
    # Cone
    _poly(c, [cx-28*s, brim_y, cx+28*s, brim_y, cx+4*s, brim_y-55*s, cx-4*s, brim_y-55*s],
          "#4a1a8a", "#2a0a5a", 2)
    # Stars on hat
    for sx, sy in [(-8, -10), (5, -25), (-3, -40)]:
        _draw_star(c, cx+sx*s, brim_y+sy*s, 4*s, "#f0c040")
    # Band
    _rect(c, cx-28*s, brim_y-6*s, cx+28*s, brim_y, "#f0c040", "", 0)

def _cloth_cape(c, cx, cy, s):
    # Cape drapes behind/around body
    _poly(c, [cx-15*s, cy-25*s, cx-45*s, cy+10*s, cx-40*s, cy+55*s,
              cx+40*s, cy+55*s, cx+45*s, cy+10*s, cx+15*s, cy-25*s],
          "#8b0000", "#600000", 2)
    # Collar
    _poly(c, [cx-15*s, cy-25*s, cx, cy-30*s, cx+15*s, cy-25*s,
              cx+12*s, cy-15*s, cx, cy-18*s, cx-12*s, cy-15*s],
          "#f0f0f0", "#cccccc", 1)
    # Clasp
    _oval(c, cx, cy-20*s, 5*s, 5*s, "#f0c040", "#c89820", 2)

def _cloth_grad_cap(c, cx, cy, s):
    head_y = cy - 42*s
    # Board (flat top)
    _poly(c, [cx-28*s, head_y-4*s, cx+28*s, head_y-4*s,
              cx+32*s, head_y-12*s, cx-32*s, head_y-12*s],
          "#1a1a2e", "#000010", 2)
    # Cap body
    _oval(c, cx, head_y, 22*s, 10*s, "#1a1a2e", "#000010", 1)
    # Tassel
    c.create_line(cx+28*s, head_y-10*s, cx+28*s, head_y+10*s,
                  fill="#f0c040", width=max(2, int(3*s)))
    _oval(c, cx+28*s, head_y+12*s, 5*s, 5*s, "#f0c040", "", 0)

def _cloth_sunglasses(c, cx, cy, s):
    ey = cy - 22*s
    # Frames
    _oval(c, cx-13*s, ey, 10*s, 7*s, "#1a1a2e", "#f0c040", 2)
    _oval(c, cx+13*s, ey, 10*s, 7*s, "#1a1a2e", "#f0c040", 2)
    # Bridge
    c.create_line(cx-3*s, ey, cx+3*s, ey, fill="#f0c040", width=max(2,int(2*s)))
    # Arms
    c.create_line(cx-23*s, ey, cx-30*s, ey+3*s, fill="#f0c040", width=max(2,int(2*s)))
    c.create_line(cx+23*s, ey, cx+30*s, ey+3*s, fill="#f0c040", width=max(2,int(2*s)))
    # Lens sheen
    _oval(c, cx-16*s, ey-2*s, 3*s, 2*s, "#99ccff", "", 0)
    _oval(c, cx+10*s, ey-2*s, 3*s, 2*s, "#99ccff", "", 0)

def _cloth_bow(c, cx, cy, s):
    by = cy - 50*s
    bx = cx + 22*s
    # Bow loops
    _poly(c, [bx, by, bx-12*s, by-10*s, bx-14*s, by, bx-12*s, by+10*s], "#e04080", "#c02060", 2)
    _poly(c, [bx, by, bx+12*s, by-10*s, bx+14*s, by, bx+12*s, by+10*s], "#e04080", "#c02060", 2)
    _oval(c, bx, by, 4*s, 4*s, "#f06090", "#c02060", 1)
    # Ribbons
    c.create_line(bx, by+4*s, bx-5*s, by+16*s, fill="#e04080", width=max(1,int(2*s)))
    c.create_line(bx, by+4*s, bx+5*s, by+16*s, fill="#e04080", width=max(1,int(2*s)))

def _cloth_hat(c, cx, cy, s):
    hy = cy - 42*s
    # Brim
    _oval(c, cx, hy, 28*s, 7*s, "#1a1a2e", "#000010", 2)
    # Top hat body
    _rect(c, cx-18*s, hy-35*s, cx+18*s, hy, "#1a1a2e", "#000010", 2)
    # Band
    _rect(c, cx-18*s, hy-8*s, cx+18*s, hy-4*s, "#c89820", "", 0)

def _cloth_scarf(c, cx, cy, s):
    sy = cy - 5*s
    # Main wrap
    _oval(c, cx, sy, 32*s, 10*s, "#e03020", "#a02010", 2)
    # Hanging end
    _poly(c, [cx+18*s, sy, cx+28*s, sy+5*s, cx+24*s, sy+28*s, cx+14*s, sy+25*s],
          "#e03020", "#a02010", 1)
    # Stripe
    c.create_arc(cx-32*s, sy-10*s, cx+32*s, sy+10*s,
                 start=0, extent=180, style="arc",
                 outline="#f0f0f0", width=max(2,int(3*s)))

def _cloth_glasses(c, cx, cy, s):
    ey = cy - 22*s
    # Round frames
    _oval(c, cx-13*s, ey, 9*s, 9*s, "", "#3d2010", 2)
    _oval(c, cx+13*s, ey, 9*s, 9*s, "", "#3d2010", 2)
    # Bridge + arms
    c.create_line(cx-4*s, ey, cx+4*s, ey, fill="#3d2010", width=max(2,int(2*s)))
    c.create_line(cx-22*s, ey, cx-30*s, ey+4*s, fill="#3d2010", width=max(2,int(2*s)))
    c.create_line(cx+22*s, ey, cx+30*s, ey+4*s, fill="#3d2010", width=max(2,int(2*s)))

def _cloth_bandana(c, cx, cy, s):
    by = cy - 3*s
    # Triangle fold around neck
    _poly(c, [cx-22*s, by-8*s, cx+22*s, by-8*s, cx, by+20*s], "#c03020", "#902010", 2)
    # Knot at back (small circles)
    _oval(c, cx+20*s, by-5*s, 5*s, 4*s, "#c03020", "#902010", 1)
    # Polka dots
    for dx, dy in [(-5, 2), (5, 5), (0, 10), (-8, 8)]:
        _oval(c, cx+dx*s, by+dy*s, 2*s, 2*s, "#ffffff", "", 0)

def _cloth_collar(c, cx, cy, s):
    cy2 = cy - 3*s
    # Collar band
    c.create_arc(cx-24*s, cy2-12*s, cx+24*s, cy2+12*s,
                 start=200, extent=140, style="arc",
                 outline="#c89820", width=max(3,int(4*s)))
    # Tag
    _oval(c, cx, cy2+10*s, 6*s, 7*s, "#c89820", "#a07010", 2)
    c.create_text(cx, cy2+10*s, text="♥", fill="#a07010",
                  font=("TkDefaultFont", max(6, int(8*s))))

def _draw_star(c, cx, cy, r, colour):
    pts = []
    for i in range(10):
        angle = math.pi/2 + i * 2*math.pi/10
        ri = r if i % 2 == 0 else r*0.45
        pts.extend([cx + ri*math.cos(angle), cy - ri*math.sin(angle)])
    c.create_polygon(pts, fill=colour, outline="", smooth=False)


def _cloth_party_hat(c, cx, cy, s):
    hy = cy - 44*s
    _poly(c, [cx-16*s, hy, cx+16*s, hy, cx, hy-36*s], "#e03090", "#a01060", 2)
    # Polka dots
    for dx, dy in [(-4,-8),(4,-18),(0,-28),(-8,-15)]:
        _oval(c, cx+dx*s, hy+dy*s, 3*s, 3*s, "#f0f040", "", 0)
    # Pom-pom
    _oval(c, cx, hy-38*s, 5*s, 5*s, "#f0f040", "#c0c000", 1)
    # Elastic
    c.create_line(cx-16*s, hy, cx-22*s, cy-5*s, fill="#888", width=max(1,int(s)))
    c.create_line(cx+16*s, hy, cx+22*s, cy-5*s, fill="#888", width=max(1,int(s)))

def _cloth_monocle(c, cx, cy, s):
    ey = cy - 22*s
    ex = cx + 10*s
    _oval(c, ex, ey, 9*s, 9*s, "", "#c89820", 3)
    c.create_line(ex+9*s, ey, ex+16*s, ey+8*s, fill="#c89820", width=max(2,int(2*s)))

def _cloth_beret(c, cx, cy, s):
    hy = cy - 44*s
    _oval(c, cx-6*s, hy, 26*s, 12*s, "#8b2fc9", "#6a1fa0", 2)
    _oval(c, cx+14*s, hy-8*s, 5*s, 5*s, "#8b2fc9", "#6a1fa0", 1)

def _cloth_headphones(c, cx, cy, s):
    ey = cy - 26*s
    # Band over head
    c.create_arc(cx-20*s, ey-20*s, cx+20*s, ey+4*s,
                 start=0, extent=180, style="arc",
                 outline="#2d2d2d", width=max(3,int(5*s)))
    # Ear cups
    _oval(c, cx-20*s, ey-8*s, 8*s, 10*s, "#2d2d2d", "#1a1a1a", 2)
    _oval(c, cx+20*s, ey-8*s, 8*s, 10*s, "#2d2d2d", "#1a1a1a", 2)
    _oval(c, cx-20*s, ey-8*s, 5*s, 7*s, "#4a90d9", "", 0)
    _oval(c, cx+20*s, ey-8*s, 5*s, 7*s, "#4a90d9", "", 0)

def _cloth_flower_crown(c, cx, cy, s):
    hy = cy - 46*s
    colours = ["#e04060","#f0a030","#60c040","#4090e0","#c040e0"]
    for i, ang in enumerate(range(0, 360, 45)):
        import math
        rx = cx + 22*s * math.cos(math.radians(ang))
        ry = hy + 8*s * math.sin(math.radians(ang))
        _oval(c, rx, ry, 5*s, 5*s, colours[i % len(colours)], "", 0)
    # Green vine
    c.create_arc(cx-24*s, hy-8*s, cx+24*s, hy+8*s,
                 start=180, extent=180, style="arc",
                 outline="#40a040", width=max(2,int(3*s)))

def _cloth_lei(c, cx, cy, s):
    ly = cy - 2*s
    colours = ["#e04060","#f0a030","#60c040","#f0f040","#c040e0","#4090e0"]
    for i, ang in enumerate(range(0, 360, 20)):
        import math
        rx = cx + 28*s * math.cos(math.radians(ang))
        ry = ly + 10*s * math.sin(math.radians(ang))
        _oval(c, rx, ry, 5*s, 5*s, colours[i % len(colours)], "", 0)

def _cloth_bow_tie(c, cx, cy, s):
    by = cy - 3*s
    _poly(c, [cx-2*s, by, cx-16*s, by-10*s, cx-18*s, by, cx-16*s, by+10*s],
          "#c03020", "#902010", 2)
    _poly(c, [cx+2*s, by, cx+16*s, by-10*s, cx+18*s, by, cx+16*s, by+10*s],
          "#c03020", "#902010", 2)
    _oval(c, cx, by, 4*s, 6*s, "#e04030", "#c03020", 1)

def _cloth_pilot_cap(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 26*s, 12*s, "#8b6914", "#6a5010", 2)
    _oval(c, cx-4*s, hy-10*s, 18*s, 14*s, "#8b6914", "#6a5010", 2)
    # Goggles
    _oval(c, cx-12*s, hy+4*s, 8*s, 6*s, "#ddd", "#999", 2)
    _oval(c, cx+12*s, hy+4*s, 8*s, 6*s, "#ddd", "#999", 2)
    c.create_line(cx-4*s, hy+4*s, cx+4*s, hy+4*s, fill="#999", width=max(2,int(2*s)))

def _cloth_beanie(c, cx, cy, s):
    hy = cy - 40*s
    _oval(c, cx, hy, 28*s, 18*s, "#3060c0", "#2040a0", 2)
    # Pom
    _oval(c, cx, hy-18*s, 8*s, 8*s, "#f0f0f0", "#cccccc", 1)
    # Stripe
    c.create_arc(cx-28*s, hy-5*s, cx+28*s, hy+5*s,
                 start=0, extent=180, style="arc",
                 outline="#f0c040", width=max(3,int(4*s)))

def _cloth_sports_cap(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 26*s, 12*s, "#e03020", "#a02010", 2)
    # Brim
    _poly(c, [cx-26*s, hy+4*s, cx+26*s, hy+4*s, cx+30*s, hy+10*s, cx-30*s, hy+10*s],
          "#c02010", "#801010", 1)
    # Logo
    _oval(c, cx, hy-2*s, 6*s, 6*s, "#ffffff", "", 0)

def _cloth_top_hat(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 28*s, 7*s, "#1a1a2e", "#000010", 2)
    _rect(c, cx-18*s, hy-40*s, cx+18*s, hy, "#1a1a2e", "#000010", 2)
    _rect(c, cx-18*s, hy-8*s, cx+18*s, hy-4*s, "#c89820", "", 0)

def _cloth_halo(c, cx, cy, s):
    hy = cy - 58*s
    _oval(c, cx, hy, 22*s, 6*s, "#f0e060", "#c0b020", 3)
    # Glow effect
    _oval(c, cx, hy, 26*s, 9*s, "", "#f0e06088"[:7], 1)

def _cloth_knight_helm(c, cx, cy, s):
    hy = cy - 38*s
    # Main helmet
    _oval(c, cx, hy-5*s, 26*s, 22*s, "#888888", "#555555", 2)
    # Visor slit
    _rect(c, cx-18*s, hy+2*s, cx+18*s, hy+7*s, "#333333", "", 0)
    # Cross visor bars
    c.create_line(cx, hy-5*s, cx, hy+12*s, fill="#555555", width=max(2,int(3*s)))
    # Plume
    _poly(c, [cx-5*s, hy-24*s, cx+5*s, hy-24*s, cx+2*s, hy-45*s, cx-2*s, hy-45*s],
          "#e03020", "#a01010", 1)

def _cloth_galaxy_scarf(c, cx, cy, s):
    sy = cy - 5*s
    # Base scarf
    _oval(c, cx, sy, 32*s, 10*s, "#1a0a3a", "#0a0020", 2)
    # Stars on it
    for dx, dy in [(-12,0),(0,-3),(12,0),(-6,4),(6,4)]:
        _oval(c, cx+dx*s, sy+dy*s, 2*s, 2*s, "#f0f0ff", "", 0)
    # Nebula colours
    _oval(c, cx-8*s, sy, 6*s, 4*s, "#6040c0", "", 0)
    _oval(c, cx+8*s, sy, 6*s, 4*s, "#c04080", "", 0)
    # Hanging end
    _poly(c, [cx+18*s, sy, cx+28*s, sy+5*s, cx+24*s, sy+28*s, cx+14*s, sy+25*s],
          "#1a0a3a", "#0a0020", 1)

def _cloth_sombrero(c, cx, cy, s):
    hy = cy - 42*s
    _oval(c, cx, hy, 40*s, 8*s, "#e8a030", "#c07820", 2)
    _oval(c, cx, hy-6*s, 20*s, 14*s, "#e8a030", "#c07820", 2)
    # Decorations
    for dx in [-24, -12, 0, 12, 24]:
        _oval(c, cx+dx*s, hy+2*s, 3*s, 3*s, "#e03020", "", 0)


class PetWidget(tk.Frame):
    """
    A self-contained widget that draws a pet with clothing.
    Can be embedded anywhere in the UI.
    """
    def __init__(self, parent, species="cat", level=1, equipped_item="",
                 size=120, bg=None, **kwargs):
        bg = bg or "#0f2040"
        super().__init__(parent, bg=bg, **kwargs)
        self.species       = species
        self.level         = level
        self.equipped_item = equipped_item
        self.size          = size
        self.bg            = bg

        self.canvas = tk.Canvas(self, width=size+20, height=size+30,
                                bg=bg, highlightthickness=0)
        self.canvas.pack()
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        cx = (self.canvas.winfo_reqwidth()) // 2
        cy = (self.canvas.winfo_reqheight()) // 2
        draw_pet(self.canvas, self.species, self.level, cx, cy, self.size)
        if self.equipped_item:
            draw_clothing(self.canvas, self.equipped_item, cx, cy, self.size)

    def update_pet(self, species=None, level=None, equipped_item=None):
        if species is not None:       self.species = species
        if level is not None:         self.level   = level
        if equipped_item is not None: self.equipped_item = equipped_item
        self.draw()
