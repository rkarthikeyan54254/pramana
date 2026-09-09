#!/usr/bin/env python3
import argparse,json
from collections import defaultdict
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('scorecard'); a=ap.parse_args()
o=json.loads(Path(a.scorecard).read_text(encoding='utf-8'))
vals=[]; by=defaultdict(list); unscored=0
for c in o['cases']:
 for d,v in c['scores'].items():
  if v is None: unscored+=1; continue
  if v not in (0,1,2): raise SystemExit(f'invalid score {v} for {c["id"]}:{d}')
  vals.append(v); by[d].append(v)
summary={'provider':o.get('provider'),'scored_checks':len(vals),'unscored_checks':unscored,'score_pct':round(sum(vals)/(2*len(vals))*100,1) if vals else None,'dimensions':{d:round(sum(x)/(2*len(x))*100,1) for d,x in sorted(by.items())}}
print(json.dumps(summary,indent=2))
