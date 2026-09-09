#!/usr/bin/env python3
"""Patikam-aware Tevaram ingester for preserved Project Madurai HTML snapshots.

Trust rules:
- Source-native patikam/verse locus (e.g. 1.2.7) is authoritative for structure.
- Displayed running verse numbers are metadata only because source pages can contain
  duplicate/typo running numbers; we preserve discrepancies as flags.
- Never infer missing verses or silently renumber.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from bs4 import BeautifulSoup

PATIKAM = re.compile(r'^\s*(\d+)\.(\d+)\s+(.+?)\s*$')
LOCUS = re.compile(r'^\s*(\d+)\.(\d+)\.(\d+)\s*$')
LEADING_NUM = re.compile(r'^\s*(\d{1,5})\s*$')
PANN = re.compile(r'^\s*பண்\s*[-–:]\s*(.+?)\s*$')
TAMIL = re.compile(r'[\u0B80-\u0BFF]')

STOP_PREFIXES = ('திருச்சிற்றம்பலம்','உள்ளுறை அட்டவணை','இத்தலம்','சுவாமிபெயர்','தேவியார்','காவிரி','திருத்தோணியில்')

def lines(path: Path):
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    for raw in soup.get_text('\n').splitlines():
        s=' '.join(raw.split())
        if s:
            yield s

def parse(path: Path, tirumurai: int):
    current_pat=None; title=None; pann=None
    current_running=None; buf=[]; rows=[]; seen=set()

    def flush(locus_tuple):
        nonlocal buf,current_running
        if locus_tuple is None: return
        t,p,v=locus_tuple
        text=' '.join(x for x in buf if TAMIL.search(x) and not x.startswith(STOP_PREFIXES)).strip()
        if not text:
            raise ValueError(f'empty text at {t}.{p}.{v}')
        key=(t,p,v)
        if key in seen:
            raise ValueError(f'duplicate source locus {t}.{p}.{v}')
        seen.add(key)
        expected_running = (rows[-1]['running_no']+1) if rows and rows[-1].get('running_no') is not None else None
        flags=[]
        if current_running is not None and expected_running is not None and current_running != expected_running:
            flags.append('display_running_number_anomaly')
        rows.append({'tirumurai':t,'patikam':p,'verse':v,'running_no':current_running,
                     'title':title,'pann':pann,'text':text,'flags':flags})
        buf=[]; current_running=None

    pending_locus=None
    for s in lines(path):
        m=PATIKAM.match(s)
        if m and int(m.group(1))==tirumurai and '.' not in m.group(3)[:5]:
            # headings such as "1.1 திருப்பிரமபுரம்"
            current_pat=int(m.group(2)); title=m.group(3).strip(); pann=None
            continue
        m=PANN.match(s)
        if m:
            pann=m.group(1).strip(); continue
        m=LOCUS.match(s)
        if m:
            locus=tuple(map(int,m.groups()))
            if locus[0] != tirumurai:
                continue
            if current_pat is not None and locus[1] != current_pat:
                # source locus wins; heading mismatch is not silently repaired
                current_pat=locus[1]
            flush(locus)
            pending_locus=None
            continue
        if LEADING_NUM.match(s):
            # A running-number cell usually starts a verse; retain but don't trust for identity.
            current_running=int(s); continue
        if TAMIL.search(s):
            # exclude page-level titles/contents-ish lines with no active patikam
            if current_pat is not None:
                buf.append(s)

    # Loci are terminal markers; no safe way to flush trailing text without a locus.
    # That is deliberate: fail rather than invent identity.
    if buf:
        raise ValueError('trailing Tamil text without terminal source locus')
    if not rows:
        raise ValueError('no Tevaram verse loci found')
    # structural monotonicity by source locus
    loci=[(r['tirumurai'],r['patikam'],r['verse']) for r in rows]
    if any(b<=a for a,b in zip(loci,loci[1:])):
        raise ValueError('non-monotonic or duplicate Tevaram source loci')
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input'); ap.add_argument('--tirumurai',type=int,required=True)
    ap.add_argument('--author',required=True); ap.add_argument('--source',required=True)
    ap.add_argument('--output',required=True); ap.add_argument('--source-license',default='PROJECT-MADURAI-SOURCE-TERMS')
    a=ap.parse_args(); parsed=parse(Path(a.input),a.tirumurai)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8') as fh:
        for r in parsed:
            flags=['translit_uncertain','needs_verification']+r['flags']
            row={
              'id':f"tirumurai.tevaram.t{r['tirumurai']}.p{r['patikam']}.v{r['verse']}",
              'corpus':'tirumurai','work':'tevaram','tradition':'saiva_siddhanta','author':a.author,'language':'tamil',
              'section':{'tirumurai':r['tirumurai'],'patikam':r['patikam'],'patikam_title':r['title'],'pann':r['pann'],'source_running_no':r['running_no']},
              'unit_no':r['verse'],'text_original':r['text'],'text_iast':'PENDING_TOOL_TRANSLITERATION',
              'source':a.source,'source_license':a.source_license,'verified':False,'verification_source':None,
              'flags':flags,'notes':'Machine-extracted using source-native tirumurai.patikam.verse locus; displayed running number preserved as metadata only.'
            }
            fh.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(f'wrote {len(parsed)} Tevaram staging rows to {out}')

if __name__=='__main__': main()
