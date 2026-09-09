#!/usr/bin/env python3
import argparse, html, json, pathlib, re
TAG=re.compile(r'<[^>]+>')
LOC=re.compile(r'(?P<text>.*?)\s*//\s*BhP_(?P<s>\d{2})\.(?P<c>\d{2})\.(?P<v>\d{3})\*?\s*//')

def textify(raw):
    raw=re.sub(r'<br\s*/?>','\n',raw,flags=re.I); raw=TAG.sub('',raw); return html.unescape(raw)

def parse(raw):
    txt=textify(raw); out=[]; seen=set()
    for m in LOC.finditer(txt):
        key=(int(m['s']),int(m['c']),int(m['v']))
        if key in seen: raise ValueError(f'duplicate locus {key}')
        seen.add(key)
        t=' '.join(m['text'].splitlines()[-2:]); t=re.sub(r'\s+',' ',t).strip()
        if not t: raise ValueError(f'empty locus {key}')
        out.append((*key,t))
    if not out: raise ValueError('no BhP loci found')
    sk=sorted({s for s,_,_,_ in out})
    if sk != list(range(1,13)): raise ValueError(f'skandha coverage mismatch: {sk}')
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output'); a=ap.parse_args()
    rows=parse(pathlib.Path(a.input).read_text(encoding='utf-8'))
    p=pathlib.Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as f:
        for s,c,v,t in rows:
            rec={'id':f'bhagavatam.{s}.{c}.{v}','corpus':'bhagavatam','work':'bhagavata_purana','tradition':'general','author':'vyasa','language':'sanskrit','section':{'skandha':s,'chapter':c},'unit_no':v,'text_original':t,'text_iast':t,'source':'gretil_bhagavata_1_12','source_license':'CC-BY-NC-SA-4.0','verified':False,'flags':['needs_second_source'],'notes':f'Parent locus BhP_{s:02}.{c:02}.{v:03}'}
            f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(f'wrote {len(rows)} verses across 12 skandhas')
if __name__=='__main__': main()
