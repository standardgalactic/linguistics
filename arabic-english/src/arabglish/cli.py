"""Command line: arabglish fwd | rev | lint | stats | glossary | roundtrip."""
from __future__ import annotations

import argparse
import logging
import re
import sys

from .corpus import describe, inventory
from .lexicon import pronounce
from .lint import fix, lint
from .translit import DENSITIES, Options, transliterate_text, transliterate_word


def _opts(a) -> Options:
    return Options(density=a.density, v=a.v, g=a.g, persian=a.persian, digits=a.digits,
                   use_attested=a.attested, the_before_vowel=a.the_before_vowel)


def _read(a) -> str:
    src = getattr(a, "input", None) or a.file
    if getattr(a, "text", None):
        return a.text
    return sys.stdin.read() if src in (None, "-") else open(src, encoding="utf-8").read()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="arabglish", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("file", nargs="?", help="input file (default stdin)")
        sp.add_argument("--text", help="text given directly on the command line")
        sp.add_argument("--input", "-i", help="input file (same as the positional file)")
        sp.add_argument("--output", "-o", help="write output to this file instead of stdout")
        sp.add_argument("--density", choices=DENSITIES, default="full")
        sp.add_argument("--v", choices=["b", "f", "context"], default="f", help="how English v is written")
        sp.add_argument("--g", choices=["ghain", "jeem"], default="ghain", help="how hard g is written")
        sp.add_argument("--persian", action="store_true", help="use Persian letters (peh, veh, gaf, tcheh)")
        sp.add_argument("--digits", choices=["indic", "latin", "spoken"], default="indic")
        sp.add_argument("--attested", action="store_true", help="prefer forms recorded in the specimens")
        sp.add_argument("--the-before-vowel", action="store_true")
        sp.add_argument("-v-log", dest="verbose", action="store_true")

    for name in ("fwd", "rev", "glossary", "roundtrip"):
        common(sub.add_parser(name))
    sub.add_parser("lint").add_argument("file", nargs="?")
    sub.add_parser("stats").add_argument("file", nargs="?")
    lp = sub.choices["lint"]
    lp.add_argument("--fix", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    if a.cmd == "fwd":
        res = transliterate_text(_read(a), _opts(a))
        if getattr(a, "output", None):
            open(a.output, "w", encoding="utf-8").write(res)
        else:
            sys.stdout.write(res)
    elif a.cmd == "rev":
        from .reader import Reader
        rd = Reader(_opts(a))
        for tok, cands in rd.read_text(_read(a)):
            print(tok, "\t", " | ".join(f"{c.word}" for c in cands[:5]) or "?")
    elif a.cmd == "lint":
        text = _read(a)
        if a.fix:
            sys.stdout.write(fix(text))
        else:
            for i in lint(text):
                print(f"{i.pos}\t{i.code}\t{i.char}\t{i.message}\t{i.suggestion}")
    elif a.cmd == "stats":
        inv = inventory(_read(a))
        for kind in ("letters", "marks"):
            print(kind)
            for ch, n in inv[kind].most_common():
                print(f"  {ch}\t{n}\t{describe(ch)}")
        print("extended:", " ".join(f"{c}:{n}" for c, n in inv["extended"].items()) or "none")
    elif a.cmd == "glossary":
        opts = _opts(a)
        seen = set()
        print("english\tarpabet\tsource\tarabic")
        for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", _read(a)):
            lw = w.lower()
            if lw in seen:
                continue
            seen.add(lw)
            ph, src = pronounce(lw)
            print(f"{lw}\t{' '.join(ph)}\t{src}\t{transliterate_word(lw, opts)}")
    elif a.cmd == "roundtrip":
        from .reader import roundtrip
        r = roundtrip(_read(a), _opts(a))
        print(f"words={r['words']} top1={r['top1']:.3f} top5={r['top5']:.3f} mean_candidates={r['mean_candidates']:.1f}")
        for w, ar, c in r["misses"][:40]:
            print(f"  {w}\t{ar}\t{c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
