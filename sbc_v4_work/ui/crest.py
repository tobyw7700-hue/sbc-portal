"""
SBC Crest image loader — no numpy dependency.
"""
import os
import tkinter as tk
from ui.theme import ACCENT, BG_MID

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
CREST_PATH = os.path.join(ASSETS_DIR, "sbc_crest.png")
CREST_ASPECT = 596 / 400

_cache: dict = {}


def _load_crest(width: int, bg_hex: str):
    from PIL import Image, ImageTk
    key = (width, bg_hex)
    if key in _cache:
        return _cache[key]

    height = max(1, int(width / CREST_ASPECT))

    # Ensure the file is actually PNG before opening
    img = Image.open(CREST_PATH)
    # Re-save as real PNG in memory if it came in as JPEG
    if img.format == "JPEG":
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        img = Image.open(buf)
    img = img.convert("RGBA").resize((width, height), Image.LANCZOS)

    # Composite: replace near-black pixels with background colour
    try:
        bg_r = int(bg_hex[1:3], 16)
        bg_g = int(bg_hex[3:5], 16)
        bg_b = int(bg_hex[5:7], 16)
    except Exception:
        bg_r, bg_g, bg_b = 10, 22, 40

    pixels = img.load()
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if (r + g + b) < 60:          # very dark → replace with bg
                pixels[x, y] = (bg_r, bg_g, bg_b, 255)
            elif a < 128:                 # transparent → replace with bg
                pixels[x, y] = (bg_r, bg_g, bg_b, 255)

    photo = ImageTk.PhotoImage(img)
    _cache[key] = photo
    return photo


class CrestImage(tk.Label):
    def __init__(self, parent, width: int = 180, bg: str = BG_MID, **kwargs):
        super().__init__(parent, bg=bg, bd=0, relief="flat", **kwargs)
        self._photo = None
        try:
            photo = _load_crest(width, bg)
            self.configure(image=photo)
            self._photo = photo
        except Exception:
            self.configure(text="SBC", fg=ACCENT,
                           font=("Georgia", max(12, width // 8), "bold"))


def crest_height(width: int) -> int:
    return int(width / CREST_ASPECT)
