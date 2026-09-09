#!/usr/bin/env python3
"""Build an auditable answer packet from retrieved evidence.

This intentionally does not freestyle scripture. It produces an evidence packet that
an LLM UI may explain, with explicit support IDs for every proposed claim.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hybrid_query import hybrid, REFUSAL
from verified_store import load_jsonl,evidence


def supported_claims(hits):
    claims=[]
    for _,r in hits:
        eid=r['id']
        # Extractive claims only. These are safe because values are carried from the row.
        claims.append({
          'claim_type':'source_locus',
          'text':f"Evidence is available at corpus locus {eid}.",
          'support_ids':[eid]
        })
        if r.get('translation_en'):
            claims.append({
              'claim_type':'translation_excerpt',
              'text':r['translation_en'],
              'support_ids':[eid],
              'translation_source':r.get('translation_source'),
              'translation_license':r.get('translation_license')
            })
    return claims


def main():
    ap=argparse.ArgumentParser(description='Assemble evidence-backed answer packet')
    ap.add_argument('query'); ap.add_argument('paths',nargs='+')
    ap.add_argument('--limit',type=int,default=5); ap.add_argument('--model'); ap.add_argument('--precomputed')
    a=ap.parse_args(); rows=load_jsonl(a.paths)
    hits=hybrid(rows,a.query,a.limit,a.model,a.precomputed,None)
    if not hits:
        out={'query':a.query,'answerable':False,'answer':None,'message':REFUSAL,'claims':[],'evidence':[]}
    else:
        out={'query':a.query,'answerable':True,
             'answer':'Evidence found. Any explanatory prose must remain grounded in the support_ids below.',
             'claims':supported_claims(hits),
             'evidence':[evidence(r) for _,r in hits],
             'generation_contract':{
               'may_explain':True,
               'must_cite_support_ids':True,
               'may_quote_only_from':'evidence[].text_original',
               'must_surface_variants':True,
               'must_refuse_unsupported_claims':True,
               'generated_text_may_enter_corpus':False
             }}
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
