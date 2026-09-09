#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from product.common import load_jsonl, load_relations

PRIORITY={
 'verification_mismatch':'P0','license_unresolved':'P0','semantic_relation_review':'P1',
 'variant_needs_source':'P1','script_normalization':'P1','transliteration_uncertain':'P1','needs_review_flag':'P2'
}

def rid(kind,subject,reason):
    h=hashlib.sha256(f'{kind}|{subject}|{reason}'.encode()).hexdigest()[:12]
    return f'review.{kind}.{h}'

def item(kind,subject,reason,evidence,created_from,action=None,priority=None):
    return {'id':rid(kind,subject,reason),'kind':kind,'priority':priority or PRIORITY[kind],'status':'open','subject_id':subject,
            'reason':reason,'evidence_ids':sorted(set(evidence)),'created_from':created_from,'suggested_action':action,
            'reviewed_by':None,'review_notes':None,'resolution':None}

def build(rows,relations,license_matrix=None):
    out=[]
    for r in rows:
        flags=set(r.get('flags') or [])
        if r.get('verified') is not True or not r.get('verification_source'):
            out.append(item('verification_mismatch',r['id'],'Record is not independently verified.',[r['id']],r.get('source','record'),'Acquire/align a second independent witness and certify only on pass.'))
        if 'needs_review' in flags:
            out.append(item('needs_review_flag',r['id'],'Record carries needs_review.',[r['id']],r.get('source','record'),'Curator must resolve the flagged issue before promotion.'))
        if 'needs_script_normalization' in flags:
            out.append(item('script_normalization',r['id'],'Source script normalization is unresolved.',[r['id']],r.get('source','record'),'Run deterministic script conversion and spot-check against witness.'))
        if 'translit_uncertain' in flags:
            out.append(item('transliteration_uncertain',r['id'],'Transliteration is uncertain.',[r['id']],r.get('source','record'),'Regenerate deterministically and review mismatch.'))
        for v in r.get('variants') or []:
            for alt in v.get('alternatives') or []:
                if alt.get('status')=='needs_source':
                    reason=f"Variant at {v.get('locus','?')} needs an attesting source: {alt.get('reading','')}"
                    out.append(item('variant_needs_source',r['id'],reason,[r['id']],r.get('source','record'),'Find an independent attestation or reject the variant.'))
    for rel in relations:
        if rel.get('status')=='needs_review' or (rel.get('classification_basis')=='curator_reviewed' and not rel.get('reviewed_by')):
            ids=(rel.get('left',{}).get('support_ids') or [])+(rel.get('right',{}).get('support_ids') or [])
            out.append(item('semantic_relation_review',rel['id'],f"Semantic relation {rel.get('relation_type')} requires curator adjudication.",ids,'cross_source_relation','Review both evidence sets; classify narrowly; never choose a preferred tradition.'))
    if license_matrix:
        for s in license_matrix.get('sources',license_matrix if isinstance(license_matrix,list) else []):
            state=(s.get('classification') or s.get('release_class') or s.get('status') or '').lower()
            if state=='metadata_only':
                continue
            if state=='cc-by-nc-sa-4.0':
                continue
            key=s.get('key') or s.get('source_key') or s.get('url','source')
            if 'unresolved' in state or 'copyright' in state:
                out.append(item('license_unresolved',key,'Source reuse/publication rights are unresolved.',[],s.get('url',key),'Resolve exact file-level terms before release; default deny.',priority='P0'))
            elif 'restricted' in state or 'conditional' in state:
                out.append(item('license_unresolved',key,'Source has restricted or conditional redistribution terms requiring packaging review.',[],s.get('url',key),'Confirm permitted release profile and preservation/attribution requirements.',priority='P1'))
    # stable de-dupe
    dedup={x['id']:x for x in out}
    return sorted(dedup.values(),key=lambda x:(x['priority'],x['kind'],x['subject_id']))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='dist/review_queue.json'); ap.add_argument('--license-matrix',default='sources/LICENSE_MATRIX.json'); a=ap.parse_args()
    rows=load_jsonl(); rel=load_relations(); lm=None
    p=ROOT/a.license_matrix
    if p.exists(): lm=json.loads(p.read_text(encoding='utf-8'))
    items=build(rows,rel,lm); schema=json.loads((ROOT/'schema/review_item.schema.json').read_text(encoding='utf-8')); v=Draft202012Validator(schema)
    errs=[(x['id'],e.message) for x in items for e in v.iter_errors(x)]
    if errs: print(json.dumps(errs,indent=2)); raise SystemExit(1)
    payload={'queue_version':'1','items':items,'counts':{k:sum(1 for x in items if x['priority']==k) for k in ['P0','P1','P2','P3']}}
    out=ROOT/a.output; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'items':len(items),'counts':payload['counts']},indent=2))
if __name__=='__main__': main()
