"""Worked passages for the monograph: public-domain texts and short originals, set in the default notation."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from arabglish.guide import respell
from arabglish.lexicon import pronounce
from arabglish.translit import Options, transliterate_text, transliterate_word
OUT = ROOT / "monograph" / "generated"

def esc(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%").replace("$", "\\$")
             .replace("#", "\\#").replace("_", "\\_").replace("{", "\\{").replace("}", "\\}"))
def ar(s): return "\\ar{" + s + "}"
def write(n, t): (OUT / n).write_text(t, encoding="utf-8")

def respelled(s):
    return " ".join(respell(pronounce(t.lower())[0]) for t in re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", s))

def block(s, densities=("full",), guide=True):
    rows = []
    for d in densities:
        rows.append(ar(transliterate_text(s, Options(density=d))))
    g = "\\\\[1pt]\n\\textit{" + esc(respelled(s)) + "}" if guide else ""
    return "\\begin{quote}\\noindent " + "\\\\[2pt]\n".join(rows) + g + "\\\\[1pt]\n" + esc(s) + "\n\\end{quote}"

PASSAGES = {
 "p_fresh": ["The book is written in English.", "The letters change, but the words remain.",
             "A reader learns the script and begins to recognise a familiar voice."],
 "p_alice": ["Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do.",
             "Once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it.",
             "And what is the use of a book, thought Alice, without pictures or conversations?"],
 "p_genesis": ["In the beginning God created the heaven and the earth.",
               "And the earth was without form, and void; and darkness was upon the face of the deep.",
               "And God said, Let there be light: and there was light."],
 "p_declaration": ["When in the Course of human events, it becomes necessary for one people to dissolve the political bands which have connected them with another, and to assume among the powers of the earth, the separate and equal station to which the Laws of Nature and of Nature's God entitle them, a decent respect to the opinions of mankind requires that they should declare the causes which impel them to the separation."],
 "p_sonnet": ["Shall I compare thee to a summer's day?", "Thou art more lovely and more temperate.",
              "Rough winds do shake the darling buds of May, and summer's lease hath all too short a date."],
 "p_raven": ["Once upon a midnight dreary, while I pondered, weak and weary,",
             "Over many a quaint and curious volume of forgotten lore."],
 "p_voltaire": ["The traveller came down from the star Sirius to our little ant hill, and measured the earth with his fingers.",
                "He found the people small, but he found them curious, and he asked them many questions about their lives."],
 "p_names": ["Helen Rollins lives in Halifax, and her brother Victor lives in Vancouver.",
             "Tuesday, the fifth of October, at seven thirty, the train from Toronto arrives."],
 "p_numbers": ["There are 25 words on this page and 3 of them are numbers.", "In 2026 it cost 1,250 dollars."],
}
for name, sents in PASSAGES.items():
    dens = ("full", "none") if name in ("p_fresh", "p_alice") else ("full",)
    write(name + ".tex", "\n".join(block(s, dens) for s in sents))

# density ladder for one sentence
s = "The letters change, but the words remain."
rows = ["\\begin{tabular}{@{}ll@{}}", "\\toprule", "Density & Result\\\\", "\\midrule"]
for d in ("full", "medial", "vowels", "none"):
    rows.append(f"{d} & {ar(transliterate_text(s, Options(density=d)))}\\\\[3pt]")
rows += ["\\bottomrule", "\\end{tabular}"]
write("p_density.tex", "\n".join(rows))

# reference vocabulary tables (three columns)
GROUPS = {
 "w_oo": "book look good foot wood food moon school too two blue true",
 "w_ee": "see tree green sleep head bread read meet meat dream bread dead",
 "w_ai": "rain day light night voice flower hour boy toy noise now how",
 "w_cons": "thing think this that church change judge measure vision singer finger garden",
 "w_clusters": "string spring splash street strength twelfth asked texts",
 "w_short": "cat bed sit hot cut put pen map top sun",
 "w_long": "make time home use cake like phone tune",
 "w_hybrid": "psychology concept Rollins on cinema Helen repression social nation system lack part flower hour power tower finger English",
 "w_r": "car far her bird turn word door more fire tire",
}
for name, ws in GROUPS.items():
    seen = []; [seen.append(w) for w in ws.split() if w not in seen]
    rows = ["\\begin{tabular}{@{}lll@{}}", "\\toprule", "English & Arabic script & Respelling\\\\", "\\midrule"]
    for w in seen:
        ph = pronounce(w)[0]
        rows.append(f"{esc(w)} & {ar(transliterate_word(w))} & \\textit{{{esc(respell(ph))}}}\\\\")
    rows += ["\\bottomrule", "\\end{tabular}"]
    write(name + ".tex", "\n".join(rows))

# approved examples with check
rows = []
bad = 0
for l in (ROOT / "specimens" / "approved_examples.txt").read_text(encoding="utf-8").splitlines():
    if not l.strip() or l.startswith("#"): continue
    en, a = l.split("\t")
    c = transliterate_text(en)
    bad += c != a
print("approved examples differing from computed:", bad)

# ---- reader demonstration -----------------------------------------------------------
from arabglish.reader import Reader
rd = Reader(Options(), 20000, include_attested=False)
sent = "The letters change, but the words remain."
arab = transliterate_text(sent)
rows = ["\\begin{tabular}{@{}lll@{}}", "\\toprule", "Written & Top candidates & Reader tier\\\\", "\\midrule"]
for tok, cands in rd.read_text(arab):
    top = ", ".join(c.word for c in cands[:4])
    rows.append(f"{ar(tok)} & {esc(top)} & {esc(cands[0].tier if cands else '-')}\\\\")
rows += ["\\bottomrule", "\\end{tabular}"]
write("reader_demo.tex", "\n".join(rows))

# ---- linter demonstration -------------------------------------------------------------
from arabglish.lint import lint, fix
bad = "ذَا گُود بُوک إِزْ ڤَرِي چِيپْ ّ"
rows = ["\\begin{tabular}{@{}lll@{}}", "\\toprule", "Character & Code & Suggested repair\\\\", "\\midrule"]
for i in lint(bad):
    rows.append(f"{ar(i.char)} & {esc(i.code)} & {ar(i.suggestion) if i.suggestion else '--'}\\\\")
rows += ["\\bottomrule", "\\end{tabular}"]
write("lint_demo.tex", "\n".join(rows))
write("lint_demo_text.tex", "\\ar{" + bad + "} \\quad $\\rightarrow$ \\quad \\ar{" + fix(bad) + "}")

# ---- sensitivity of the agreement to the open switches --------------------------------
import evaluate
rows = ["\\begin{tabular}{@{}llrr@{}}", "\\toprule", "$v$ & hard $g$ & Exact & Letters\\\\", "\\midrule"]
for v in ("f", "b"):
    for g in ("ghain", "jeem"):
        _, ex, lt = evaluate.run(Options(v=v, g=g))
        rows.append(f"{ {'f':'ف','b':'ب'}[v] and ar({'f':'ف','b':'ب'}[v])} & {ar({'ghain':'غ','jeem':'ج'}[g])} & {ex} & {lt}\\\\")
rows += ["\\bottomrule", "\\end{tabular}"]
write("sensitivity.tex", "\n".join(rows))

# ---- approved examples, word by word ------------------------------------------------------
diffs = []
tot = same = 0
for l in (ROOT / "specimens" / "approved_examples.txt").read_text(encoding="utf-8").splitlines():
    if not l.strip() or l.startswith("#"): continue
    en, a = l.split("\t")
    toks = re.findall(r"[A-Za-z]+", en)
    atoks = re.findall(r"[^\s،.]+", a)
    if len(toks) != len(atoks): continue
    for t, x in zip(toks, atoks):
        c = transliterate_word(t); tot += 1; same += c == x
        if c != x: diffs.append((t, x, c))
rows = ["\\begin{tabular}{@{}lll@{}}", "\\toprule", "English & Approved & Computed\\\\", "\\midrule"]
for t, x, c in diffs:
    rows.append(f"{esc(t)} & {ar(x)} & {ar(c)}\\\\")
rows += ["\\bottomrule", "\\end{tabular}"]
write("approved_diffs.tex", "\n".join(rows))
write("approved_numbers.tex", f"\\newcommand{{\\NApprovedWords}}{{{tot}}}\\newcommand{{\\NApprovedSame}}{{{same}}}")
print("approved words", tot, same)
