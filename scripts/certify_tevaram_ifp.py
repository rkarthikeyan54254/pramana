#!/usr/bin/env python3
"""Promote Tevaram rows only when strict IFP witness verification passed."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def load(path): return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('primary'); ap.add_argument('verification'); ap.add_argument('output'); a=ap.parse_args()
    rows=load(a.primary); ver={x['id']:x for x in load(a.verification)}
    out=[]
    for r in rows:
        v=ver.get(r['id'])
        if not v or v.get('status')!='verified_exact_normalized':
            raise SystemExit(f"cannot certify {r['id']}: {None if not v else v.get('status')}")
        r=dict(r); r['verified']=True; r['verification_source']=v['verification_source']
        flags=[x for x in r.get('flags',[]) if x!='needs_verification']
        r['flags']=flags
        note=(r.get('notes') or '')+' Second-source text matched IFP/EFEO PIFI witness after conservative Tamil normalization.'
        r['notes']=note.strip(); out.append(r)
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as fh:
        for r in out: fh.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f'certified {len(out)} Tevaram rows')
if __name__=='__main__': main()
