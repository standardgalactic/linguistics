# Build the English in Arabic Script book and cheat sheet from the Python tools.
# Needs: python3 (cmudict, wordfreq, pytest), xelatex, DejaVu fonts, FreeSerif/FreeMono.

PY      = python3
TOOLS   = arabic-english
TEX     = xelatex -interaction=nonstopmode -halt-on-error

all: tables book cheatsheet

tables:
	cd $(TOOLS) && PYTHONPATH=src $(PY) scripts/make_tex_tables.py
	cd $(TOOLS) && PYTHONPATH=src $(PY) scripts/make_passages.py

book: tables
	cd monograph && $(TEX) main.tex && $(TEX) main.tex
	cp monograph/main.pdf english-in-arabic-script.pdf

cheatsheet:
	cd cheatsheet && $(TEX) arabglish-cheatsheet.tex
	cp cheatsheet/arabglish-cheatsheet.pdf arabglish-cheatsheet.pdf

test:
	cd $(TOOLS) && $(PY) -m pytest -q tests

clean:
	rm -f monograph/*.aux monograph/*.log monograph/*.out monograph/*.toc
	rm -f cheatsheet/*.aux cheatsheet/*.log

.PHONY: all tables book cheatsheet test clean

