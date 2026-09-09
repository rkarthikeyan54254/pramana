#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verified_store import load_jsonl, search as lexical_search, evidence
from semantic_store import semantic_search, load_precomputed

REFUSAL='No verified corpus evidence matched this query. I will not answer from model memory.'

def rrf(rank, k=60): return 1.0/(k+rank)

def hybrid(rows, query, limit=8, model=None, precomputed_path=None, query_vector=None):
    lex=lexical_search(rows,query,limit=max(limit*3,12))
    sem=[]
    if model or precomputed_path:
        pc=load_precomputed(precomputed_path) if precomputed_path else None
        sem=[r for _,r in semantic_search(rows,query,limit=max(limit*3,12),model_name=model,
                                           precomputed=pc,query_vector=query_vector)]
    scores={}; byid={}
    for rank,r in enumerate(lex,1):
        byid[r['id']]=r; scores[r['id']]=scores.get(r['id'],0)+rrf(rank)
    for rank,r in enumerate(sem,1):
        byid[r['id']]=r; scores[r['id']]=scores.get(r['id'],0)+rrf(rank)
    ids=sorted(scores,key=lambda i:(-scores[i],i))[:limit]
    return [(scores[i],byid[i]) for i in ids]

def main():
    ap=argparse.ArgumentParser(description='Hybrid verified-only retrieval')
    ap.add_argument('query'); ap.add_argument('paths',nargs='+')
    ap.add_argument('--limit',type=int,default=8)
    ap.add_argument('--model',help='local sentence-transformers model name/path')
    ap.add_argument('--precomputed',help='JSON vectors for deterministic/offline retrieval')
    ap.add_argument('--query-vector',help='comma separated floats; overrides __query__')
    a=ap.parse_args()
    qv=[float(x) for x in a.query_vector.split(',')] if a.query_vector else None
    rows=load_jsonl(a.paths)
    hits=hybrid(rows,a.query,a.limit,a.model,a.precomputed,qv)
    out={'query':a.query,'policy':'verified_only_hybrid','matched':len(hits),'answerable':bool(hits),
         'message':None if hits else REFUSAL,
         'evidence':[dict(evidence(r),retrieval_score=round(score,8)) for score,r in hits]}
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
