"""Arabic-script English -> candidate English words.

The notation is many-to-one (b/p/v can share a letter, vowels are partly optional), so the
reader returns ranked candidates instead of a single answer, and reports how ambiguous it is.
"""
from __future__ import annotations

import pickle
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from . import tables as T
from .lexicon import _cmu
from .translit import Options, apply_density, attested, word_to_arabic_full

_CACHE = Path.home() / ".cache" / "arabglish"
_MATRES = set(T.ALEF + T.WAW + T.YEH + T.HAMZA_ALEF + T.HAMZA_ALEF_BELOW + T.MADDA)


def skeleton(s: str) -> str:
    return "".join(c for c in s if not T.is_mark(c))


def consonant_key(s: str) -> str:
    return "".join(c for c in skeleton(s) if c not in _MATRES)


def _freq(word: str) -> float:
    try:
        from wordfreq import zipf_frequency
        return zipf_frequency(word, "en")
    except Exception:
        return 0.0


@dataclass
class Candidate:
    word: str
    arabic: str
    tier: str     # attested | skeleton | consonants
    score: float


class Reader:
    def __init__(self, opts: Options | None = None, max_words: int | None = None, include_attested: bool = True):
        self.include_attested = include_attested
        self.opts = opts or Options()
        self.profile = self.opts.profile()
        self._by_skel: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._by_cons: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._attested: dict[str, str] = {}
        self._build(max_words)

    def _cache_path(self, max_words):
        return _CACHE / f"index-{self.profile.name}-{max_words}.pkl"

    def _build(self, max_words):
        p = self._cache_path(max_words)
        if p.exists():
            self._by_skel, self._by_cons = pickle.loads(p.read_bytes())
        else:
            d = _cmu()
            words = [w for w in d if re.fullmatch(r"[a-z]+", w)]
            words.sort(key=lambda w: -_freq(w))
            if max_words:
                words = words[:max_words]
            for w in words:
                seen = set()
                for pron in d[w]:
                    try:
                        full = word_to_arabic_full(w, self.profile, list(pron))
                    except Exception:
                        continue
                    if full in seen:
                        continue
                    seen.add(full)
                    self._by_skel[skeleton(full)].append((w, full))
                    self._by_cons[consonant_key(full)].append((w, full))
            _CACHE.mkdir(parents=True, exist_ok=True)
            p.write_bytes(pickle.dumps((dict(self._by_skel), dict(self._by_cons))))
        for en, ar in T.COMMON_WORDS.items():     # fixed spellings are part of the notation, not specimen evidence
            self._attested.setdefault(skeleton(ar), en)
        if self.include_attested:
            for en, forms in attested().items():
                for ar, _src in forms:
                    self._attested.setdefault(skeleton(ar), en)

    @staticmethod
    def _marks_compatible(inp: str, cand: str) -> bool:
        a = [(c, "") for c in inp if not T.is_mark(c)]
        # collect marks per letter index
        def per_letter(s):
            out = []
            for ch in s:
                if T.is_mark(ch):
                    if out:
                        out[-1][1] += ch
                else:
                    out.append([ch, ""])
            return out
        pi, pc = per_letter(inp), per_letter(cand)
        if len(pi) != len(pc):
            return True
        for (_, mi), (_, mc) in zip(pi, pc):
            if mi and mc and mi != mc and not (mi == T.SUKUN or mc == T.SUKUN):
                return False
        return True

    def read_word(self, arabic: str, limit: int = 8) -> list[Candidate]:
        """Candidates for one Arabic-script word, best first."""
        if self.opts.persian is False:
            from .lint import fix
            arabic = fix(arabic)
        arabic = arabic.strip("،.:;!؟?\"'()")
        key = skeleton(arabic)
        out: list[Candidate] = []
        if key in self._attested:
            out.append(Candidate(self._attested[key], arabic, "attested", 99.0))
        for w, full in self._by_skel.get(key, []):
            ok = self._marks_compatible(arabic, full)
            out.append(Candidate(w, full, "skeleton", _freq(w) + (0.5 if ok else -5)))
        if not out or len(out) < 2:
            for w, full in self._by_cons.get(consonant_key(arabic), [])[:50]:
                out.append(Candidate(w, full, "consonants", _freq(w) - 3))
        seen, res = set(), []
        for c in sorted(out, key=lambda c: -c.score):
            if c.word not in seen:
                seen.add(c.word)
                res.append(c)
        return res[:limit]

    def read_text(self, text: str) -> list[tuple[str, list[Candidate]]]:
        return [(t, self.read_word(t)) for t in text.split()]


def roundtrip(text: str, opts: Options | None = None) -> dict:
    """Forward then reverse each word; report how often the original is the top candidate."""
    from .translit import transliterate_word
    opts = opts or Options()
    rd = Reader(opts)
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    top1 = in5 = 0
    sizes = []
    misses = []
    for w in words:
        ar = transliterate_word(w, opts)
        cands = rd.read_word(ar, limit=50)
        names = [c.word for c in cands]
        sizes.append(len(names))
        lw = w.lower()
        if names and names[0] == lw:
            top1 += 1
        else:
            misses.append((w, ar, names[:3]))
        if lw in names[:5]:
            in5 += 1
    n = max(len(words), 1)
    return {"words": len(words), "top1": top1 / n, "top5": in5 / n,
            "mean_candidates": sum(sizes) / n, "misses": misses}
