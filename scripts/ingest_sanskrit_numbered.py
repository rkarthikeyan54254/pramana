#!/usr/bin/env python3
"""Strict generic ingester for already-downloaded Sanskrit numbered text.

This intentionally does not encode a guessed GRETIL/BORI marker format. The caller
provides a regex with named groups such as book/chapter/verse. Every marker found
becomes a locus boundary; duplicate/out-of-order loci fail closed.

Example marker regex for a source that literally uses `Ram_2,1.1`:
  --marker-regex 'Ram_(?P<book>\\d+),(?P<chapter>\\d+)\\.(?P<verse>\\d+)'

Use only after the exact source format has been inspected and pinned.
"""
import argparse
import json
import re
from pathlib import Path


def locus_key(groups, order):
    vals=[]
    for name in order:
        v=groups.get(name)
        if v is None:
            continue
        vals.append(int(v) if v.isdigit() else v)
    return tuple(vals)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--marker-regex', required=True)
    ap.add_argument('--order', default='book,chapter,verse', help='comma-separated named groups used for ordering')
    ap.add_argument('--output', required=True)
    ap.add_argument('--expected', type=int)
    args=ap.parse_args()

    text=Path(args.input).read_text(encoding='utf-8')
    pat=re.compile(args.marker_regex)
    matches=list(pat.finditer(text))
    if not matches:
        raise SystemExit('No markers matched; refusing to emit data')
    order=[x.strip() for x in args.order.split(',') if x.strip()]

    rows=[]
    seen=set()
    prev=None
    for i,m in enumerate(matches):
        groups={k:v for k,v in m.groupdict().items() if v is not None}
        key=locus_key(groups, order)
        if key in seen:
            raise SystemExit(f'Duplicate locus: {key}')
        if prev is not None and key <= prev:
            raise SystemExit(f'Out-of-order locus: {key} after {prev}')
        seen.add(key)
        prev=key
        body_start=m.end()
        body_end=matches[i+1].start() if i+1 < len(matches) else len(text)
        body=' '.join(text[body_start:body_end].split())
        if not body:
            raise SystemExit(f'Empty text at locus: {key}')
        rows.append({'section':groups,'source_locus':m.group(0),'text_source_roman':body})

    if args.expected is not None and len(rows) != args.expected:
        raise SystemExit(f'Expected {args.expected} rows, found {len(rows)}')

    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(f'Wrote {len(rows)} strict staging loci to {out}')


if __name__=='__main__':
    main()
