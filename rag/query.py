#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from verified_store import load_jsonl, search, evidence

REFUSAL = "No verified corpus evidence matched this query. I will not answer from model memory."

def main():
    ap=argparse.ArgumentParser(description='Verified-only corpus retrieval')
    ap.add_argument('query')
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--limit', type=int, default=8)
    args=ap.parse_args()
    rows=load_jsonl(args.paths)
    hits=search(rows,args.query,args.limit)
    out={
      'query':args.query,
      'policy':'verified_only',
      'matched':len(hits),
      'answerable':bool(hits),
      'message':None if hits else REFUSAL,
      'evidence':[evidence(r) for r in hits]
    }
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
