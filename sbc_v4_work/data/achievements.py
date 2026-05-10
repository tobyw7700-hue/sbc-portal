"""
Achievement definitions and detection logic — 100+ achievements.
"""
from dataclasses import dataclass
from typing import Optional, List
import json, os


@dataclass
class Achievement:
    id:          str
    title:       str
    description: str
    emoji:       str
    xp_reward:   int
    subject:     Optional[str] = None
    hidden:      bool = False   # hidden until unlocked


ALL_ACHIEVEMENTS = [
    # ── First steps ──────────────────────────────────────────────────────────
    Achievement("first_login",       "Welcome!",               "Log in for the first time",                              "🎉", 50),
    Achievement("first_grade",       "First Result",           "Receive your first graded assessment",                   "📝", 30),
    Achievement("first_crate",       "Unboxing!",              "Open your first crate",                                  "📦", 50),
    Achievement("dressed_up",        "Fashion Icon",           "Equip a clothing item to your pet",                      "👗", 50),
    Achievement("new_pet",           "New Friend",             "Unlock a new pet species",                               "🐾", 100),
    Achievement("renamed_pet",       "Identity",               "Give your pet a custom name",                            "✏️", 20),

    # ── Grade volume milestones ───────────────────────────────────────────────
    Achievement("ten_assessments",   "Getting Started",        "Complete 10 graded assessments",                         "📚", 50),
    Achievement("twenty_assessments","Picking Up Pace",        "Complete 20 graded assessments",                         "📖", 80),
    Achievement("thirty_assessments","Committed",              "Complete 30 graded assessments",                         "✅", 100),
    Achievement("fifty_assessments", "Scholar",                "Complete 50 graded assessments",                         "🏫", 150),
    Achievement("seventy_five_ass",  "Dedicated",              "Complete 75 graded assessments",                         "🎓", 200),
    Achievement("hundred_ass",       "Century",                "Complete 100 graded assessments",                        "💯", 300),

    # ── Grade quality ─────────────────────────────────────────────────────────
    Achievement("first_a_plus",      "First A+",               "Score A+ (90%+) on any assessment",                      "⭐", 80),
    Achievement("first_perfect",     "Perfect Score",          "Get 100% on any assessment",                             "💯", 200),
    Achievement("five_a_plus",       "On A Roll",              "Get A+ on 5 assessments",                                "🌟", 120),
    Achievement("ten_a_plus",        "High Achiever",          "Get A+ on 10 assessments",                               "🏆", 200),
    Achievement("twenty_a_plus",     "Excellence",             "Get A+ on 20 assessments",                               "👑", 350),
    Achievement("fifty_a_plus",      "Legendary Student",      "Get A+ on 50 assessments",                               "🌠", 500),
    Achievement("three_perfect",     "Hat Trick",              "Get 100% on 3 assessments",                              "🎩", 250),
    Achievement("no_d_ug",           "Passing Grade",          "Have no D or UG grades this year",                       "👍", 100),
    Achievement("no_ug_ever",        "Never Gave Up",          "Never receive a UG grade",                               "🛡️", 200),
    Achievement("all_above_60",      "Respectable",            "Score 60%+ in every subject",                            "📊", 100),
    Achievement("all_above_70",      "Solid",                  "Score 70%+ in every subject",                            "📈", 150),
    Achievement("all_above_80",      "Outstanding",            "Score 80%+ in every subject",                            "⭐", 250),
    Achievement("all_above_90",      "Perfect Semester",       "Score 90%+ in every subject",                            "🌟", 500),

    # ── Subject averages — A+ (90%) ───────────────────────────────────────────
    Achievement("math_90",           "Maths Maestro",          "Score 90%+ average in Mathematics",                      "📐", 200, "Mathematics"),
    Achievement("eng_90",            "Wordsmith",              "Score 90%+ average in English",                          "📖", 200, "English"),
    Achievement("sci_90",            "Science Whiz",           "Score 90%+ average in Science",                          "🔬", 200, "Science"),
    Achievement("hum_90",            "Historian",              "Score 90%+ average in Humanities",                       "🌍", 200, "Humanities"),
    Achievement("rels_90",           "Faithful",               "Score 90%+ average in Religion & Society",               "✝️", 200, "Religion & Society"),
    Achievement("hepe_90",           "Athlete",                "Score 90%+ average in Health & PE",                      "🏃", 200, "Health & PE"),
    Achievement("ital_90",           "Linguist",               "Score 90%+ average in Italian",                          "🇮🇹", 200, "Italian"),
    Achievement("viscom_90",         "Designer",               "Score 90%+ average in Visual Communication",             "🎨", 200, "Visual Communication"),
    Achievement("bus_90",            "Entrepreneur",           "Score 90%+ average in Business Management",              "💼", 200, "Business Management"),

    # ── Subject averages — A (80%) ────────────────────────────────────────────
    Achievement("math_80",           "Number Cruncher",        "Score 80%+ average in Mathematics",                      "🔢", 100, "Mathematics"),
    Achievement("eng_80",            "Storyteller",            "Score 80%+ average in English",                          "✍️", 100, "English"),
    Achievement("sci_80",            "Lab Rat",                "Score 80%+ average in Science",                          "⚗️", 100, "Science"),
    Achievement("hum_80",            "Geographer",             "Score 80%+ average in Humanities",                       "🗺️", 100, "Humanities"),
    Achievement("rels_80",           "Spiritual",              "Score 80%+ average in Religion & Society",               "🙏", 100, "Religion & Society"),
    Achievement("hepe_80",           "Fit",                    "Score 80%+ average in Health & PE",                      "💪", 100, "Health & PE"),
    Achievement("ital_80",           "Italiano",               "Score 80%+ average in Italian",                          "🍕", 100, "Italian"),
    Achievement("viscom_80",         "Artist",                 "Score 80%+ average in Visual Communication",             "🖌️", 100, "Visual Communication"),
    Achievement("bus_80",            "Business Minded",        "Score 80%+ average in Business Management",              "📊", 100, "Business Management"),

    # ── Improvement streaks ───────────────────────────────────────────────────
    Achievement("improvement_5",     "Better Every Time",      "Improve 5%+ from one test to the next",                  "📈", 60),
    Achievement("improvement_10",    "10% Jump",               "Improve 10%+ from one test to the next",                 "🚀", 120),
    Achievement("improvement_20",    "20% Jump",               "Improve 20%+ from one test to the next",                 "🔥", 250),
    Achievement("improvement_30",    "Comeback Kid",           "Improve 30%+ from one test to the next",                 "💪", 400),
    Achievement("b_to_a",            "Level Up",               "Improve from a B to an A in any subject",                "⬆️", 150),
    Achievement("c_to_a",            "Two Grades Up",          "Improve from a C to an A in any subject",                "🎯", 300),
    Achievement("d_to_pass",         "Never Say Die",          "Improve from a D to a C or above",                       "💫", 200),

    # ── Assessment streaks ────────────────────────────────────────────────────
    Achievement("streak_3",          "Hat Trick",              "Get A+ on 3 assessments in a row",                       "🎩", 150),
    Achievement("streak_5",          "On Fire",                "Get A+ on 5 assessments in a row",                       "🔥", 300),
    Achievement("streak_10",         "Unstoppable",            "Get A+ on 10 assessments in a row",                      "⚡", 500),
    Achievement("a_streak_5",        "Consistent",             "Get A or above on 5 assessments in a row",               "✨", 150),
    Achievement("a_streak_10",       "Reliable",               "Get A or above on 10 assessments in a row",              "🌟", 300),
    Achievement("no_drop",           "Steady",                 "Never drop below your opening grade in a subject",       "📊", 150),

    # ── Submission & effort ───────────────────────────────────────────────────
    Achievement("all_submitted",     "No Excuses",             "Submit every assessment on time",                        "✅", 100),
    Achievement("early_bird",        "Early Bird",             "Submit an assessment before the due date",               "🐦", 50),
    Achievement("ten_submitted",     "Diligent",               "Submit 10 assessments on time",                          "📬", 80),
    Achievement("twenty_submitted",  "Reliable Student",       "Submit 20 assessments on time",                          "📮", 120),
    Achievement("fifty_submitted",   "No Late Work",           "Submit 50 assessments on time",                          "🏅", 200),

    # ── Crate milestones ──────────────────────────────────────────────────────
    Achievement("golden_crate",      "Gold Rush",              "Open a Golden Crate (A+)",                               "🥇", 200),
    Achievement("open_5",            "Lucky",                  "Open 5 crates",                                          "📦", 60),
    Achievement("open_10",           "Crate Addict",           "Open 10 crates",                                         "📦", 100),
    Achievement("open_25",           "Collector",              "Open 25 crates",                                         "📦", 150),
    Achievement("open_50",           "Loot Master",            "Open 50 crates",                                         "🎰", 300),
    Achievement("open_100",          "Hoarder",                "Open 100 crates",                                        "🏰", 500),
    Achievement("all_crate_types",   "Full House",             "Open every type of crate",                               "🎲", 200),

    # ── Wardrobe & pet ────────────────────────────────────────────────────────
    Achievement("five_items",        "Getting Stylish",        "Collect 5 clothing items",                               "👔", 80),
    Achievement("ten_items",         "Wardrobe",               "Collect 10 clothing items",                              "🧳", 150),
    Achievement("all_items",         "Fashionista",            "Own every clothing item",                                 "👑", 500),
    Achievement("rare_item",         "Rare Find",              "Own a rare or better item",                              "💎", 100),
    Achievement("epic_item",         "Epic Find",              "Own an epic item",                                       "🌟", 200),
    Achievement("legendary_item",    "Legendary Find",         "Own a legendary item",                                   "👑", 400),
    Achievement("three_pets",        "Animal Lover",           "Unlock 3 pet species",                                   "🐾", 200),
    Achievement("all_pets",          "Pokémon Master",         "Unlock all pet species",                                  "🐉", 600),
    Achievement("dragon_unlocked",   "Here Be Dragons",        "Unlock the Dragon pet",                                  "🐲", 300),

    # ── Pet levels ────────────────────────────────────────────────────────────
    Achievement("level_5",           "Growing Up",             "Reach pet level 5",                                      "🌱", 30),
    Achievement("level_10",          "Rising Star",            "Reach pet level 10",                                     "⭐", 60),
    Achievement("level_20",          "First Evolution",        "Reach pet level 20 (pet evolves!)",                      "✨", 100),
    Achievement("level_30",          "Seasoned",               "Reach pet level 30",                                     "🌟", 150),
    Achievement("level_40",          "Expert",                 "Reach pet level 40",                                     "💫", 200),
    Achievement("level_50",          "Veteran",                "Reach pet level 50",                                     "🏆", 300),
    Achievement("level_60",          "Elite",                  "Reach pet level 60",                                     "💎", 350),
    Achievement("level_70",          "Master",                 "Reach pet level 70",                                     "👑", 400),
    Achievement("level_80",          "Grand Master",           "Reach pet level 80",                                     "🌠", 450),
    Achievement("level_90",          "Transcendent",           "Reach pet level 90",                                     "⚡", 500),
    Achievement("level_99",          "Legendary",              "Reach the max level 99!",                                "🔥", 1000),

    # ── Special / hidden ──────────────────────────────────────────────────────
    Achievement("top_of_class",      "Top of Class",           "Achieve 95%+ in any subject",                            "🏅", 250),
    Achievement("top_math",          "Top of Maths",           "Score 95%+ average in Mathematics",                      "📐", 300, "Mathematics"),
    Achievement("speed_learner",     "Speed Learner",          "Complete 5 assessments in a week",                       "⚡", 150, hidden=True),
    Achievement("all_time_high",     "Personal Best",          "Break your highest ever score in a subject",              "🎯", 100),
    Achievement("perfect_year",      "Year of Excellence",     "Maintain A average all year",                             "🏆", 400),
    Achievement("multi_subject_90",  "Renaissance Student",    "Score 90%+ in 3 or more subjects simultaneously",        "🎓", 350),
    Achievement("multi_subject_80",  "Well Rounded",           "Score 80%+ in 5 or more subjects simultaneously",        "🌍", 200),
    Achievement("xp_500",            "XP Grinder",             "Earn 500 total XP",                                      "⚡", 0),
    Achievement("xp_1000",           "XP Hunter",              "Earn 1000 total XP",                                     "💫", 0),
    Achievement("xp_5000",           "XP Legend",              "Earn 5000 total XP",                                     "🌟", 0),
    Achievement("ten_achievements",  "Achievement Hunter",     "Unlock 10 achievements",                                 "🏅", 100),
    Achievement("twenty_five_ach",   "Overachiever",           "Unlock 25 achievements",                                 "🏆", 200),
    Achievement("fifty_ach",         "Completionist",          "Unlock 50 achievements",                                 "👑", 400),
    Achievement("all_ach",           "100% Completion",        "Unlock every achievement",                               "💎", 1000, hidden=True),
    Achievement("night_owl",         "Night Owl",              "Have an assessment due after 10pm",                      "🦉", 30, hidden=True),
    Achievement("close_call",        "Squeaky Clean",          "Pass with exactly 60%",                                  "😅", 50, hidden=True),
    Achievement("five_in_one_sub",   "Deep Diver",             "Have 5+ graded items in one subject",                    "🤿", 80),
    Achievement("all_subjects_done", "No Subject Left Behind", "Have at least one grade in every subject",               "📚", 150),
    Achievement("b_avg",             "B Student",              "Achieve B average (70%+) in any subject",                "📘", 60),
    Achievement("a_avg",             "A Student",              "Achieve A average (80%+) in any subject",                "📗", 100),
    Achievement("a_plus_avg",        "A+ Student",             "Achieve A+ average (90%+) in any subject",               "📕", 200),
    Achievement("five_a_plus_subj",  "Multi-Subject Star",     "Achieve A+ average in 5 or more subjects",               "🌟", 400),
]

