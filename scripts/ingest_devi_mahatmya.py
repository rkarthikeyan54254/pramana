#!/usr/bin/env python3
import argparse, html, json, pathlib, re, sys
from bs4 import BeautifulSoup
TAG=re.compile(r'<[^>]+>')
LOC=re.compile(r'(?P<text>.*?)\s*//\s*MarkP_(?P<ch>\d+)\.(?P<v>\d+)\s*//')

def textify(raw):
    raw=re.sub(r'<br\s*/?>','\n',raw,flags=re.I)
    raw=TAG.sub('',raw)
    return html.unescape(raw)

def parse(raw):
    soup=BeautifulSoup(raw, 'html.parser')
    blocks=[p.get_text(' ', strip=True) for p in soup.find_all('p')]
    if not blocks: blocks=textify(raw).splitlines()
    out=[]
    for m in (m for block in blocks for m in LOC.finditer(block)):
        ch,v=int(m['ch']),int(m['v'])
        if 81<=ch<=93:
            verse=' '.join(m['text'].splitlines()[-2:]).strip()
            verse=re.sub(r'\s+',' ',verse)
            if not verse: raise ValueError(f'empty MarkP_{ch}.{v}')
            out.append((ch,v,verse))
    if not out: raise ValueError('no Devi Mahatmya loci found')
    loci=[(c,v) for c,v,_ in out]
    if len(loci)!=len(set(loci)): raise ValueError('duplicate locus')
    chapters=sorted({c for c,_,_ in out})
    if chapters!=list(range(81,94)): raise ValueError(f'chapter coverage mismatch: {chapters}')
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output')
    a=ap.parse_args(); rows=parse(pathlib.Path(a.input).read_text(encoding='utf-8'))
    p=pathlib.Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as f:
        for ch,v,t in rows:
            rec={'id':f'purana.devi_mahatmya.c{ch}.v{v}','corpus':'purana','work':'devi_mahatmya','tradition':'shakta','author':'unknown','language':'sanskrit','section':{'parent_work':'markandeya_purana','chapter':ch},'unit_no':v,'text_original':t,'text_iast':t,'source':'https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_mArkaNDeyapurANa1-93.htm','source_license':'CC-BY-NC-SA-4.0','verified':False,'flags':['needs_second_source','needs_script_normalization'],'notes':f'Parent locus MarkP_{ch}.{v}'}
            f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(f'wrote {len(rows)} rows across 13 chapters')
if __name__=='__main__': main()
