#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from graph.sqlite_store import build,query_node
from product.service import dispatch
with tempfile.TemporaryDirectory() as td:
 db=Path(td)/'p.sqlite'; c=build(ROOT,db,ROOT/'data/public/graph/global_evidence_graph.json')
 assert c['records']>=24 and c['nodes']>=30 and c['edges']>=41,c
 q=query_node(db,'person:prahlada',2); assert q['edges'] and q['evidence']
 h=dispatch('health',{}); assert h['status']=='ok' and h['verified_records']>=24
 v=dispatch('verify',{'claim':'Everything happens for a reason'}); assert not v['verified']
print('sqlite-service-test: PASS')