ACHIEVEMENT_MAP = {a.id: a for a in ALL_ACHIEVEMENTS}


def detect_achievements(data, pet_data, username: str) -> List[Achievement]:
    """Detect newly earned achievements and return them."""
    import datetime
    earned = set(pet_data.achievements)
    new_achievements = []

    def earn(aid: str):
        if aid not in earned and aid in ACHIEVEMENT_MAP:
            earned.add(aid)
            new_achievements.append(ACHIEVEMENT_MAP[aid])

    if not data:
        earn("first_login")
        return new_achievements

    yr = datetime.datetime.now().year
    subjects = data.subjects_by_year.get(yr, [])

    earn("first_login")

    # ── Assessment counts ─────────────────────────────────────────────────────
    total_graded = sum(1 for s in subjects for a in s.assignments if a.grade_raw is not None)
    if total_graded >= 1:   earn("first_grade")
    if total_graded >= 10:  earn("ten_assessments")
    if total_graded >= 20:  earn("twenty_assessments")
    if total_graded >= 30:  earn("thirty_assessments")
    if total_graded >= 50:  earn("fifty_assessments")
    if total_graded >= 75:  earn("seventy_five_ass")
    if total_graded >= 100: earn("hundred_ass")

    # ── Submission counts ─────────────────────────────────────────────────────
    submitted_count = sum(
        1 for s in subjects for a in s.assignments
        if a.status and ("submitted" in a.status.lower() or "reviewed" in a.status.lower())
    )
    if submitted_count >= 1:  earn("early_bird")
    if submitted_count >= 10: earn("ten_submitted")
    if submitted_count >= 20: earn("twenty_submitted")
    if submitted_count >= 50: earn("fifty_submitted")

    all_sub = all(
        a.status and ("submitted" in a.status.lower() or "reviewed" in a.status.lower())
        for s in subjects for a in s.assignments if a.due_date
    )
    if all_sub and total_graded > 0:
        earn("all_submitted")

    # ── A+ counts across all assignments ─────────────────────────────────────
    a_plus_count = sum(1 for s in subjects for a in s.assignments
                       if a.grade_raw is not None and a.grade_raw >= 90)
    perfect_count = sum(1 for s in subjects for a in s.assignments
                        if a.grade_raw is not None and a.grade_raw >= 99.9)
    if a_plus_count >= 1:  earn("first_a_plus")
    if a_plus_count >= 5:  earn("five_a_plus")
    if a_plus_count >= 10: earn("ten_a_plus")
    if a_plus_count >= 20: earn("twenty_a_plus")
    if a_plus_count >= 50: earn("fifty_a_plus")
    if perfect_count >= 1: earn("first_perfect")
    if perfect_count >= 3: earn("three_perfect")

    # ── Subject averages ──────────────────────────────────────────────────────
    a_plus_subjects = 0
    a_subjects      = 0
    subj_above_90   = 0
    subj_above_80   = 0
    subj_above_70   = 0
    subj_above_60   = 0
    all_above_d     = True
    subjects_with_grade = [s for s in subjects if s.grade_raw is not None]

    for subj in subjects_with_grade:
        g = subj.grade_raw
        n = subj.name

        if g >= 90:
            earn("a_plus_avg"); earn("a_avg"); earn("b_avg")
            a_plus_subjects += 1; a_subjects += 1
            subj_above_90 += 1; subj_above_80 += 1; subj_above_70 += 1; subj_above_60 += 1
        elif g >= 80:
            earn("a_avg"); earn("b_avg")
            a_subjects += 1; subj_above_80 += 1; subj_above_70 += 1; subj_above_60 += 1
        elif g >= 70:
            earn("b_avg"); subj_above_70 += 1; subj_above_60 += 1
        elif g >= 60:
            subj_above_60 += 1
        if g < 40: all_above_d = False
        if g >= 95: earn("top_of_class")

        # Subject-specific (for subjects we have defined achievements)
        SM = {
            "Mathematics":          ("math_90", "math_80", "top_math"),
            "English":              ("eng_90",  "eng_80",  None),
            "Science":              ("sci_90",  "sci_80",  None),
            "Humanities":           ("hum_90",  "hum_80",  None),
            "Religion & Society":   ("rels_90", "rels_80", None),
            "Health & PE":          ("hepe_90", "hepe_90", None),
            "Italian":              ("ital_90", "ital_80", None),
            "Visual Communication": ("viscom_90","viscom_80",None),
            "Business Management":  ("bus_90",  "bus_80",  None),
        }
        if n in SM:
            a90, a80, a95 = SM[n]
            if a90 and g >= 90: earn(a90)
            if a80 and g >= 80: earn(a80)
            if a95 and g >= 95: earn(a95)

    if a_plus_subjects >= 5:       earn("five_a_plus_subj")
    if subj_above_90 >= 3:         earn("multi_subject_90")
    if subj_above_80 >= 5:         earn("multi_subject_80")
    if subjects_with_grade:
        if subj_above_60 == len(subjects_with_grade): earn("all_above_60")
        if subj_above_70 == len(subjects_with_grade): earn("all_above_70")
        if subj_above_80 == len(subjects_with_grade): earn("all_above_80")
        if subj_above_90 == len(subjects_with_grade): earn("all_above_90")
    if all_above_d and total_graded > 0: earn("no_d_ug"); earn("no_ug_ever")

    # ── Improvement checks ────────────────────────────────────────────────────
    for subj in subjects:
        graded = sorted(
            [a for a in subj.assignments if a.grade_raw is not None],
            key=lambda a: a.due_date or ""
        )
        for i in range(1, len(graded)):
            diff = graded[i].grade_raw - graded[i-1].grade_raw
            if diff >= 5:  earn("improvement_5")
            if diff >= 10: earn("improvement_10")
            if diff >= 20: earn("improvement_20")
            if diff >= 30: earn("improvement_30")

        if subj.grade_raw:
            prev = sum(a.grade_raw for a in graded[:-1]) / max(1, len(graded)-1) if len(graded) > 1 else None
            curr = subj.grade_raw
            if prev:
                if prev < 70 <= curr: earn("b_to_a")
                if prev < 60 <= curr and curr >= 80: earn("c_to_a")
                if prev < 40 <= curr and curr >= 60: earn("d_to_pass")

        # Streaks
        streak_ap = 0; streak_a = 0
        for a in reversed(graded):
            if a.grade_raw >= 90: streak_ap += 1
            else: break
        for a in reversed(graded):
            if a.grade_raw >= 80: streak_a += 1
            else: break
        if streak_ap >= 3:  earn("streak_3")
        if streak_ap >= 5:  earn("streak_5")
        if streak_ap >= 10: earn("streak_10")
        if streak_a >= 5:   earn("a_streak_5")
        if streak_a >= 10:  earn("a_streak_10")

        # Deep diver
        if len(graded) >= 5: earn("five_in_one_sub")

    # ── All subjects have a grade ─────────────────────────────────────────────
    if subjects and all(s.grade_raw is not None for s in subjects):
        earn("all_subjects_done")

    # ── Pet level achievements ────────────────────────────────────────────────
    lv = pet_data.level
    for thresh, aid in [(5,"level_5"),(10,"level_10"),(20,"level_20"),
                        (30,"level_30"),(40,"level_40"),(50,"level_50"),
                        (60,"level_60"),(70,"level_70"),(80,"level_80"),
                        (90,"level_90"),(99,"level_99")]:
        if lv >= thresh: earn(aid)

    # ── Pet / crate / wardrobe ────────────────────────────────────────────────
    if pet_data.crates_opened >= 1:   earn("first_crate")
    if pet_data.crates_opened >= 5:   earn("open_5")
    if pet_data.crates_opened >= 10:  earn("open_10")
    if pet_data.crates_opened >= 25:  earn("open_25")
    if pet_data.crates_opened >= 50:  earn("open_50")
    if pet_data.crates_opened >= 100: earn("open_100")
    if pet_data.equipped_item:        earn("dressed_up")
    if len(pet_data.unlocked_pets) >= 2: earn("new_pet")
    if len(pet_data.unlocked_pets) >= 3: earn("three_pets")
    if len(pet_data.unlocked_pets) >= len(PET_SPECIES): earn("all_pets")
    if "dragon" in pet_data.unlocked_pets: earn("dragon_unlocked")

    # Wardrobe
    from data.pet_models import CLOTHING, RARITY_COLOURS
    inv = pet_data.inventory
    if len(inv) >= 5:  earn("five_items")
    if len(inv) >= 10: earn("ten_items")
    if len(inv) >= len(CLOTHING): earn("all_items")
    rarities = {CLOTHING[k]["rarity"] for k in inv if k in CLOTHING}
    if "rare" in rarities or "epic" in rarities or "legendary" in rarities:
        earn("rare_item")
    if "epic" in rarities or "legendary" in rarities:
        earn("epic_item")
    if "legendary" in rarities:
        earn("legendary_item")

    # ── Achievement count achievements ────────────────────────────────────────
    total_earned = len(earned)
    if total_earned >= 10: earn("ten_achievements")
    if total_earned >= 25: earn("twenty_five_ach")
    if total_earned >= 50: earn("fifty_ach")
    if total_earned >= len(ALL_ACHIEVEMENTS) - 1: earn("all_ach")

    # ── XP milestones (track via pet total xp) ───────────────────────────────
    total_xp = pet_data.xp + pet_data.level * 150  # approximate total
    if total_xp >= 500:  earn("xp_500")
    if total_xp >= 1000: earn("xp_1000")
    if total_xp >= 5000: earn("xp_5000")

    return new_achievements


