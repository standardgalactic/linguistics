"""Generate every table and number used by the monograph from the code and the specimens."""
import re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from arabglish import tables as T
from arabglish.corpus import inventory
from arabglish.guide import respell
from arabglish.lexicon import pronounce
from arabglish.lint import lint
from arabglish.translit import Options, attested, transliterate_text, transliterate_word

OUT = ROOT / "monograph" / "generated"
OUT.mkdir(parents=True, exist_ok=True)


def esc(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%").replace("$", "\\$")
             .replace("#", "\\#").replace("_", "\\_").replace("{", "\\{").replace("}", "\\}"))


def ar(s):
    return "\\ar{" + s + "}"


def write(name, text):
    (OUT / name).write_text(text, encoding="utf-8")


def skel(s):
    return "".join(c for c in s if not T.is_mark(c))


nums = {}
default = Options()

# ---- consonants -------------------------------------------------------------
cons_rows = [
    ("P", "part", "firm", "ب in every specimen; no specimen uses peh"),
    ("B", "big", "firm", ""),
    ("T", "top", "firm", ""),
    ("D", "dog", "firm", ""),
    ("K", "cat", "firm", ""),
    ("G", "gap", "proposed", "غ proposed by the author; ج appears in generated passages"),
    ("F", "fan", "firm", ""),
    ("V", "very", "open", "ف by default (v is a voiced f); ب in universal, individual; see census"),
    ("TH", "think", "firm", "ث"),
    ("DH", "this", "firm", "ذ"),
    ("S", "sun", "firm", ""),
    ("Z", "zoo", "firm", ""),
    ("SH", "she", "firm", ""),
    ("ZH", "vision", "provisional", "ز in the cleaned script; no specimen word"),
    ("HH", "hat", "firm", ""),
    ("CH", "nature", "firm", "تْش on the handwritten page; ش in one typed word"),
    ("JH", "subject", "firm", "ج"),
    ("M", "man", "firm", ""),
    ("N", "no", "firm", ""),
    ("NG", "sing", "provisional", "follows G; typed passages show نْجْ"),
    ("L", "lack", "firm", ""),
    ("R", "red", "firm", ""),
    ("W", "way", "firm", "و as a consonant"),
    ("Y", "yes", "firm", "ي as a consonant"),
]
prof = default.profile()
lines = ["\\begin{tabular}{@{}llcll@{}}", "\\toprule", "ARPAbet & Example & Letters & Status & Note\\\\", "\\midrule"]
for ph, ex, st, note in cons_rows:
    lines.append(f"{ph} & {esc(ex)} & {ar(prof.consonants[ph])} & {st} & {esc(note)}\\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
write("consonants.tex", "\n".join(lines))

# ---- vowels -----------------------------------------------------------------
vex = {"AA": "part", "AE": "lack", "AH": "cultural", "AO": "on", "AW": "flower", "AY": "psychocinema",
       "EH": "delves", "ER": "nature", "EY": "nature", "IH": "this", "IY": "she", "OW": "Rollins",
       "OY": "void", "UH": "could", "UW": "into"}
names = {T.FATHA: "fatha", T.DAMMA: "damma", T.KASRA: "kasra"}
lines = ["\\begin{tabular}{@{}lllll@{}}", "\\toprule", "ARPAbet & Mark & Letters & Example & Rendered\\\\", "\\midrule"]
for ph, (mark, mater, kind) in T.VOWELS.items():
    w = vex[ph]
    lines.append(f"{ph} & {names[mark]} & {ar(mater) if mater else '--'} & {esc(w)} & {ar(transliterate_word(w))}\\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
write("vowels.tex", "\n".join(lines))

# ---- common words -----------------------------------------------------------
lines = ["\\begin{tabular}{@{}ll@{\\qquad}ll@{}}", "\\toprule", "English & Spelling & English & Spelling\\\\", "\\midrule"]
items = list(T.COMMON_WORDS.items())
half = (len(items) + 1) // 2
for i in range(half):
    a = items[i]
    b = items[i + half] if i + half < len(items) else ("", "")
    lines.append(f"{esc(a[0])} & {ar(a[1])} & {esc(b[0])} & {ar(b[1]) if b[1] else ''}\\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
write("common.tex", "\n".join(lines))

# ---- attested comparison ----------------------------------------------------
rows = []
for en, forms in sorted(attested().items()):
    for a, src in forms:
        got = transliterate_word(en, default)
        status = "exact" if got == a else ("letters" if skel(got) == skel(a) else "differs")
        rows.append((en, a, got, src, status))
n = len(rows)
ex = sum(r[4] == "exact" for r in rows)
lt = sum(r[4] in ("exact", "letters") for r in rows)
nums.update(NAttested=n, NExact=ex, NLetters=lt, PctExact=round(100 * ex / n), PctLetters=round(100 * lt / n))
n_f = sum(1 for en, forms in attested().items() for a, s in forms if skel(transliterate_word(en, Options(v="f"))) == skel(a))
lines = ["\\begin{longtable}{@{}lllll@{}}", "\\toprule", "English & Attested & Source & Computed & Match\\\\", "\\midrule", "\\endhead"]
sym = {"exact": "exact", "letters": "letters", "differs": "differs"}
for en, a, got, src, st in rows:
    lines.append(f"{esc(en)} & {ar(a)} & {src} & {ar(got)} & {sym[st]}\\\\")
lines += ["\\bottomrule", "\\end{longtable}"]
write("attested.tex", "\n".join(lines))
diff = [r for r in rows if r[4] == "differs"]
lines = ["\\begin{tabular}{@{}lll@{}}", "\\toprule", "English & Attested & Computed\\\\", "\\midrule"]
for en, a, got, src, st in diff:
    lines.append(f"{esc(en)} & {ar(a)} & {ar(got)}\\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
write("differs.tex", "\n".join(lines))
nums["NDiffers"] = len(diff)

# ---- v census ----------------------------------------------------------------
typed = (ROOT / "specimens/typed_passage.txt").read_text(encoding="utf-8")
gloss = (ROOT / "specimens/typed_passage_A.txt").read_text(encoding="utf-8")
census = [
    ("delves", "دِلْفْزْ", "ف", "page, typed", None),
    ("universal", "يُونِبِرْسَلْ", "ب", "typed", typed),
    ("individual", "إِنْدِبِدْيُوَالْ", "ب", "typed", typed),
    ("however", "هَوِبَرْ", "ب", "typed", typed),
    ("generative", "جِنِرَاتِبْ", "ب", "typed", typed),
    ("never", "نِبَرْ", "ب", "typed", typed),
    ("resolved", "رِزُولْبْدْ", "ب", "typed", typed),
    ("deliver", "دِلِبَرْ", "ب", "typed", typed),
    ("subjective", "سُوبْجِكْتِفْ", "ف", "glossary", gloss),
    ("living", "لَافِنْجْ", "ف", "glossary", gloss),
    ("reveal", "رِيفِيلْ", "ف", "glossary", gloss),
    ("selves", "إِنْسْلِيفْزْ", "ف", "glossary", gloss),
]
checked = []
for en, a, letter, src, text in census:
    if text is not None and a not in text:
        # tolerate mark differences: compare skeleton presence
        if skel(a) not in skel(text):
            print("WARNING census token not found:", en, a)
            continue
    checked.append((en, a, letter, src))
cb = sum(1 for c in checked if c[2] == "ب")
cf = sum(1 for c in checked if c[2] == "ف")
nums.update(VCensusB=cb, VCensusF=cf)
lines = ["\\begin{tabular}{@{}llcl@{}}", "\\toprule", "English & Spelling & Letter for v & Specimen\\\\", "\\midrule"]
for en, a, letter, src in checked:
    lines.append(f"{esc(en)} & {ar(a)} & {ar(letter)} & {src}\\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
write("vcensus.tex", "\n".join(lines))

# ---- demonstration -----------------------------------------------------------
sent = "In this part of Helen Rollins' psychocinema, she delves into the nature of lack."
lines = ["\\begin{tabular}{@{}lp{0.72\\textwidth}@{}}", "\\toprule", "Setting & Output\\\\", "\\midrule"]
for label, o in [("full marks", Options(use_attested=True)), ("computed, full", Options()), ("medial sukoon", Options(density="medial")),
                 ("vowel marks only", Options(density="vowels")), ("unmarked", Options(density="none")),
                 ("v as feh, g as jeem", Options(v="f", g="jeem"))]:
    lines.append(f"{esc(label)} & {ar(transliterate_text(sent, o))}\\\\[3pt]")
lines += ["\\bottomrule", "\\end{tabular}"]
write("demo.tex", "\n".join(lines))

# ---- teaching glossary (three rows) -------------------------------------------
page_en = ["The repression of lack and its cultural symptoms.", "In this part of Helen Rollins' psychocinema,",
           "she delves into the nature of lack."]
lines = []
for s in page_en:
    toks = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", s)
    ens = " ".join(toks)
    ars = " ".join(transliterate_word(t, Options(use_attested=True)) for t in toks)
    guide = " ".join(respell(pronounce(t.lower())[0]) for t in toks)
    lines.append("\\begin{quote}\\noindent " + ar(ars) + "\\\\[1pt]\n\\textit{" + esc(guide) + "}\\\\[1pt]\n" + esc(s) + "\n\\end{quote}")
write("glossary_lines.tex", "\n".join(lines))

# ---- notation collisions on the most frequent words -----------------------------
try:
    from wordfreq import top_n_list
    import cmudict
    d = cmudict.dict()
    words = [w for w in top_n_list("en", 8000) if re.fullmatch(r"[a-z]+", w) and w in d][:5000]
except Exception as e:
    words = []
    print("wordfreq unavailable:", e)
if words:
    classes_full, classes_none = defaultdict(list), defaultdict(list)
    for w in words:
        f = transliterate_word(w, Options())
        classes_full[f].append(w)
        classes_none[skel(f)].append(w)
    def shared(cl):
        return sum(len(v) for v in cl.values() if len(v) > 1) / len(words)
    nums.update(NFreq=len(words), PctSharedFull=round(100 * shared(classes_full), 1), PctSharedSkel=round(100 * shared(classes_none), 1))
    big = sorted(classes_none.values(), key=len, reverse=True)[:6]
    lines = ["\\begin{tabular}{@{}lp{0.6\\textwidth}@{}}", "\\toprule", "Unmarked form & Words sharing it\\\\", "\\midrule"]
    for v in big:
        lines.append(f"{ar(skel(transliterate_word(v[0], Options())))} & {esc(', '.join(v[:10]))}\\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    write("collisions.tex", "\n".join(lines))

# ---- inventory of specimens -----------------------------------------------------
specs = [("Page transcript", "page_handwritten_transcript.txt"), ("Typed passage", "typed_passage.txt"),
         ("Glossary passage", "typed_passage_A.txt"), ("Micromegas", "micromegas.txt"), ("Atlas Shrugged", "atlas.txt")]
lines = ["\\begin{tabular}{@{}lrrll@{}}", "\\toprule", "Specimen & Letters & Marks & Extended letters & Lint issues\\\\", "\\midrule"]
for label, fn in specs:
    s = (ROOT / "specimens" / fn).read_text(encoding="utf-8")
    inv = inventory(s)
    exts = " ".join(f"{c}\\,{k}" for c, k in inv["extended"].items())
    lines.append(f"{label} & {sum(inv['letters'].values())} & {sum(inv['marks'].values())} & {ar(exts) if exts else 'none'} & {len(lint(s))}\\\\")
    if fn == "atlas.txt":
        nums["AtlasExtended"] = sum(inv["extended"].values())
lines += ["\\bottomrule", "\\end{tabular}"]
write("inventory.tex", "\n".join(lines))


# ---- reader round trip ---------------------------------------------------------------
from arabglish.reader import Reader
rd = Reader(default, include_attested=False)
words_rt = words[:2000]
t1 = t5 = 0
sizes = []
for w in words_rt:
    ar_w = transliterate_word(w, default)
    c = [x.word for x in rd.read_word(ar_w, limit=60)]
    sizes.append(len(c))
    t1 += bool(c) and c[0] == w
    t5 += w in c[:5]
nums.update(RtWords=len(words_rt), RtTopOne=round(100 * t1 / len(words_rt)), RtTopFive=round(100 * t5 / len(words_rt)),
            RtMeanCand=round(sum(sizes) / len(sizes), 1))
pairs = [("knight", "night"), ("planet", "plant"), ("their", "there"), ("write", "right")]
lines = ["\\begin{tabular}{@{}llll@{}}", "\\toprule", "English & Spelling & Top candidates & Rank of original\\\\", "\\midrule"]
for w, _ in pairs:
    a = transliterate_word(w, default)
    c = [x.word for x in rd.read_word(a, limit=10)]
    lines.append(f"{esc(w)} & {ar(a)} & {esc(', '.join(c[:4]))} & {c.index(w) + 1 if w in c else '--'}\\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
write("roundtrip_examples.tex", "\n".join(lines))

# ---- write numbers ----------------------------------------------------------------
macro = {"NAttested": "NAttested", "NExact": "NExact", "NLetters": "NLetters", "PctExact": "PctExact",
         "PctLetters": "PctLetters", "NDiffers": "NDiffers", "VCensusB": "VCensusB", "VCensusF": "VCensusF",
         "NFreq": "NFreq", "RtWords": "RtWords", "RtTopOne": "RtTopOne", "RtTopFive": "RtTopFive", "RtMeanCand": "RtMeanCand", "PctSharedFull": "PctSharedFull", "PctSharedSkel": "PctSharedSkel", "AtlasExtended": "AtlasExtended"}
write("numbers.tex", "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in nums.items()))
print(nums)
