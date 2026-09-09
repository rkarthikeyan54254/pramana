#!/usr/bin/env python3
import json, re
from pathlib import Path

TOKEN_RE = re.compile(r"[\w\u0900-\u097F\u0B80-\u0BFF]+", re.UNICODE)


def load_jsonl(paths):
    rows=[]
    for p in paths:
        p=Path(p)
        if not p.exists():
            continue
        for ln,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
            if not line.strip(): continue
            obj=json.loads(line)
            obj['_file']=str(p); obj['_line']=ln
            rows.append(obj)
    return rows


def verified_only(rows):
    out=[]
    for r in rows:
        if r.get('verified') is True and r.get('verification_source'):
            out.append(r)
    return out


def tokens(text):
    return {t.casefold() for t in TOKEN_RE.findall(text or '') if len(t) > 1}


def searchable_text(r):
    fields=[r.get('id',''),r.get('corpus',''),r.get('work',''),r.get('author',''),r.get('language',''),
            r.get('text_original',''),r.get('text_iast',''),r.get('translation_en',''),r.get('notes','')]
    fields += [str(x) for x in r.get('themes',[]) or []]
    return ' '.join(x for x in fields if x)


def search(rows, query, limit=8):
    q=tokens(query)
    scored=[]
    for r in verified_only(rows):
        rt=tokens(searchable_text(r))
        overlap=len(q & rt)
        exact=1 if query.casefold() in searchable_text(r).casefold() else 0
        if overlap or exact:
            scored.append((exact*100+overlap, r))
    scored.sort(key=lambda x:(-x[0], x[1].get('id','')))
    return [r for _,r in scored[:limit]]


def evidence(r):
    return {
        'id': r['id'],
        'corpus': r['corpus'],
        'work': r['work'],
        'section': r.get('section',{}),
        'unit_no': r['unit_no'],
        'text_original': r['text_original'],
        'text_iast': r.get('text_iast'),
        'translation_en': r.get('translation_en'),
        'source': r['source'],
        'verification_source': r['verification_source'],
        'variants': r.get('variants',[]),
        'flags': r.get('flags',[]),
    }
