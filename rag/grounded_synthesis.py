#!/usr/bin/env python3
"""Validate and assemble claim-by-claim grounded synthesis.

The model may propose prose, but this module decides whether each claim is admissible.
Authority comes only from verified corpus rows. Claims without support IDs are rejected.
Quoted Sanskrit/Tamil must be extractive from supporting evidence.
"""
from __future__ import annotations
import argparse,json,re,sys,unicodedata
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verified_store import load_jsonl, verified_only, evidence

PUNCT=re.compile(r'[\s\u0964\u0965.,;:!?“”"\'‘’()\[\]{}\-–—_/|]+')
def norm(s): return PUNCT.sub('',unicodedata.normalize('NFC',s or '').casefold())

def validate_claims(rows, proposed):
    eligible={r['id']:r for r in verified_only(rows)}
    accepted=[]; rejected=[]
    for i,c in enumerate(proposed):
        ids=c.get('support_ids') or []
        reason=None
        if not ids: reason='missing_support_ids'
        elif any(i not in eligible for i in ids): reason='support_not_verified_or_missing'
        quote=c.get('quote')
        if reason is None and quote:
            q=norm(quote)
            if not q: reason='empty_quote'
            elif not any(q in norm(eligible[i].get('text_original','')) or q in norm(eligible[i].get('text_iast','')) for i in ids):
                reason='quote_not_extractable_from_support'
        item=dict(c)
        if reason:
            item['accepted']=False; item['reason']=reason; rejected.append(item)
        else:
            item['accepted']=True; accepted.append(item)
    return accepted,rejected,eligible

def assemble(rows, proposed):
    accepted,rejected,eligible=validate_claims(rows,proposed)
    support=sorted({i for c in accepted for i in c['support_ids']})
    return {
      'answerable': bool(accepted),
      'claims': accepted,
      'rejected_claims': rejected,
      'evidence': [evidence(eligible[i]) for i in support],
      'policy': {
        'authority':'verified corpus rows only',
        'unsupported_claims':'rejected',
        'quotes':'must be extractive from supporting rows',
        'model_memory':'not evidence',
        'generated_text_may_enter_corpus':False
      },
      'message': None if accepted else 'No proposed claim is supported by verified corpus evidence; refuse rather than improvise.'
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('claims_json'); ap.add_argument('paths',nargs='+')
    a=ap.parse_args(); proposed=json.loads(Path(a.claims_json).read_text(encoding='utf-8'))
    if isinstance(proposed,dict): proposed=proposed.get('claims',[])
    print(json.dumps(assemble(load_jsonl(a.paths),proposed),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
