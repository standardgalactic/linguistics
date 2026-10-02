import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from arabglish import Options, fix, lint, transliterate_text, transliterate_word  # noqa: E402
from arabglish import tables as T  # noqa: E402
from arabglish.g2p import g2p  # noqa: E402
from arabglish.translit import attested  # noqa: E402

SAMPLE = ("In this part of Helen Rollins' Psychocinema, she delves into the nature of capitalist "
          "ideology as it intersects with the psychoanalytic concept of Lack. The quick brown fox "
          "jumps over thirty lazy dogs, and George sang a song about 25 vivid giants in the village.")


def skel(s):
    return "".join(c for c in s if not T.is_mark(c))


def test_core_output_uses_only_standard_letters():
    for v in ("b", "f", "context"):
        for g in ("ghain", "jeem"):
            out = transliterate_text(SAMPLE, Options(v=v, g=g))
            bad = [i for i in lint(out) if i.code in ("extended-letter", "unknown-arabic", "orphan-mark",
                                                      "double-vowel", "sukoon-and-vowel", "shadda")]
            assert bad == [], (v, g, bad[:3])


def test_persian_profile_uses_persian_letters_and_lint_fixes_them():
    out = transliterate_text("pave the very good chip", Options(persian=True))
    assert any(c in out for c in "پڤگچ")
    assert lint(out)
    assert not [i for i in lint(fix(out)) if i.code == "extended-letter"]


@pytest.mark.parametrize("word,expected", [
    ("the", "ذَا"), ("this", "ذِسْ"), ("that", "ذَتْ"), ("of", "أُفْ"), ("and", "أَنْدْ"),
    ("in", "إِنْ"), ("to", "تُو"), ("is", "إِزْ"), ("she", "شِي"), ("its", "إِتْسْ"),
])
def test_common_words_are_fixed(word, expected):
    assert transliterate_word(word) == expected


def test_digraphs_carry_sukoon_on_both_letters():
    assert transliterate_word("which").endswith("تْشْ")
    assert transliterate_word("sing").endswith("نْغْ")


def test_density_levels():
    full = transliterate_word("capitalist")
    assert T.SUKUN in full
    assert T.SUKUN not in transliterate_word("capitalist", Options(density="vowels"))
    assert not any(T.is_mark(c) for c in transliterate_word("capitalist", Options(density="none")))
    med = transliterate_word("capitalist", Options(density="medial"))
    assert med.count(T.SUKUN) == full.count(T.SUKUN) - 1


def test_density_never_changes_the_skeleton():
    base = skel(transliterate_text(SAMPLE, Options(density="full")))
    for d in ("medial", "vowels", "none"):
        assert skel(transliterate_text(SAMPLE, Options(density=d))) == base


def test_unresolved_choices_are_switchable():
    assert "ب" in transliterate_word("delves", Options(v="b"))
    assert "ف" in transliterate_word("delves", Options(v="f"))
    assert "غ" in transliterate_word("gap", Options(g="ghain"))
    assert "ج" in transliterate_word("gap", Options(g="jeem"))
    assert transliterate_word("part").startswith("ب")  # p is firm


def test_attested_forms_win_when_requested():
    for en, forms in attested().items():
        got = transliterate_word(en, Options(use_attested=True))
        assert got == forms[0][0], en


def test_regression_against_specimens():
    import evaluate
    rows, exact, letters = evaluate.run(Options(v="f"))
    n = len(rows)
    # ratchet: raise these when rules improve; never lower them silently
    assert letters / n >= 0.77
    assert exact / n >= 0.72


def test_fallback_g2p_handles_unknown_words():
    assert g2p("zyxquv")
    assert transliterate_word("Taggartish")


def test_digits():
    assert transliterate_text("25", Options()) == "٢٥"
    assert transliterate_text("25", Options(digits="latin")) == "25"
    assert transliterate_text("25", Options(digits="spoken", density="none")) == "تونتي فايف"


def test_lint_flags_corruption_and_orphans():
    codes = {i.code for i in lint("� َ ب")}
    assert "corrupt" in codes and "orphan-mark" in codes


def test_punctuation_is_arabic_style():
    assert transliterate_text("a, b? c;") .count("،") == 1


def test_reader_returns_original_among_candidates():
    from arabglish.reader import Reader
    rd = Reader(max_words=30000)
    hits = 0
    words = ["planet", "capital", "table", "house", "water", "nature", "system", "people"]
    for w in words:
        ar = transliterate_word(w)
        if w in [c.word for c in rd.read_word(ar, limit=10)]:
            hits += 1
    assert hits >= 7


def test_possessive_apostrophe_after_s_is_silent():
    out = transliterate_text("Rollins' book", Options())
    assert "'" not in out
    assert transliterate_text("it's", Options())  # inner apostrophe still handled


def test_written_double_o_keeps_waw():
    for w, a in [("book", "بُوكْ"), ("good", "غُودْ"), ("foot", "فُوتْ"), ("look", "لُوكْ")]:
        assert transliterate_word(w) == a
