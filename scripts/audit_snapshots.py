#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--index',default='sources/SNAPSHOT_INDEX.json'); args=ap.parse_args(); p=Path(args.index)
 if not p.exists(): raise SystemExit('snapshot index missing')
 idx=json.loads(p.read_text()); errs=[]
 for s in idx['snapshots']:
  f=Path(s['path'])
  if not f.exists(): errs.append(f"missing {f}"); continue
  h=hashlib.sha256(f.read_bytes()).hexdigest()
  if h!=s['sha256']: errs.append(f"checksum mismatch {f}")
  side=f.with_suffix(f.suffix+'.sha256')
  if not side.exists() or side.read_text().strip()!=h: errs.append(f"bad sha sidecar {f}")
 if errs:
  print('\n'.join('ERROR '+e for e in errs)); raise SystemExit(1)
 print('snapshot-audit GREEN',idx['snapshot_count'],'snapshots')
if __name__=='__main__': main()
