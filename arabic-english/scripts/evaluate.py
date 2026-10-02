"""Compare computed forms with attested specimen forms. Skeleton = letters only (marks removed)."""
import sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/"src"))
from arabglish.translit import attested, transliterate_word, Options
from arabglish import tables as T

def skel(s): return "".join(c for c in s if not T.is_mark(c))
def run(opts, verbose=True):
    rows=[]
    for en, forms in attested().items():
        for ar, src in forms:
            got = transliterate_word(en, opts)
            rows.append((en, ar, got, src))
    exact = sum(1 for e,a,g,s in rows if a==g)
    letters = sum(1 for e,a,g,s in rows if skel(a)==skel(g))
    return rows, exact, letters
if __name__=="__main__":
    for v in ("b","f"):
        for g in ("ghain","jeem"):
            rows, exact, letters = run(Options(v=v,g=g))
            print(f"v={v} g={g}: n={len(rows)} exact={exact} skeleton={letters}")
    rows, exact, letters = run(Options())
    print("\nMismatches at skeleton level (computed vs attested):")
    for e,a,g,s in rows:
        if skel(a)!=skel(g): print(f"  {e:14s} attested[{s}] {a}   computed {g}")
