#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from product.verify_claim import run as verify
from product.compare_sources import run as compare
from product.trace_evidence import run as trace

CASES=json.loads((ROOT/'benchmark/cases.json').read_text(encoding='utf-8'))

def assess(case,out):
    must=case['must']; checks=[]
    def add(name,ok,detail=None): checks.append({'check':name,'pass':bool(ok),'detail':detail})
    task=case['task']
    if task=='verify_claim':
        add('verified',out.get('verified')==must['verified'],out.get('verified'))
        add('verdict',out.get('verdict')==must['verdict'],out.get('verdict'))
        if 'evidence_id' in must:
            ids={m.get('id') for m in out.get('matches',[])}
            add('evidence_id',must['evidence_id'] in ids,sorted(i for i in ids if i))
    elif task=='compare_sources':
        add('source_count',len(out.get('sources',[]))==must['source_count'],len(out.get('sources',[])))
        add('zero_rejected_claims',(len(out.get('rejected_claims',[]))==0)==must['zero_rejected_claims'],len(out.get('rejected_claims',[])))
        gaps={(g.get('source_key'),g.get('dimension')) for g in out.get('gaps',[])}
        for sk in must['place_gap_sources']:
            add(f'place_gap:{sk}',(sk,'place_association') in gaps,sorted(gaps))
        add('reviewed_relation_min',len(out.get('reviewed_cross_source_relations',[]))>=must['reviewed_relation_min'],len(out.get('reviewed_cross_source_relations',[])))
    elif task=='trace_evidence':
        node_ids={n['id'] for n in out.get('nodes',[])}; preds={e['predicate'] for e in out.get('edges',[])}
        if 'contains_node' in must: add('contains_node',must['contains_node'] in node_ids,sorted(node_ids))
        if 'forbid_node_prefix' in must: add('forbid_node_prefix',not any(n.startswith(must['forbid_node_prefix']) for n in node_ids),sorted(node_ids))
        if 'predicate_any' in must: add('predicate_any',bool(preds.intersection(must['predicate_any'])),sorted(preds))
        if must.get('all_edges_evidenced'):
            add('all_edges_evidenced',all(e.get('evidence_ids') for e in out.get('edges',[])),None)
        if 'evidence_count_min' in must: add('evidence_count_min',len(out.get('evidence',[]))>=must['evidence_count_min'],len(out.get('evidence',[])))
    return checks

def run_case(case):
    if case['task']=='verify_claim': out=verify(case['input'])
    elif case['task']=='compare_sources': out=compare()
    elif case['task']=='trace_evidence': out=trace(case['input'],case.get('depth',2))
    else: raise ValueError(case['task'])
    checks=assess(case,out)
    return {'id':case['id'],'task':case['task'],'pass':all(c['pass'] for c in checks),'checks':checks,'output':out}

def main():
    results=[run_case(c) for c in CASES['cases']]
    total=sum(len(r['checks']) for r in results); passed=sum(sum(c['pass'] for c in r['checks']) for r in results)
    report={'benchmark':CASES['benchmark'],'cases_passed':sum(r['pass'] for r in results),'cases_total':len(results),'checks_passed':passed,'checks_total':total,'score':round(passed/total*100,1) if total else 0,'results':results}
    out=ROOT/'benchmark/native_baseline.json'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('benchmark','cases_passed','cases_total','checks_passed','checks_total','score')},indent=2))
    if not all(r['pass'] for r in results): raise SystemExit(1)
if __name__=='__main__': main()
