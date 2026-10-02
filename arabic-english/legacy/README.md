# Legacy sources (verbatim, not modified)

- `toarabic.ahk`: AutoHotkey keyboard layout from standardgalactic/alphabet (pasted copy shows
  commit 4c64278, 53 lines). It maps Latin keys to Arabic letters one key at a time. It is an
  INPUT METHOD, not a sound key: `p -> لأ` and `v -> آ` are key assignments, not claims about
  how English /p/ or /v/ should be written.
- `pronouncing_translit_chat_version.py`: the "no Farsi letters" cleanup of the pronouncing-based
  script, as it appears in a pasted chat. It is a chat revision, so it may differ from the file
  that was actually run. Known defects: `VOWELS` mixes letters and diacritics, the `'sh'` entry
  is never reached, `is_voiced_v` indexes letters with a phoneme index, and the output joins
  letters with no vowel/sukoon placement.
- `cli_main_as_pasted.py` (also kept runnable as `../main.py`): the command-line wrapper as pasted. It
  imports `transliterate_text` from a module named `transliterator`, which is supplied by the
  shim `../transliterator.py` that forwards to the `arabglish` package.
- `old_version_mappings.py`, `old_version_transliterator.py`: the author's OLD version (nltk cmudict, first
  pronunciation, one letter+mark per phoneme, nine fixed words). Consonants: p->ب, v->ف, hard g->ج,
  ch->ش, ng->ن, zh->ز. Vowels are appended letter-then-mark (AY gives يَ), no sukoon outside the fixed words.
  `utils.py` (tokenize_text, clean_phoneme) was not supplied. The author states it is not definitive.
