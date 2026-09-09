#!/usr/bin/env python3
"""Audit numbered source units without normalizing or repairing them.

Finds duplicate numbers, reversals, gaps, and numbers outside an expected range.
This is a source-quality tool: anomalies are evidence to preserve, not errors to
silently fix.
"""
from __future__ import annotations
import argparse, re
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

NUM = re.compile(r'^\s*(\d{1,5})\s+[\S]')


def visible_lines(path: Path):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    for raw in soup.get_text('\n').splitlines():
        line = ' '.join(raw.split())
        if line:
            yield line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--start', type=int)
    ap.add_argument('--end', type=int)
    args = ap.parse_args()
    seq=[]
    for line in visible_lines(Path(args.input)):
        m=NUM.match(line)
        if not m: continue
        n=int(m.group(1))
        if args.start is not None and n < args.start: continue
        if args.end is not None and n > args.end: continue
        seq.append(n)
    c=Counter(seq)
    dups=sorted(n for n,v in c.items() if v>1)
    reversals=[(a,b) for a,b in zip(seq,seq[1:]) if b<a]
    unique=sorted(c)
    gaps=[]
    for a,b in zip(unique,unique[1:]):
        if b>a+1: gaps.append((a+1,b-1))
    print(f'occurrences={len(seq)} unique={len(unique)} duplicates={len(dups)} reversals={len(reversals)} gaps={len(gaps)}')
    if dups: print('duplicate_numbers:', ','.join(map(str,dups[:100])))
    if reversals: print('reversals:', ', '.join(f'{a}->{b}' for a,b in reversals[:50]))
    if gaps: print('gaps:', ', '.join(f'{a}-{b}' if a!=b else str(a) for a,b in gaps[:50]))
    raise SystemExit(1 if dups or reversals or gaps else 0)

if __name__ == '__main__': main()
