#!/usr/bin/env python3
from __future__ import annotations
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from scripts.build_review_queue import build
from scripts.export_proof_bundle import build as proof
from product.common import load_jsonl,load_relations

def main():
    rows=load_jsonl(); rels=load_relations()
    # Synthetic bad rows prove queue creation without polluting authoritative data.
    bad=dict(rows[0]); bad['id']='fixture.unverified.1'; bad['verified']=False; bad['verification_source']=None; bad['flags']=['needs_review','translit_uncertain']
    badv=dict(rows[0]); badv['id']='fixture.variant.1'; badv['variants']=[{'locus':'x','primary':'a','alternatives':[{'reading':'b','status':'needs_source'}]}]
    q=build(rows+[bad,badv],rels,None); kinds={x['kind'] for x in q}
    assert {'verification_mismatch','needs_review_flag','transliteration_uncertain','variant_needs_source'} <= kinds
    eid=rows[0]['id']; b=proof([eid],{'operation':'test','claim':'fixture'})
    assert b['records'][0]['id']==eid and b['records'][0]['verified'] is True
    try: proof(['fixture.unverified.1'],{})
    except ValueError: pass
    else: raise AssertionError('unverified evidence entered proof bundle')
    print(json.dumps({'review_items':len(q),'proof_bundle':b['bundle_id'],'status':'PASS'},indent=2))
if __name__=='__main__': main()
