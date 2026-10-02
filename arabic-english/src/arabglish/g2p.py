"""Small spelling-to-ARPABET fallback for words missing from the CMU dictionary.

Deliberately simple. It exists so the transliterator never fails on names and coinages
(Taggart, psychocinema); every use is logged by the caller so weak spots stay visible.
"""
from __future__ import annotations

import re

_VOWEL_LETTERS = "aeiouy"

# Ordered longest-first. Value is a list of ARPABET symbols (stress digits added later).
_MULTI = [
    ("tch", ["CH"]), ("sch", ["S", "K"]), ("dge", ["JH"]), ("igh", ["AY"]),
    ("ph", ["F"]), ("sh", ["SH"]), ("ch", ["CH"]), ("th", ["TH"]), ("ck", ["K"]),
    ("ng", ["NG"]), ("qu", ["K", "W"]), ("wh", ["W"]), ("gh", []),
    ("ee", ["IY"]), ("ea", ["IY"]), ("oo", ["UW"]), ("ou", ["AW"]), ("ow", ["OW"]),
    ("oi", ["OY"]), ("oy", ["OY"]), ("ai", ["EY"]), ("ay", ["EY"]), ("au", ["AO"]),
    ("aw", ["AO"]), ("ie", ["IY"]), ("ue", ["UW"]), ("ew", ["UW"]),
    ("tion", ["SH", "AH0", "N"]), ("sion", ["ZH", "AH0", "N"]),
]
_SINGLE = {
    "a": ["AE"], "e": ["EH"], "i": ["IH"], "o": ["AA"], "u": ["AH"],
    "b": ["B"], "d": ["D"], "f": ["F"], "h": ["HH"], "j": ["JH"], "k": ["K"],
    "l": ["L"], "m": ["M"], "n": ["N"], "p": ["P"], "q": ["K"], "r": ["R"],
    "s": ["S"], "t": ["T"], "v": ["V"], "w": ["W"], "x": ["K", "S"], "z": ["Z"],
}
_LONG = {"a": "EY", "e": "IY", "i": "AY", "o": "OW", "u": "UW"}


def g2p(word: str) -> list[str]:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return []
    out: list[str] = []
    # magic-e: vowel + consonant + final e lengthens the vowel
    magic = bool(re.search(r"[aeiou][^aeiouy]e$", w)) and len(w) > 3
    last_vowel_idx = None
    i = 0
    while i < len(w):
        matched = False
        for pat, ph in _MULTI:
            if w.startswith(pat, i):
                if pat in ("tion", "sion") and i == 0:
                    continue
                out.extend(ph)
                i += len(pat)
                matched = True
                break
        if matched:
            continue
        c = w[i]
        if i == 0 and w[:2] == "kn":
            i += 1
            continue
        if i == 0 and w[:2] == "wr":
            i += 1
            continue
        if c == "c":
            out.append("S" if i + 1 < len(w) and w[i + 1] in "eiy" else "K")
        elif c == "g":
            out.append("JH" if i + 1 < len(w) and w[i + 1] in "eiy" else "G")
        elif c == "y":
            if i == 0:
                out.append("Y")
            else:
                out.append("IY" if i == len(w) - 1 else "IH")
        elif c in _SINGLE:
            if c in "aeiou" and i == len(w) - 1 and c == "e" and len(w) > 2:
                pass  # silent final e
            else:
                out.extend(_SINGLE[c])
        i += 1
    if magic:
        for j in range(len(out) - 1, -1, -1):
            sym = out[j]
            if sym in ("AE", "EH", "IH", "AA", "AH"):
                letter = {"AE": "a", "EH": "e", "IH": "i", "AA": "o", "AH": "u"}[sym]
                out[j] = _LONG[letter]
                break
    # assign primary stress to the first vowel, 0 to others
    vowels = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}
    seen = False
    res = []
    for sym in out:
        base = re.sub(r"\d", "", sym)
        if base in vowels:
            if re.search(r"\d", sym):
                res.append(sym)
            else:
                res.append(base + ("1" if not seen else "0"))
            seen = True
        else:
            res.append(sym)
    return res
