#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,shutil
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

PROFILE_LICENSES={
 'open':{'PD','PD-TRANS','CC0','CC-BY','CC-BY-4.0','CC-BY-SA','CC-BY-SA-4.0'},
 'research-nc':{'PD','PD-TRANS','CC0','CC-BY','CC-BY-4.0','CC-BY-SA','CC-BY-SA-4.0','CC-BY-NC-SA-4.0'},
 'internal':None,
}

def sha256(p:Path):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def eligible(r,profile):
 if r.get('verified') is not True: return False,'not_verified'
 if not r.get('verification_source'): return False,'missing_verification_source'
 lic=r.get('source_license')
 allow=PROFILE_LICENSES[profile]
 if allow is not None and lic not in allow: return False,f'license_not_allowed:{lic}'
 if not r.get('source'): return False,'missing_source'
 return True,'included'

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--profile',choices=PROFILE_LICENSES,default='research-nc'); ap.add_argument('--root',default='data/public'); ap.add_argument('--outdir'); args=ap.parse_args()
 out=Path(args.outdir or f'dist/{args.profile}');
 if out.exists(): shutil.rmtree(out)
 out.mkdir(parents=True)
 records={}; excluded=Counter(); input_files=[]
 for p in sorted(Path(args.root).rglob('*.jsonl')):
  input_files.append(str(p))
  for ln,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
   if not line.strip(): continue
   r=json.loads(line); ok,reason=eligible(r,args.profile)
   if not ok: excluded[reason]+=1; continue
   rid=r['id']
   if rid in records and records[rid]!=r: raise SystemExit(f'conflicting duplicate id {rid} from {p}:{ln}')
   records[rid]=r
 rp=out/'records.jsonl'
 with rp.open('w',encoding='utf-8') as f:
  for rid in sorted(records): f.write(json.dumps(records[rid],ensure_ascii=False,separators=(',',':'))+'\n')
 # Filter global evidence graph to released evidence IDs.
 graph_src=Path(args.root)/'graph/global_evidence_graph.json'
 graph_out={'version':'1.0','nodes':[],'edges':[]}
 if graph_src.exists():
  raw=json.loads(graph_src.read_text(encoding='utf-8'))
  g=raw.get('graph',raw)
  edges=[e for e in g.get('edges',[]) if e.get('evidence_ids') and all(x in records for x in e['evidence_ids'])]
  used={e.get('subject',e.get('from')) for e in edges}|{e.get('object',e.get('to')) for e in edges}
  used.discard(None)
  # A released node must itself be evidence-backed by released rows unless it is explicitly taxonomy-only.
  nodes=[]
  for n in g.get('nodes',[]):
   if n.get('id') not in used: continue
   ev=n.get('evidence_ids',[])
   if ev and not all(x in records for x in ev): continue
   nodes.append(n)
  node_ids={n['id'] for n in nodes}
  edges=[e for e in edges if e.get('subject',e.get('from')) in node_ids and e.get('object',e.get('to')) in node_ids]
  graph_out={'id':g.get('id','release-evidence-graph'),'nodes':nodes,'edges':edges,'policy':g.get('policy')}
 (out/'evidence_graph.json').write_text(json.dumps(graph_out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 by_corpus=Counter(r.get('corpus','unknown') for r in records.values()); by_work=Counter(r.get('work','unknown') for r in records.values()); by_license=Counter(r.get('source_license','unknown') for r in records.values())
 manifest={
  'release_profile':args.profile,'generated_at_utc':datetime.now(timezone.utc).isoformat(),
  'policy':'verified rows only; profile-approved primary source licenses only; restricted second witnesses may be cited as verification metadata but their protected text is not redistributed.',
  'record_count':len(records),'graph_node_count':len(graph_out['nodes']),'graph_edge_count':len(graph_out['edges']),
  'counts_by_corpus':dict(sorted(by_corpus.items())),'counts_by_work':dict(sorted(by_work.items())),'counts_by_source_license':dict(sorted(by_license.items())),
  'excluded_counts':dict(sorted(excluded.items())),'input_jsonl_files':input_files,
  'artifacts':{}
 }
 for p in [rp,out/'evidence_graph.json']:
  manifest['artifacts'][p.name]={'sha256':sha256(p),'bytes':p.stat().st_size}
 mp=out/'release_manifest.json'; mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f"release profile={args.profile} records={len(records)} graph={len(graph_out['nodes'])}n/{len(graph_out['edges'])}e excluded={sum(excluded.values())}")
if __name__=='__main__': main()
