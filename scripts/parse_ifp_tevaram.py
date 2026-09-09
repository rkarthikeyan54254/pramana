#!/usr/bin/env python3
"""Parse IFP/EFEO Digital Tevaram Tamil-script patikam HTML into witness rows.

This is a verification-witness parser, not a publication ingester.
It extracts only source-locus identity and Tamil verse text from the PIFI lane.
English gloss, audio, maps, and other copyrighted enrichment are excluded.
"""
from __future__ import annotations
import argparse, json, re, unicodedata
from pathlib import Path
from bs4 import BeautifulSoup

PATIKAM_RE = re.compile(r'(?:பதிகம்|patikam)\s*:\s*\[(\d+)\s*[:\-]\s*(\d+)\]', re.I)
VERSE_RE = re.compile(r'^\s*\*?\s*(\d{1,3})\s*$')
TAMIL_RE = re.compile(r'[\u0B80-\u0BFF]')
META_PREFIXES = ('பதிகம்:', 'தலம்:', 'பண்:', 'VMS:', 'Vocal rendering', 'patikam:', 'talam:', 'paṇ:')

def clean_line(s: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', s).replace('\ufeff','').split()).strip()

def parse(path: Path):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    lines = [clean_line(x) for x in soup.get_text('\n').splitlines()]
    lines = [x for x in lines if x]
    tm = pat = None
    for s in lines:
        m = PATIKAM_RE.search(s)
        if m:
            tm, pat = map(int, m.groups())
            break
    if tm is None:
        raise ValueError(f'no IFP patikam locus found in {path}')

    rows=[]; current=None; buf=[]
    def flush():
        nonlocal current, buf
        if current is None:
            return
        text=' '.join(x for x in buf if TAMIL_RE.search(x) and not x.startswith(META_PREFIXES)).strip()
        if not text:
            raise ValueError(f'empty IFP witness text at {tm}:{pat}:{current}')
        rows.append({'tirumurai':tm,'patikam':pat,'verse':current,'text':text,'witness_file':path.name})
        current=None; buf=[]

    for s in lines:
        m=VERSE_RE.match(s)
        if m:
            n=int(m.group(1))
            # IFP verse markers are 1..~12. Ignore unrelated isolated numbers before first Tamil verse.
            if 1 <= n <= 20:
                if current is not None:
                    flush()
                current=n
                continue
        if current is not None and TAMIL_RE.search(s) and not s.startswith(META_PREFIXES):
            buf.append(s)
    if current is not None:
        flush()
    if not rows:
        raise ValueError(f'no IFP witness verses found in {path}')
    nums=[r['verse'] for r in rows]
    if nums != sorted(set(nums)):
        raise ValueError(f'non-monotonic/duplicate IFP verse numbering in {path}: {nums}')
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('--output', required=True)
    a=ap.parse_args()
    rows=[]
    for f in a.inputs:
        rows.extend(parse(Path(f)))
    keys=[(r['tirumurai'],r['patikam'],r['verse']) for r in rows]
    if len(keys)!=len(set(keys)):
        raise SystemExit('duplicate IFP structural witness locus across inputs')
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8') as fh:
        for r in sorted(rows,key=lambda x:(x['tirumurai'],x['patikam'],x['verse'])):
            fh.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f'wrote {len(rows)} IFP Tevaram witness rows to {out}')

if __name__=='__main__': main()
