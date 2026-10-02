"""English text -> English written in Arabic script (forward transliterator)."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path

from . import tables as T
from .lexicon import align_vowels, is_vowel, pronounce

log = logging.getLogger("arabglish")
_DATA = Path(__file__).parent / "data"

_VOICED = {"B", "D", "G", "JH", "L", "M", "N", "R", "W", "Y", "Z", "ZH", "DH", "NG", "V"}
_TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*|\d[\d,]*(?:\.\d+)?|\s+|.", re.S)
DENSITIES = ("full", "medial", "vowels", "none")


@dataclass(frozen=True)
class Options:
    density: str = "full"        # full | medial | vowels | none
    v: str = "f"                 # f | b | context  (v is a voiced f; b is the alternative)
    g: str = "ghain"             # ghain | jeem
    persian: bool = False        # use the Persian letters seen in the Atlas text
    digits: str = "indic"        # indic | latin | spoken
    use_attested: bool = False   # prefer forms recorded in specimens over computed forms
    the_before_vowel: bool = False  # True: the -> ذِي before a vowel sound (phonemic)

    def profile(self) -> T.Profile:
        return T.make_profile(v=self.v, persian=self.persian, g=self.g)


@dataclass
class Seg:
    c: str
    kind: str          # cons | mater | glide | seat
    mark: str = ""
    unit: int = 0


def apply_density(arabic: str, density: str) -> str:
    if density == "full":
        return arabic
    if density == "none":
        return "".join(ch for ch in arabic if not T.is_mark(ch))
    if density == "vowels":
        return arabic.replace(T.SUKUN, "")
    if density == "medial":
        return re.sub(T.SUKUN + r"(?=[^ء-ي٠-٩]|$)", "", arabic)
    raise ValueError(f"unknown density {density!r}")


def _ah_colour(letters: str, stress: int, prev: str | None, nxt: str | None, final: bool, before_final_m: bool = False):
    """Colour of AH from the vowel letter(s) of the spelling (hybrid policy)."""
    if not letters:
        return T.FATHA, ""
    if letters[:2] in ("io", "ia"):
        return T.FATHA, ""                # social, nation: the vowel pair is read as a schwa
    c = letters[0]
    if c == "e" and before_final_m:
        return T.FATHA, ""                # word-final -em (system) is fatha in the typed passage
    if c in "eiy":
        return T.KASRA, ""
    if c == "o":
        return (T.DAMMA, T.WAW) if nxt == "JH" else (T.DAMMA, "")
    if c == "a":
        if stress == 0 and final and prev != "ER":
            return T.FATHA, T.ALEF
        return T.FATHA, ""
    return T.FATHA, ""


def _er_mark(letters: str) -> str:
    if not letters:
        return T.FATHA
    c = letters[0]
    if c == "o":
        return T.DAMMA
    if c in "eiy":
        return T.KASRA
    return T.FATHA


def build_segments(word: str, phones: list[str], profile: T.Profile) -> list[Seg]:
    align = align_vowels(word, phones)
    segs: list[Seg] = []
    unit = 0
    lw = word.lower()
    drop_schwa_ism = bool(re.search(r"isms?$", lw))
    for i, ph in enumerate(phones):
        base = re.sub(r"\d", "", ph)
        stress = int(re.sub(r"\D", "", ph) or 0)
        prev = re.sub(r"\d", "", phones[i - 1]) if i else None
        nxt = re.sub(r"\d", "", phones[i + 1]) if i + 1 < len(phones) else None
        if base not in T.VOWEL_NAMES:
            letters = profile.consonants.get(base)
            if base == "G" and prev == "NG":
                continue                          # English = ng+g: the ghain of NG already writes it
            if base == "V" and profile.v_policy == "context" and not profile.persian:
                nv = (nxt in _VOICED or (nxt and nxt in T.VOWEL_NAMES)) or (prev in _VOICED or (prev and prev in T.VOWEL_NAMES))
                letters = T.BEH if nv else T.FEH
            if not letters:
                log.warning("no letter for phoneme %s in %r", base, word)
                continue
            unit += 1
            for ch in letters:
                segs.append(Seg(ch, "cons", "", unit))
            continue
        # vowels
        if base == "AH" and stress == 0 and drop_schwa_ism and nxt == "M" and i + 2 >= len(phones):
            continue
        mark, mater, kind = T.VOWELS[base]
        letters, open_syl = align.get(i, ("", False))
        final = i == len(phones) - 1
        initial = not segs
        if base == "AH":
            mark, mater = _ah_colour(letters, stress, prev, nxt, final, nxt == "M" and i + 2 == len(phones))
            if letters.startswith("o") and stress >= 1:
                mark, mater = T.DAMMA, T.WAW
        elif base == "ER":
            mark = T.FATHA if stress == 0 else _er_mark(letters)   # unstressed er is fatha in every attested form
            if stress == 0 and re.match(r"(inter|enter)", lw) and letters[:1] == "e":
                mark = T.KASRA                    # the prefix inter- keeps kasra (intersects, internal)
            if stress and letters.startswith("ea"):
                mark = T.FATHA                    # learn, heard, search
        elif base == "UH" and letters in ("oo", "ou") and not mater:
            mater = T.WAW                         # written double o keeps its waw (book, good, foot)
        elif base in ("AA", "AO") and letters.startswith("o"):
            mark, mater = T.DAMMA, T.WAW          # spelling o -> ُو (Rollins, on, psychology)
        elif base == "AE" and stress >= 1 and not initial:
            mater = T.ALEF
        elif base in ("EH", "IH") and stress >= 1 and open_syl and letters[:1] in ("e", "i"):
            mater = T.YEH                         # open-syllable e/i -> ِي (Helen, cinema)
        elif base in ("IY", "UW") and stress == 0 and not any(s.kind in ("mater", "seat") or s.mark in (T.FATHA, T.DAMMA, T.KASRA) for s in segs):
            mater = ""                            # unstressed first vowel is written short (re-, u-topia)
        unit += 1
        _place_vowel(segs, base, mark, mater, kind, unit)
    return segs


def _place_vowel(segs: list[Seg], base: str, mark: str, mater: str, kind: str, unit: int) -> None:
    host_ok = bool(segs) and (segs[-1].kind in ("cons",) or (segs[-1].kind in ("mater", "glide") and segs[-1].c == T.YEH)
                              or (base in ("ER", "AH") and segs[-1].kind == "glide" and segs[-1].c == T.WAW
                                  and len(segs) > 1 and segs[-2].c in (T.ALEF, T.MADDA)))  # flower, power, tower
    if host_ok:
        if segs[-1].kind in ("mater", "glide"):
            segs[-1].kind = "cons"  # a preceding ي acts as a glide hosting the next vowel
        segs[-1].mark = mark
        rest = mater
    else:
        initial = not segs
        if initial and mark == T.FATHA and mater.startswith(T.ALEF):
            segs.append(Seg(T.MADDA, "seat", "", unit))
            rest = mater[1:]
        else:
            seat = T.HAMZA_ALEF_BELOW if mark == T.KASRA else T.HAMZA_ALEF
            segs.append(Seg(seat, "seat", mark, unit))
            rest = mater[1:] if mater.startswith(T.ALEF) and not initial else mater
    if kind == "rhotic":
        segs.append(Seg(T.REH, "cons", "", unit))
        return
    for j, ch in enumerate(rest):
        k = "mater"
        if kind == "glide" and ch in (T.YEH, T.WAW) and j == len(rest) - 1:
            k = "glide"
        segs.append(Seg(ch, k, "", unit))


def render_segments(segs: list[Seg]) -> str:
    out = list(segs)
    for j, s in enumerate(out):
        if s.mark or s.kind in ("mater", "seat"):
            continue
        s.mark = T.SUKUN
    return "".join(s.c + s.mark for s in out)


def word_to_arabic_full(word: str, profile: T.Profile, phones: list[str] | None = None) -> str:
    if phones is None:
        phones, _ = pronounce(word)
    return render_segments(build_segments(word, phones, profile))


# ---- attested forms -------------------------------------------------------

@lru_cache(maxsize=1)
def attested() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    p = _DATA / "attested.tsv"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            en, ar, src = line.split("\t")[:3]
            out.setdefault(en, []).append((ar, src))
    return out


# ---- numbers ---------------------------------------------------------------

_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + number_words(n % 100))
    if n < 1_000_000:
        return number_words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + number_words(n % 1000))
    return str(n)


# ---- text ------------------------------------------------------------------

def _starts_with_vowel_sound(word: str | None) -> bool:
    if not word:
        return False
    ph, _ = pronounce(word)
    return bool(ph) and is_vowel(ph[0])


def transliterate_text(text: str, opts: Options | None = None) -> str:
    opts = opts or Options()
    profile = opts.profile()
    toks = _TOKEN.findall(text)
    words = [t for t in toks if re.match(r"[A-Za-z]", t)]
    wi = 0
    out: list[str] = []
    for ti, t in enumerate(toks):
        if t in ("'", "\u2019") and ti and toks[ti - 1].lower().endswith("s") and re.match(r"[A-Za-z]", toks[ti - 1]) \
                and not (ti + 1 < len(toks) and re.match(r"[A-Za-z]", toks[ti + 1])):
            continue  # possessive apostrophe after s is silent (Rollins')
        if re.match(r"[A-Za-z]", t):
            nxt = words[wi + 1] if wi + 1 < len(words) else None
            wi += 1
            out.append(transliterate_word(t, opts, profile, next_word=nxt))
        elif re.match(r"\d", t):
            digits = t.replace(",", "")
            if opts.digits == "latin":
                out.append(t)
            elif opts.digits == "spoken" and digits.isdigit():
                out.append(transliterate_text(number_words(int(digits)), replace(opts, digits="latin")))
            else:
                out.append(t.translate(T.ARABIC_INDIC))
        else:
            out.append(T.PUNCT.get(t, t))
    return "".join(out)


def transliterate_word(word: str, opts: Options | None = None, profile: T.Profile | None = None,
                       next_word: str | None = None) -> str:
    opts = opts or Options()
    profile = profile or opts.profile()
    lw = word.lower().replace("’", "'")
    form = None
    if opts.use_attested and lw in attested():
        form = attested()[lw][0][0]
    elif lw == "the" and opts.the_before_vowel and _starts_with_vowel_sound(next_word):
        form = T.THAL + T.KASRA + T.YEH
    elif lw in T.COMMON_WORDS:
        form = T.COMMON_WORDS[lw]
    if form is None:
        form = word_to_arabic_full(word, profile)
    return apply_density(form, opts.density)
