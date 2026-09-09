#!/usr/bin/env python3
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
root=Path(__file__).resolve().parents[1]
schema=json.loads((root/'schema/comparison.schema.json').read_text(encoding='utf-8'))
# Validate a shape produced by the engine after dropping diagnostic-only keys.
sys.path.insert(0,str(root/'rag'))
from verified_store import load_jsonl
from cross_text_compare import build_comparison
spec=json.loads((root/'tests/rag/cross_text_spec.json').read_text(encoding='utf-8'))
out=build_comparison(load_jsonl([str(root/'tests/rag/cross_text_fixture.jsonl')]),spec)
public={k:v for k,v in out.items() if k in schema['required']}
public['claims']=[{kk:vv for kk,vv in c.items() if kk!='accepted'} for c in public['claims']]
errs=sorted(Draft202012Validator(schema).iter_errors(public),key=lambda e:list(e.path))
if errs:
    for e in errs: print(f"comparison schema error at {list(e.path)}: {e.message}")
    raise SystemExit(1)
print('comparison schema: PASS')
