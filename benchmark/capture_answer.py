#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('scorecard'); ap.add_argument('case_id'); ap.add_argument('--answer-file'); ap.add_argument('--answer'); ap.add_argument('--citation',action='append',default=[]); a=ap.parse_args()
p=Path(a.scorecard); o=json.loads(p.read_text(encoding='utf-8')); case=next((x for x in o['cases'] if x['id']==a.case_id),None)
if not case: raise SystemExit(f'unknown case {a.case_id}')
if bool(a.answer_file)==bool(a.answer): raise SystemExit('provide exactly one of --answer-file or --answer')
text=Path(a.answer_file).read_text(encoding='utf-8') if a.answer_file else a.answer
case['evidence']['answer_capture']=text; case['evidence']['citations_or_links']=a.citation
p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8'); print(f'captured {a.case_id} -> {p}')
