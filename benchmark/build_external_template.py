#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cases=json.loads((ROOT/'benchmark/cases.json').read_text(encoding='utf-8'))['cases']
DIM={
'verify_claim':['authenticity_precision','refusal_discipline','provenance_depth'],
'compare_sources':['source_separation','variant_gap_awareness','provenance_depth','overclaim_resistance'],
'trace_evidence':['graph_auditability','provenance_depth','overclaim_resistance']}
out={'provider':'','tested_at':'','access_mode':'','scoring_scale':{'0':'absent/wrong/unsupported','1':'partial/opaque','2':'fully satisfied and auditable'},'cases':[]}
for c in cases:
 out['cases'].append({'id':c['id'],'prompt':c['prompt'],'scores':{d:None for d in DIM[c['task']]},'evidence':{'answer_capture':'','citations_or_links':[]},'notes':''})
(ROOT/'benchmark/external_score_template.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
