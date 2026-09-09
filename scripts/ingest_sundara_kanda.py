#!/usr/bin/env python3
import argparse, html, json, pathlib, re
TAG=re.compile(r'<[^>]+>')
LINE=re.compile(r'(?m)^\s*5\.(?P<s>\d{3})\.(?P<v>\d{3})(?P<p>[a-z])\s+(?P<t>.+?)\s*$')

def textify(raw):
    raw=re.sub(r'<br\s*/?>','\n',raw,flags=re.I); raw=TAG.sub('',raw); return html.unescape(raw)

def parse(raw):
    txt=textify(raw); by={}
    for m in LINE.finditer(txt):
        s,v,p=int(m['s']),int(m['v']),m['p']; t=' '.join(m['t'].split())
        key=(s,v); by.setdefault(key,{})
        if p in by[key]: raise ValueError(f'duplicate pada {s}.{v}{p}')
        by[key][p]=t
    if not by: raise ValueError('no Sundara Kanda loci found')
    sargas=sorted({s for s,_ in by})
    if sargas!=list(range(1,67)): raise ValueError(f'sarga coverage mismatch: first={sargas[:3]} last={sargas[-3:]} count={len(sargas)}')
    rows=[]
    for (s,v),parts in sorted(by.items()):
        # GRETIL typically exposes a/c half-verse lines; retain any other pada markers in lexical order.
        rows.append((s,v,' / '.join(parts[p] for p in sorted(parts))))
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output'); a=ap.parse_args()
    rows=parse(pathlib.Path(a.input).read_text(encoding='utf-8'))
    p=pathlib.Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as f:
        for s,v,t in rows:
            rec={'id':f'ramayana.valmiki_critical.k5.s{s}.v{v}','corpus':'ramayana','work':'valmiki_ramayana','tradition':'general','author':'valmiki','language':'sanskrit','section':{'kanda':5,'sarga':s},'unit_no':v,'text_original':t,'text_iast':t,'source':'gretil_ramayana_sundara','source_license':'REVIEW_REQUIRED','verified':False,'flags':['needs_second_source','license_review'],'notes':f'Sundara Kanda parent locus 5.{s:03}.{v:03}'}
            f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(f'wrote {len(rows)} sloka records across 66 sargas')
if __name__=='__main__': main()
