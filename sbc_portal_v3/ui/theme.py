"""
Theme — St Bernard's College · Modern flat design
Navy + Gold palette, sharp geometry, clean typography.
"""
import os

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK    = "#0a1628"   # near-black navy
BG_MID     = "#0f2040"   # sidebar navy
BG_CARD    = "#162d55"   # card navy
BG_LIGHT   = "#1e3d70"   # hover / elevated
BG_INPUT   = "#0f2040"   # input fields

ACCENT     = "#c9a030"   # SBC gold
ACCENT_LT  = "#f0c84a"   # bright gold
ACCENT_DIM = "#8a6b1a"   # dark gold

ROYAL      = "#1a4fc4"   # royal blue (hover)
TEAL       = "#0d9488"   # teal accent for upcoming/calendar

FG_PRIMARY = "#f0f4ff"   # near-white
FG_SEC     = "#8da4cc"   # secondary text
FG_MUTED   = "#4a6080"   # muted / placeholders
FG_GOLD    = "#c9a030"

BORDER     = "#1a3358"
BORDER_LT  = "#243f6a"

SUCCESS    = "#22c55e"
WARNING    = "#f59e0b"
DANGER     = "#ef4444"
INFO       = "#3b82f6"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_DISPLAY = ("Georgia", 28, "bold")
FONT_HEADING = ("Georgia", 20, "bold")
FONT_SUBHEAD = ("Georgia", 13, "bold")
FONT_BODY    = ("TkDefaultFont", 11)
FONT_SMALL   = ("TkDefaultFont", 9)
FONT_LABEL   = ("TkDefaultFont", 10, "bold")
FONT_NAV     = ("TkDefaultFont", 11, "bold")
FONT_MONO    = ("Courier", 10)
FONT_TITLE   = ("Georgia", 32, "bold")

# ── Assets ────────────────────────────────────────────────────────────────────
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
CREST_PATH = os.path.join(ASSETS_DIR, "sbc_crest.png")


def grade_color(grade_raw):
    """SBC grading: A+=90+, A=80-89, B=70-79, C=60-69, D=40-59, UG=<40"""
    if grade_raw is None:
        return FG_MUTED
    if grade_raw >= 90:  return "#22c55e"   # green  — A+
    if grade_raw >= 80:  return "#4ade80"   # light green — A
    if grade_raw >= 70:  return "#facc15"   # yellow — B
    if grade_raw >= 60:  return "#fb923c"   # orange — C
    if grade_raw >= 40:  return "#f87171"   # red    — D
    return "#dc2626"                        # dark red — UG


def grade_label(grade_raw):
    """SBC grading scale: A+=90+, A=80-89, B=70-79, C=60-69, D=40-59, UG=<40"""
    if grade_raw is None: return ""
    if grade_raw >= 90:   return "A+"
    if grade_raw >= 80:   return "A"
    if grade_raw >= 70:   return "B"
    if grade_raw >= 60:   return "C"
    if grade_raw >= 40:   return "D"
    return "UG"


def fmt_grade(grade_raw):
    """Format to 1 decimal place."""
    if grade_raw is None:
        return "N/A"
    return f"{grade_raw:.1f}%"
