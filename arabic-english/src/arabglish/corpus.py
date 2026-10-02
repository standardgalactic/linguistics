"""Inventory statistics for Arabic-script English specimens."""
from __future__ import annotations

import unicodedata
from collections import Counter

from . import tables as T


def inventory(text: str) -> dict:
    letters, marks, other = Counter(), Counter(), Counter()
    for ch in text:
        o = ord(ch)
        if T.is_mark(ch):
            marks[ch] += 1
        elif 0x0600 <= o <= 0x06FF:
            (letters if ch.isalpha() else other)[ch] += 1
    return {"letters": letters, "marks": marks, "other": other,
            "extended": {c: n for c, n in letters.items() if not T.is_core_letter(c)}}


def describe(ch: str) -> str:
    return unicodedata.name(ch, f"U+{ord(ch):04X}").title()
