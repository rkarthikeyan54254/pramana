#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path

def summarize(p):
    o=json.loads(Path(p).read_text(encoding='utf-8')); by=defaultdict(list); total=[]
    for c in o['cases']:
        for d,v in c['scores'].items():
            if v is not None: by[d].append(v); total.append(v)
    return {'provider':o.get('provider') or Path(p).stem,'scored_checks':len(total),'score_pct':round(sum(total)/(2*len(total))*100,1) if total else None,'dimensions':{d:round(sum(v)/(2*len(v))*100,1) for d,v in sorted(by.items())}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('scorecards',nargs='+'); a=ap.parse_args(); print(json.dumps({'scorecards':[summarize(p) for p in a.scorecards]},indent=2))
if __name__=='__main__': main()
