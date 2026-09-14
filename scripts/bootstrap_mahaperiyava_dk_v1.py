#!/usr/bin/env python3
"""
Bootstrap the complete Deivathin Kural Volume 1 corpus for Pramana.

Run from the pramana repo root.

Recommended:
    python ~/Downloads/bootstrap_mahaperiyava_dk_v1.py --create-branch --commit --push

This script:
- creates/switches to mahaperiyava-dk-v1-corpus;
- fetches the official Kanchi DK Volume 1 index;
- discovers every linked Volume 1 chapter;
- stores source HTML only under ignored/private sources/raw/;
- pins SHA-256 sidecars and updates ignored SNAPSHOT_INDEX.json;
- creates public metadata-only catalog + extraction queue;
- preserves the existing 10-chapter pilot metadata;
- updates sources/manifest.json with metadata/checksums only;
- adds a research plan and tests;
- copies itself into scripts/;
- runs diff/pytest/snapshot checks;
- optionally commits and pushes.

It does NOT generate teaching summaries, auto-upgrade authority,
or put Deivathin Kural source text into tracked/public files.
"""

from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path.cwd()

TARGET_BRANCH = "mahaperiyava-dk-v1-corpus"
BASE_BRANCH = "local-checkpoint-20260910"
EXPECTED_BASE_PREFIX = "7657a0c"

INDEX_URL = "https://www.kamakoti.org/tamil/part1index.htm"

PILOT = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_pilot.json"
MANIFEST = ROOT / "sources/manifest.json"
SNAPSHOT_INDEX = ROOT / "sources/SNAPSHOT_INDEX.json"

RAW_DIR = ROOT / "sources/raw/verification/mahaperiyava/deivathin_kural/v1"
INDEX_RAW = RAW_DIR / "part1index.htm"

CATALOG = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
PLAN = ROOT / "data/research/mahaperiyava_deivathin_kural_v1_corpus_plan.md"
TEST = ROOT / "tests/test_mahaperiyava_dk_v1_catalog.py"
REPO_SCRIPT = ROOT / "scripts/bootstrap_mahaperiyava_dk_v1.py"

USER_AGENT = (
    "PramanaResearch/0.1 "
    "(private scholarly source verification; "
    "https://github.com/rkarthikeyan54254/pramana)"
)

MIN_EXPECTED_CHAPTERS = 100


def die(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sh(
    cmd: list[str],
    *,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=check,
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def git_status() -> str:
    return sh(["git", "status", "--porcelain"], capture=True).stdout.strip()


def current_branch() -> str:
    return sh(["git", "branch", "--show-current"], capture=True).stdout.strip()


def current_head() -> str:
    return sh(["git", "rev-parse", "--short", "HEAD"], capture=True).stdout.strip()


def local_branch_exists(name: str) -> bool:
    cp = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{name}"],
        cwd=ROOT,
    )
    return cp.returncode == 0


def ensure_repo() -> None:
    if not (ROOT / ".git").exists():
        die("Run this script from the pramana repository root.")
    for p in (PILOT, MANIFEST):
        if not p.exists():
            die(f"Missing expected repo file: {p.relative_to(ROOT)}")


def ensure_clean_before_branching() -> None:
    dirty = git_status()
    if dirty:
        die(
            "Working tree is not clean. Commit/stash unrelated changes first.\n"
            + dirty
        )


def ensure_target_branch(create_branch: bool) -> None:
    branch = current_branch()
    if branch == TARGET_BRANCH:
        print(f"Already on {TARGET_BRANCH}")
        return

    if not create_branch:
        die(
            f"Current branch is {branch!r}; expected {TARGET_BRANCH!r}. "
            "Use --create-branch from the clean checkpoint."
        )

    if branch != BASE_BRANCH:
        die(
            f"--create-branch is only allowed from {BASE_BRANCH!r}; "
            f"current branch is {branch!r}."
        )

    head = current_head()
    if not head.startswith(EXPECTED_BASE_PREFIX):
        die(
            f"Expected base checkpoint {EXPECTED_BASE_PREFIX}..., "
            f"but HEAD is {head}. Re-check the repo before proceeding."
        )

    if local_branch_exists(TARGET_BRANCH):
        sh(["git", "switch", TARGET_BRANCH])
    else:
        sh(["git", "switch", "-c", TARGET_BRANCH])


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._active_href: str | None = None
        self._text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._active_href = href.strip()
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._active_href is not None:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._active_href is not None:
            title = " ".join("".join(self._text_parts).split())
            self.links.append((self._active_href, html.unescape(title)))
            self._active_href = None
            self._text_parts = []


def request_bytes(url: str, *, retries: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                    "Accept-Language": "ta,en;q=0.8",
                },
            )
            with urlopen(req, timeout=30) as resp:
                data = resp.read()
                if not data:
                    raise RuntimeError("empty response")
                return data
        except Exception as exc:
            last = exc
            if attempt < retries:
                print(
                    f"WARN fetch attempt {attempt} failed for {url}: {exc}"
                )
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def decode_html(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_snapshot(path: Path, data: bytes) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    digest = sha256_bytes(data)
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(digest + "\n", encoding="utf-8")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "bytes": len(data),
    }


