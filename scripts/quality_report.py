#!/usr/bin/env python3
"""Corpus-level progress and quality gate reporter.

Reports counts without upgrading any record's verification status. Designed to be
safe to run on staging or public JSONL trees.
"""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path


def rows(paths):
    for root in paths:
        root = Path(root)
        files = [root] if root.is_file() else sorted(root.rglob('*.jsonl'))
        for f in files:
            for n, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    yield f, n, json.loads(line)
                except json.JSONDecodeError as e:
                    yield f, n, {"__parse_error__": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    args = ap.parse_args()
    total = verified = provenance = parse_errors = 0
    by_work = defaultdict(Counter)
    flags = Counter()
    for f, n, r in rows(args.paths):
        total += 1
        if '__parse_error__' in r:
            parse_errors += 1
            continue
        work = r.get('work','<missing>')
        by_work[work]['rows'] += 1
        if r.get('verified') is True:
            verified += 1; by_work[work]['verified'] += 1
        if r.get('source') and r.get('source_license'):
            provenance += 1; by_work[work]['provenance'] += 1
        flags.update(r.get('flags') or [])
    print(f"rows={total} parse_errors={parse_errors} provenance={provenance}/{total} verified={verified}/{total}")
    for work, c in sorted(by_work.items()):
        print(f"{work}: rows={c['rows']} provenance={c['provenance']} verified={c['verified']}")
    if flags:
        print('flags: ' + ', '.join(f'{k}={v}' for k,v in flags.most_common()))

if __name__ == '__main__':
    main()
