#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from product.common import load_jsonl, load_graph, load_relations

def canonical(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def sha(obj): return hashlib.sha256(canonical(obj)).hexdigest()

def collect_ids(obj):
    out=set()
    def walk(x,key=None):
        if isinstance(x,dict):
            if isinstance(x.get('id'),str) and key=='evidence': out.add(x['id'])
            for k,v in x.items():
                if k in {'support_ids','evidence_ids'} and isinstance(v,list): out.update(i for i in v if isinstance(i,str))
                elif k=='evidence' and isinstance(v,dict) and isinstance(v.get('id'),str): out.add(v['id'])
                else: walk(v,k)
        elif isinstance(x,list):
            for y in x: walk(y,key)
    walk(obj)
    return out

def source_meta(rows):
    p=ROOT/'sources/LICENSE_MATRIX.json'; matrix=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'sources':[]}
    entries=matrix.get('sources',[]); used=[]; seen=set()
    texts=[]
    for r in rows: texts += [r.get('source',''),r.get('verification_source','')]
    for e in entries:
        url=e.get('url','')
        if url and any(url in t or t in url for t in texts if t):
            if e.get('key') not in seen: used.append(e); seen.add(e.get('key'))
    # Preserve unmatched provenance strings explicitly.
    matched=' '.join((e.get('url','') for e in used))
    for t in sorted(set(x for x in texts if x)):
        if t not in matched and not any((e.get('url','') and e.get('url','') in t) for e in used):
            used.append({'key':f'unmatched:{hashlib.sha256(t.encode()).hexdigest()[:10]}','url':t,'classification':'unmatched_provenance','reason':'No exact LICENSE_MATRIX entry matched this provenance string.'})
    return used

def build(evidence_ids,context):
    all_rows={r['id']:r for r in load_jsonl()}
    missing=sorted(set(evidence_ids)-set(all_rows))
    if missing: raise ValueError(f'Unknown evidence ids: {missing}')
    rows=[]
    for eid in sorted(set(evidence_ids)):
        r=all_rows[eid]
        if r.get('verified') is not True or not r.get('verification_source'): raise ValueError(f'Unverified evidence cannot enter proof bundle: {eid}')
        rows.append(r)
    relations=[]
    for rel in load_relations():
        support=set(rel.get('left',{}).get('support_ids',[])+rel.get('right',{}).get('support_ids',[]))
        if support and support.issubset(set(evidence_ids)): relations.append(rel)
    g=load_graph(); nodes=[]; edges=[]
    for n in g.get('nodes',[]):
        if set(n.get('evidence_ids',[])) & set(evidence_ids) or set(n.get('relation_ids',[])) & {r['id'] for r in relations}: nodes.append(n)
    node_ids={n['id'] for n in nodes}
    for e in g.get('edges',[]):
        if (set(e.get('evidence_ids',[])) & set(evidence_ids)) or (set(e.get('relation_ids',[])) & {r['id'] for r in relations}):
            edges.append(e); node_ids.update([e['subject'],e['object']])
    byid={n['id']:n for n in g.get('nodes',[])}
    nodes=[byid[n] for n in sorted(node_ids) if n in byid]
    payload_core={'query_context':context,'evidence_ids':sorted(set(evidence_ids)),'records':rows,'relations':relations,'graph':{'nodes':nodes,'edges':edges},'sources':source_meta(rows)}
    bundle={
      'bundle_version':'1','bundle_id':'proof.'+sha(payload_core)[:16],
      'created_at':datetime.now(timezone.utc).isoformat(),'authority_policy':'verified corpus evidence only',**payload_core,
      'integrity':{'algorithm':'sha256','record_hashes':{r['id']:sha(r) for r in rows},'bundle_payload_sha256':sha(payload_core)}
    }
    schema=json.loads((ROOT/'schema/proof_bundle.schema.json').read_text(encoding='utf-8')); errs=list(Draft202012Validator(schema).iter_errors(bundle))
    if errs: raise ValueError('; '.join(e.message for e in errs))
    return bundle

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--evidence-id',action='append',default=[]); ap.add_argument('--from-json'); ap.add_argument('--context',default='{}'); ap.add_argument('--output',required=True); a=ap.parse_args()
    ids=set(a.evidence_id)
    ctx=json.loads(a.context)
    if a.from_json:
        obj=json.loads(Path(a.from_json).read_text(encoding='utf-8')); ids |= collect_ids(obj); ctx={'source_artifact':a.from_json,**ctx}
    if not ids: raise SystemExit('No evidence ids found/provided.')
    bundle=build(ids,ctx); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(bundle,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'bundle_id':bundle['bundle_id'],'records':len(bundle['records']),'relations':len(bundle['relations']),'nodes':len(bundle['graph']['nodes']),'edges':len(bundle['graph']['edges'])},indent=2))
if __name__=='__main__': main()
