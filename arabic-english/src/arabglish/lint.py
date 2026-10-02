"""Inventory and mark-order checks for English written in Arabic script."""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import tables as T

_PUNCT_OK = set("،؛؟") | set(".,:;!?()[]{}'\"-—–’“”/ \t\n\r0123456789")
_VOWEL_MARKS = {T.FATHA, T.DAMMA, T.KASRA}


@dataclass(frozen=True)
class Issue:
    pos: int
    char: str
    code: str
    message: str
    suggestion: str = ""


def lint(text: str, allow_persian: bool = False) -> list[Issue]:
    issues: list[Issue] = []
    prev = ""
    run_marks = ""
    for i, ch in enumerate(text):
        o = ord(ch)
        if ch == "�":
            issues.append(Issue(i, ch, "corrupt", "replacement character: original letter lost"))
        elif T.is_mark(ch):
            if ch == "ّ":
                issues.append(Issue(i, ch, "shadda", "shadda is not used by this system (English doubling is not marked)"))
            elif ch not in T.MARKS:
                issues.append(Issue(i, ch, "mark", f"mark U+{o:04X} is outside fatha/damma/kasra/sukoon"))
            if not (prev and (T.is_core_letter(prev) or prev in T.EXTENDED_TO_CORE or ord(prev) > 0x066F and 0x0600 <= ord(prev) <= 0x06FF)) and not T.is_mark(prev):
                issues.append(Issue(i, ch, "orphan-mark", "mark without a base letter"))
            run_marks += ch
        else:
            run_marks = ""
            if 0x0600 <= o <= 0x06FF:
                if T.is_core_letter(ch) or ch in "،؛؟" or 0x0660 <= o <= 0x0669:
                    pass
                elif ch in T.EXTENDED_TO_CORE:
                    if not allow_persian:
                        issues.append(Issue(i, ch, "extended-letter", f"{ch} is outside the standard Arabic letters", T.EXTENDED_TO_CORE[ch]))
                elif o == 0x0640:
                    issues.append(Issue(i, ch, "tatweel", "tatweel is not part of the system", ""))
                else:
                    issues.append(Issue(i, ch, "unknown-arabic", f"U+{o:04X} is not in the inventory"))
        # combos on one letter
        if T.is_mark(ch):
            letters_marks = ""
            j = i
            while j > 0 and T.is_mark(text[j]):
                letters_marks = text[j] + letters_marks
                j -= 1
            vm = [m for m in letters_marks if m in _VOWEL_MARKS]
            if len(vm) > 1:
                issues.append(Issue(i, ch, "double-vowel", "two vowel marks on one letter"))
            if T.SUKUN in letters_marks and vm:
                issues.append(Issue(i, ch, "sukoon-and-vowel", "sukoon and a vowel mark on the same letter"))
        prev = ch
    return issues


def fix(text: str) -> str:
    """Rewrite extended letters to the core inventory (the deterministic part of linting)."""
    return "".join(T.EXTENDED_TO_CORE.get(ch, ch) for ch in text)
