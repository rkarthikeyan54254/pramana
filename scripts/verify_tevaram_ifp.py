#!/usr/bin/env python3
"""Strict Project Madurai Tevaram ↔ IFP/EFEO PIFI witness verifier.

Authority rule: only exact text after conservative Tamil normalization is auto-verified.
A mismatch is preserved for review; fuzzy similarity never promotes a row.
"""
from __future__ import annotations
import argparse, json, re, unicodedata, hashlib
from pathlib import Path

TAMIL_MARKS = re.compile(r'[\s\-–—,.;:!?"“”\'’‘()\[\]{}…]+')
EDITORIAL = str.maketrans({'(':'',')':'','[':'',']':'','{':'','}':''})

def norm_tamil(s: str) -> str:
    s=unicodedata.normalize('NFC', s)
    s=s.translate(EDITORIAL)
    s=TAMIL_MARKS.sub('',s)
    return s

def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def primary_key(r):
    sec=r.get('section') or {}
    return (int(sec['tirumurai']), int(sec['patikam']), int(r['unit_no']))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('primary')
    ap.add_argument('witness')
    ap.add_argument('--output',required=True)
    ap.add_argument('--verification-source',default='IFP/EFEO Digital Tevaram (PIFI T.V. Gopal Iyer edition, 1984/1985)')
    a=ap.parse_args()
    prim=load_jsonl(a.primary); wit=load_jsonl(a.witness)
    wmap={(int(w['tirumurai']),int(w['patikam']),int(w['verse'])):w for w in wit}
    outrows=[]; matched=0; mismatched=0; missing=0
    for r in prim:
        k=primary_key(r); w=wmap.get(k)
        pnorm=norm_tamil(r['text_original'])
        rec={'id':r['id'],'primary_locus':f'{k[0]}.{k[1]}.{k[2]}','verification_source':a.verification_source,
             'status':None,'witness_locus':None,'primary_hash':hashlib.sha256(pnorm.encode()).hexdigest(),
             'witness_hash':None,'notes':None}
        if not w:
            rec['status']='missing_witness'; rec['notes']='No structurally matching IFP PIFI witness row.'; missing+=1
        else:
            wnorm=norm_tamil(w['text']); rec['witness_locus']=f'{k[0]}:{k[1]}:{k[2]}'
            rec['witness_hash']=hashlib.sha256(wnorm.encode()).hexdigest()
            if pnorm==wnorm:
                rec['status']='verified_exact_normalized'; matched+=1
            else:
                rec['status']='variant_or_transcription_mismatch'; rec['notes']='Conservative normalized Tamil differs; requires curator review. No auto-promotion.'; mismatched+=1
        outrows.append(rec)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8') as fh:
        for x in outrows: fh.write(json.dumps(x,ensure_ascii=False)+'\n')
    print(f'Tevaram IFP verification: matched={matched} mismatch={mismatched} missing={missing} total={len(outrows)}')
    if mismatched or missing:
        raise SystemExit(2)

if __name__=='__main__': main()
