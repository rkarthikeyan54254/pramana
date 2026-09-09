#!/usr/bin/env python3
"""Deterministic Sanskrit IAST -> Devanagari transliterator.

Purposefully narrow: classical Sanskrit IAST as used by our pinned e-texts.
No guessing, no NLP, no external service. Unsupported alphabetic characters fail closed.
"""
import argparse, re, sys, unicodedata

VOWELS = {
    'a': ('अ',''), 'ā': ('आ','ा'), 'i': ('इ','ि'), 'ī': ('ई','ी'),
    'u': ('उ','ु'), 'ū': ('ऊ','ू'), 'ṛ': ('ऋ','ृ'), 'ṝ': ('ॠ','ॄ'),
    'ḷ': ('ऌ','ॢ'), 'ḹ': ('ॡ','ॣ'), 'e': ('ए','े'), 'ai': ('ऐ','ै'),
    'o': ('ओ','ो'), 'au': ('औ','ौ'),
}
CONS = {
    'k':'क','kh':'ख','g':'ग','gh':'घ','ṅ':'ङ',
    'c':'च','ch':'छ','j':'ज','jh':'झ','ñ':'ञ',
    'ṭ':'ट','ṭh':'ठ','ḍ':'ड','ḍh':'ढ','ṇ':'ण',
    't':'त','th':'थ','d':'द','dh':'ध','n':'न',
    'p':'प','ph':'फ','b':'ब','bh':'भ','m':'म',
    'y':'य','r':'र','l':'ल','v':'व',
    'ś':'श','ṣ':'ष','s':'स','h':'ह',
}
MARKS = {'ṃ':'ं','ṁ':'ं','ḥ':'ः','~':'ँ'}
# longest first
TOKENS = sorted(set(VOWELS)|set(CONS)|set(MARKS), key=len, reverse=True)
TOK_RE = re.compile('|'.join(re.escape(x) for x in TOKENS))
LETTER_RE = re.compile(r'[A-Za-zāīūṛṝḷḹṅñṭḍṇśṣṃṁḥ]')


def transliterate(text: str) -> str:
    text = unicodedata.normalize('NFC', text.lower())
    out=[]; i=0; pending_consonant=False
    while i < len(text):
        # common punctuation / editorial forms
        if text.startswith('//', i):
            if pending_consonant: out.append('्'); pending_consonant=False
            out.append('॥'); i += 2; continue
        if text[i] == '/':
            if pending_consonant: out.append('्'); pending_consonant=False
            out.append('।'); i += 1; continue
        if text[i] in "'’":
            if pending_consonant: out.append('्'); pending_consonant=False
            out.append('ऽ'); i += 1; continue
        if text[i].isspace():
            if pending_consonant: out.append('्'); pending_consonant=False
            out.append(text[i]); i += 1; continue
        if text[i] in '.,;:!?()[]{}—–-0123456789':
            if pending_consonant: out.append('्'); pending_consonant=False
            out.append(text[i]); i += 1; continue

        m = TOK_RE.match(text, i)
        if not m:
            ch=text[i]
            if LETTER_RE.match(ch):
                raise ValueError(f'unsupported IAST sequence at offset {i}: {text[i:i+8]!r}')
            if pending_consonant: out.append('्'); pending_consonant=False
            out.append(ch); i += 1; continue
        tok=m.group(0); i=m.end()
        if tok in CONS:
            if pending_consonant:
                out.append('्')
            out.append(CONS[tok]); pending_consonant=True
        elif tok in VOWELS:
            indep, matra = VOWELS[tok]
            if pending_consonant:
                if tok != 'a': out.append(matra)
                pending_consonant=False
            else:
                out.append(indep)
        else: # marks
            if pending_consonant:
                # inherent a before anusvara/visarga
                pending_consonant=False
            out.append(MARKS[tok])
    if pending_consonant: out.append('्')
    return ''.join(out)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('text', nargs='?')
    ap.add_argument('--stdin', action='store_true')
    args=ap.parse_args()
    src=sys.stdin.read() if args.stdin else args.text
    if src is None: raise SystemExit('provide text or --stdin')
    print(transliterate(src))

if __name__=='__main__': main()