def discover_chapters(index_html: str) -> list[dict[str, str]]:
    parser = LinkCollector()
    parser.feed(index_html)

    discovered: list[dict[str, str]] = []
    seen: set[str] = set()

    for href, title in parser.links:
        abs_url = urljoin(INDEX_URL, href)
        parsed = urlparse(abs_url)

        if parsed.netloc not in {"www.kamakoti.org", "kamakoti.org"}:
            continue

        basename = Path(parsed.path).name
        stem = Path(basename).stem.lower()

        # Includes historical filename oddities such as part1kurall08.htm.
        if not stem.startswith("part1kural"):
            continue
        if not basename.lower().endswith((".htm", ".html")):
            continue

        canonical = f"https://www.kamakoti.org{parsed.path}"
        if canonical in seen:
            continue
        seen.add(canonical)

        clean_title = " ".join(title.split()) or basename

        discovered.append(
            {
                "title_ta": clean_title,
                "url": canonical,
                "basename": basename,
                "stem": stem,
            }
        )

    if len(discovered) < MIN_EXPECTED_CHAPTERS:
        die(
            f"Only discovered {len(discovered)} Volume 1 chapter links. "
            f"Expected at least {MIN_EXPECTED_CHAPTERS}; refusing to build "
            "an incomplete catalog."
        )

    return discovered


def source_key_for(stem: str) -> str:
    safe = re.sub(r"[^a-z0-9_-]+", "-", stem.lower()).strip("-")
    return f"kamakoti-dk-v1-{safe}"


def load_or_create_snapshot_index() -> dict[str, Any]:
    if SNAPSHOT_INDEX.exists():
        data = load_json(SNAPSHOT_INDEX)
        data.setdefault("snapshots", [])
        return data
    return {"snapshot_count": 0, "snapshots": []}


def upsert_snapshot_index(
    index: dict[str, Any],
    snap: dict[str, Any],
    url: str,
) -> None:
    record = {
        "path": snap["path"],
        "sha256": snap["sha256"],
        "bytes": snap["bytes"],
        "url": url,
        "fetched_at": now_iso(),
    }
    items = index.setdefault("snapshots", [])
    for i, old in enumerate(items):
        if old.get("path") == record["path"]:
            items[i] = record
            break
    else:
        items.append(record)

    items.sort(key=lambda x: x["path"])
    index["snapshot_count"] = len(items)


def upsert_manifest_source(
    manifest: dict[str, Any],
    entry: dict[str, Any],
) -> None:
    sources = manifest.setdefault("sources", [])
    for i, old in enumerate(sources):
        if old.get("key") == entry["key"]:
            merged = dict(old)
            merged.update(entry)
            sources[i] = merged
            return
    sources.append(entry)