# Avoid circular import
try:
    from data.pet_models import PET_SPECIES
except ImportError:
    PET_SPECIES = {}

# ── Special chest achievements (non-academic) ─────────────────────────────────
CHEST_ACHIEVEMENTS = [
    Achievement("open_10_crates",    "Crate Enthusiast",   "Open 10 crates total",                   "📦", 100,  hidden=False),
    Achievement("open_25_crates",    "Unboxer",            "Open 25 crates",                          "🎁", 150,  hidden=False),
    Achievement("open_50_crates",    "Addicted",           "Open 50 crates",                          "📬", 200,  hidden=False),
    Achievement("open_100_crates",   "Hoarder",            "Open 100 crates",                         "🏭", 350,  hidden=False),
    Achievement("get_epic",          "Epic Find",          "Receive an Epic item from a crate",        "💜", 120,  hidden=False),
    Achievement("get_legendary",     "Legendary Pull",     "Receive a Legendary item from a crate",   "🌟", 200,  hidden=False),
    Achievement("get_mythic",        "Mythic Pull",        "Receive a Mythic item from a crate",      "🔥", 400,  hidden=True),
    Achievement("get_divine",        "Divine Touch",       "Receive a Divine item from a crate",      "✨", 800,  hidden=True),
    Achievement("all_crate_types",   "Collector",          "Open every type of crate",                "🗝️",  300,  hidden=False),
    Achievement("equip_legendary",   "Dressed to Kill",    "Equip a Legendary accessory",             "👑", 150,  hidden=False),
    Achievement("equip_mythic",      "Beyond Rare",        "Equip a Mythic accessory",                "🔥", 300,  hidden=True),
    Achievement("equip_divine",      "God Tier",           "Equip a Divine accessory",                "✨", 600,  hidden=True),
    Achievement("full_wardrobe",     "Fashion God",        "Own 20+ accessories",                     "👗", 250,  hidden=False),
    Achievement("all_pets",          "Zookeeper",          "Unlock every pet",                        "🦁", 500,  hidden=False),
    Achievement("mythic_beast",      "Mythic Tamer",       "Unlock a Mythic pet",                     "🌑", 400,  hidden=True),
    Achievement("divine_beast",      "God Tamer",          "Unlock the God Beast",                    "👁️",  800,  hidden=True),
    # Special chests granted by these achievements
    Achievement("chest_1",           "First Chest",        "Open 10 crates (grants Mythic Chest!)",   "🎁", 50,   hidden=False),
    Achievement("chest_2",           "Dedicated Opener",   "Open 50 crates (grants Mythic Chest!)",   "📦", 50,   hidden=False),
    Achievement("chest_3",           "Divine Seeker",      "Unlock a Mythic item (grants Divine Chest!)", "✨", 50, hidden=True),
]

# Achievements that grant special chests
CHEST_GRANTS = {
    "chest_1": ("mythic_chest", 1),
    "chest_2": ("mythic_chest", 2),
    "chest_3": ("divine_chest", 1),
    "open_100_crates": ("mythic_chest", 1),
    "get_divine": ("divine_chest", 1),
    "all_pets": ("mythic_chest", 3),
}

ALL_ACHIEVEMENTS = ALL_ACHIEVEMENTS + CHEST_ACHIEVEMENTS
