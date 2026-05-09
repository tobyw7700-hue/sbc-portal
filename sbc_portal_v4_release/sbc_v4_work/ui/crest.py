"""
SBC Crest image loader — shared across all pages.
Loads assets/sbc_crest.png, preserves aspect ratio (596x400 → 3:2 landscape).
Black background is composited onto the parent bg colour.
"""
import os
import tkinter as tk
from PIL import Image, ImageTk

from ui.theme import ACCENT, BG_MID, BG_DARK

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
CREST_PATH = os.path.join(ASSETS_DIR, "sbc_crest.png")

# Original image ratio: 596 × 400  →  aspect = 596/400 = 1.49
CREST_ASPECT = 596 / 400   # width / height

_cache: dict = {}  # {(width, bg_color): ImageTk.PhotoImage}


def _load_crest(width: int, bg_hex: str) -> ImageTk.PhotoImage:
    """Return a cached PhotoImage of the crest at the given width."""
    key = (width, bg_hex)
    if key in _cache:
        return _cache[key]

    height = int(width / CREST_ASPECT)

    img = Image.open(CREST_PATH).convert("RGB")
    img = img.resize((width, height), Image.LANCZOS)

    # Composite black pixels onto the parent background colour so the logo
    # blends cleanly on navy without a black rectangle.
    bg_r = int(bg_hex[1:3], 16)
    bg_g = int(bg_hex[3:5], 16)
    bg_b = int(bg_hex[5:7], 16)

    import numpy as np
    arr = np.array(img, dtype=float)
    # Pixels close to black → replace with bg colour
    darkness = (arr[:, :, 0] + arr[:, :, 1] + arr[:, :, 2]) / 3
    mask = darkness < 30          # very dark → background
    arr[mask] = [bg_r, bg_g, bg_b]
    img2 = Image.fromarray(arr.astype("uint8"))

    photo = ImageTk.PhotoImage(img2)
    _cache[key] = photo
    return photo


class CrestImage(tk.Label):
    """
    A Label that displays the SBC crest PNG at a given width.
    Height is calculated automatically from the 596:400 aspect ratio.
    """

    def __init__(self, parent, width: int = 180, bg: str = BG_MID, **kwargs):
        super().__init__(parent, bg=bg, bd=0, relief="flat", **kwargs)
        self._width = width
        self._bg = bg
        try:
            photo = _load_crest(width, bg)
            self.configure(image=photo)
            self._photo = photo   # keep reference
        except Exception as e:
            # Graceful fallback
            self.configure(text="SBC", fg=ACCENT,
                           font=("Georgia", max(12, width // 8), "bold"))


def crest_height(width: int) -> int:
    """Return the pixel height for a given crest width."""
    return int(width / CREST_ASPECT)
