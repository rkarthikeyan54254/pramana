#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
q=root/'rag'/'query.py'; data=root/'tests'/'rag'/'verified_mix.jsonl'

def run(term):
    p=subprocess.run([sys.executable,str(q),term,str(data)],capture_output=True,text=True,check=True)
    return json.loads(p.stdout)

a=run('Narayana')
assert a['answerable'] is True
assert [x['id'] for x in a['evidence']] == ['test.verified.1'], a
b=run('asatyaṃ')
assert b['answerable'] is False, b
assert b['evidence'] == [], b
assert 'will not answer from model memory' in b['message']
print('verified-rag: GREEN')
