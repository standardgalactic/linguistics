"""Compatibility shim: lets the original main.py import `transliterate_text` unchanged.

The implementation lives in the `arabglish` package (src/arabglish). Defaults here are the
package defaults (core letters, ghain for g, v as beh, full marks). Use `python -m arabglish`
for the density, v/g and attested-form options.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from arabglish import Options, transliterate_text as _tt  # noqa: E402


def transliterate_text(text, options=None):
    return _tt(text, options or Options())
