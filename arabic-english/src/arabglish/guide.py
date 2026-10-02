"""Latin respelling used as the third row of a teaching glossary (a reading aid, not part of the notation)."""
from __future__ import annotations

import re

_C = {"DH": "dh", "TH": "th", "SH": "sh", "CH": "ch", "JH": "j", "NG": "ng", "ZH": "zh", "HH": "h"}
_V = {"AA": "aa", "AE": "a", "AH": "u", "AO": "aw", "AW": "ow", "AY": "ay", "EH": "e", "ER": "er",
      "EY": "ey", "IH": "i", "IY": "ee", "OW": "oh", "OY": "oy", "UH": "u", "UW": "oo"}


def respell(phones: list[str]) -> str:
    out = []
    for ph in phones:
        base = re.sub(r"\d", "", ph)
        out.append(_V.get(base) or _C.get(base) or base.lower())
    return "".join(out)
