#!/usr/bin/env python3
"""Extract numbered Tamil units from a preserved Project Madurai HTML snapshot.

ACQUIRE/STRUCTURE only: never verifies, translates, repairs source numbering, or
fabricates transliteration. Duplicate/out-of-order numbering causes failure.
"""
from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

NUM = re.compile(r'^\s*(\d{1,5})\s+[\t ]*(.*)$')

def visible_lines(path: Path):
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    for raw in soup.get_text('\n').splitlines():
        line=' '.join(raw.split())
        if line: yield line

def extract_occurrences(path: Path,start:int,end:int):
    occurrences=[]; current=None; buf=[]
    def flush():
        nonlocal current,buf
        if current is not None and start<=current<=end and buf:
            occurrences.append((current,' '.join(buf).strip()))
        buf=[]
    for line in visible_lines(path):
        m=NUM.match(line)
        if m:
            n=int(m.group(1))
            if start<=n<=end:
                flush(); current=n
                if m.group(2): buf.append(m.group(2)); continue
            elif current is not None:
                flush(); current=None
        elif current is not None:
            buf.append(line)
    flush(); return occurrences

def main():
    ap=argparse.ArgumentParser()
    for x in ('input','work','author','source','output'): ap.add_argument('--'+x,required=True)
    ap.add_argument('--start',type=int,required=True); ap.add_argument('--end',type=int,required=True)
    ap.add_argument('--source-license',default='PROJECT-MADURAI-SOURCE-TERMS')
    a=ap.parse_args(); occ=extract_occurrences(Path(a.input),a.start,a.end)
    nums=[n for n,_ in occ]; counts=Counter(nums)
    dups=sorted(n for n,v in counts.items() if v>1)
    reversals=[(x,y) for x,y in zip(nums,nums[1:]) if y<x]
    expected=set(range(a.start,a.end+1)); missing=sorted(expected-set(nums)); extras=sorted(set(nums)-expected)
    if dups or reversals or missing or extras:
        parts=[f'FAIL CLOSED source numbering audit for {a.work}: occurrences={len(nums)} unique={len(counts)} expected={len(expected)}']
        if dups: parts.append('duplicates='+','.join(map(str,dups[:40])))
        if reversals: parts.append('reversals='+','.join(f'{x}->{y}' for x,y in reversals[:20]))
        if missing: parts.append('missing='+','.join(map(str,missing[:40])))
        if extras: parts.append('extras='+','.join(map(str,extras[:40])))
        raise SystemExit('; '.join(parts))
    units=dict(occ); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8') as fh:
        for g in range(a.start,a.end+1):
            local=g-a.start+1
            row={'id':f'divya_prabandham.{a.work}.{local}','corpus':'divya_prabandham','work':a.work,'tradition':'sri_vaishnava','author':a.author,'language':'tamil','section':{'global_pasuram_no':g},'unit_no':local,'text_original':units[g],'text_iast':'PENDING_TOOL_TRANSLITERATION','source':a.source,'source_license':a.source_license,'verified':False,'verification_source':None,'flags':['translit_uncertain','needs_verification'],'notes':'Machine-extracted from preserved raw snapshot; source numbering audited; not independently verified.'}
            fh.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(f'wrote {len(units)} staging rows to {out}')
if __name__=='__main__': main()
