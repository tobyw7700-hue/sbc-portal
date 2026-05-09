"""
Pet system data models — 20+ species, 100+ clothing items, 7 rarity tiers.
Mythic and Divine added above Legendary.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import json, os, hmac, hashlib, base64

SAVE_DIR  = os.path.expanduser("~/.sbc_portal")
_APP_KEY  = b"sbc_portal_2026_immutable_key_x7"

# ── Rarity tiers (7) ──────────────────────────────────────────────────────────
RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "divine"]

RARITY_COLOURS = {
    "common":    "#8da4cc",
    "uncommon":  "#22c55e",
    "rare":      "#4a90d9",
    "epic":      "#c77dff",
    "legendary": "#f0c040",
    "mythic":    "#ff6b35",   # fiery orange
    "divine":    "#ffffff",   # pure white / rainbow
}

RARITY_GLOW = {
    "common":    None,
    "uncommon":  None,
    "rare":      None,
    "epic":      "#c77dff",
    "legendary": "#f0c040",
    "mythic":    "#ff6b35",
    "divine":    "#ffffff",
}

# ── Pet species (22) ──────────────────────────────────────────────────────────
PET_SPECIES = {
    "cat":       {"name": "Cat",         "emoji_base": "🐱", "unlock": "default"},
    "dog":       {"name": "Dog",         "emoji_base": "🐶", "unlock": "common"},
    "bunny":     {"name": "Bunny",       "emoji_base": "🐰", "unlock": "common"},
    "frog":      {"name": "Frog",        "emoji_base": "🐸", "unlock": "common"},
    "bear":      {"name": "Bear",        "emoji_base": "🐻", "unlock": "uncommon"},
    "penguin":   {"name": "Penguin",     "emoji_base": "🐧", "unlock": "uncommon"},
    "koala":     {"name": "Koala",       "emoji_base": "🐨", "unlock": "uncommon"},
    "fox":       {"name": "Fox",         "emoji_base": "🦊", "unlock": "rare"},
    "wolf":      {"name": "Wolf",        "emoji_base": "🐺", "unlock": "rare"},
    "owl":       {"name": "Owl",         "emoji_base": "🦉", "unlock": "rare"},
    "panda":     {"name": "Panda",       "emoji_base": "🐼", "unlock": "rare"},
    "deer":      {"name": "Deer",        "emoji_base": "🦌", "unlock": "rare"},
    "capybara":  {"name": "Capybara",    "emoji_base": "🦫", "unlock": "rare"},
    "tiger":     {"name": "Tiger",       "emoji_base": "🐯", "unlock": "epic"},
    "axolotl":   {"name": "Axolotl",     "emoji_base": "🦎", "unlock": "epic"},
    "shark":     {"name": "Shark",       "emoji_base": "🦈", "unlock": "legendary"},
    "dragon":    {"name": "Dragon",      "emoji_base": "🐲", "unlock": "legendary"},
    "unicorn":   {"name": "Unicorn",     "emoji_base": "🦄", "unlock": "legendary"},
    "phoenix":   {"name": "Phoenix",     "emoji_base": "🦅", "unlock": "legendary"},
    "dino":      {"name": "Dinosaur",    "emoji_base": "🦕", "unlock": "legendary"},
    "celestial": {"name": "Celestial",   "emoji_base": "🌟", "unlock": "mythic"},
    "void":      {"name": "Void",        "emoji_base": "🌑", "unlock": "mythic"},
    "god_beast": {"name": "God Beast",   "emoji_base": "👁️",  "unlock": "divine"},
}

# ── Clothing items (100+) ─────────────────────────────────────────────────────
CLOTHING = {
    # ── Divine ───────────────────────────────────────────────────────────────
    "divine_halo":      {"name": "Divine Halo",       "emoji": "✨", "rarity": "divine"},
    "void_crown":       {"name": "Void Crown",         "emoji": "🌑", "rarity": "divine"},
    "celestial_wings":  {"name": "Celestial Wings",    "emoji": "🌟", "rarity": "divine"},
    "gods_crown":       {"name": "God's Crown",        "emoji": "👑", "rarity": "divine"},
    # ── Mythic ───────────────────────────────────────────────────────────────
    "inferno_crown":    {"name": "Inferno Crown",      "emoji": "🔥", "rarity": "mythic"},
    "shadow_cloak":     {"name": "Shadow Cloak",       "emoji": "🌑", "rarity": "mythic"},
    "cosmic_helm":      {"name": "Cosmic Helmet",      "emoji": "🪐", "rarity": "mythic"},
    "dragon_soul":      {"name": "Dragon Soul",        "emoji": "🐉", "rarity": "mythic"},
    "eternity_ring":    {"name": "Eternity Ring",      "emoji": "💫", "rarity": "mythic"},
    "void_mask":        {"name": "Void Mask",          "emoji": "😶‍🌫️", "rarity": "mythic"},
    # ── Legendary ────────────────────────────────────────────────────────────
    "crown":            {"name": "Crown",              "emoji": "👑", "rarity": "legendary"},
    "wizard_hat":       {"name": "Wizard Hat",         "emoji": "🧙", "rarity": "legendary"},
    "halo":             {"name": "Halo",               "emoji": "😇", "rarity": "legendary"},
    "knight_helm":      {"name": "Knight Helmet",      "emoji": "⛑️",  "rarity": "legendary"},
    "galaxy_scarf":     {"name": "Galaxy Scarf",       "emoji": "🌌", "rarity": "legendary"},
    "dragon_wings":     {"name": "Dragon Wings",       "emoji": "🐉", "rarity": "legendary"},
    "phoenix_feather":  {"name": "Phoenix Feather",    "emoji": "🔥", "rarity": "legendary"},
    "unicorn_horn":     {"name": "Unicorn Horn",       "emoji": "🦄", "rarity": "legendary"},
    "samurai_helm":     {"name": "Samurai Helmet",     "emoji": "⚔️",  "rarity": "legendary"},
    "space_helmet":     {"name": "Space Helmet",       "emoji": "🚀", "rarity": "legendary"},
    "thunder_crown":    {"name": "Thunder Crown",      "emoji": "⚡", "rarity": "legendary"},
    "ice_crown":        {"name": "Ice Crown",          "emoji": "❄️",  "rarity": "legendary"},
    "black_cape":       {"name": "Dark Cape",          "emoji": "🖤", "rarity": "legendary"},
    # ── Epic ─────────────────────────────────────────────────────────────────
    "cape":             {"name": "Cape",               "emoji": "🦸", "rarity": "epic"},
    "graduation_cap":   {"name": "Grad Cap",           "emoji": "🎓", "rarity": "epic"},
    "monocle":          {"name": "Monocle",            "emoji": "🧐", "rarity": "epic"},
    "top_hat":          {"name": "Top Hat",            "emoji": "🎩", "rarity": "epic"},
    "sombrero":         {"name": "Sombrero",           "emoji": "🪅", "rarity": "epic"},
    "jester_hat":       {"name": "Jester Hat",         "emoji": "🃏", "rarity": "epic"},
    "viking_helm":      {"name": "Viking Helmet",      "emoji": "🪖", "rarity": "epic"},
    "detective_hat":    {"name": "Detective Hat",      "emoji": "🔍", "rarity": "epic"},
    "cowboy_hat":       {"name": "Cowboy Hat",         "emoji": "🤠", "rarity": "epic"},
    "chef_hat":         {"name": "Chef Hat",           "emoji": "👨‍🍳", "rarity": "epic"},
    "ninja_mask":       {"name": "Ninja Mask",         "emoji": "🥷", "rarity": "epic"},
    "pirate_hat":       {"name": "Pirate Hat",         "emoji": "🏴‍☠️", "rarity": "epic"},
    "witch_hat":        {"name": "Witch Hat",          "emoji": "🧙‍♀️", "rarity": "epic"},
    "astronaut_helm":   {"name": "Astronaut Helmet",   "emoji": "👨‍🚀", "rarity": "epic"},
    "fez":              {"name": "Fez",                "emoji": "🎭", "rarity": "epic"},
    "graduation_sash":  {"name": "Grad Sash",          "emoji": "🎓", "rarity": "epic"},
    # ── Rare ─────────────────────────────────────────────────────────────────
    "sunglasses":       {"name": "Sunglasses",         "emoji": "😎", "rarity": "rare"},
    "bow":              {"name": "Bow",                "emoji": "🎀", "rarity": "rare"},
    "pilot_cap":        {"name": "Pilot Cap",          "emoji": "🛩️",  "rarity": "rare"},
    "lei":              {"name": "Flower Lei",         "emoji": "🌺", "rarity": "rare"},
    "party_hat":        {"name": "Party Hat",          "emoji": "🎉", "rarity": "rare"},
    "nurse_cap":        {"name": "Nurse Cap",          "emoji": "💊", "rarity": "rare"},
    "construction_hat": {"name": "Hard Hat",           "emoji": "🏗️",  "rarity": "rare"},
    "santa_hat":        {"name": "Santa Hat",          "emoji": "🎅", "rarity": "rare"},
    "angel_wings":      {"name": "Angel Wings",        "emoji": "😇", "rarity": "rare"},
    "devil_horns":      {"name": "Devil Horns",        "emoji": "😈", "rarity": "rare"},
    "tiny_crown":       {"name": "Tiny Crown",         "emoji": "👑", "rarity": "rare"},
    "rainbow_hat":      {"name": "Rainbow Hat",        "emoji": "🌈", "rarity": "rare"},
    "elf_hat":          {"name": "Elf Hat",            "emoji": "🎄", "rarity": "rare"},
    "pirate_eyepatch":  {"name": "Pirate Eyepatch",    "emoji": "🏴‍☠️", "rarity": "rare"},
    "mushroom_hat":     {"name": "Mushroom Hat",       "emoji": "🍄", "rarity": "rare"},
    "shark_fin":        {"name": "Shark Fin",          "emoji": "🦈", "rarity": "rare"},
    "mortarboard":      {"name": "Mortarboard",        "emoji": "🏫", "rarity": "rare"},
    # ── Uncommon ─────────────────────────────────────────────────────────────
    "hat":              {"name": "Hat",                "emoji": "🎩", "rarity": "uncommon"},
    "scarf":            {"name": "Scarf",              "emoji": "🧣", "rarity": "uncommon"},
    "glasses":          {"name": "Glasses",            "emoji": "🤓", "rarity": "uncommon"},
    "beret":            {"name": "Beret",              "emoji": "🎨", "rarity": "uncommon"},
    "headphones":       {"name": "Headphones",         "emoji": "🎧", "rarity": "uncommon"},
    "bow_tie":          {"name": "Bow Tie",            "emoji": "🎀", "rarity": "uncommon"},
    "flower_crown":     {"name": "Flower Crown",       "emoji": "🌸", "rarity": "uncommon"},
    "cap_backwards":    {"name": "Backwards Cap",      "emoji": "🧢", "rarity": "uncommon"},
    "propeller_hat":    {"name": "Propeller Hat",      "emoji": "🌀", "rarity": "uncommon"},
    "bunny_ears":       {"name": "Bunny Ears",         "emoji": "🐰", "rarity": "uncommon"},
    "cat_ears":         {"name": "Cat Ears",           "emoji": "🐱", "rarity": "uncommon"},
    "reindeer_antlers": {"name": "Reindeer Antlers",   "emoji": "🦌", "rarity": "uncommon"},
    "superhero_mask":   {"name": "Superhero Mask",     "emoji": "🦸", "rarity": "uncommon"},
    "swim_goggles":     {"name": "Swim Goggles",       "emoji": "🏊", "rarity": "uncommon"},
    "tiara":            {"name": "Tiara",              "emoji": "💍", "rarity": "uncommon"},
    "knitted_hat":      {"name": "Knitted Hat",        "emoji": "🧶", "rarity": "uncommon"},
    "paper_crown":      {"name": "Paper Crown",        "emoji": "📄", "rarity": "uncommon"},
    "sweatband":        {"name": "Sweatband",          "emoji": "🏃", "rarity": "uncommon"},
    "laurel_wreath":    {"name": "Laurel Wreath",      "emoji": "🏛️",  "rarity": "uncommon"},
    "bandaid":          {"name": "Bandaid",            "emoji": "🩹", "rarity": "uncommon"},
    # ── Common ───────────────────────────────────────────────────────────────
    "bandana":          {"name": "Bandana",            "emoji": "🏴", "rarity": "common"},
    "collar":           {"name": "Collar",             "emoji": "🔵", "rarity": "common"},
    "beanie":           {"name": "Beanie",             "emoji": "🧢", "rarity": "common"},
    "sports_cap":       {"name": "Sports Cap",         "emoji": "🧢", "rarity": "common"},
    "hair_bow":         {"name": "Hair Bow",           "emoji": "🎀", "rarity": "common"},
    "wristband":        {"name": "Wristband",          "emoji": "💪", "rarity": "common"},
    "necklace":         {"name": "Necklace",           "emoji": "📿", "rarity": "common"},
    "friendship_band":  {"name": "Friendship Band",    "emoji": "🌈", "rarity": "common"},
    "sticker_star":     {"name": "Star Sticker",       "emoji": "⭐", "rarity": "common"},
    "sticker_heart":    {"name": "Heart Sticker",      "emoji": "❤️",  "rarity": "common"},
    "medal":            {"name": "Medal",              "emoji": "🥇", "rarity": "common"},
    "tag":              {"name": "Name Tag",           "emoji": "🏷️",  "rarity": "common"},
    "rubber_duck":      {"name": "Rubber Duck",        "emoji": "🦆", "rarity": "common"},
    "leaf":             {"name": "Leaf",               "emoji": "🍃", "rarity": "common"},
    "star_badge":       {"name": "Star Badge",         "emoji": "⭐", "rarity": "common"},
    "cloud_hat":        {"name": "Cloud Hat",          "emoji": "☁️",  "rarity": "common"},
    "bow_pink":         {"name": "Pink Bow",           "emoji": "🌸", "rarity": "common"},
}

# ── Crate types by SBC grade ──────────────────────────────────────────────────
def _clothes_by_rarity(*rarities):
    return [k for k, v in CLOTHING.items() if v["rarity"] in rarities]

def _pets_by_rarity(*rarities):
    return [k for k, v in PET_SPECIES.items() if v["unlock"] in rarities]

CRATE_TYPES = {
    "A+": {
        "name": "Golden Crate", "colour": "#f0c040", "grade": "A+",
        "weights": {"divine":2, "mythic":5, "legendary":12, "epic":20, "rare":28, "uncommon":20, "common":13},
        "pets":    _pets_by_rarity("legendary","mythic","divine","epic","rare"),
        "clothes": _clothes_by_rarity("divine","mythic","legendary","epic","rare","uncommon","common"),
    },
    "A":  {
        "name": "Silver Crate", "colour": "#c0c0c0", "grade": "A",
        "weights": {"divine":0, "mythic":1, "legendary":6, "epic":16, "rare":28, "uncommon":30, "common":19},
        "pets":    _pets_by_rarity("epic","rare","uncommon","common"),
        "clothes": _clothes_by_rarity("mythic","legendary","epic","rare","uncommon","common"),
    },
    "B":  {
        "name": "Bronze Crate", "colour": "#cd7f32", "grade": "B",
        "weights": {"divine":0, "mythic":0, "legendary":2, "epic":8, "rare":22, "uncommon":35, "common":33},
        "pets":    _pets_by_rarity("rare","uncommon","common"),
        "clothes": _clothes_by_rarity("legendary","epic","rare","uncommon","common"),
    },
    "C":  {
        "name": "Common Crate", "colour": "#4a90d9", "grade": "C",
        "weights": {"divine":0, "mythic":0, "legendary":0, "epic":3, "rare":12, "uncommon":35, "common":50},
        "pets":    _pets_by_rarity("common","uncommon"),
        "clothes": _clothes_by_rarity("epic","rare","uncommon","common"),
    },
    "D":  {
        "name": "Worn Crate",   "colour": "#7c7c7c", "grade": "D",
        "weights": {"divine":0, "mythic":0, "legendary":0, "epic":0, "rare":5, "uncommon":20, "common":75},
        "pets":    [],
        "clothes": _clothes_by_rarity("rare","uncommon","common"),
    },
    "UG": {"name": "", "colour": "", "grade": "UG",
           "weights": {}, "pets": [], "clothes": []},
    # ── Special crates from achievements ─────────────────────────────────────
    "mythic_chest": {
        "name": "Mythic Chest", "colour": "#ff6b35", "grade": None,
        "weights": {"divine":5, "mythic":20, "legendary":35, "epic":25, "rare":10, "uncommon":4, "common":1},
        "pets":    _pets_by_rarity("mythic","divine","legendary","epic"),
        "clothes": _clothes_by_rarity("divine","mythic","legendary","epic"),
    },
    "divine_chest": {
        "name": "Divine Chest", "colour": "#ffffff", "grade": None,
        "weights": {"divine":25, "mythic":40, "legendary":25, "epic":8, "rare":2, "uncommon":0, "common":0},
        "pets":    _pets_by_rarity("divine","mythic","legendary"),
        "clothes": _clothes_by_rarity("divine","mythic","legendary"),
    },
}

# ── Evolution tiers ───────────────────────────────────────────────────────────
def get_pet_emoji(species: str, level: int) -> str:
    evolutions = {
        "cat":       ["🐱","😸","😺","🐯","🦁"],
        "dog":       ["🐶","🐕","🦮","🐕‍🦺","🐺"],
        "fox":       ["🦊","🦊","🦝","🦝","🦊"],
        "dragon":    ["🐲","🐲","🐉","🐉","🔥"],
        "bunny":     ["🐰","🐇","🐇","🐇","⭐"],
        "bear":      ["🐻","🐼","🐻‍❄️","🐨","💎"],
        "wolf":      ["🐺","🐺","🌙","🌕","⚡"],
        "penguin":   ["🐧","🐧","❄️","🧊","💎"],
        "owl":       ["🦉","🦉","🌙","🦅","✨"],
        "tiger":     ["🐯","🐯","🦁","🦁","🔥"],
        "panda":     ["🐼","🐼","🎋","🐼","💮"],
        "unicorn":   ["🦄","🦄","🌈","✨","👑"],
        "phoenix":   ["🐦","🦅","🔥","🌟","👑"],
        "frog":      ["🐸","🐸","🌿","🌊","💚"],
        "axolotl":   ["🦎","🦎","💧","🌊","🌟"],
        "deer":      ["🦌","🦌","🌿","🍂","🌟"],
        "koala":     ["🐨","🐨","🌿","🍃","💫"],
        "shark":     ["🦈","🦈","🌊","⚡","💀"],
        "capybara":  ["🦫","🦫","🌊","🏊","👑"],
        "dino":      ["🦕","🦕","🦖","🔥","💎"],
        "celestial": ["🌟","💫","✨","🌠","🌌"],
        "void":      ["🌑","🌒","🌓","🌔","🌕"],
        "god_beast": ["👁️","🔮","🌀","💠","⚜️"],
    }
    evos = evolutions.get(species, ["🐾","🐾","🐾","🐾","🐾"])
    tier = min(level // 10, len(evos) - 1)
    return evos[tier]


def xp_for_level(level: int) -> int:
    return 179


# ── Secure storage helpers ────────────────────────────────────────────────────
def _sign(data: str) -> str:
    return hmac.new(_APP_KEY, data.encode(), hashlib.sha256).hexdigest()

def _secure_write(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = json.dumps(obj, separators=(",", ":"), sort_keys=True)
    sig = _sign(payload)
    with open(path, "w") as f:
        json.dump({"d": payload, "s": sig}, f)

def _secure_read(path: str) -> dict:
    with open(path) as f:
        wrapper = json.load(f)
    payload = wrapper["d"]
    if not hmac.compare_digest(_sign(payload), wrapper["s"]):
        raise ValueError("Tampered file detected")
    return json.loads(payload)


# ── PetData ───────────────────────────────────────────────────────────────────
@dataclass
class PetData:
    species:        str  = "cat"
    name:           str  = "Buddy"
    level:          int  = 1
    xp:             int  = 0
    equipped_item:  str  = ""
    inventory:      List = field(default_factory=list)
    unlocked_pets:  List = field(default_factory=lambda: ["cat"])
    achievements:   List = field(default_factory=list)
    crates_opened:  int  = 0
    crates_by_type: Dict = field(default_factory=dict)
    special_crates: Dict = field(default_factory=dict)  # mythic_chest, divine_chest counts

    def emoji(self) -> str:
        return get_pet_emoji(self.species, self.level)

    def clothing_emoji(self) -> str:
        if self.equipped_item and self.equipped_item in CLOTHING:
            return CLOTHING[self.equipped_item]["emoji"]
        return ""

    def display(self) -> str:
        base  = self.emoji()
        cloth = self.clothing_emoji()
        return f"{cloth}{base}" if cloth else base

    def add_xp(self, amount: int) -> List[str]:
        messages = []
        self.xp += amount
        while self.xp >= xp_for_level(self.level) and self.level < 99:
            self.xp -= xp_for_level(self.level)
            self.level += 1
            if self.level % 10 == 0:
                messages.append(f"🎉 {self.name} evolved! Now level {self.level}!")
            else:
                messages.append(f"⬆️ {self.name} reached level {self.level}!")
        return messages

    def xp_progress(self) -> float:
        needed = xp_for_level(self.level)
        return min(1.0, self.xp / needed) if needed > 0 else 1.0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: dict) -> "PetData":
        p = cls()
        for k, v in d.items():
            if hasattr(p, k):
                setattr(p, k, v)
        return p


def load_pet(username: str) -> PetData:
    path = os.path.expanduser(f"~/.sbc_portal/pet_{username}.json")
    if os.path.exists(path):
        try:
            return PetData.from_dict(_secure_read(path))
        except Exception:
            pass
    return PetData(level=1, xp=0)


def save_pet(pet: PetData, username: str):
    path = os.path.expanduser(f"~/.sbc_portal/pet_{username}.json")
    _secure_write(path, pet.to_dict())


# Coins earned per grade tier (from assessments)
GRADE_COINS = {"A+": 20, "A": 14, "B": 9, "C": 5, "D": 2, "UG": 0}
# Coins earned per crate opened
CRATE_OPEN_COINS = 3


def count_crates(data, username: str = "") -> dict:
    import datetime
    from scraper.grade_logic import grade_label as gl
    counts = {"A+":0,"A":0,"B":0,"C":0,"D":0}
    if not data:
        return counts
    yr = datetime.datetime.now().year
    for year, subjects in data.subjects_by_year.items():
        if year < yr - 1:
            continue
        for subj in subjects:
            for a in subj.assignments:
                if a.grade_raw is not None:
                    label = gl(a.grade_raw)
                    if label in counts:
                        counts[label] += 1
    return counts


def compute_grade_coins(data) -> int:
    """Total coins earned from all graded assessments (current + last year)."""
    import datetime
    from scraper.grade_logic import grade_label as gl
    if not data:
        return 0
    yr = datetime.datetime.now().year
    total = 0
    for year, subjects in data.subjects_by_year.items():
        if year < yr - 1:
            continue
        for subj in subjects:
            for a in subj.assignments:
                if a.grade_raw is not None:
                    label = gl(a.grade_raw)
                    total += GRADE_COINS.get(label, 0)
    return total


def load_crate_counts(username: str) -> dict:
    path = os.path.expanduser(f"~/.sbc_portal/crates_{username}.json")
    if os.path.exists(path):
        try:
            return _secure_read(path)
        except Exception:
            pass
    return {"A+":0,"A":0,"B":0,"C":0,"D":0}


def save_crate_counts(counts: dict, username: str):
    path = os.path.expanduser(f"~/.sbc_portal/crates_{username}.json")
    _secure_write(path, counts)
