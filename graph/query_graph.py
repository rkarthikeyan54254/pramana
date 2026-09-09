#!/usr/bin/env python3
"""Inspect an evidence node and its certified neighborhood."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('graph_json'); ap.add_argument('node'); a=ap.parse_args()
    raw=json.loads(Path(a.graph_json).read_text(encoding='utf-8')); g=raw.get('graph',raw)
    nodes={n['id']:n for n in g['nodes']}
    if a.node not in nodes: raise SystemExit(f'unknown node: {a.node}')
    edges=[e for e in g['edges'] if e['subject']==a.node or e['object']==a.node]
    print(json.dumps({'node':nodes[a.node],'edges':edges},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
