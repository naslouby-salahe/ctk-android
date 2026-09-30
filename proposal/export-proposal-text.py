#!/usr/bin/env python3
"""Export the reader-facing proposal from its LaTeX source."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NAME = "ctk-android_proposal"
source = (ROOT / f"{NAME}.tex").read_text(encoding="utf-8")
lines = source.splitlines()


def latex_text(value: str) -> str:
    accents = {
        r"\'e": "é", r"\'a": "á", r"\'e": "é", r"\'i": "í",
        r"\'o": "ó", r"\'u": "ú", r'\"u': "ü",
    }
    for old, new in accents.items():
        value = value.replace(old, new)
    value = value.replace(r"\&", "&").replace("--", "-")
    value = value.replace("``", '"').replace("''", '"')
    value = re.sub(r"\\url\{([^{}]+)\}", r"\1", value)
    value = re.sub(r"\\emph\{([^{}]+)\}", r"*\1*", value)
    value = re.sub(r"\\textbf\{([^{}]+)\}", r"**\1**", value)
    value = value.replace(r"\small", "").replace(r"\par", "").replace(r"\\", " ")
    return re.sub(r"\s+", " ", value).strip(" {}")


title_line = next(line for line in lines if r"\LARGE" in line)
title = latex_text(title_line.split(r"\color{ink}", 1)[1])
subtitle_line = next(line for line in lines if r"\normalsize\color{accent}" in line)
subtitle = latex_text(subtitle_line.split(r"\color{accent}", 1)[1])
entries = [re.match(r"\\bibitem\[([^]]+)\]\{([^}]+)\}\s*(.*)", line)
           for line in lines if line.startswith(r"\bibitem")]
assert all(entries)
authors_years = {entry.group(2): entry.group(1) for entry in entries}


def replace_citation(match: re.Match[str]) -> str:
    kind, keys = match.groups()
    cited = []
    for key in keys.split(","):
        label = latex_text(authors_years[key])
        author, year = label.rsplit("(", 1)
        year = year.rstrip(")")
        if kind == "p":
            cited.append(f"{author.replace(' and ', ' & ')}, {year}")
        else:
            cited.append(f"{author} ({year})")
    return "(" + "; ".join(cited) + ")" if kind == "p" else "; ".join(cited)


parts = [
    f"# {title}",
    f"*{subtitle}*",
    "Proposed chapter for *Advances in Mobile Application Privacy and Security*",
]
in_body = False
in_references = False
for line in lines:
    if line.startswith("An Android malware detector"):
        in_body = True
    if not in_body:
        continue
    if line.startswith(r"\begin{thebibliography}"):
        in_references = True
        parts.append("## References")
        continue
    if line.startswith(r"\end{thebibliography}"):
        break
    if in_references:
        if line.startswith(r"\bibitem"):
            match = re.match(r"\\bibitem\[[^]]+\]\{([^}]+)\}\s*(.*)", line)
            assert match is not None
            parts.append(latex_text(match.group(2)))
        continue
    if line.startswith(r"\section*{"):
        parts.append("## " + latex_text(line[len(r"\section*{"):-1]))
    elif line.startswith(r"{\small\textbf{AI assistance disclosure."):
        parts.append(latex_text(line))
    elif line and not line.startswith("\\") and not line.startswith("{"):
        parts.append(latex_text(re.sub(r"\\cite([pt])\{([^}]+)\}", replace_citation, line)))

markdown = "\n\n".join(parts) + "\n"
plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", markdown)
plain = re.sub(r"\*([^*]+)\*", r"\1", plain)
plain = re.sub(r"(?m)^##? ", "", plain)
(ROOT / f"{NAME}.md").write_text(markdown, encoding="utf-8")
(ROOT / f"{NAME}.txt").write_text(plain, encoding="utf-8")
