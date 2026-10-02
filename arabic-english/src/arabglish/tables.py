"""Sound-to-letter tables for English written in standard Arabic script.

Every choice that the specimens do not settle is exposed as an option rather than
hard-coded. See monograph chapter "Evidence and Open Decisions".
"""
from __future__ import annotations

from dataclasses import dataclass

FATHA = "َ"
DAMMA = "ُ"
KASRA = "ِ"
SUKUN = "ْ"
MARKS = frozenset({FATHA, DAMMA, KASRA, SUKUN})

ALEF, BEH, TEH, THEH, JEEM, DAL, THAL, REH, ZAIN = "ا", "ب", "ت", "ث", "ج", "د", "ذ", "ر", "ز"
GHAIN = "غ"  # proposed by the author for hard /g/; JEEM is the alternative seen in generated passages
SEEN, SHEEN, FEH, KAF, LAM, MEEM, NOON, HEH, WAW, YEH = "س", "ش", "ف", "ك", "ل", "م", "ن", "ه", "و", "ي"
HAMZA_ALEF, HAMZA_ALEF_BELOW, MADDA = "أ", "إ", "آ"

# ARPABET consonant -> letters (core profile: standard Arabic letters only).
CORE_CONSONANTS = {
    "P": BEH, "B": BEH, "T": TEH, "D": DAL, "K": KAF, "G": GHAIN,
    "F": FEH, "V": FEH,  # V is an option, see make_profile(v=...)
    "TH": THEH, "DH": THAL, "S": SEEN, "Z": ZAIN, "SH": SHEEN, "ZH": ZAIN,
    "HH": HEH, "CH": TEH + SHEEN, "JH": JEEM, "M": MEEM, "N": NOON,
    "NG": NOON + GHAIN, "L": LAM, "R": REH, "W": WAW, "Y": YEH,
}

# Persian-extended letters seen in early specimens (Atlas Shrugged text).
PERSIAN_CONSONANTS = {**CORE_CONSONANTS, "P": "پ", "V": "ڤ", "G": "گ", "CH": "چ",
                      "ZH": "ژ", "NG": NOON + "گ"}

# ARPABET vowel -> (short mark, mater letters, kind). kind: long | short | glide.
# glide means the trailing mater is a glide that takes sukoon (َايْ, َاوْ, ُويْ).
VOWELS = {
    "AA": (FATHA, ALEF, "long"),
    "AE": (FATHA, "", "short"),   # stressed AE gains ALEF in the engine (لَاك)
    "AH": (FATHA, "", "short"),   # colour chosen from spelling, see translit.py
    "AO": (DAMMA, WAW, "long"),
    "AW": (FATHA, ALEF + WAW, "glide"),
    "AY": (FATHA, ALEF + YEH, "glide"),
    "EH": (KASRA, "", "short"),
    "ER": (FATHA, REH, "rhotic"),
    "EY": (FATHA, YEH, "glide"),
    "IH": (KASRA, "", "short"),
    "IY": (KASRA, YEH, "long"),
    "OW": (DAMMA, WAW, "long"),
    "OY": (DAMMA, WAW + YEH, "glide"),
    "UH": (DAMMA, "", "short"),
    "UW": (DAMMA, WAW, "long"),
}
VOWEL_NAMES = frozenset(VOWELS)

# Fixed forms recorded in the Python COMMON_WORDS table plus forms attested in both
# the typed passage and the handwritten page. Marks shown in full density.
COMMON_WORDS = {
    "the": "ذَا", "this": "ذِسْ", "that": "ذَتْ", "of": "أُفْ", "and": "أَنْدْ",
    "in": "إِنْ", "to": "تُو", "a": "أَ", "is": "إِزْ",
    "she": "شِي", "it": "إِتْ", "its": "إِتْسْ", "as": "أَزْ", "into": "إِنْتُو",
    "with": "وِذْ", "are": "أَرْ",
}

PUNCT = {",": "،", ";": "؛", "?": "؟"}
ARABIC_INDIC = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


@dataclass(frozen=True)
class Profile:
    name: str
    consonants: dict
    v_policy: str = "f"  # b | f | context
    g_policy: str = "ghain"  # ghain | jeem

    @property
    def persian(self) -> bool:
        return self.consonants["P"] == "پ"


def make_profile(v: str = "f", persian: bool = False, g: str = "ghain") -> Profile:
    if v not in ("b", "f", "context"):
        raise ValueError("v must be 'b', 'f' or 'context'")
    if g not in ("ghain", "jeem"):
        raise ValueError("g must be 'ghain' or 'jeem'")
    base = dict(PERSIAN_CONSONANTS if persian else CORE_CONSONANTS)
    if g == "jeem" and not persian:
        base["G"] = JEEM
        base["NG"] = NOON + JEEM
    if not persian:  # the Persian profile keeps its own ڤ
        if v == "b":
            base["V"] = BEH
        elif v == "f":
            base["V"] = FEH
    name = ("persian" if persian else "core") + f"-v{v}-g{g}"
    return Profile(name=name, consonants=base, v_policy=v, g_policy=g)


# Inventory used by the linter. Core inventory is the basic Arabic letter block.
def is_core_letter(ch: str) -> bool:
    o = ord(ch)
    return 0x0621 <= o <= 0x064A


def is_mark(ch: str) -> bool:
    return 0x064B <= ord(ch) <= 0x0652

# Extended letters and their core replacements (used by the linter's fix mode).
EXTENDED_TO_CORE = {
    "پ": BEH, "ڤ": FEH, "گ": GHAIN, "چ": TEH + SUKUN + SHEEN, "ژ": ZAIN,
    "ک": KAF, "ی": YEH, "ى": YEH,
}
