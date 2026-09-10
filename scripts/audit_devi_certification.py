#!/usr/bin/env python3
"""Audit a completed Devī Māhātmya certification set.

Fail closed unless:
- every staging row has exactly one verification row;
- every verification row is a match;
- chapters 81..93 are all present;
- primary loci are unique and monotonic inside each chapter;
- secondary loci are present and chapter-mapped 1..13;
- no certified row retains verification/script-normalization blocker flags.
"""
import argparse, json, pathlib, re

PRIMARY_LOC = re.compile(r"^MarkP_(\d+)\.(\d+)$")
SECONDARY_LOC = re.compile(r"^(\d+)\.(\d+)$")
BLOCKERS = {"needs_second_source", "needs_script_normalization", "license_review", "needs_review"}

def load(path):
    return [json.loads(x) for x in pathlib.Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('staging_jsonl')
    ap.add_argument('verification_jsonl')
    ap.add_argument('--certified-jsonl')
    a=ap.parse_args()
    rows=load(a.staging_jsonl); vr=load(a.verification_jsonl)
    if not rows: raise SystemExit('no staging rows')
    ids=[r['id'] for r in rows]
    if len(ids)!=len(set(ids)): raise SystemExit('duplicate staging ids')
    vids=[v['id'] for v in vr]
    if len(vids)!=len(set(vids)): raise SystemExit('duplicate verification ids')
    if set(ids)!=set(vids):
        raise SystemExit(f'id coverage mismatch missing={len(set(ids)-set(vids))} extra={len(set(vids)-set(ids))}')
    chapters={r['section']['chapter'] for r in rows}
    if chapters != set(range(81,94)):
        raise SystemExit(f'chapter coverage mismatch: {sorted(chapters)}')
    per={}
    for r in rows: per.setdefault(r['section']['chapter'],[]).append(int(r['unit_no']))
    for ch, nums in per.items():
        if nums != sorted(nums) or len(nums)!=len(set(nums)):
            raise SystemExit(f'non-monotonic/duplicate primary numbering in chapter {ch}')
    for v in vr:
        if v.get('status')!='match': raise SystemExit(f"unresolved verification: {v['id']}")
        pm=PRIMARY_LOC.match(v.get('primary_locus') or '')
        sm=SECONDARY_LOC.match(v.get('secondary_locus') or '')
        if not pm or not sm: raise SystemExit(f"bad locus mapping: {v['id']}")
        if int(sm.group(1)) != int(pm.group(1))-80:
            raise SystemExit(f"secondary chapter drift: {v['id']}")
        if v.get('score') != 1.0: raise SystemExit(f"bad verification score: {v['id']}")
    if a.certified_jsonl:
        cert=load(a.certified_jsonl)
        if {r['id'] for r in cert} != set(ids): raise SystemExit('certified id coverage mismatch')
        for r in cert:
            if not r.get('verified') or not r.get('verification_source'): raise SystemExit(f"uncertified row: {r['id']}")
            if BLOCKERS.intersection(r.get('flags',[])): raise SystemExit(f"blocker flag retained: {r['id']}")
            if not re.search(r'[\u0900-\u097f]',r.get('text_original','')): raise SystemExit(f"not Devanagari: {r['id']}")
    print(f'Devi certification audit GREEN: {len(rows)} rows, chapters 81-93, 1:1 verification coverage')
if __name__=='__main__': main()
