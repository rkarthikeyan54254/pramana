#!/usr/bin/env python3
"""Fetch immutable raw source snapshots with provenance sidecars.

Designed for a network-enabled laptop/CI runner. Supports ordinary manifest entries and
chapter-expanded url_template entries. Raw snapshots are never part of a public release;
rights policy is enforced later by build_release.py.
"""
from __future__ import annotations
import argparse,hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path


def expanded(entry):
    if entry.get('url_template') and entry.get('chapters'):
        for chapter in entry['chapters']:
            e=dict(entry)
            e['key']=f"{entry['key']}-ch{chapter}"
            e['url']=entry['url_template'].format(chapter=chapter,CHAPTER=chapter)
            e['path']=entry['path'].format(chapter=chapter,CHAPTER=chapter)
            e['parent_key']=entry['key']; e['chapter']=chapter
            yield e
    else:
        yield entry


def fetch(e,force=False,timeout=45):
    out=Path(e['path']); out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists() and not force:
        data=out.read_bytes(); action='SKIP'
        side=out.with_suffix(out.suffix+'.sha256')
        meta_path=out.with_suffix(out.suffix+'.meta.json')
        if not side.exists() or not meta_path.exists(): raise ValueError(f'unprovenanced existing snapshot: {out}')
        if hashlib.sha256(data).hexdigest()!=side.read_text().strip(): raise ValueError(f'snapshot checksum mismatch: {out}')
        meta=json.loads(meta_path.read_text())
        if meta['sha256']!=hashlib.sha256(data).hexdigest() or meta['url']!=e['url']: raise ValueError(f'snapshot provenance mismatch: {out}')
        print(action,e['key'],len(data),'bytes',meta['sha256'])
        return meta
    else:
        req=urllib.request.Request(e['url'],headers={'User-Agent':'bhakthi-corpus/0.2 provenance-preserving research fetch'})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            data=r.read(); content_type=r.headers.get('Content-Type'); final_url=r.geturl()
        out.write_bytes(data); action='FETCHED'
    sha=hashlib.sha256(data).hexdigest()
    out.with_suffix(out.suffix+'.sha256').write_text(sha+'\n',encoding='utf-8')
    meta={
        'key':e['key'],'parent_key':e.get('parent_key'),'url':e['url'],'path':str(out),
        'sha256':sha,'bytes':len(data),'final_url':final_url,'content_type':content_type,'fetched_or_checked_at_utc':datetime.now(timezone.utc).isoformat(),
        'source_status':e.get('status'),'recorded_terms':e.get('terms'),'covers':e.get('covers')
    }
    out.with_suffix(out.suffix+'.meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(action,e['key'],len(data),'bytes',sha)
    return meta


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest'); ap.add_argument('--force',action='store_true'); ap.add_argument('--keys',help='comma-separated manifest keys'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--index',default='sources/SNAPSHOT_INDEX.json'); args=ap.parse_args()
    manifest=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    wanted=set(args.keys.split(',')) if args.keys else None
    entries=[]
    for base in manifest['sources']:
        if wanted and base['key'] not in wanted: continue
        entries.extend(expanded(base))
    if wanted:
        found={e.get('parent_key',e['key']) for e in entries}; missing=wanted-found
        if missing: raise SystemExit(f'unknown source keys: {sorted(missing)}')
    if args.dry_run:
        for e in entries: print(e['key'],e['url'],'->',e['path'])
        return
    p=Path(args.index); p.parent.mkdir(parents=True,exist_ok=True)
    existing=json.loads(p.read_text()).get('snapshots',[]) if p.exists() else []
    merged={s['key']:s for s in existing}; failures=[]
    for e in entries:
        try: merged[e['key']]=fetch(e,args.force)
        except Exception as error:
            failures.append({'key':e['key'],'error':str(error)}); print('FAILED',e['key'],str(error))
    snapshots=sorted(merged.values(),key=lambda s:s['key'])
    p.write_text(json.dumps({'version':'1.0','snapshot_count':len(snapshots),'snapshots':snapshots},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('snapshot-index',p,len(snapshots))
    if failures:
        p.with_name('FETCH_FAILURES.json').write_text(json.dumps(failures,indent=2)+'\n')
        raise SystemExit(1)
if __name__=='__main__': main()
