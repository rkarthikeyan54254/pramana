#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
w=Path('/tmp/ifp_witness.jsonl'); v=Path('/tmp/ifp_verify.jsonl'); c=Path('/tmp/ifp_certified.jsonl')
subprocess.run([sys.executable,str(root/'scripts/parse_ifp_tevaram.py'),str(root/'tests/ifp_tevaram_fixture.html'),'--output',str(w)],check=True)
rows=[json.loads(x) for x in w.read_text(encoding='utf-8').splitlines()]
assert [(x['tirumurai'],x['patikam'],x['verse']) for x in rows]==[(1,1,1),(1,1,2)]
subprocess.run([sys.executable,str(root/'scripts/verify_tevaram_ifp.py'),str(root/'tests/tevaram_ifp_primary_fixture.jsonl'),str(w),'--output',str(v)],check=True)
vr=[json.loads(x) for x in v.read_text(encoding='utf-8').splitlines()]
assert all(x['status']=='verified_exact_normalized' for x in vr)
subprocess.run([sys.executable,str(root/'scripts/certify_tevaram_ifp.py'),str(root/'tests/tevaram_ifp_primary_fixture.jsonl'),str(v),str(c)],check=True)
cr=[json.loads(x) for x in c.read_text(encoding='utf-8').splitlines()]
assert all(x['verified'] for x in cr)
assert all(x['verification_source'] for x in cr)
print('tevaram-ifp-verification: GREEN')
