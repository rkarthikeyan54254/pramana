#!/usr/bin/env python3
"""Reusable, source-faithful witness extractors for Pramāṇa review workflows."""
from __future__ import annotations
import re
from pathlib import Path
from bs4 import BeautifulSoup

NUMBERED = re.compile(r"^(\d{1,4})\.\s*(.*)$")
BRACKET_GLOSS = re.compile(r"\[[^\]]*\]")


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def extract_wikisource_numbered_paragraphs(path: Path, expected_units: int, *, remove_bracket_glosses: bool = True):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    content = soup.select_one("#mw-content-text") or soup
    units = {}
    current = None
    started = False
    for tag in content.find_all(["p", "h2", "h3", "h4"]):
        if tag.name in {"h2", "h3", "h4"}:
            if started and current == expected_units:
                break
            continue
        text = _clean(tag.get_text(" ", strip=True))
        if remove_bracket_glosses:
            text = _clean(BRACKET_GLOSS.sub("", text))
        if not text:
            continue
        m = NUMBERED.match(text)
        if m:
            n = int(m.group(1))
            if 1 <= n <= expected_units:
                started = True
                current = n
                units.setdefault(n, {"lines": []})
                first = _clean(m.group(2))
                if first:
                    units[n]["lines"].append(first)
                continue
            if started and n > expected_units:
                break
        if current is not None:
            units[current]["lines"].append(text)

    expected = set(range(1, expected_units + 1))
    got = set(units)
    if got != expected:
        raise ValueError(f"witness unit coverage mismatch: got={len(got)} expected={expected_units} missing={sorted(expected-got)[:20]} extra={sorted(got-expected)[:20]}")
    for n, unit in units.items():
        lines = [x for x in unit["lines"] if x]
        if not lines:
            raise ValueError(f"empty witness unit {n}")
        unit["lines"] = lines
        unit["text"] = " ".join(lines)
    return units


EXTRACTORS = {"wikisource_numbered_paragraphs": extract_wikisource_numbered_paragraphs}


def extract(name: str, path: Path, expected_units: int, **options):
    if name not in EXTRACTORS:
        raise ValueError(f"unknown witness extractor: {name}")
    return EXTRACTORS[name](path, expected_units, **options)
