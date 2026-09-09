#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=root/'tests'/'rag'/'verified_mix.jsonl'; vec=root/'tests'/'rag'/'semantic_vectors.json'
q=root/'rag'/'hybrid_query.py'; a=root/'rag'/'assemble_answer.py'

def run(script,term):
    p=subprocess.run([sys.executable,str(script),term,str(data),'--precomputed',str(vec)],capture_output=True,text=True,check=True)
    return json.loads(p.stdout)
# Query deliberately has no lexical overlap; semantic vector retrieves verified row.
r=run(q,'elephant rescue concept')
assert r['answerable'] is True, r
ids=[x['id'] for x in r['evidence']]
assert ids == ['test.verified.1'], ids
assert 'test.unverified.2' not in ids
p=run(a,'elephant rescue concept')
assert p['answerable'] is True
assert all(c['support_ids'] == ['test.verified.1'] for c in p['claims'])
assert p['generation_contract']['generated_text_may_enter_corpus'] is False
print('semantic-rag: GREEN')
