#!/usr/bin/env python3
"""Build an evidence graph without allowing model-inferred nodes or edges to become facts."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verified_store import load_jsonl, verified_only

_ALLOWED_DERIVATIONS = ('deterministic_metadata','curator_reviewed','accepted_cross_source_relation')

def _authority_reason(item, eligible, valid_relation_ids, require_evidence=True):
    ids=item.get('evidence_ids') or []
    deriv=item.get('derivation')
    if require_evidence and not ids:
        return 'missing_evidence_ids'
    if any(i not in eligible for i in ids):
        return 'evidence_not_verified_or_missing'
    if deriv == 'accepted_cross_source_relation':
        if not item.get('relation_ids') or any(i not in valid_relation_ids for i in item['relation_ids']):
            return 'unknown_or_rejected_relation_id'
    elif deriv == 'curator_reviewed' and not item.get('reviewed_by'):
        return 'missing_reviewer'
    elif deriv not in _ALLOWED_DERIVATIONS:
        return 'invalid_or_missing_derivation'
    return None

def build_graph(rows, spec, relations=None):
    eligible = {r['id']: r for r in verified_only(rows)}
    valid_relation_ids = set()
    if relations:
        valid_relation_ids = {r['id'] for r in relations.get('relations', [])}

    # Nodes are facts too. A node must be anchored in verified evidence and have
    # an auditable derivation before an edge is allowed to reference it.
    nodes, rejected_nodes = [], []
    for node in spec.get('nodes', []):
        reason = _authority_reason(node, eligible, valid_relation_ids)
        if reason:
            x=dict(node); x['reason']=reason; rejected_nodes.append(x); continue
        nodes.append({k:v for k,v in node.items() if k in (
            'id','kind','label','aliases','evidence_ids','relation_ids','derivation','reviewed_by','notes')})

    node_ids = {n['id'] for n in nodes}
    edges, rejected = [], []
    for edge in spec.get('edges', []):
        reason=None
        if edge.get('subject') not in node_ids or edge.get('object') not in node_ids:
            reason='unknown_or_unverified_node'
        else:
            reason=_authority_reason(edge, eligible, valid_relation_ids)
        if reason:
            x=dict(edge); x['reason']=reason; rejected.append(x); continue
        edges.append({k:v for k,v in edge.items() if k in ('id','kind','subject','predicate','object','evidence_ids','relation_ids','derivation','reviewed_by','status','notes')})
    graph = {
      'id': spec['id'], 'nodes': nodes, 'edges': edges,
      'policy': {
        'node_authority':'verified corpus evidence only',
        'edge_authority':'verified corpus evidence only',
        'generated_nodes':'forbidden without verified evidence_ids',
        'generated_edges':'forbidden without verified evidence_ids',
        'silent_harmonization':False
      }
    }
    return {'graph': graph, 'rejected_nodes': rejected_nodes, 'rejected_edges': rejected}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('spec_json'); ap.add_argument('paths', nargs='+'); ap.add_argument('--relations')
    a=ap.parse_args(); spec=json.loads(Path(a.spec_json).read_text(encoding='utf-8'))
    rel=json.loads(Path(a.relations).read_text(encoding='utf-8')) if a.relations else None
    print(json.dumps(build_graph(load_jsonl(a.paths),spec,rel), ensure_ascii=False, indent=2))
if __name__=='__main__': main()
