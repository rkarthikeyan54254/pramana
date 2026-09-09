#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; data=root/'tests/rag/verified_mix.jsonl'; script=root/'rag/claim_verifier.py'; product=root/'product/verify_claim.py'
def run(q):
 p=subprocess.run([sys.executable,str(script),q,str(data)],capture_output=True,text=True,check=True); return json.loads(p.stdout)
r=run('ॐ नमो नारायणाय'); assert r['verified'] is True and r['matches'][0]['id']=='test.verified.1' and 'original_script' in r['matches'][0]['match_modes']
r=run('oṃ namo nārāyaṇāya'); assert r['verified'] is True and 'canonical_transliteration' in r['matches'][0]['match_modes']
# ASCII is lossy discovery only, not authentication.
r=run('om namo narayanaya'); assert r['verified'] is False and r['transliteration_candidates']
# This string exists exactly in an unverified row and MUST NOT authenticate.
r=run('असत्यं परीक्षणपाठः'); assert r['verified'] is False and r['verdict']=='no_verified_exact_match' and r['unverified_exact_match_count']==1
p=subprocess.run([sys.executable,str(product),'Everything happens for a reason','--format','markdown'],capture_output=True,text=True,check=True)
assert '**Authenticated:** no.' in p.stdout and 'No evidence' in p.stdout
print('claim-verifier: GREEN')
