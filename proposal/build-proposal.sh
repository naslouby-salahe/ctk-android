#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
name=ctk-android_proposal
builddir="$(mktemp -d)"
trap 'rm -rf -- "$builddir"' EXIT
if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir="$builddir" "$name.tex"
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$builddir" "$name.tex"
  pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$builddir" "$name.tex"
else
  echo 'A LaTeX engine (latexmk or pdflatex) is required.' >&2
  exit 1
fi
test -s "$builddir/$name.pdf"
if grep -Eq 'LaTeX Warning|Overfull \\hbox|Underfull \\hbox|Undefined control sequence' "$builddir/$name.log"; then
  echo 'LaTeX log contains a warning or box defect:' >&2
  grep -E 'LaTeX Warning|Overfull \\hbox|Underfull \\hbox|Undefined control sequence' "$builddir/$name.log" >&2
  exit 1
fi
cp -- "$builddir/$name.pdf" "$name.pdf"
python3 export-proposal-text.py
