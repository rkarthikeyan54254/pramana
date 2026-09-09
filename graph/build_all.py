#!/usr/bin/env python3
"""Rebuild all registered real cross-source relations and evidence graphs, then merge."""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rag')); sys.path.insert(0,str(ROOT/'graph'))
from verified_store import load_jsonl
from variant_relations import build_relations
from evidence_graph import build_graph
from merge_graphs import merge_graphs

def main():
    manifest=json.loads((ROOT/'graph/manifest.json').read_text(encoding='utf-8'))
    for item in manifest.get('relation_sets',[]):
        spec=json.loads((ROOT/item['spec']).read_text(encoding='utf-8'))
        rows=load_jsonl([str(ROOT/p) for p in item['rows']])
        out=build_relations(rows,spec)
        if out['rejected_relations']:
            raise SystemExit(f"{item['id']}: rejected relations: {out['rejected_relations']}")
        (ROOT/item['output']).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f"built relation set {item['id']}: relations={len(out['relations'])}")
    built=[]
    for item in manifest['graphs']:
        spec=json.loads((ROOT/item['spec']).read_text(encoding='utf-8'))
        rows=load_jsonl([str(ROOT/p) for p in item['rows']])
        rel=json.loads((ROOT/item['relations']).read_text(encoding='utf-8')) if item.get('relations') else None
        out=build_graph(rows,spec,rel)
        if out['rejected_nodes'] or out['rejected_edges']:
            raise SystemExit(f"{item['id']}: rejected nodes/edges: {out['rejected_nodes']} {out['rejected_edges']}")
        (ROOT/item['output']).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        built.append(out['graph'])
        print(f"built {item['id']}: nodes={len(out['graph']['nodes'])} edges={len(out['graph']['edges'])}")
    merged=merge_graphs(built,manifest['global']['id'])
    if merged['conflicts']: raise SystemExit(f"merge conflicts: {merged['conflicts']}")
    (ROOT/manifest['global']['output']).write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"global: nodes={len(merged['graph']['nodes'])} edges={len(merged['graph']['edges'])}")
if __name__=='__main__': main()
