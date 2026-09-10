#!/usr/bin/env python3
"""Run independent acquisition/materialization lanes; report every blocked lane.

A successful fetch or ingest never grants authority. Canonical numbering, full
coverage, exact witness equality and publication rights remain separate gates.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAN={x['key']:x for x in json.loads((ROOT/'sources/manifest.json').read_text())['sources']}
CAT=json.loads((ROOT/'schema/work_catalog.json').read_text())
GROUPS=json.loads((ROOT/'sources/PRIORITY_GROUPS.json').read_text())['groups']

def call(cmd):
    subprocess.run([str(x) for x in cmd],cwd=ROOT,check=True)

def source(key):
    p=ROOT/MAN[key]['path']
    sha=p.with_suffix(p.suffix+'.sha256')
    if not p.exists() or not sha.exists(): raise ValueError(f'missing checksummed snapshot: {key}')
    if hashlib.sha256(p.read_bytes()).hexdigest()!=sha.read_text().strip(): raise ValueError(f'snapshot checksum mismatch: {key}')
    return p

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--group',choices=GROUPS,default='core-materialization')
    ap.add_argument('--fetch',action='store_true'); ap.add_argument('--force-fetch',action='store_true'); ap.add_argument('--materialize',action='store_true')
    args=ap.parse_args(); results=[]
    logdir=ROOT/'dist/network'/args.group; logdir.mkdir(parents=True,exist_ok=True)
    def task(name,cmd,out=None,expected=None):
        if out:
            out=Path(out); out.parent.mkdir(parents=True,exist_ok=True)
            # These are generated staging outputs, never canonical evidence.
            # Remove stale results before a retry can report failure.
            if out.exists(): out.unlink()
        with (logdir/f'{name}.log').open('w') as log:
            proc=subprocess.run([str(x) for x in cmd],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        result={'lane':name,'status':'ok' if proc.returncode==0 else 'blocked','exit_code':proc.returncode}
        if proc.returncode==0 and out:
            rows=[json.loads(x) for x in out.read_text().splitlines() if x.strip()]
            result.update(rows=len(rows),verified=sum(r.get('verified') is True for r in rows),output=str(out.relative_to(ROOT)))
            if expected is not None and len(rows)!=expected:
                result.update(status='blocked',reason=f'row count {len(rows)} != {expected}')
                out.unlink()
        if result['status']=='blocked': result.setdefault('reason',(logdir/f'{name}.log').read_text()[-3000:])
        results.append(result); print(name,result['status'],result.get('rows',''),flush=True)
        return result['status']=='ok'
    py=sys.executable
    if args.fetch:
        cmd=[py,'scripts/fetch_sources.py','sources/manifest.json','--keys',','.join(GROUPS[args.group]['keys'])]
        if args.force_fetch: cmd.append('--force')
        task('fetch',cmd)
        task('snapshot-audit',[py,'scripts/audit_snapshots.py'])
    if args.materialize:
        # A changed/missing snapshot blocks ingestion even if an old output exists.
        task('snapshot-audit-before-ingest',[py,'scripts/audit_snapshots.py'])
        if results[-1]['status']!='ok':
            raise SystemExit('snapshot integrity gate failed; no ingestion attempted')
        if args.group=='core-materialization':
            for w in CAT['divya_prabandham']['works']:
                out=ROOT/'data/staging/divya_prabandham'/f"{w['work']}.jsonl"
                if task(w['work'],[py,'scripts/ingest_work.py',w['work'],'--output',out],out,w['expected_units']):
                    task(w['work']+'-schema',[py,'scripts/validate.py',out])
            for t in CAT['tevaram']['tirumurai']:
                parts=[]
                for key in t['source_keys']:
                    s=MAN[key];out=ROOT/'data/staging/tevaram'/f'{key}.jsonl'
                    if task(key,[py,'scripts/ingest_tevaram.py',source(key),'--tirumurai',t['tirumurai'],'--author',t['author'],'--source',s['url'],'--output',out],out):
                        task(key+'-schema',[py,'scripts/validate.py',out]); parts.extend(json.loads(x) for x in out.read_text().splitlines() if x.strip())
                complete=len(parts)==t['expected_units'] and len({r['id'] for r in parts})==len(parts)
                results.append({'lane':f"tevaram-t{t['tirumurai']}-coverage",'status':'ok' if complete else 'blocked','rows':len(parts),'expected':t['expected_units']})
            st=ROOT/'data/staging/devi_mahatmya.jsonl'; vr=ROOT/'data/staging/devi_mahatmya_verification.jsonl'
            if task('devi-ingest',[py,'scripts/ingest_devi_mahatmya.py',source('gretil-markandeya-1-93'),st],st):
                task('devi-schema',[py,'scripts/validate.py',st])
                sec=MAN['vedpath-durga-saptashati']; paths=[ROOT/sec['path'].format(chapter=i) for i in sec['chapters']]
                if task('devi-align',[py,'scripts/verify_devi_mahatmya_secondary.py',st,*paths,'--output',vr],vr):
                    # Certification is built off to the side; only audited output is promoted.
                    cert=ROOT/'dist/devi_full_certified_candidate.jsonl'
                    if task('devi-certify',[py,'scripts/certify_devi_mahatmya.py',st,vr,cert],cert):
                        task('devi-audit',[py,'scripts/audit_devi_certification.py',st,vr,'--certified-jsonl',cert])
                        task('devi-cert-schema',[py,'scripts/validate.py',cert])
                if vr.exists():
                    v=[json.loads(x) for x in vr.read_text().splitlines() if x.strip()]
                    results.append({'lane':'devi-exact-alignment','status':'ok' if all(x['status']=='match' for x in v) else 'blocked','rows':len(v),'exact_matches':sum(x['status']=='match' for x in v),'needs_review':sum(x['status']!='match' for x in v)})
            out=ROOT/'data/staging/bhagavata_parent.jsonl'
            if task('bhagavata-parent',[py,'scripts/ingest_bhagavata.py',source('gretil-bhagavata-1-12'),out],out):
                task('bhagavata-schema',[py,'scripts/validate.py',out])
        elif args.group=='mahabharata-parent':
            out=ROOT/'data/staging/mahabharata_critical_edition.jsonl'
            if task('mahabharata-parent',[py,'scripts/ingest_mahabharata_ce.py',*[source(k) for k in GROUPS[args.group]['keys']],'--output',out],out):
                task('mahabharata-schema',[py,'scripts/validate.py',out])
                task('mahabharata-slices',[py,'scripts/materialize_mahabharata_slices.py',out,'--outdir',ROOT/'data/staging/mahabharata_slices'])
        else: results.append({'lane':'sundara-print-comparison','status':'blocked','reason':'Independent print-witness comparison required.'})
    report={'group':args.group,'run_at_utc':datetime.now(timezone.utc).isoformat(),'results':results,'authority':'No staging record is promoted by acquisition or ingestion.'}
    (logdir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(1 if any(r['status']=='blocked' for r in results) else 0)
if __name__=='__main__':main()
