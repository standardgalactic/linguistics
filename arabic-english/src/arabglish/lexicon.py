"""Pronunciation lookup: overrides, CMU dictionary, possessives, then g2p fallback."""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

from .g2p import g2p

log = logging.getLogger("arabglish")
_DATA = Path(__file__).parent / "data"
_VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}


@lru_cache(maxsize=1)
def _cmu() -> dict:
    import cmudict
    return cmudict.dict()


@lru_cache(maxsize=1)
def _overrides() -> dict:
    out = {}
    p = _DATA / "pron_overrides.tsv"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            w, ph = line.split("\t", 1)
            out[w.strip().lower()] = ph.split()
    return out


def is_vowel(ph: str) -> bool:
    return re.sub(r"\d", "", ph) in _VOWELS


def pronounce(word: str) -> tuple[list[str], str]:
    """Return (phonemes, source) where source is override | cmu | possessive | g2p."""
    w = word.lower().replace("’", "'")
    ov = _overrides()
    if w in ov:
        return list(ov[w]), "override"
    d = _cmu()
    if w in d:
        return list(d[w][0]), "cmu"
    base = w.rstrip("'")
    if base.endswith("'s") or w.endswith("s'"):
        stem = re.sub(r"'s$|s'$", "", w) if w.endswith("'s") else base[:-1] if base.endswith("s") else base
        stem = stem or base
        if stem in ov or stem in d:
            ph, _ = pronounce(stem)
            last = re.sub(r"\d", "", ph[-1])
            if last in ("S", "Z", "SH", "ZH", "CH", "JH"):
                return ph + ["IH0", "Z"], "possessive"
            return ph + (["S"] if last in ("P", "T", "K", "F", "TH") else ["Z"]), "possessive"
    if base in d:
        return list(d[base][0]), "cmu"
    log.warning("no dictionary entry for %r, using spelling fallback", word)
    return g2p(w), "g2p"


def _clean(word: str) -> str:
    w = re.sub(r"[^a-z]", "", word.lower())
    if len(w) > 2 and re.search(r"[^aeiou]e$", w) and re.search(r"[aeiouy]", w[:-1]):
        w = w[:-1]
    return w


def vowel_letter_groups(word: str) -> list[str]:
    """Vowel-letter groups of the spelling, used to colour vowels from the spelling."""
    return [m.group(0) for m in re.finditer(r"qu|[aeiou]+y?|y", _clean(word))]


def align_vowels(word: str, phones: list[str]) -> dict[int, tuple[str, bool]]:
    """Map vowel phoneme index -> (vowel letters, open_syllable) when counts agree.

    open_syllable is true for a vowel letter followed by one consonant and another vowel
    letter (he-len, ci-nema), which the specimens write with a long ي.
    """
    w = _clean(word)
    spans = [(m.group(0), m.end()) for m in re.finditer(r"qu|[aeiou]+y?|y", w)]
    vidx = [i for i, p in enumerate(phones) if is_vowel(p)]
    if len(spans) != len(vidx):
        return {}
    out = {}
    for i, (g, end) in zip(vidx, spans):
        out[i] = (g, bool(re.match(r"[^aeiouy][aeiouy]", w[end:])))
    return out
