#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(x): return hashlib.sha256(canon(x)).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bundle'); a=ap.parse_args(); b=json.loads(Path(a.bundle).read_text(encoding='utf-8'))
    sch=json.loads((ROOT/'schema/proof_bundle.schema.json').read_text()); errs=list(Draft202012Validator(sch).iter_errors(b))
    core={k:b[k] for k in ['query_context','evidence_ids','records','relations','graph','sources']}
    bad=[r['id'] for r in b['records'] if b['integrity']['record_hashes'].get(r['id'])!=sha(r)]
    payload_ok=b['integrity']['bundle_payload_sha256']==sha(core)
    ids={r['id'] for r in b['records']}; authority_ok=all(r.get('verified') is True and r.get('verification_source') and r['id'] in set(b['evidence_ids']) for r in b['records']) and set(b['evidence_ids'])==ids
    result={'schema_errors':len(errs),'record_hash_errors':bad,'payload_hash_ok':payload_ok,'authority_ok':authority_ok,'records':len(b['records'])}
    print(json.dumps(result,indent=2))
    if errs or bad or not payload_ok or not authority_ok: raise SystemExit(1)
if __name__=='__main__': main()
