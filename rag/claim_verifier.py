#!/usr/bin/env python3
"""Conservative scriptural quote/claim verifier.

Authority rules:
- Only exact/normalized matches in independently verified corpus rows authenticate text.
- The query may match either original script or the row's canonical transliteration.
- ASCII/diacritic folding and fuzzy similarity are discovery aids only; they never authenticate.
- Exact text that exists only in an unverified staging row is reported as ignored, not evidence.
"""
from __future__ import annotations
import argparse,json,re,sys,unicodedata
from difflib import SequenceMatcher
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verified_store import load_jsonl, verified_only, evidence

PUNCT=re.compile(r'[\s\u0964\u0965.,;:!?“”"\'‘’()\[\]{}\-–—_/|]+')

def norm(s):
    s=unicodedata.normalize('NFC',s or '').casefold()
    return PUNCT.sub('',s)

def ascii_fold(s):
    """Lossy discovery normalization. Never use this to authenticate."""
    s=unicodedata.normalize('NFD',s or '').casefold()
    return ''.join(c for c in s if not unicodedata.combining(c) and ord(c)<128 and c.isalnum())

def row_exact_modes(r,q):
    out=[]
    for field,mode in [('text_original','original_script'),('text_iast','canonical_transliteration')]:
        x=r.get(field,'')
        if x and (q==norm(x) or q in norm(x)): out.append(mode)
    return out

def verify(rows, claim, limit=5, fuzzy_threshold=0.72):
    eligible=verified_only(rows); q=norm(claim)
    if not q:
        return {'verdict':'invalid_query','verified':False,'matches':[],'policy':'Empty/normalization-empty queries cannot authenticate text.'}

    exact=[]
    for r in eligible:
        modes=row_exact_modes(r,q)
        if modes: exact.append((r,modes))
    if exact:
        return {
            'verdict':'verified_text_match','verified':True,
            'matches':[{'match_modes':modes,**evidence(r)} for r,modes in exact[:limit]],
            'policy':'Only exact normalized text in independently verified corpus rows establishes authenticity.'
        }

    # Tell the caller if the string exists only in non-authoritative rows, without treating it as evidence.
    unverified=[]
    for r in rows:
        if r.get('verified') is True and r.get('verification_source'): continue
        if row_exact_modes(r,q): unverified.append(r.get('id'))

    # Lossy ASCII/diacritic candidate retrieval, never authentication.
    qa=ascii_fold(claim); ascii_candidates=[]
    if qa:
        for r in eligible:
            best=0; field=None
            for f in ('text_iast','text_original'):
                x=ascii_fold(r.get(f,''))
                if not x: continue
                score=1.0 if qa==x or qa in x else SequenceMatcher(None,qa,x).ratio()
                if score>best: best=score; field=f
            if best>=0.90: ascii_candidates.append((best,field,r))
        ascii_candidates.sort(key=lambda x:x[0],reverse=True)

    scored=[]
    for r in eligible:
        best=max((SequenceMatcher(None,q,norm(x)).ratio() for x in (r.get('text_original',''),r.get('text_iast','')) if x),default=0)
        if best>=fuzzy_threshold: scored.append((best,r))
    scored.sort(key=lambda x:x[0],reverse=True)

    return {
        'verdict':'no_verified_exact_match','verified':False,
        'message':'No exact claim text was found in verified corpus evidence. Similar passages are discovery candidates only and do not authenticate the claim.',
        'unverified_exact_match_count':len(unverified),
        'unverified_exact_match_ids':unverified[:limit],
        'transliteration_candidates':[{'similarity':round(s,4),'matched_field':f,'evidence':evidence(r)} for s,f,r in ascii_candidates[:limit]],
        'candidates':[{'similarity':round(s,4),'evidence':evidence(r)} for s,r in scored[:limit]],
        'policy':'Fuzzy or lossy transliteration similarity never establishes scriptural authenticity.'
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('claim'); ap.add_argument('paths',nargs='+'); ap.add_argument('--limit',type=int,default=5)
    a=ap.parse_args(); print(json.dumps(verify(load_jsonl(a.paths),a.claim,a.limit),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
