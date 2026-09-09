#!/usr/bin/env python3
import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 out=Path(td)/'release'
 subprocess.run(['python3','scripts/build_release.py','--profile','research-nc','--outdir',str(out)],cwd=ROOT,check=True)
 subprocess.run(['python3','scripts/check_release.py',str(out)],cwd=ROOT,check=True)
 m=json.loads((out/'release_manifest.json').read_text())
 assert m['record_count']>0
 assert set(m['counts_by_source_license']) <= {'PD','PD-TRANS','CC0','CC-BY','CC-BY-4.0','CC-BY-SA','CC-BY-SA-4.0','CC-BY-NC-SA-4.0'}
 # Open profile must exclude current NC-only seed rows.
 out2=Path(td)/'open'
 subprocess.run(['python3','scripts/build_release.py','--profile','open','--outdir',str(out2)],cwd=ROOT,check=True)
 subprocess.run(['python3','scripts/check_release.py',str(out2)],cwd=ROOT,check=True)
 m2=json.loads((out2/'release_manifest.json').read_text())
 assert m2['record_count'] <= m['record_count']
print('release-builder-test: GREEN')
