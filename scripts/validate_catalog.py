#!/usr/bin/env python3
"""Validate catalog arithmetic and coverage invariants."""
import json, sys
from pathlib import Path
p=Path(__file__).parents[1]/'schema/work_catalog.json'
c=json.loads(p.read_text(encoding='utf-8'))
dp=c['divya_prabandham']; works=dp['works']
errs=[]
last=0; total=0
for w in works:
    a,b=w['global_range']; expected=b-a+1
    if w['expected_units']!=expected: errs.append(f"{w['work']}: expected_units {w['expected_units']} != range size {expected}")
    if a!=last+1: errs.append(f"{w['work']}: range starts {a}, expected {last+1}")
    last=b; total+=w['expected_units']
if last!=dp['expected_total']: errs.append(f"coverage ends {last}, expected {dp['expected_total']}")
if total!=dp['expected_total']: errs.append(f"sum expected_units={total}, expected {dp['expected_total']}")
if errs:
    print('\n'.join('ERROR '+e for e in errs)); sys.exit(1)
print(f"OK: {len(works)} works cover 1-{last}; expected_units sum={total}")
print(f"Andal={sum(w['expected_units'] for w in works if w['author']=='andal')} units")
print(f"Tevaram mapped={sum(t['expected_units'] for t in c['tevaram']['tirumurai'])} verses across 7 Tirumurai")
