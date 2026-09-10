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
from html.parser import HTMLParser

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

class VerseTables(HTMLParser):
    """Read table cells even in legacy HTML with omitted closing td tags."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[]; self.contexts=[]; self.heading=None; self.heading_buf=None; self.row_heading=None; self.cells=None; self.cell=None
    def end_cell(self):
        if self.cells is not None and self.cell is not None:
            self.cells.append(' '.join(''.join(self.cell).split()))
        self.cell=None
    def end_row(self):
        self.end_cell(); self.rows.append(self.cells); self.contexts.append(self.row_heading); self.cells=None
    def handle_starttag(self,tag,attrs):
        if tag in ('h2','h3'):
            self.heading_buf=[]
        if tag=='tr':
            if self.cells is not None:
                self.end_row()
            self.cells=[]; self.row_heading=self.heading
        elif tag in ('td','th'):
            if self.cells is None: self.cells=[]; self.row_heading=self.heading
            self.end_cell(); self.cell=[]
        elif tag=='br' and self.cell is not None: self.cell.append(' ')
    def handle_endtag(self,tag):
        if tag in ('h2','h3') and self.heading_buf is not None:
            m=PATIKAM.fullmatch(' '.join(''.join(self.heading_buf).split()))
            if m: self.heading=(int(m[1]),int(m[2]),m[3])
            self.heading_buf=None
        if tag in ('td','th'): self.end_cell()
        elif tag=='tr' and self.cells is not None:
            self.end_row()
    def handle_data(self,data):
        if self.heading_buf is not None: self.heading_buf.append(data)
        if self.cell is not None: self.cell.append(data)

def parse(path: Path, tirumurai: int):
    raw=path.read_text(encoding='utf-8-sig')
    parser=VerseTables(); parser.feed(raw)
    if parser.cells is not None:
        parser.end_row()
    rows=[]; seen=set(); previous=None
    for cells,heading in zip(parser.rows,parser.contexts):
        loci=[(i,LOCUS.fullmatch(c)) for i,c in enumerate(cells) if LOCUS.fullmatch(c)]
        if not loci and not heading:
            continue  # numbered contents rows precede explicit patikam headings
        if not loci:
            # Some editions print the chapter in a heading and only the local
            # verse number in the final cell. Both components are source-backed.
            if len(cells)>=3 and any(TAMIL.search(c) for c in cells[1:-1]) and LEADING_NUM.fullmatch(cells[-1].lstrip('.')):
                if not heading: raise ValueError('local verse number without source patikam heading')
                m=LOCUS.fullmatch(f"{heading[0]}.{heading[1]}.{int(cells[-1].lstrip('.'))}")
                loci=[(len(cells)-1,m)]
            elif len(cells)>=2 and LEADING_NUM.fullmatch(cells[0]) and any(TAMIL.search(c) for c in cells[1:]):
                raise ValueError('verse row missing a terminal locus')
            else: continue
        if len(loci)!=1: raise ValueError('ambiguous verse row: multiple loci')
        idx,m=loci[0]; t,p,v=map(int,m.groups())
        if t!=tirumurai: raise ValueError(f'wrong tirumurai {t}.{p}.{v}')
        key=(t,p,v)
        if key in seen: raise ValueError(f'duplicate source locus {t}.{p}.{v}')
        if previous and key<=previous: raise ValueError('non-monotonic Tevaram source loci')
        text=' '.join(c for c in cells[:idx] if TAMIL.search(c))
        if not text: raise ValueError(f'empty text at {t}.{p}.{v}')
        running=int(cells[0]) if cells and LEADING_NUM.fullmatch(cells[0]) else None
        flags=[]
        if rows and running is not None and rows[-1]['running_no'] is not None and running!=rows[-1]['running_no']+1:
            flags.append('display_running_number_anomaly')
        rows.append({'tirumurai':t,'patikam':p,'verse':v,'running_no':running,
            'title':heading[2] if heading else None,'pann':None,'text':text,'flags':flags})
        seen.add(key); previous=key
    if not rows: raise ValueError('no Tevaram verse loci found')
    source_loci=[tuple(map(int, m.groups())) for m in re.finditer(r'>\s*(\d+)\.(\d+)\.(\d+)\s*<',raw)]
    if any(key not in seen for key in source_loci):
        raise ValueError('not every source verse marker was extracted in order')
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
