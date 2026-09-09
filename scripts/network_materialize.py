#!/usr/bin/env python3
"""Network-host orchestration for priority corpus materialization.

This script deliberately separates *acquisition* from *authority*:
- fetching a source only creates a checksummed raw snapshot;
- ingestion creates staging rows;
- only explicit second-source certification promotes verified rows.

Run this on a network-enabled laptop/CI host, never by reconstructing missing scripture text.
"""
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'sources/manifest.json').read_text(encoding='utf-8'))
MAN={x['key']:x for x in MANIFEST['sources']}
CAT=json.loads((ROOT/'schema/work_catalog.json').read_text(encoding='utf-8'))
GROUPS=json.loads((ROOT/'sources/PRIORITY_GROUPS.json').read_text(encoding='utf-8'))['groups']

def call(cmd):
    print('+',' '.join(map(str,cmd)))
    subprocess.run([str(x) for x in cmd],cwd=ROOT,check=True)

def count_jsonl(p):
    return sum(1 for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip())

def fetch_group(name,force=False):
    keys=GROUPS[name]['keys']
    cmd=[sys.executable,'scripts/fetch_sources.py','sources/manifest.json','--keys',','.join(keys)]
    if force: cmd.append('--force')
    call(cmd); call([sys.executable,'scripts/audit_snapshots.py'])

def materialize_divya():
    outdir=ROOT/'data/staging/divya_prabandham'; outdir.mkdir(parents=True,exist_ok=True)
    total=0
    for w in CAT['divya_prabandham']['works']:
        out=outdir/f"{w['work']}.jsonl"
        call([sys.executable,'scripts/ingest_work.py',w['work'],'--output',out])
        n=count_jsonl(out)
        if n!=w['expected_units']: raise SystemExit(f"{w['work']} count {n}!={w['expected_units']}")
        total+=n
    if total!=4000: raise SystemExit(f'Divya Prabandham total {total} != 4000')
    print('MATERIALIZED Divya Prabandham',total)

def materialize_tevaram():
    outdir=ROOT/'data/staging/tevaram'; outdir.mkdir(parents=True,exist_ok=True)
    grand=0
    for t in CAT['tevaram']['tirumurai']:
        allrows=[]; ids=set()
        for key in t['source_keys']:
            s=MAN[key]; tmp=outdir/f"t{t['tirumurai']}_{key}.jsonl"
            call([sys.executable,'scripts/ingest_tevaram.py',ROOT/s['path'],'--tirumurai',t['tirumurai'],'--author',t['author'],'--source',s['url'],'--output',tmp])
            for line in tmp.read_text(encoding='utf-8').splitlines():
                if not line.strip(): continue
                r=json.loads(line)
                if r['id'] in ids: raise SystemExit(f"duplicate Tevaram id across source parts: {r['id']}")
                ids.add(r['id']); allrows.append(r)
        allrows.sort(key=lambda r:(r['section']['tirumurai'],r['section']['patikam'],int(r['unit_no'])))
        out=outdir/f"tirumurai_{t['tirumurai']}.jsonl"
        out.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in allrows)+'\n',encoding='utf-8')
        if len(allrows)!=t['expected_units']: raise SystemExit(f"Tevaram t{t['tirumurai']} count {len(allrows)}!={t['expected_units']}")
        grand+=len(allrows)
    if grand!=8240: raise SystemExit(f'Tevaram total {grand} != 8240')
    print('MATERIALIZED Tevaram',grand)

def materialize_devi():
    src=ROOT/MAN['gretil-markandeya-1-93']['path']
    second=MAN['vedpath-durga-saptashati']
    sec=[ROOT/second['path'].format(chapter=i,CHAPTER=i) for i in second['chapters']]
    staging=ROOT/'data/staging/devi_mahatmya.jsonl'; ver=ROOT/'data/staging/devi_mahatmya_verification.jsonl'; cert=ROOT/'data/public/purana/devi_mahatmya_full_certified.jsonl'
    call([sys.executable,'scripts/ingest_devi_mahatmya.py',src,staging])
    call([sys.executable,'scripts/verify_devi_mahatmya_secondary.py',staging,*sec,'--output',ver])
    call([sys.executable,'scripts/certify_devi_mahatmya.py',staging,ver,cert])
    call([sys.executable,'scripts/audit_devi_certification.py',staging,ver,'--certified-jsonl',cert])
    call([sys.executable,'scripts/validate.py',cert])
    print('CERTIFIED Devi Mahatmya',count_jsonl(cert))

def materialize_bhagavata():
    src=ROOT/MAN['gretil-bhagavata-1-12']['path']; out=ROOT/'data/staging/bhagavata_parent.jsonl'
    call([sys.executable,'scripts/ingest_bhagavata.py',src,out]); call([sys.executable,'scripts/validate.py',out])
    print('MATERIALIZED Bhagavata staging',count_jsonl(out),'(not promoted: second-source verification still required)')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--group',choices=GROUPS,default='core-materialization'); ap.add_argument('--fetch',action='store_true'); ap.add_argument('--force-fetch',action='store_true'); ap.add_argument('--materialize',action='store_true'); args=ap.parse_args()
    if args.fetch: fetch_group(args.group,args.force_fetch)
    if not args.materialize: return
    if args.group=='core-materialization':
        materialize_divya(); materialize_tevaram(); materialize_devi(); materialize_bhagavata()
    elif args.group=='mahabharata-parent':
        paths=[ROOT/MAN[k]['path'] for k in GROUPS[args.group]['keys']]
        out=ROOT/'data/staging/mahabharata_critical_edition.jsonl'
        call([sys.executable,'scripts/ingest_mahabharata_ce.py',*paths,'--output',out]); call([sys.executable,'scripts/validate.py',out])
        call([sys.executable,'scripts/materialize_mahabharata_slices.py',out,'--outdir',ROOT/'data/staging/mahabharata_slices'])
    elif args.group=='sundara-verification':
        print('Sundara source snapshots acquired. Full Baroda-print transcription comparison remains a separate manual/print-witness gate.')
if __name__=='__main__': main()
