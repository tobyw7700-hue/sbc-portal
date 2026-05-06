"""
Pet system data models — 15 species, 75+ clothing items.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import json, os

SAVE_PATH = os.path.expanduser("~/.sbc_portal/pet_data.json")

# ── Pet species (15) ──────────────────────────────────────────────────────────
PET_SPECIES = {
    "cat":      {"name": "Cat",        "emoji_base": "🐱", "unlock": "default"},
    "dog":      {"name": "Dog",        "emoji_base": "🐶", "unlock": "common"},
    "fox":      {"name": "Fox",        "emoji_base": "🦊", "unlock": "rare"},
    "dragon":   {"name": "Dragon",     "emoji_base": "🐲", "unlock": "legendary"},
    "bunny":    {"name": "Bunny",      "emoji_base": "🐰", "unlock": "common"},
    "bear":     {"name": "Bear",       "emoji_base": "🐻", "unlock": "uncommon"},
    "wolf":     {"name": "Wolf",       "emoji_base": "🐺", "unlock": "rare"},
    "penguin":  {"name": "Penguin",    "emoji_base": "🐧", "unlock": "uncommon"},
    "owl":      {"name": "Owl",        "emoji_base": "🦉", "unlock": "rare"},
    "tiger":    {"name": "Tiger",      "emoji_base": "🐯", "unlock": "epic"},
    "panda":    {"name": "Panda",      "emoji_base": "🐼", "unlock": "rare"},
    "unicorn":  {"name": "Unicorn",    "emoji_base": "🦄", "unlock": "legendary"},
    "phoenix":  {"name": "Phoenix",    "emoji_base": "🦅", "unlock": "legendary"},
    "frog":     {"name": "Frog",       "emoji_base": "🐸", "unlock": "common"},
    "axolotl":  {"name": "Axolotl",   "emoji_base": "🦎", "unlock": "epic"},
    "deer":     {"name": "Deer",       "emoji_base": "🦌", "unlock": "rare"},
    "koala":    {"name": "Koala",      "emoji_base": "🐨", "unlock": "uncommon"},
    "shark":    {"name": "Shark",      "emoji_base": "🦈", "unlock": "legendary"},
    "capybara": {"name": "Capybara",   "emoji_base": "🦫", "unlock": "rare"},
    "dino":     {"name": "Dinosaur",   "emoji_base": "🦕", "unlock": "legendary"},
}

# ── Crate types by SBC grade ──────────────────────────────────────────────────
_ALL_PETS = list(PET_SPECIES.keys())

CRATE_TYPES = {
    "A+": {
        "name": "Golden Crate", "colour": "#f0c040",
        "pets": ["dragon","fox","wolf","tiger","unicorn","phoenix","owl","axolotl","shark","dino"],
        "clothes": [
            "crown","wizard_hat","halo","knight_helm","galaxy_scarf","dragon_wings",
            "phoenix_feather","unicorn_horn","samurai_helm","space_helmet",
            "cape","graduation_cap","monocle","top_hat","sombrero","jester_hat",
            "party_hat","pilot_cap","lei","sunglasses","bow","bow_tie",
            "flower_crown","scarf","glasses","hat","headphones","beret",
            "bandana","collar","beanie","sports_cap","tiny_crown",
        ],
    },
    "A":  {
        "name": "Silver Crate", "colour": "#c0c0c0",
        "pets": ["fox","dog","bunny","bear","wolf","penguin","panda","owl","deer","capybara"],
        "clothes": [
            "cape","graduation_cap","monocle","top_hat","sombrero","jester_hat",
            "party_hat","pilot_cap","lei","sunglasses","bow","bow_tie",
            "flower_crown","scarf","glasses","hat","headphones","beret",
            "bandana","collar","beanie","sports_cap","tiny_crown",
            "chef_hat","ninja_mask","cowboy_hat","detective_hat","viking_helm",
        ],
    },
    "B":  {
        "name": "Bronze Crate", "colour": "#cd7f32",
        "pets": ["dog","bunny","bear","penguin","panda","frog","koala","deer"],
        "clothes": [
            "party_hat","pilot_cap","sunglasses","bow","bow_tie",
            "flower_crown","scarf","glasses","hat","headphones","beret",
            "bandana","collar","beanie","sports_cap","tiny_crown",
            "chef_hat","cowboy_hat","detective_hat","viking_helm",
            "pirate_hat","witch_hat","nurse_cap","construction_hat",
        ],
    },
    "C":  {
        "name": "Common Crate", "colour": "#4a90d9",
        "pets": ["cat","bunny","frog","dog","koala","capybara"],
        "clothes": [
            "bandana","collar","beanie","sports_cap","tiny_crown",
            "flower_crown","headphones","beret","scarf","hat","glasses",
            "pirate_hat","witch_hat","nurse_cap","construction_hat","party_hat",
        ],
    },
    "D":  {
        "name": "Worn Crate",   "colour": "#7c7c7c",
        "pets": [],
        "clothes": [
            "collar","bandana","beanie","sports_cap","scarf","hat","glasses",
        ],
    },
    "UG": {"name": "", "colour": "", "pets": [], "clothes": []},
}

# ── Clothing items (75+) ──────────────────────────────────────────────────────
CLOTHING = {
    # ── Legendary ────────────────────────────────────────────────────────────
    "crown":          {"name": "Crown",            "emoji": "👑", "rarity": "legendary"},
    "wizard_hat":     {"name": "Wizard Hat",       "emoji": "🧙", "rarity": "legendary"},
    "halo":           {"name": "Halo",             "emoji": "😇", "rarity": "legendary"},
    "knight_helm":    {"name": "Knight Helmet",    "emoji": "⛑️",  "rarity": "legendary"},
    "galaxy_scarf":   {"name": "Galaxy Scarf",     "emoji": "🌌", "rarity": "legendary"},
    "dragon_wings":   {"name": "Dragon Wings",     "emoji": "🐉", "rarity": "legendary"},
    "phoenix_feather":{"name": "Phoenix Feather",  "emoji": "🔥", "rarity": "legendary"},
    "unicorn_horn":   {"name": "Unicorn Horn",     "emoji": "🦄", "rarity": "legendary"},
    "samurai_helm":   {"name": "Samurai Helmet",   "emoji": "⚔️",  "rarity": "legendary"},
    "space_helmet":   {"name": "Space Helmet",     "emoji": "🚀", "rarity": "legendary"},
    # ── Epic ─────────────────────────────────────────────────────────────────
    "cape":           {"name": "Cape",             "emoji": "🦸", "rarity": "epic"},
    "graduation_cap": {"name": "Grad Cap",         "emoji": "🎓", "rarity": "epic"},
    "monocle":        {"name": "Monocle",          "emoji": "🧐", "rarity": "epic"},
    "top_hat":        {"name": "Top Hat",          "emoji": "🎩", "rarity": "epic"},
    "sombrero":       {"name": "Sombrero",         "emoji": "🪅", "rarity": "epic"},
    "jester_hat":     {"name": "Jester Hat",       "emoji": "🃏", "rarity": "epic"},
    "viking_helm":    {"name": "Viking Helmet",    "emoji": "🪖", "rarity": "epic"},
    "detective_hat":  {"name": "Detective Hat",    "emoji": "🔍", "rarity": "epic"},
    "cowboy_hat":     {"name": "Cowboy Hat",       "emoji": "🤠", "rarity": "epic"},
    "chef_hat":       {"name": "Chef Hat",         "emoji": "👨‍🍳", "rarity": "epic"},
    "ninja_mask":     {"name": "Ninja Mask",       "emoji": "🥷", "rarity": "epic"},
    "pirate_hat":     {"name": "Pirate Hat",       "emoji": "🏴‍☠️", "rarity": "epic"},
    "witch_hat":      {"name": "Witch Hat",        "emoji": "🧙‍♀️", "rarity": "epic"},
    # ── Rare ─────────────────────────────────────────────────────────────────
    "sunglasses":     {"name": "Sunglasses",       "emoji": "😎", "rarity": "rare"},
    "bow":            {"name": "Bow",              "emoji": "🎀", "rarity": "rare"},
    "pilot_cap":      {"name": "Pilot Cap",        "emoji": "🛩️",  "rarity": "rare"},
    "lei":            {"name": "Flower Lei",       "emoji": "🌺", "rarity": "rare"},
    "party_hat":      {"name": "Party Hat",        "emoji": "🎉", "rarity": "rare"},
    "nurse_cap":      {"name": "Nurse Cap",        "emoji": "💊", "rarity": "rare"},
    "construction_hat":{"name":"Hard Hat",         "emoji": "🏗️",  "rarity": "rare"},
    "santa_hat":      {"name": "Santa Hat",        "emoji": "🎅", "rarity": "rare"},
    "viking_horns":   {"name": "Viking Horns",     "emoji": "🎭", "rarity": "rare"},
    "angel_wings":    {"name": "Angel Wings",      "emoji": "😇", "rarity": "rare"},
    "devil_horns":    {"name": "Devil Horns",      "emoji": "😈", "rarity": "rare"},
    "crown_flowers":  {"name": "Flower Crown",     "emoji": "🌸", "rarity": "rare"},
    "tiny_crown":     {"name": "Tiny Crown",       "emoji": "👑", "rarity": "rare"},
    "rainbow_hat":    {"name": "Rainbow Hat",      "emoji": "🌈", "rarity": "rare"},
    # ── Uncommon ─────────────────────────────────────────────────────────────
    "hat":            {"name": "Hat",              "emoji": "🎩", "rarity": "uncommon"},
    "scarf":          {"name": "Scarf",            "emoji": "🧣", "rarity": "uncommon"},
    "glasses":        {"name": "Glasses",          "emoji": "🤓", "rarity": "uncommon"},
    "beret":          {"name": "Beret",            "emoji": "🎨", "rarity": "uncommon"},
    "headphones":     {"name": "Headphones",       "emoji": "🎧", "rarity": "uncommon"},
    "bow_tie":        {"name": "Bow Tie",          "emoji": "🎀", "rarity": "uncommon"},
    "flower_crown":   {"name": "Flower Crown",     "emoji": "🌸", "rarity": "uncommon"},
    "lei_simple":     {"name": "Simple Lei",       "emoji": "🌼", "rarity": "uncommon"},
    "cap_backwards":  {"name": "Backwards Cap",    "emoji": "🧢", "rarity": "uncommon"},
    "propeller_hat":  {"name": "Propeller Hat",    "emoji": "🌀", "rarity": "uncommon"},
    "bunny_ears":     {"name": "Bunny Ears",       "emoji": "🐰", "rarity": "uncommon"},
    "cat_ears":       {"name": "Cat Ears",         "emoji": "🐱", "rarity": "uncommon"},
    "reindeer_antlers":{"name":"Reindeer Antlers", "emoji": "🦌", "rarity": "uncommon"},
    "superhero_mask": {"name": "Superhero Mask",   "emoji": "🦸", "rarity": "uncommon"},
    "swim_goggles":   {"name": "Swim Goggles",     "emoji": "🏊", "rarity": "uncommon"},
    "safety_glasses": {"name": "Safety Glasses",   "emoji": "🥽", "rarity": "uncommon"},
    "3d_glasses":     {"name": "3D Glasses",       "emoji": "🎬", "rarity": "uncommon"},
    "tiara":          {"name": "Tiara",            "emoji": "💍", "rarity": "uncommon"},
    # ── Common ───────────────────────────────────────────────────────────────
    "bandana":        {"name": "Bandana",          "emoji": "🏴", "rarity": "common"},
    "collar":         {"name": "Collar",           "emoji": "🔵", "rarity": "common"},
    "beanie":         {"name": "Beanie",           "emoji": "🧢", "rarity": "common"},
    "sports_cap":     {"name": "Sports Cap",       "emoji": "🧢", "rarity": "common"},
    "hair_bow":       {"name": "Hair Bow",         "emoji": "🎀", "rarity": "common"},
    "hair_clip":      {"name": "Hair Clip",        "emoji": "✨", "rarity": "common"},
    "wristband":      {"name": "Wristband",        "emoji": "💪", "rarity": "common"},
    "necklace":       {"name": "Necklace",         "emoji": "📿", "rarity": "common"},
    "earring":        {"name": "Earring",          "emoji": "💎", "rarity": "common"},
    "nose_ring":      {"name": "Nose Ring",        "emoji": "💫", "rarity": "common"},
    "friendship_band":{"name": "Friendship Band",  "emoji": "🌈", "rarity": "common"},
    "sticker_star":   {"name": "Star Sticker",     "emoji": "⭐", "rarity": "common"},
    "sticker_heart":  {"name": "Heart Sticker",    "emoji": "❤️",  "rarity": "common"},
    "paint_splat":    {"name": "Paint Splat",      "emoji": "🎨", "rarity": "common"},
    "medal":          {"name": "Medal",            "emoji": "🥇", "rarity": "common"},
    # More legendary
    "thunder_crown":  {"name": "Thunder Crown",    "emoji": "⚡", "rarity": "legendary"},
    "ice_crown":      {"name": "Ice Crown",        "emoji": "❄️",  "rarity": "legendary"},
    "black_cape":     {"name": "Dark Cape",        "emoji": "🖤", "rarity": "legendary"},
    # More epic
    "astronaut_helm": {"name": "Astronaut Helmet", "emoji": "👨‍🚀", "rarity": "epic"},
    "fez":            {"name": "Fez",              "emoji": "🎭", "rarity": "epic"},
    "crown_gold":     {"name": "Gold Crown",       "emoji": "🥇", "rarity": "epic"},
    "graduation_sash":{"name": "Grad Sash",        "emoji": "🎓", "rarity": "epic"},
    # More rare
    "elf_hat":        {"name": "Elf Hat",          "emoji": "🎄", "rarity": "rare"},
    "pirate_eyepatch":{"name": "Pirate Eyepatch",  "emoji": "🏴‍☠️", "rarity": "rare"},
    "mortarboard":    {"name": "Mortarboard",      "emoji": "🏫", "rarity": "rare"},
    "mushroom_hat":   {"name": "Mushroom Hat",     "emoji": "🍄", "rarity": "rare"},
    "shark_fin":      {"name": "Shark Fin",        "emoji": "🦈", "rarity": "rare"},
    # More uncommon
    "knitted_hat":    {"name": "Knitted Hat",      "emoji": "🧶", "rarity": "uncommon"},
    "paper_crown":    {"name": "Paper Crown",      "emoji": "📄", "rarity": "uncommon"},
    "sweatband":      {"name": "Sweatband",        "emoji": "🏃", "rarity": "uncommon"},
    "detective_glass":{"name": "Magnifying Glass", "emoji": "🔍", "rarity": "uncommon"},
    "laurel_wreath":  {"name": "Laurel Wreath",    "emoji": "🏛️",  "rarity": "uncommon"},
    "bandaid":        {"name": "Bandaid",          "emoji": "🩹", "rarity": "uncommon"},
    # More common
    "tag":            {"name": "Name Tag",         "emoji": "🏷️",  "rarity": "common"},
    "rubber_duck":    {"name": "Rubber Duck",      "emoji": "🦆", "rarity": "common"},
    "leaf":           {"name": "Leaf",             "emoji": "🍃", "rarity": "common"},
    "bow_pink":       {"name": "Pink Bow",         "emoji": "🌸", "rarity": "common"},
    "star_badge":     {"name": "Star Badge",       "emoji": "⭐", "rarity": "common"},
    "cloud_hat":      {"name": "Cloud Hat",        "emoji": "☁️",  "rarity": "common"},
}

RARITY_COLOURS = {
    "legendary": "#f0c040",
    "epic":      "#c77dff",
    "rare":      "#4a90d9",
    "uncommon":  "#22c55e",
    "common":    "#8da4cc",
}

# Evolution tiers — pet visual changes every 10 levels (tiers: 0,10,20,30,40,50,60,70,80,90)
def get_pet_emoji(species: str, level: int) -> str:
    evolutions = {
        "cat":     ["🐱","😸","😺","🐯","🦁"],
        "dog":     ["🐶","🐕","🦮","🐕‍🦺","🐺"],
        "fox":     ["🦊","🦊","🦝","🦝","🦊"],
        "dragon":  ["🐲","🐲","🐉","🐉","🔥"],
        "bunny":   ["🐰","🐇","🐇","🐇","⭐"],
        "bear":    ["🐻","🐼","🐻‍❄️","🐨","💎"],
        "wolf":    ["🐺","🐺","🌙","🌕","⚡"],
        "penguin": ["🐧","🐧","❄️","🧊","💎"],
        "owl":     ["🦉","🦉","🌙","🦅","✨"],
        "tiger":   ["🐯","🐯","🦁","🦁","🔥"],
        "panda":   ["🐼","🐼","🎋","🐼","💮"],
        "unicorn": ["🦄","🦄","🌈","✨","👑"],
        "phoenix": ["🐦","🦅","🔥","🌟","👑"],
        "frog":    ["🐸","🐸","🌿","🌊","💚"],
        "axolotl": ["🦎","🦎","💧","🌊","🌟"],
        "deer":    ["🦌","🦌","🌿","🍂","🌟"],
        "koala":   ["🐨","🐨","🌿","🍃","💫"],
        "shark":   ["🦈","🦈","🌊","⚡","💀"],
        "capybara":["🦫","🦫","🌊","🏊","👑"],
        "dino":    ["🦕","🦕","🦖","🔥","💎"],
    }
    evos = evolutions.get(species, ["🐾","🐾","🐾","🐾","🐾"])
    tier = min(level // 10, len(evos) - 1)
    return evos[tier]


def xp_for_level(level: int) -> int:
    """
    179 XP per level. Total for level 99 = 98 * 179 = 17542.
    Total available from all achievements = ~17590.
    This means you can ONLY reach level 99 by unlocking every achievement.
    No other XP source exists.
    """
    return 179


@dataclass
class PetData:
    species:       str  = "cat"
    name:          str  = "Buddy"
    level:         int  = 1
    xp:            int  = 0
    equipped_item: str  = ""
    inventory:     List = field(default_factory=list)
    unlocked_pets: List = field(default_factory=lambda: ["cat"])
    achievements:  List = field(default_factory=list)
    crates_opened: int  = 0
    crates_by_type:Dict = field(default_factory=dict)  # track which types opened

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
            with open(path) as f:
                return PetData.from_dict(json.load(f))
        except Exception:
            pass
    # Brand new pet — always starts at level 1, 0 xp
    return PetData(level=1, xp=0)


def save_pet(pet: PetData, username: str):
    os.makedirs(os.path.expanduser("~/.sbc_portal"), exist_ok=True)
    path = os.path.expanduser(f"~/.sbc_portal/pet_{username}.json")
    with open(path, "w") as f:
        json.dump(pet.to_dict(), f, indent=2)


def count_crates(data, username: str = "") -> dict:
    import datetime
    from scraper.grade_logic import grade_label as gl
    counts = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0}
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
    if username:
        path = os.path.expanduser(f"~/.sbc_portal/crates_{username}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(counts, f)
    return counts


def load_crate_counts(username: str) -> dict:
    path = os.path.expanduser(f"~/.sbc_portal/crates_{username}.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0}
