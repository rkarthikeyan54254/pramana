#!/usr/bin/env python3
"""Evidence-gated contradiction / variant relation builder.

This module never decides which source is 'correct'. It validates that both sides
of a proposed relation are backed by verified rows from the declared sources and
then preserves the difference as structured data.
"""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verified_store import load_jsonl, verified_only

PUNCT = re.compile(r'[\s\u0964\u0965.,;:!?“”"\'‘’()\[\]{}\-–—_/|]+')
def norm(s): return PUNCT.sub('', unicodedata.normalize('NFC', s or '').casefold())

def _quote_ok(quote, ids, eligible):
    if not quote:
        return True
    nq = norm(quote)
    return bool(nq) and any(
        nq in norm(eligible[i].get('text_original','')) or nq in norm(eligible[i].get('text_iast',''))
        for i in ids
    )

def build_relations(rows, spec):
    eligible = {r['id']: r for r in verified_only(rows)}
    source_specs = {s['source_key']: s for s in spec.get('sources', [])}
    accepted, rejected = [], []
    for rel in spec.get('relations', []):
        item = dict(rel)
        reason = None
        for side_name in ('left','right'):
            side = rel.get(side_name) or {}
            sk = side.get('source_key')
            ids = side.get('support_ids') or []
            if sk not in source_specs:
                reason = f'{side_name}_undeclared_source_key'; break
            if not ids:
                reason = f'{side_name}_missing_support_ids'; break
            if any(i not in eligible for i in ids):
                reason = f'{side_name}_support_not_verified_or_missing'; break
            ss = source_specs[sk]
            if any(eligible[i].get('corpus') != ss.get('corpus') or eligible[i].get('work') != ss.get('work') for i in ids):
                reason = f'{side_name}_support_from_wrong_source_or_work'; break
            if not _quote_ok(side.get('quote'), ids, eligible):
                reason = f'{side_name}_quote_not_extractable_from_support'; break
        if reason:
            item['reason'] = reason
            rejected.append(item)
            continue
        basis = rel.get('classification_basis')
        semantic_types = {'agreement','expansion','omission','contradiction','scope_difference','unresolved_difference'}
        if rel.get('relation_type') in semantic_types and basis != 'curator_reviewed':
            item['reason'] = 'semantic_relation_requires_curator_review'
            rejected.append(item); continue
        if basis == 'curator_reviewed' and not rel.get('reviewed_by'):
            item['reason'] = 'missing_reviewer'
            rejected.append(item); continue
        clean = {
            'id': rel['id'], 'concept': rel['concept'], 'dimension': rel['dimension'],
            'relation_type': rel['relation_type'], 'classification_basis': basis,
            'reviewed_by': rel.get('reviewed_by'), 'left': rel['left'], 'right': rel['right'],
            'status': rel.get('status','supported'),
            'notes': rel.get('notes',''),
            'policy': {'authority':'verified corpus rows only','silent_resolution':False,'preferred_side':None}
        }
        accepted.append(clean)
    return {'relations': accepted, 'rejected_relations': rejected}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('spec_json'); ap.add_argument('paths', nargs='+')
    a=ap.parse_args(); spec=json.loads(Path(a.spec_json).read_text(encoding='utf-8'))
    print(json.dumps(build_relations(load_jsonl(a.paths), spec), ensure_ascii=False, indent=2))
if __name__=='__main__': main()
