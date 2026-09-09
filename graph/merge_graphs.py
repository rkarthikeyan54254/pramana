#!/usr/bin/env python3
"""Merge already-certified evidence graphs without inventing nodes or edges."""
from __future__ import annotations
import argparse, json
from pathlib import Path

AUTH_FIELDS=('kind','label')

def load_graph(path):
    x=json.loads(Path(path).read_text(encoding='utf-8'))
    return x.get('graph',x)

def merge_graphs(graphs, graph_id='graph.global.v1'):
    nodes={}; edges={}; conflicts=[]
    for g in graphs:
        for n in g.get('nodes',[]):
            if n['id'] in nodes:
                old=nodes[n['id']]
                if any(old.get(k)!=n.get(k) for k in AUTH_FIELDS):
                    conflicts.append({'type':'node_conflict','id':n['id'],'left':old,'right':n}); continue
                # Evidence union is safe: both source nodes were already certified.
                merged=dict(old)
                merged['evidence_ids']=sorted(set(old.get('evidence_ids',[])+n.get('evidence_ids',[])))
                if n.get('aliases') or old.get('aliases'):
                    merged['aliases']=sorted(set(old.get('aliases',[])+n.get('aliases',[])))
                nodes[n['id']]=merged
            else:
                nodes[n['id']]=dict(n)
        for e in g.get('edges',[]):
            if e['id'] in edges and edges[e['id']] != e:
                conflicts.append({'type':'edge_conflict','id':e['id'],'left':edges[e['id']],'right':e}); continue
            edges[e['id']]=dict(e)
    out={
      'id':graph_id,
      'nodes':sorted(nodes.values(),key=lambda x:x['id']),
      'edges':sorted(edges.values(),key=lambda x:x['id']),
      'policy':{
        'node_authority':'verified corpus evidence only',
        'edge_authority':'verified corpus evidence only',
        'generated_nodes':'forbidden without verified evidence_ids',
        'generated_edges':'forbidden without verified evidence_ids',
        'silent_harmonization':False
      }
    }
    return {'graph':out,'conflicts':conflicts}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('graphs',nargs='+'); ap.add_argument('--id',default='graph.global.v1'); ap.add_argument('--out')
    a=ap.parse_args(); result=merge_graphs([load_graph(p) for p in a.graphs],a.id)
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.out: Path(a.out).write_text(text,encoding='utf-8')
    else: print(text,end='')
    if result['conflicts']: raise SystemExit(2)
if __name__=='__main__': main()
