"""
Theme system — multiple UI themes for SBC Portal.
"""
import os

# ── Available themes ──────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "name": "Dark (Default)",
        "BG_DARK":    "#0a1628",
        "BG_MID":     "#0f2040",
        "BG_CARD":    "#162d55",
        "BG_LIGHT":   "#1e3d70",
        "BG_INPUT":   "#0f2040",
        "ACCENT":     "#c9a030",
        "ACCENT_LT":  "#f0c84a",
        "ACCENT_DIM": "#8a6b1a",
        "FG_PRIMARY": "#f0f4ff",
        "FG_SEC":     "#8da4cc",
        "FG_MUTED":   "#4a6080",
        "BORDER":     "#1a3358",
        "BORDER_LT":  "#243f6a",
    },
    "light": {
        "name": "Light",
        "BG_DARK":    "#f0f4ff",
        "BG_MID":     "#e2e8f5",
        "BG_CARD":    "#ffffff",
        "BG_LIGHT":   "#d0d8ee",
        "BG_INPUT":   "#e8edf8",
        "ACCENT":     "#8a6b1a",
        "ACCENT_LT":  "#c9a030",
        "ACCENT_DIM": "#6b5214",
        "FG_PRIMARY": "#0a1628",
        "FG_SEC":     "#2d4070",
        "FG_MUTED":   "#7a8aaa",
        "BORDER":     "#c8d4ea",
        "BORDER_LT":  "#dde5f5",
    },
    "midnight": {
        "name": "Midnight",
        "BG_DARK":    "#050510",
        "BG_MID":     "#0a0a20",
        "BG_CARD":    "#10102e",
        "BG_LIGHT":   "#18183c",
        "BG_INPUT":   "#0a0a20",
        "ACCENT":     "#7c6dff",
        "ACCENT_LT":  "#a094ff",
        "ACCENT_DIM": "#4a3dcc",
        "FG_PRIMARY": "#e8e8ff",
        "FG_SEC":     "#8888cc",
        "FG_MUTED":   "#444466",
        "BORDER":     "#1a1a44",
        "BORDER_LT":  "#252558",
    },
    "forest": {
        "name": "Forest",
        "BG_DARK":    "#0a1a0e",
        "BG_MID":     "#0f2614",
        "BG_CARD":    "#163320",
        "BG_LIGHT":   "#1e442a",
        "BG_INPUT":   "#0f2614",
        "ACCENT":     "#4ade80",
        "ACCENT_LT":  "#86efac",
        "ACCENT_DIM": "#22c55e",
        "FG_PRIMARY": "#f0fff4",
        "FG_SEC":     "#86efac",
        "FG_MUTED":   "#4a7055",
        "BORDER":     "#1a4428",
        "BORDER_LT":  "#245535",
    },
    "crimson": {
        "name": "Crimson",
        "BG_DARK":    "#1a0808",
        "BG_MID":     "#2a0f0f",
        "BG_CARD":    "#3a1515",
        "BG_LIGHT":   "#4a1e1e",
        "BG_INPUT":   "#2a0f0f",
        "ACCENT":     "#ef4444",
        "ACCENT_LT":  "#f87171",
        "ACCENT_DIM": "#b91c1c",
        "FG_PRIMARY": "#fff0f0",
        "FG_SEC":     "#fca5a5",
        "FG_MUTED":   "#7a4444",
        "BORDER":     "#4a1a1a",
        "BORDER_LT":  "#5a2424",
    },
}

_current_theme = "dark"

def set_theme(name: str):
    global _current_theme
    if name in THEMES:
        _current_theme = name
        _apply()

def get_theme_name() -> str:
    return _current_theme

def _apply():
    t = THEMES[_current_theme]
    import ui.theme as _self
    _self.BG_DARK    = t["BG_DARK"]
    _self.BG_MID     = t["BG_MID"]
    _self.BG_CARD    = t["BG_CARD"]
    _self.BG_LIGHT   = t["BG_LIGHT"]
    _self.BG_INPUT   = t["BG_INPUT"]
    _self.ACCENT     = t["ACCENT"]
    _self.ACCENT_LT  = t["ACCENT_LT"]
    _self.ACCENT_DIM = t["ACCENT_DIM"]
    _self.FG_PRIMARY = t["FG_PRIMARY"]
    _self.FG_SEC     = t["FG_SEC"]
    _self.FG_MUTED   = t["FG_MUTED"]
    _self.BORDER     = t["BORDER"]
    _self.BORDER_LT  = t["BORDER_LT"]

# Apply dark theme defaults immediately
t = THEMES["dark"]
BG_DARK    = t["BG_DARK"]
BG_MID     = t["BG_MID"]
BG_CARD    = t["BG_CARD"]
BG_LIGHT   = t["BG_LIGHT"]
BG_INPUT   = t["BG_INPUT"]
ACCENT     = t["ACCENT"]
ACCENT_LT  = t["ACCENT_LT"]
ACCENT_DIM = t["ACCENT_DIM"]
FG_PRIMARY = t["FG_PRIMARY"]
FG_SEC     = t["FG_SEC"]
FG_MUTED   = t["FG_MUTED"]
BORDER     = t["BORDER"]
BORDER_LT  = t["BORDER_LT"]

ROYAL      = "#1a4fc4"
TEAL       = "#0d9488"
FG_GOLD    = "#c9a030"
SUCCESS    = "#22c55e"
WARNING    = "#f59e0b"
DANGER     = "#ef4444"
INFO       = "#3b82f6"

FONT_DISPLAY = ("Georgia", 28, "bold")
FONT_HEADING = ("Georgia", 20, "bold")
FONT_SUBHEAD = ("Georgia", 13, "bold")
FONT_BODY    = ("TkDefaultFont", 11)
FONT_SMALL   = ("TkDefaultFont", 9)
FONT_LABEL   = ("TkDefaultFont", 10, "bold")
FONT_NAV     = ("TkDefaultFont", 11, "bold")
FONT_MONO    = ("Courier", 10)
FONT_TITLE   = ("Georgia", 32, "bold")

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
CREST_PATH = os.path.join(ASSETS_DIR, "sbc_crest.png")


def grade_color(grade_raw):
    if grade_raw is None: return FG_MUTED
    if grade_raw >= 90:  return "#22c55e"
    if grade_raw >= 80:  return "#4ade80"
    if grade_raw >= 70:  return "#facc15"
    if grade_raw >= 60:  return "#fb923c"
    if grade_raw >= 40:  return "#f87171"
    return "#dc2626"

def grade_label(grade_raw):
    if grade_raw is None: return ""
    if grade_raw >= 90:   return "A+"
    if grade_raw >= 80:   return "A"
    if grade_raw >= 70:   return "B"
    if grade_raw >= 60:   return "C"
    if grade_raw >= 40:   return "D"
    return "UG"

def fmt_grade(grade_raw):
    if grade_raw is None: return "N/A"
    return f"{grade_raw:.1f}%"
