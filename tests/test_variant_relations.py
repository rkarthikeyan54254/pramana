#!/usr/bin/env python3
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rag'))
from verified_store import load_jsonl
from variant_relations import build_relations
rows=load_jsonl([str(ROOT/'tests/rag/cross_text_fixture.jsonl')])
spec=json.loads((ROOT/'tests/rag/variant_relation_spec.json').read_text(encoding='utf-8'))
out=build_relations(rows,spec)
assert [r['id'] for r in out['relations']] == ['rel.prahlada.fixture.1']
reasons={r['id']:r['reason'] for r in out['rejected_relations']}
assert reasons['rel.bad.unverified']=='right_support_not_verified_or_missing'
assert reasons['rel.bad.model_semantic']=='semantic_relation_requires_curator_review'
schema=json.loads((ROOT/'schema/cross_source_relation.schema.json').read_text())
v=Draft202012Validator(schema)
for r in out['relations']:
    errs=list(v.iter_errors(r)); assert not errs, errs
assert out['relations'][0]['policy']['silent_resolution'] is False
assert out['relations'][0]['policy']['preferred_side'] is None
print('variant / contradiction relations: PASS')
