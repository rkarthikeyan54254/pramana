#!/usr/bin/env python3
"""Align Devī Māhātmya primary GRETIL rows with a secondary liturgical edition.

Why sequence alignment instead of verse-number equality?
Secondary editions such as Ved Path number standalone speaker cues (uvāca) as
mantras, while GRETIL's Markandeya Purana source leaves many of those cues
unnumbered. The substantive śloka stream therefore drifts numerically even when
text agrees. We align normalized text in order and preserve BOTH native loci.
"""
import argparse, html, json, pathlib, re, unicodedata
from difflib import SequenceMatcher
from bs4 import BeautifulSoup

TAG = re.compile(r"<[^>]+>")
IAST_LOC = re.compile(r"(?P<text>[^\n]+?)\s*\|\|\s*(?P<ch>\d+)\.(?P<v>\d+)\s*\|\|")
SPEAKER_ONLY = re.compile(r"^(?:mārkaṇḍeya|ṛṣi|rājā|vaiśya|devī|śrīdevī|śrībhagavān|dūta|niśumbha|śumbha)\s*ru?vāca$|^(?:mārkaṇḍeya|ṛṣi|rājā|vaiśya|devī|śrīdevī|śrībhagavān|dūta|niśumbha|śumbha)\s*uvāca$", re.I)


def textify(raw: str) -> str:
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    return html.unescape(TAG.sub("\n", raw))


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower()
    s = s.replace("’", "'").replace("ऽ", "'")
    # normalize common web romanization punctuation but retain letters/diacritics
    s = re.sub(r"[|/।॥.,;:!?()\[\]{}\-—–'\"`~]", " ", s)
    # Never delete lexical syllables to manufacture agreement.
    return re.sub(r"\s+", " ", s).strip()


def parse_secondary_html(raw: str):
    soup = BeautifulSoup(raw, 'html.parser')
    blocks = soup.select('.verse-block > p[lang="en"]') or soup.find_all('p')
    txt = '\n'.join(' '.join(p.get_text(' ', strip=True).split()) for p in blocks)
    out = []
    for m in IAST_LOC.finditer(txt):
        text = m.group('text').strip()
        # Page contains Devanagari followed by IAST. Keep only roman-script lines.
        if re.search(r"[\u0900-\u097f]", text):
            continue
        if not re.search(r"[a-zA-Zāīūṛṝḷḹṅñṭḍṇśṣṃḥ]", text):
            continue
        n = norm(text)
        speaker_key = n.replace(' ', '')
        if not n or speaker_key.endswith('uvāca') and len(speaker_key) < 40:
            continue
        out.append({'chapter': int(m.group('ch')), 'verse': int(m.group('v')), 'text': text, 'norm': n})
    return out


def load_primary(path):
    rows=[]
    for line in pathlib.Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        r=json.loads(line)
        text=r['text_iast']
        rows.append({'id':r['id'],'chapter':r['section']['chapter'],'verse':r['unit_no'],'text':text,'norm':norm(text)})
    return rows


def align(primary, secondary, threshold=1.0):
    by_ch_p={}; by_ch_s={}
    for r in primary: by_ch_p.setdefault(r['chapter'],[]).append(r)
    for r in secondary: by_ch_s.setdefault(r['chapter']+80,[]).append(r)
    results=[]
    for ch in sorted(by_ch_p):
        p=by_ch_p[ch]; s=by_ch_s.get(ch,[])
        # Sequence alignment is over entire verses, with exact compact equality only.
        pn=[r['norm'].replace(' ','') for r in p]
        sn=[r['norm'].replace(' ','') for r in s]
        matches={}
        for block in SequenceMatcher(None,pn,sn,autojunk=False).get_matching_blocks():
            for offset in range(block.size): matches[block.a+offset]=block.b+offset
        for i,pr in enumerate(p):
            k=matches.get(i)
            results.append({'id':pr['id'],'primary_locus':f"MarkP_{ch}.{pr['verse']}",
                'secondary_locus':f"{ch-80}.{s[k]['verse']}" if k is not None else None,
                'score':1.0 if k is not None else 0.0,
                'status':'match' if k is not None else 'needs_review'})
    return results


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('primary_jsonl')
    ap.add_argument('secondary_html', nargs='+')
    ap.add_argument('--output', required=True)
    ap.add_argument('--threshold', type=float, default=1.0)
    a=ap.parse_args()
    if a.threshold != 1.0: ap.error("Only exact normalized equality can certify; threshold must be 1.0")
    primary=load_primary(a.primary_jsonl)
    secondary=[]
    for p in a.secondary_html:
        secondary += parse_secondary_html(pathlib.Path(p).read_text(encoding='utf-8'))
    result=align(primary,secondary,a.threshold)
    out=pathlib.Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in result)+'\n',encoding='utf-8')
    m=sum(x['status']=='match' for x in result)
    print(f'aligned {m}/{len(result)} substantive primary rows; review={len(result)-m}')
    if m != len(result): raise SystemExit(2)

if __name__=='__main__': main()
