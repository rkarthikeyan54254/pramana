#!/usr/bin/env python3
import argparse, json, pathlib, re, unicodedata
from iast_to_devanagari import transliterate

LINE_RE = re.compile(r'^(?P<base>\d{8})(?P<pada>[a-zA-Z]?)\s+(?P<text>.+?)\s*$')


def iso15919_to_iast(s: str) -> str:
    s = unicodedata.normalize('NFC', s)
    # Bombay-Indology Unicode Roman uses combining forms such as r̥/l̥ and m̐.
    # Normalize only graphemes with deterministic IAST equivalents used by our transliterator.
    repl = {
        'r̥̄': 'ṝ', 'r̥': 'ṛ', 'l̥̄': 'ḹ', 'l̥': 'ḷ',
        'm̐': 'ँ',  # source candrabindu-like nasalization; transliterator preserves Devanagari mark
    }
    for a,b in repl.items(): s = s.replace(a,b)
    return s


def decode_base(base: str):
    return int(base[:2]), int(base[2:5]), int(base[5:])


def parse_file(path: pathlib.Path, source_url: str):
    acc = {}
    order = []
    for ln, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        if not raw or raw.startswith('%'): continue
        m = LINE_RE.match(raw)
        if not m: raise ValueError(f'unrecognized source line {ln}: {raw[:40]!r}')
        base, pada, text = m.group('base'), m.group('pada'), m.group('text')
        parva, chapter, verse = decode_base(base)
        if base not in acc:
            acc[base] = {'parva':parva,'chapter':chapter,'verse':verse,'cue':None,'padas':[],'lines':[]}
            order.append(base)
        rec=acc[base]; rec['lines'].append(ln)
        text=iso15919_to_iast(text)
        if pada:
            if any(label == pada for label, _ in rec['padas']):
                raise ValueError(f'duplicate pada {base}{pada} at line {ln}')
            rec['padas'].append((pada,text))
        else:
            if rec['cue'] is not None:
                raise ValueError(f'duplicate unlettered cue for {base} at line {ln}')
            rec['cue']=text
    rows=[]; last=None
    for base in order:
        r=acc[base]; locus=(r['parva'],r['chapter'],r['verse'])
        if last and locus <= last:
            raise ValueError(f'non-monotonic locus {locus} after {last}')
        last=locus
        if not r['padas']:
            raise ValueError(f'{base}: no verse padas found')
        padas=[t for _,t in sorted(r['padas'], key=lambda x:x[0])]
        iast=' / '.join(padas)
        try:
            devanagari=transliterate(iast)
        except ValueError as e:
            raise ValueError(f'{base}: transliteration failed: {e}') from e
        flags=['needs_second_source_verification']
        notes=[]
        if r['cue']: notes.append('speaker/source cue: '+r['cue'])
        notes.append('source line(s): '+','.join(map(str,r['lines'])))
        rows.append({
            'id':f"mahabharata.ce.p{r['parva']:02d}.c{r['chapter']:03d}.v{r['verse']:03d}",
            'corpus':'mahabharata','work':'mahabharata_critical_edition','tradition':'general','author':'vyasa',
            'language':'sanskrit','section':{'parva':r['parva'],'chapter':r['chapter']},'unit_no':r['verse'],
            'text_original':devanagari,'text_iast':iast,
            'source':source_url,'source_license':'SOURCE-TERMS','verified':False,
            'verification_source':None,'flags':flags,'notes':' | '.join(notes)
        })
    if not rows: raise ValueError(f'no source units in {path}')
    return rows


def main():
    ap=argparse.ArgumentParser(description='Ingest Bombay-Indology Unicode Roman Mahabharata CE files into canonical JSONL.')
    ap.add_argument('input', nargs='+')
    ap.add_argument('--output', required=True)
    ap.add_argument('--source-base', default='https://bombay.indology.info/mahabharata/text/UR/')
    args=ap.parse_args()
    allrows=[]
    for f in args.input:
        p=pathlib.Path(f)
        allrows.extend(parse_file(p,args.source_base+p.name))
    # global monotonic + duplicate ID check
    seen=set()
    for r in allrows:
        if r['id'] in seen: raise SystemExit(f'duplicate id: {r["id"]}')
        seen.add(r['id'])
    out=pathlib.Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in allrows),encoding='utf-8')
    print(f'ingested {len(allrows)} Mahabharata CE verses from {len(args.input)} file(s)')

if __name__=='__main__': main()