def build() -> int:
    print("\n=== Fetch official DK Volume 1 index ===")
    index_bytes = request_bytes(INDEX_URL)
    index_snap = write_snapshot(INDEX_RAW, index_bytes)
    chapters = discover_chapters(decode_html(index_bytes))
    print(
        f"Discovered {len(chapters)} unique official Volume 1 chapter links."
    )

    pilot = load_json(PILOT)
    pilot_by_url = {c["url"]: c for c in pilot.get("chapters", [])}

    manifest = load_json(MANIFEST)
    snap_index = load_or_create_snapshot_index()

    upsert_snapshot_index(snap_index, index_snap, INDEX_URL)

    upsert_manifest_source(
        manifest,
        {
            "key": "kamakoti-dk-v1-index",
            "url": INDEX_URL,
            "path": str(INDEX_RAW.relative_to(ROOT)),
            "covers": (
                "Official Kanchi Deivathin Kural Volume 1 index and table "
                "of contents"
            ),
            "terms": (
                "Official Kanchi digital Deivathin Kural. Private "
                "research/verification snapshot only; do not redistribute "
                "source text. Public export is metadata only."
            ),
            "status": "verified-live-restricted-private-snapshot",
            "expected_sha256": index_snap["sha256"],
            "expected_bytes": index_snap["bytes"],
        },
    )

    catalog_chapters: list[dict[str, Any]] = []
    failures: list[str] = []

    print("\n=== Fetch official DK Volume 1 chapters ===")
    for ordinal, chapter in enumerate(chapters, start=1):
        url = chapter["url"]
        basename = chapter["basename"]
        raw_path = RAW_DIR / basename
        key = source_key_for(chapter["stem"])

        try:
            body = request_bytes(url)
            snap = write_snapshot(raw_path, body)
            upsert_snapshot_index(snap_index, snap, url)
            snapshot_status = "pinned"
        except Exception as exc:
            print(f"ERROR {ordinal:03d} {url}: {exc}")
            failures.append(url)
            snap = {
                "path": str(raw_path.relative_to(ROOT)),
                "sha256": None,
                "bytes": None,
            }
            snapshot_status = "fetch_failed"

        pilot_rec = pilot_by_url.get(url)

        entry: dict[str, Any] = {
            "ordinal": ordinal,
            "title_ta": chapter["title_ta"],
            "url": url,
            "source_key": key,
            "raw_path": snap["path"],
            "snapshot_status": snapshot_status,
            "snapshot_sha256": snap["sha256"],
            "snapshot_bytes": snap["bytes"],
            "review_status": "needs_teaching_unit_review",
            "public_text_policy": "metadata_only",
            "rights": "restricted_private_research",
            "pilot": bool(pilot_rec),
        }

        if pilot_rec:
            entry["pilot_slug"] = pilot_rec.get("slug")
            entry["pilot_theme"] = pilot_rec.get("theme")
            entry["pilot_dk_attestation"] = pilot_rec.get("dk_attestation")
            entry["pilot_primary_source_status"] = pilot_rec.get(
                "primary_source_status"
            )

        catalog_chapters.append(entry)

        manifest_entry: dict[str, Any] = {
            "key": key,
            "url": url,
            "path": snap["path"],
            "covers": (
                f"Deivathin Kural Volume 1 chapter {ordinal}: "
                f"{chapter['title_ta']}"
            ),
            "terms": (
                "Official Kanchi digital Deivathin Kural. Private "
                "research/verification snapshot only; do not redistribute "
                "source text. Public export is metadata only."
            ),
            "status": (
                "verified-live-restricted-private-snapshot"
                if snapshot_status == "pinned"
                else "restricted-private-snapshot-fetch-failed"
            ),
        }
        if snap["sha256"]:
            manifest_entry["expected_sha256"] = snap["sha256"]
            manifest_entry["expected_bytes"] = snap["bytes"]
        upsert_manifest_source(manifest, manifest_entry)

        if ordinal % 20 == 0 or ordinal == len(chapters):
            print(f"  fetched {ordinal}/{len(chapters)}")
        time.sleep(0.08)

    if failures:
        die(
            f"{len(failures)} chapter fetches failed. Work is left in place "
            "for inspection/resume, but the script refuses to commit an "
            "incomplete Volume 1 bootstrap.\nFirst failures:\n"
            + "\n".join(failures[:10])
        )

    catalog = {
        "version": "0.10",
        "corpus": "mahaperiyava_teachings",
        "work": "deivathin_kural",
        "volume": 1,
        "phase": "complete_volume_chapter_catalog",
        "generated_at": now_iso(),
        "official_index_source_key": "kamakoti-dk-v1-index",
        "official_index_url": INDEX_URL,
        "chapter_count": len(catalog_chapters),
        "rights_policy": {
            "source_text_tracked": False,
            "raw_snapshots_private": True,
            "public_export": "metadata_only",
            "human_review_required_for_teaching_units": True,
            "automatic_authority_upgrade": False,
        },
        "chapters": catalog_chapters,
    }

    write_json(CATALOG, catalog)

    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w", encoding="utf-8") as f:
        for c in catalog_chapters:
            queue_rec = {
                "ordinal": c["ordinal"],
                "title_ta": c["title_ta"],
                "url": c["url"],
                "source_key": c["source_key"],
                "raw_path": c["raw_path"],
                "pilot": c["pilot"],
                "pilot_slug": c.get("pilot_slug"),
                "stage": "needs_teaching_unit_review",
                "teaching_units_created": 0,
                "review_notes": None,
            }
            f.write(
                json.dumps(queue_rec, ensure_ascii=False) + "\n"
            )

    write_json(MANIFEST, manifest)
    write_json(SNAPSHOT_INDEX, snap_index)

    return len(catalog_chapters)


