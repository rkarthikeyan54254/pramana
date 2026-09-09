#!/usr/bin/env python3
"""Audit a materialized evidence graph against certified JSONL rows and accepted relations."""
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'rag'))
from verified_store import load_jsonl,verified_only
from jsonschema import Draft202012Validator

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('graph_json')
    ap.add_argument('rows',nargs='+')
    ap.add_argument('--relations',nargs='*',default=[])
    ap.add_argument('--schema',default='schema/evidence_graph.schema.json')
    ap.add_argument('--relation-schema',default='schema/cross_source_relation.schema.json')
    a=ap.parse_args(); root=Path(__file__).resolve().parents[1]
    raw=json.loads(Path(a.graph_json).read_text(encoding='utf-8')); g=raw.get('graph',raw)
    schema=json.loads((root/a.schema).read_text(encoding='utf-8'))
    errs=list(Draft202012Validator(schema).iter_errors(g))
    eligible={r['id'] for r in verified_only(load_jsonl(a.rows))}
    dangling=[]
    for typ,items in [('node',g.get('nodes',[])),('edge',g.get('edges',[]))]:
        for item in items:
            for eid in item.get('evidence_ids',[]):
                if eid not in eligible: dangling.append((typ,item['id'],eid))
    node_ids={n['id'] for n in g.get('nodes',[])}
    bad_refs=[e['id'] for e in g.get('edges',[]) if e['subject'] not in node_ids or e['object'] not in node_ids]

    relation_ids=set(); relation_schema_errors=[]
    rel_schema=json.loads((root/a.relation_schema).read_text(encoding='utf-8'))
    rel_validator=Draft202012Validator(rel_schema)
    for path in a.relations:
        x=json.loads(Path(path).read_text(encoding='utf-8'))
        for rel in x.get('relations',[]):
            relation_ids.add(rel['id'])
            relation_schema_errors.extend((path,rel.get('id'),e.message) for e in rel_validator.iter_errors(rel))
    dangling_relations=[]
    for typ,items in [('node',g.get('nodes',[])),('edge',g.get('edges',[]))]:
        for item in items:
            for rid in item.get('relation_ids',[]):
                if rid not in relation_ids: dangling_relations.append((typ,item['id'],rid))

    result={
      'graph_id':g.get('id'),'nodes':len(g.get('nodes',[])),'edges':len(g.get('edges',[])),
      'node_kinds':dict(Counter(n['kind'] for n in g.get('nodes',[]))),
      'edge_kinds':dict(Counter(e['kind'] for e in g.get('edges',[]))),
      'schema_errors':len(errs),'dangling_evidence':dangling,'bad_node_refs':bad_refs,
      'accepted_relation_ids':len(relation_ids),'relation_schema_errors':relation_schema_errors,
      'dangling_relation_refs':dangling_relations
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errs or dangling or bad_refs or relation_schema_errors or dangling_relations: raise SystemExit(1)
if __name__=='__main__': main()
