#!/usr/bin/env python3
"""Moat-gated cross-text comparison.

The model may propose comparison claims, but this module admits only claims whose
support IDs resolve to verified rows from the declared source/work. It preserves
source differences and emits explicit gaps instead of filling them from memory.
"""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verified_store import load_jsonl, verified_only

PUNCT = re.compile(r'[\s\u0964\u0965.,;:!?“”"\'‘’()\[\]{}\-–—_/|]+')
def norm(s): return PUNCT.sub('', unicodedata.normalize('NFC', s or '').casefold())

def _source_matches(row, spec):
    return row.get('corpus') == spec.get('corpus') and row.get('work') == spec.get('work')

def build_comparison(rows, spec):
    eligible = {r['id']: r for r in verified_only(rows)}
    sources = {s['source_key']: s for s in spec['sources']}
    dims = list(spec['dimensions'])
    accepted, rejected = [], []
    presence = {k: False for k in sources}

    for idx, claim in enumerate(spec.get('claims', []), 1):
        item = dict(claim)
        reason = None
        sk = claim.get('source_key')
        ids = claim.get('support_ids') or []
        if sk not in sources:
            reason = 'undeclared_source_key'
        elif claim.get('dimension') not in dims:
            reason = 'undeclared_dimension'
        elif not ids:
            reason = 'missing_support_ids'
        elif any(i not in eligible for i in ids):
            reason = 'support_not_verified_or_missing'
        elif any(not _source_matches(eligible[i], sources[sk]) for i in ids):
            reason = 'support_from_wrong_source_or_work'
        else:
            q = claim.get('quote')
            if q:
                nq = norm(q)
                if not nq or not any(nq in norm(eligible[i].get('text_original','')) or nq in norm(eligible[i].get('text_iast','')) for i in ids):
                    reason = 'quote_not_extractable_from_support'
        if reason:
            item['accepted'] = False; item['reason'] = reason; rejected.append(item)
        else:
            item['accepted'] = True
            item.setdefault('status', 'supported')
            item.setdefault('variant_notes', [])
            accepted.append(item); presence[sk] = True

    out_sources = []
    for sk, s in sources.items():
        o = {k:v for k,v in s.items() if k in ('source_key','corpus','work','tradition')}
        o['status'] = 'evidence_present' if presence[sk] else 'no_verified_evidence'
        out_sources.append(o)

    supplied_gaps = {(g['source_key'], g['dimension']): g for g in spec.get('gaps', [])}
    gaps=[]
    for sk in sources:
        for d in dims:
            has = any(c['source_key']==sk and c['dimension']==d for c in accepted)
            if not has:
                gaps.append(supplied_gaps.get((sk,d), {
                    'source_key': sk, 'dimension': d, 'reason': 'no_verified_evidence'
                }))

    return {
      'id': spec['id'], 'concept': spec['concept'], 'question': spec['question'],
      'dimensions': dims, 'sources': out_sources, 'claims': accepted, 'gaps': gaps,
      'rejected_claims': rejected,
      'evidence_ids': sorted({i for c in accepted for i in c['support_ids']}),
      'policy': {
        'authority':'verified corpus rows only',
        'cross_text_rule':'compare sources; do not collapse them into one harmonized account',
        'model_memory':'not evidence',
        'silent_reconciliation': False
      }
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('spec_json'); ap.add_argument('paths', nargs='+')
    a=ap.parse_args(); spec=json.loads(Path(a.spec_json).read_text(encoding='utf-8'))
    print(json.dumps(build_comparison(load_jsonl(a.paths), spec), ensure_ascii=False, indent=2))
if __name__=='__main__': main()
