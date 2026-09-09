#!/usr/bin/env python3
from __future__ import annotations
import json,glob
from collections import Counter
from pathlib import Path

def main():
 rows=[]
 for p in glob.glob('data/public/**/*.jsonl',recursive=True):
  for line in open(p,encoding='utf-8'):
   if line.strip(): rows.append(json.loads(line))
 verified=[r for r in rows if r.get('verified') is True and r.get('verification_source')]
 licenses=Counter(r.get('source_license','UNKNOWN') for r in verified)
 print('RELEASE READINESS')
 print('repository_rows',len(rows)); print('verified_with_witness',len(verified)); print('licenses',dict(licenses))
 print('open_eligible',sum(n for l,n in licenses.items() if l in {'PD','PD-TRANS','CC0','CC-BY','CC-BY-4.0','CC-BY-SA','CC-BY-SA-4.0'}))
 print('research_nc_eligible',sum(n for l,n in licenses.items() if l in {'PD','PD-TRANS','CC0','CC-BY','CC-BY-4.0','CC-BY-SA','CC-BY-SA-4.0','CC-BY-NC-SA-4.0'}))
 print('raw_snapshot_index', 'present' if Path('sources/SNAPSHOT_INDEX.json').exists() else 'MISSING (expected in network-enabled acquisition run)')
if __name__=='__main__': main()
