#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('provider'); ap.add_argument('--access-mode',default='manual'); ap.add_argument('--output'); a=ap.parse_args()
t=json.loads((ROOT/'benchmark/external_score_template.json').read_text(encoding='utf-8')); t['provider']=a.provider; t['tested_at']=datetime.datetime.now(datetime.timezone.utc).isoformat(); t['access_mode']=a.access_mode
out=Path(a.output) if a.output else ROOT/'benchmark/results'/f"{a.provider.lower().replace(' ','_')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(t,ensure_ascii=False,indent=2),encoding='utf-8'); print(out)
