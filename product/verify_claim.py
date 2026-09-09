#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rag')); sys.path.insert(0,str(ROOT/'product'))
from claim_verifier import verify
from common import load_jsonl

def run(claim:str):
    rows=load_jsonl(); verified=[r for r in rows if r.get('verified') and r.get('verification_source')]
    result=verify(rows,claim,limit=5)
    result['experience']='verify_a_claim'; result['claim']=claim
    result['coverage']={
        'verified_rows_searched':len(verified),
        'works':dict(sorted(Counter(r.get('work','unknown') for r in verified).items())),
        'corpora':dict(sorted(Counter(r.get('corpus','unknown') for r in verified).items()))
    }
    result['moat_contract']={
        'model_memory':'never used as evidence',
        'exact_verified_match_required_for_authentication':True,
        'canonical_transliteration_is_searchable':True,
        'lossy_ascii_or_fuzzy_match_is_candidate_only':True,
        'unverified_exact_matches_are_ignored_for_authority':True
    }
    return result

def markdown_report(result):
    verdict=result['verdict']; claim=result['claim']
    lines=[f'# Claim verification',f'',f'**Claim:** {claim}',f'',f'**Verdict:** {verdict}']
    if result.get('verified'):
        lines.append(''); lines.append('**Authenticated:** yes — exact text found in independently verified corpus evidence.')
        for m in result.get('matches',[]):
            lines += ['',f"- `{m['id']}` — match: {', '.join(m.get('match_modes',[]))}",f"  - primary: {m.get('source')}",f"  - verification: {m.get('verification_source')}"]
    else:
        lines += ['', '**Authenticated:** no.']
        if result.get('unverified_exact_match_count'):
            lines.append(f"- The exact text occurs in {result['unverified_exact_match_count']} unverified staging row(s), which are ignored for authority.")
        if result.get('transliteration_candidates'):
            lines.append('- Lossy transliteration candidates exist, but cannot authenticate the quote.')
        if result.get('candidates'):
            lines.append('- Similar verified passages exist, but similarity cannot authenticate the quote.')
    c=result['coverage']; lines += ['',f"**Coverage searched:** {c['verified_rows_searched']} verified rows across {len(c['works'])} works.",'', '> No evidence → no model-memory substitution.']
    return '\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('claim'); ap.add_argument('--format',choices=['json','markdown'],default='json'); a=ap.parse_args(); out=run(a.claim)
    print(markdown_report(out) if a.format=='markdown' else json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
