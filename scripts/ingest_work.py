#!/usr/bin/env python3
"""Catalog-driven wrapper for Project Madurai Divya Prabandham ingestion.

It chooses a preserved raw source snapshot based on the pinned work catalog and
refuses ambiguous/unsupported source layouts. It does not verify or normalize.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).parents[1]
CAT=ROOT/'schema/work_catalog.json'
MAN=ROOT/'sources/manifest.json'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('work'); ap.add_argument('--output')
    a=ap.parse_args()
    cat=json.loads(CAT.read_text(encoding='utf-8'))['divya_prabandham']
    matches=[w for w in cat['works'] if w['work']==a.work]
    if len(matches)!=1: raise SystemExit(f'unknown/non-unique work: {a.work}')
    w=matches[0]; start,end=w['global_range']
    # Work-to-source policy. Tiruvaymozhi intentionally uses part 4, whose HTML
    # contains the complete work despite the file's nominal 2971-4000 label.
    if end<=947: key='pm-dp-1-947'
    elif start>=948 and end<=2081: key='pm-dp-948-2081'
    elif start>=2082 and end<=2790: key='pm-dp-2082-2970'
    elif a.work in ('tiruvaymozhi','ramanuja_nutrandadi'): key='pm-dp-2971-4000'
    else: raise SystemExit(f'no unambiguous source policy for {a.work} {start}-{end}')
    manifest={x['key']:x for x in json.loads(MAN.read_text(encoding='utf-8'))['sources']}
    s=manifest[key]; inp=ROOT/s['path']
    if not inp.exists(): raise SystemExit(f'missing raw snapshot: {inp}; run make fetch on a network-enabled host')
    out=Path(a.output) if a.output else ROOT/f'data/staging/divya_prabandham/{a.work}.jsonl'
    cmd=[sys.executable,str(ROOT/'scripts/ingest_project_madurai.py'),'--input',str(inp),'--start',str(start),'--end',str(end),'--work',a.work,'--author',w['author'],'--source',s['url'],'--source-license','PROJECT-MADURAI-SOURCE-TERMS','--output',str(out)]
    print(' '.join(cmd)); raise SystemExit(subprocess.call(cmd))
if __name__=='__main__': main()
