#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from collections import deque
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from product.common import load_graph, evidence_index

def run(start_node:str, depth:int=2):
    g=load_graph(); nodes={n['id']:n for n in g['nodes']}; idx=evidence_index()
    if start_node not in nodes: raise ValueError(f'unknown node: {start_node}')
    seen={start_node:0}; q=deque([start_node]); edge_ids=set(); edges=[]
    while q:
        node=q.popleft(); d=seen[node]
        if d>=depth: continue
        for e in g['edges']:
            if e['subject']!=node and e['object']!=node: continue
            if e['id'] in edge_ids: continue
            # closed-loop audit at query time too
            missing=[i for i in e.get('evidence_ids',[]) if i not in idx]
            if missing: continue
            edge_ids.add(e['id']); edges.append(e)
            other=e['object'] if e['subject']==node else e['subject']
            if other not in seen:
                seen[other]=d+1; q.append(other)
    evidence_ids=sorted({i for e in edges for i in e.get('evidence_ids',[])})
    return {
      'experience':'trace_evidence','start_node':nodes[start_node],'depth':depth,
      'nodes':[nodes[i] for i in seen], 'edges':edges,
      'evidence':[{'id':i,'source':idx[i].get('source'),'verification_source':idx[i].get('verification_source'),'text_original':idx[i].get('text_original')} for i in evidence_ids],
      'moat_contract':{'all_edges_have_verified_evidence':True,'model_inferred_edges':False,'semantic_edges_must_be_reviewed_or_accepted_relations':True}
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('node'); ap.add_argument('--depth',type=int,default=2); a=ap.parse_args()
    print(json.dumps(run(a.node,a.depth),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
