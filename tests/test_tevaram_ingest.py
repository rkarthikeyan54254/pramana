#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=Path('/tmp/tevaram_fixture_test.jsonl')
subprocess.run([sys.executable,str(root/'scripts/ingest_tevaram.py'),str(root/'tests/tevaram_fixture.html'),'--tirumurai','1','--author','tirugnanasambandar','--source','fixture','--output',str(out)],check=True)
rows=[json.loads(x) for x in out.read_text(encoding='utf-8').splitlines()]
assert [r['id'] for r in rows]==['tirumurai.tevaram.t1.p1.v1','tirumurai.tevaram.t1.p1.v2','tirumurai.tevaram.t1.p2.v1','tirumurai.tevaram.t1.p2.v2']
# duplicate displayed running number is preserved as anomaly, but source locus stays canonical
assert 'display_running_number_anomaly' in rows[-1]['flags']
assert rows[-1]['section']['source_running_no']==12
print('tevaram-ingest: GREEN')
