#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
from collections import Counter
ALLOWED={
 'open':{'PD','PD-TRANS','CC0','CC-BY','CC-BY-4.0','CC-BY-SA','CC-BY-SA-4.0'},
 'research-nc':{'PD','PD-TRANS','CC0','CC-BY','CC-BY-4.0','CC-BY-SA','CC-BY-SA-4.0','CC-BY-NC-SA-4.0'},
 'internal':None,
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('release_dir'); args=ap.parse_args(); d=Path(args.release_dir)
 m=json.loads((d/'release_manifest.json').read_text()); profile=m['release_profile']; allow=ALLOWED[profile]
 ids=set(); errors=[]; count=0
 for i,line in enumerate((d/'records.jsonl').read_text(encoding='utf-8').splitlines(),1):
  if not line.strip(): continue
  r=json.loads(line); count+=1
  if r.get('verified') is not True: errors.append(f'row {i}: not verified')
  if not r.get('verification_source'): errors.append(f'row {i}: missing verification_source')
  if allow is not None and r.get('source_license') not in allow: errors.append(f"row {i}: disallowed license {r.get('source_license')}")
  if r['id'] in ids: errors.append(f"duplicate id {r['id']}")
  ids.add(r['id'])
 g=json.loads((d/'evidence_graph.json').read_text())
 nodes={n['id'] for n in g.get('nodes',[])}
 for e in g.get('edges',[]):
  subj=e.get('subject',e.get('from')); obj=e.get('object',e.get('to'))
  if subj not in nodes or obj not in nodes: errors.append(f"bad graph node reference {e.get('id')}")
  miss=[x for x in e.get('evidence_ids',[]) if x not in ids]
  if miss: errors.append(f"graph edge {e.get('id')} has unreleased evidence {miss}")
 if count!=m['record_count']: errors.append('manifest record_count mismatch')
 for name,meta in m['artifacts'].items():
  p=d/name
  if sha(p)!=meta['sha256']: errors.append(f'sha mismatch {name}')
 if errors:
  print('\n'.join('ERROR '+x for x in errors)); raise SystemExit(1)
 print(f'release-check GREEN profile={profile} records={count} graph={len(nodes)}n/{len(g.get("edges",[]))}e')
if __name__=='__main__': main()
