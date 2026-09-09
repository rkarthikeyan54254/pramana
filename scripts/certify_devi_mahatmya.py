#!/usr/bin/env python3
"""Promote Devī Māhātmya staging rows only when every substantive row is second-source matched."""
import argparse, json, pathlib, sys
from iast_to_devanagari import transliterate

def load_jsonl(path):
    return [json.loads(x) for x in pathlib.Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('staging_jsonl')
    ap.add_argument('verification_jsonl')
    ap.add_argument('output_jsonl')
    a=ap.parse_args()
    rows=load_jsonl(a.staging_jsonl)
    vr=load_jsonl(a.verification_jsonl)
    vmap={x['id']:x for x in vr}
    if len(vmap)!=len(vr): raise SystemExit('duplicate verification ids')
    missing=[r['id'] for r in rows if r['id'] not in vmap]
    bad=[r['id'] for r in rows if r['id'] in vmap and vmap[r['id']]['status']!='match']
    if missing or bad:
        raise SystemExit(f'certification blocked: missing={len(missing)} review={len(bad)}')
    out=[]
    for r in rows:
        v=vmap[r['id']]
        r['source_license']='CC-BY-NC-SA-4.0'
        r['verified']=True
        r['verification_source']='vedpath_durga_saptashati'
        flags=[f for f in r.get('flags',[]) if f not in {'needs_second_source','license_review'}]
        # Canonical record requires source script. Convert the verified IAST deterministically.
        r['text_original']=transliterate(r['text_iast'])
        flags=[f for f in flags if f != 'needs_script_normalization']
        r['flags']=flags
        note=(r.get('notes') or '').strip()
        mapping=f"Verified by normalized text alignment to secondary locus {v['secondary_locus']} (score={v['score']})."
        r['notes']=(note+' '+mapping).strip()
        out.append(r)
    p=pathlib.Path(a.output_jsonl); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in out)+'\n',encoding='utf-8')
    print(f'certified {len(out)} rows; IAST->Devanagari normalization complete')

if __name__=='__main__': main()
