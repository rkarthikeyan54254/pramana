import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as d:
 d=Path(d);out=d/'cert.jsonl'
 # Historical near-match metadata must no longer pass promotion.
 p=subprocess.run([sys.executable,str(ROOT/'scripts/certify_devi_mahatmya.py'),str(ROOT/'tests/devi_primary_fixture.jsonl'),str(ROOT/'tests/devi_verification_fixture.jsonl'),str(out)],capture_output=True)
 assert p.returncode!=0 and not out.exists()
 # Exact fixture remains certifiable, including conversion and schema checks.
 st=d/'st.jsonl';vr=d/'vr.jsonl'
 st.write_text((ROOT/'tests/devi_primary_fixture.jsonl').read_text().splitlines()[0]+'\n')
 vr.write_text((ROOT/'tests/devi_verification_fixture.jsonl').read_text().splitlines()[0]+'\n')
 subprocess.run([sys.executable,str(ROOT/'scripts/certify_devi_mahatmya.py'),str(st),str(vr),str(out)],check=True)
 subprocess.run([sys.executable,str(ROOT/'scripts/validate.py'),str(out)],check=True)
print('strict Devi certification: PASS')