def write_plan(chapter_count: int) -> None:
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(
        f"""# Mahaperiyava Corpus v0.1 — Deivathin Kural Volume 1

## Goal

Build the first complete evidence-bounded source layer for an eventual
**Ask Mahaperiyava** experience.

The app must answer from Mahaperiyava-source material and expose the evidence
behind every answer. It must be able to say **not established from the corpus**
instead of filling gaps with generic devotional or Vedantic prose.

## Current bootstrap

Official index:

`{INDEX_URL}`

Discovered and pinned chapter pages: **{chapter_count}**

Tracked/public files contain metadata, provenance and review state only.
The fetched Deivathin Kural HTML is retained under ignored `sources/raw/`.

## Architecture

```text
official DK Volume 1 index
        |
        v
complete chapter catalog
        |
        v
human-curated teaching units
        |
        +--> DK attestation / print check
        |
        +--> earlier historical witness matching
        |
        +--> primary-source matching where available
        |
        v
public evidence metadata + private retrieval corpus
```

## What is a teaching unit?

A teaching unit is an answerable proposition or closely related cluster of
propositions from a source passage. It is **not** an arbitrary token chunk.

Examples of the shape we want:

- Why perform bhakti?
- Who gives the fruits of karma?
- What is the purpose of temple worship?
- Why should a temple be kept clean?
- What relationship does Advaita have to bhakti?

The exact DK wording remains private/restricted unless rights are explicitly
cleared.

## Authority ladder

```text
unreviewed
dk_attested
dk_print_checked
earlier_witness_supported
primary_source_verified
unattested
```

Collection-level provenance never silently propagates authority to individual
teaching units.

## Next review loop

For each queue entry in
`data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl`:

1. read the private source snapshot;
2. identify natural teaching units;
3. create curator-authored claim summaries;
4. attach source loci and topics/entities;
5. validate against `schema/teaching_record.schema.json`;
6. keep exact source wording private;
7. search historical witnesses only after the DK unit is well-defined;
8. upgrade authority only when evidence supports that specific unit.

## Hugging Face target

The eventual public artifact should be an evidence dataset, not a dump of
Deivathin Kural text. Candidate tables/configurations:

- `sources`
- `teachings`
- `witness_links`
- `chronology`

A later `mahaperiyava-qa-benchmark` can test whether an Ask Mahaperiyava system
answers from this corpus, cites correctly and refuses unsupported claims.
""",
        encoding="utf-8",
    )


