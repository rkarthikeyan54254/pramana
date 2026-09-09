#!/usr/bin/env python3
"""Stable local service contract for Pramāṇa product experiences."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from product.verify_claim import run as verify_claim
from product.compare_sources import run as compare_sources
from product.trace_evidence import run as trace_evidence
from product.common import load_jsonl
from scripts.export_proof_bundle import build as build_proof_bundle, collect_ids

def health():
    rows=load_jsonl(); verified=[r for r in rows if r.get('verified') and r.get('verification_source')]
    graph=json.loads((ROOT/'data/public/graph/global_evidence_graph.json').read_text(encoding='utf-8')); g=graph.get('graph',graph)
    return {'status':'ok','contract_version':'1','verified_records':len(verified),'graph_nodes':len(g['nodes']),'graph_edges':len(g['edges']),'authority_policy':'verified evidence only'}

def dispatch(operation:str,payload:dict):
    if operation=='health': return health()
    if operation=='verify': return verify_claim(payload['claim'])
    if operation=='compare': return compare_sources()
    if operation=='trace': return trace_evidence(payload['node'],int(payload.get('depth',2)))
    if operation=='proof':
        ids=payload.get('evidence_ids') or []
        if payload.get('artifact'):
            ids=sorted(set(ids)|collect_ids(payload['artifact']))
        return build_proof_bundle(ids,payload.get('context') or {'operation':'proof'})
    raise ValueError(f'unknown operation: {operation}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('operation',choices=['health','verify','compare','trace','proof']); ap.add_argument('--payload',default='{}'); a=ap.parse_args()
    try: out=dispatch(a.operation,json.loads(a.payload))
    except Exception as e: print(json.dumps({'status':'error','error':str(e)})); raise
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
