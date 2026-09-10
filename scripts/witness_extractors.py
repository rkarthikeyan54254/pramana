#!/usr/bin/env python3
"""Reusable, source-faithful witness extractors for Pramāṇa review workflows."""
from __future__ import annotations
import re
from pathlib import Path
from bs4 import BeautifulSoup

NUMBERED = re.compile(r"^(\d{1,4})\.\s*(.*)$")
BRACKET_GLOSS = re.compile(r"\[[^\]]*\]")

WIKISOURCE_STRUCTURAL_PARAGRAPHS = {
    "அறுசீர்க் கழிநெடிலடி ஆசிரிய விருத்தம்",
    "கலி விருத்தம்",
    "எழுசீர்க் கழிநெடிலடி ஆசிரிய விருத்தம்",
    "கலிவிருத்தம்",
    "தரவு கொச்சகக் கலிப்பா",
    "கலிநிலைத்துறை",
    "தரவு சொச்சகக் கலிப்பா",
    "ஸ்ரீ ஆண்டாள் திருவடிகளே சரணம்",
}


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


def extract_wikisource_colon_paragraphs(
    path: Path,
    expected_units: int,
    *,
    start_number: int,
    remove_bracket_glosses: bool = True,
    strip_trailing_numeric_apparatus: bool = False,
) -> dict[int, dict]:
    """Extract a Wikisource work with global ``N:`` paragraph numbering.

    A numbered paragraph starts a unit; following unnumbered <p> elements
    belong to that same unit until the next numbered paragraph.

    Source/global numbering is preserved as metadata, while returned dictionary
    keys are local unit numbers 1..expected_units.
    """
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    content = soup.select_one("#mw-content-text") or soup

    end_number = start_number + expected_units - 1

    global_units: dict[int, dict] = {}
    current: int | None = None

    numbered = re.compile(r"^(\d{1,5}):\s*(.*)$")

    for tag in content.find_all(["p", "h2", "h3", "h4"]):
        if tag.name != "p":
            continue

        text = _clean(tag.get_text(" ", strip=True))

        if remove_bracket_glosses:
            text = BRACKET_GLOSS.sub("", text)
            text = _clean(text)

        if not text:
            continue

        # Skip only exact known structural/footer paragraphs.
        # Never use substring matching: words like "விருத்தம்" can occur
        # legitimately inside scripture text.
        if text in WIKISOURCE_STRUCTURAL_PARAGRAPHS:
            continue

        m = numbered.match(text)

        if m:
            source_no = int(m.group(1))

            if source_no < start_number:
                continue

            if source_no > end_number:
                if current is not None:
                    break
                continue

            current = source_no
            global_units.setdefault(
                source_no,
                {
                    "source_display_unit_no": source_no,
                    "lines": [],
                },
            )

            first = _clean(m.group(2))
            if first:
                global_units[source_no]["lines"].append(first)

            continue

        if current is not None:
            global_units[current]["lines"].append(text)

    expected_global = set(range(start_number, end_number + 1))
    got = set(global_units)

    if got != expected_global:
        missing = sorted(expected_global - got)
        extra = sorted(got - expected_global)

        raise ValueError(
            f"witness global coverage mismatch: "
            f"got={len(got)} expected={expected_units} "
            f"missing={missing[:20]} extra={extra[:20]}"
        )

    result: dict[int, dict] = {}

    for source_no in range(start_number, end_number + 1):
        local_no = source_no - start_number + 1

        unit = global_units[source_no]
        lines = [x for x in unit["lines"] if x]

        if not lines:
            raise ValueError(
                f"empty witness unit source={source_no} local={local_no}"
            )

        source_text = " ".join(lines)
        source_trailing_apparatus = None

        if strip_trailing_numeric_apparatus:
            # This witness appends local structural numbering such as:
            #   "4", "(2) 10", "2 10", "(2) 10:"
            # Preserve that apparatus separately; never alter the raw snapshot.
            m = re.search(
                r"\s+((?:\(\d+\)\s*)?\d+(?:\s+\d+)?[:]?)\s*$",
                source_text,
            )
            if m:
                source_trailing_apparatus = m.group(1)
                source_text = source_text[:m.start()].rstrip()

        result[local_no] = {
            "source_display_unit_no": source_no,
            "source_trailing_apparatus": source_trailing_apparatus,
            "lines": lines,
            "text": source_text,
        }

    return result


EXTRACTORS = {
    "wikisource_numbered_paragraphs": extract_wikisource_numbered_paragraphs,
    "wikisource_colon_paragraphs": extract_wikisource_colon_paragraphs,
}


def extract(name: str, path: Path, expected_units: int, **options):
    if name not in EXTRACTORS:
        raise ValueError(f"unknown witness extractor: {name}")
    return EXTRACTORS[name](path, expected_units, **options)
