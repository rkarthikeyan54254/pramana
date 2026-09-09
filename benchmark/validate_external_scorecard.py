#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIMENSIONS={'authenticity_precision','refusal_discipline','provenance_depth','source_separation','variant_gap_awareness','overclaim_resistance','graph_auditability'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('scorecard'); ap.add_argument('--require-complete',action='store_true'); ap.add_argument('--allow-template-provider',action='store_true'); a=ap.parse_args()
    o=json.loads(Path(a.scorecard).read_text(encoding='utf-8')); errors=[]
    if not o.get('provider') and not a.allow_template_provider: errors.append('provider is required')
    ids=set()
    for c in o.get('cases',[]):
        if c.get('id') in ids: errors.append(f"duplicate case id {c.get('id')}")
        ids.add(c.get('id'))
        for d,v in c.get('scores',{}).items():
            if d not in DIMENSIONS: errors.append(f"unknown dimension {d}")
            if v is not None and v not in (0,1,2): errors.append(f"invalid score {v} at {c.get('id')}:{d}")
            if a.require_complete and v is None: errors.append(f"unscored {c.get('id')}:{d}")
        ev=c.get('evidence',{})
        if any(v is not None for v in c.get('scores',{}).values()) and not ev.get('answer_capture'):
            errors.append(f"scored case lacks answer_capture: {c.get('id')}")
    if errors:
        print(json.dumps({'valid':False,'errors':errors},indent=2)); raise SystemExit(1)
    print(json.dumps({'valid':True,'provider':o.get('provider'),'cases':len(o.get('cases',[]))},indent=2))
if __name__=='__main__': main()