def write_tests() -> None:
    TEST.parent.mkdir(parents=True, exist_ok=True)
    TEST.write_text(
        r"""from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _queue():
    p = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_complete_v1_catalog_is_large_and_unique():
    data = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    chapters = data["chapters"]
    assert data["volume"] == 1
    assert data["chapter_count"] == len(chapters)
    assert len(chapters) >= 100
    urls = [c["url"] for c in chapters]
    keys = [c["source_key"] for c in chapters]
    assert len(urls) == len(set(urls))
    assert len(keys) == len(set(keys))


def test_v1_catalog_is_official_kamakoti_and_metadata_only():
    data = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    assert data["official_index_url"] == (
        "https://www.kamakoti.org/tamil/part1index.htm"
    )
    assert data["rights_policy"]["source_text_tracked"] is False
    assert data["rights_policy"]["public_export"] == "metadata_only"

    for c in data["chapters"]:
        assert c["url"].startswith(
            "https://www.kamakoti.org/tamil/part1kural"
        )
        assert c["raw_path"].startswith(
            "sources/raw/verification/mahaperiyava/deivathin_kural/v1/"
        )
        assert c["snapshot_status"] == "pinned"
        assert len(c["snapshot_sha256"]) == 64
        assert "exact_text" not in c
        assert "text" not in c


def test_existing_ten_chapter_pilot_survives_in_complete_catalog():
    pilot = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_pilot.json"
    )
    catalog = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    by_url = {c["url"]: c for c in catalog["chapters"]}
    assert len(pilot["chapters"]) == 10

    for p in pilot["chapters"]:
        assert p["url"] in by_url
        c = by_url[p["url"]]
        assert c["pilot"] is True
        assert c["pilot_slug"] == p["slug"]


def test_extraction_queue_covers_every_catalog_chapter_once():
    catalog = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    queue = _queue()

    assert len(queue) == catalog["chapter_count"]
    assert [q["ordinal"] for q in queue] == list(
        range(1, catalog["chapter_count"] + 1)
    )
    assert {q["source_key"] for q in queue} == {
        c["source_key"] for c in catalog["chapters"]
    }
    assert all(q["stage"] == "needs_teaching_unit_review" for q in queue)
    assert all(q["teaching_units_created"] == 0 for q in queue)


def test_every_v1_catalog_source_resolves_in_manifest():
    catalog = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    manifest = _load("sources/manifest.json")
    by_key = {s["key"]: s for s in manifest["sources"]}

    assert "kamakoti-dk-v1-index" in by_key

    for c in catalog["chapters"]:
        entry = by_key[c["source_key"]]
        assert entry["url"] == c["url"]
        assert entry["path"] == c["raw_path"]
        assert "restricted" in entry["status"]
        assert entry["expected_sha256"] == c["snapshot_sha256"]
        assert entry["expected_bytes"] == c["snapshot_bytes"]
""",
        encoding="utf-8",
    )


def install_repo_script() -> None:
    REPO_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    if src != REPO_SCRIPT.resolve():
        shutil.copyfile(src, REPO_SCRIPT)
        REPO_SCRIPT.chmod(0o755)


def run_checks() -> None:
    print("\n=== Repo checks ===")
    sh(["git", "diff", "--check"])
    sh([sys.executable, "-m", "pytest", "-q"])
    sh([sys.executable, "scripts/audit_snapshots.py"])
    sh(["git", "diff", "--stat"])
    sh(["git", "status", "--short"])


def tracked_targets() -> list[Path]:
    return [
        MANIFEST,
        CATALOG,
        QUEUE,
        PLAN,
        TEST,
        REPO_SCRIPT,
    ]


def commit_changes() -> None:
    paths = [str(p.relative_to(ROOT)) for p in tracked_targets()]
    sh(["git", "add", "--", *paths])
    sh(
        [
            "git",
            "commit",
            "-m",
            "Bootstrap complete Mahaperiyava DK Volume 1 corpus",
        ]
    )


def push_branch() -> None:
    sh(["git", "push", "-u", "origin", TARGET_BRANCH])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create-branch",
        action="store_true",
        help=f"Create/switch to {TARGET_BRANCH} from {BASE_BRANCH}.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit tracked metadata/bootstrap files after checks pass.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the target branch after a successful commit.",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip pytest/snapshot/git checks (not recommended).",
    )
    args = parser.parse_args()

    ensure_repo()
    ensure_clean_before_branching()
    ensure_target_branch(args.create_branch)

    chapter_count = build()
    write_plan(chapter_count)
    write_tests()
    install_repo_script()

    if not args.skip_checks:
        run_checks()

    if args.commit:
        commit_changes()
    else:
        print("\nChanges are ready but not committed.")

    if args.push:
        if not args.commit:
            die("--push requires --commit")
        push_branch()

    print("\n=== Done ===")
    print(f"Branch: {current_branch()}")
    print(f"DK Volume 1 chapters cataloged: {chapter_count}")
    print("Public/tracked source text: NONE")
    print("Raw snapshots: sources/raw/ (gitignored)")
    print("Next phase: human/curated teaching-unit extraction.")


if __name__ == "__main__":
    main()
