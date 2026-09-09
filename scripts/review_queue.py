#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('queue'); ap.add_argument('item_id'); ap.add_argument('--status',required=True,choices=['open','in_review','resolved','rejected','deferred']); ap.add_argument('--reviewed-by'); ap.add_argument('--notes'); ap.add_argument('--resolution'); a=ap.parse_args()
    p=Path(a.queue); q=json.loads(p.read_text(encoding='utf-8')); hit=None
    for x in q['items']:
        if x['id']==a.item_id: hit=x; break
    if not hit: raise SystemExit(f'unknown review item: {a.item_id}')
    hit['status']=a.status
    if a.reviewed_by is not None: hit['reviewed_by']=a.reviewed_by
    if a.notes is not None: hit['review_notes']=a.notes
    if a.resolution is not None: hit['resolution']=a.resolution
    if a.status in {'resolved','rejected'} and not hit.get('reviewed_by'): raise SystemExit('resolved/rejected requires --reviewed-by')
    p.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(hit,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
