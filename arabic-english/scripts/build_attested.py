import re, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
lines = (root/"specimens/typed_passage.txt").read_text(encoding="utf-8").splitlines()
title_ar, para_ar = lines[0], lines[2]
title_en = "Capitalist Utopianism: The Repression of Lack and Its Cultural Symptoms"
para_en = ("In this part of Helen Rollins' Psychocinema, she delves into the nature of capitalist ideology "
           "as it intersects with the psychoanalytic concept of Lack. She frames capitalism as a system built on "
           "the repression of the universal truth of Lack, and she explores the ramification of this denial for "
           "both individual psychology and social structures.")
# Only the first two segments are aligned: the remaining typed lines contain tokens (e.g. a real Arabic
# word where English was expected) whose English counterpart cannot be reconstructed with confidence.
def clean_ar(t): return re.sub(r"^[،.:;!?؟\"']+|[،.:;!?؟\"']+$", "", t)
def clean_en(t): return re.sub(r"[^a-z']", "", t.lower().replace("’","'")).rstrip("'")
pairs = []
for ar, en, src in ((title_ar, title_en, "T"), (para_ar, para_en, "T")):
    ar_t = ar.split(); en_t = en.split()
    # the paragraph Arabic runs sentences together, so sentence-wise count check happens on the total
    assert len(ar_t) == len(en_t), (src, len(ar_t), len(en_t))
    for a, e in zip(ar_t, en_t):
        pairs.append((clean_en(e), clean_ar(a), src))
page_lines = [l for l in (root/"specimens/page_handwritten_transcript.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
page_en = ["Capitalist Utopianism", "The repression of lack and its cultural symptoms.",
           "In this part of Helen Rollins' psychocinema,", "she delves into the nature of lack."]
assert len(page_lines) == len(page_en)
for ar, en in zip(page_lines, page_en):
    ar_t, en_t = ar.split(), en.split()
    assert len(ar_t) == len(en_t), (en, len(ar_t), len(en_t))
    for a, e in zip(ar_t, en_t):
        pairs.append((clean_en(e), clean_ar(a), "P"))  # P = the author's handwritten page, transcribed with all marks
out = ["# english<TAB>arabic<TAB>sources (P handwritten page transcript, T typed passage). Tokens verbatim. P forms come first."]
merged = {}
for e, a, src in pairs:
    merged.setdefault((e, a), set()).add(src)
rows = sorted(merged.items(), key=lambda kv: (kv[0][0], "P" not in kv[1], kv[0][1]))
for (e, a), srcs in rows:
    out.append(f"{e}\t{a}\t{''.join(sorted(srcs, reverse=True))}")
dest = root/"src/arabglish/data/attested.tsv"
dest.write_text("\n".join(out)+"\n", encoding="utf-8")
print(len(out)-1, "attested pairs ->", dest)
