#!/usr/bin/env python3
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rag'))
from verified_store import load_jsonl
from variant_relations import build_relations
from evidence_graph import build_graph
rows=load_jsonl([str(ROOT/'tests/rag/cross_text_fixture.jsonl')])
rel_spec=json.loads((ROOT/'tests/rag/variant_relation_spec.json').read_text())
relations=build_relations(rows,rel_spec)
graph_spec=json.loads((ROOT/'tests/rag/evidence_graph_spec.json').read_text())
out=build_graph(rows,graph_spec,relations)
assert {e['id'] for e in out['graph']['edges']} == {'edge.fixture.bhagavata','edge.fixture.relation'}
assert {n['id'] for n in out['graph']['nodes']} == {'episode:prahlada_narasimha','text:bhagavata_purana','text:vishnu_purana'}
assert out['rejected_nodes'][0]['id'] == 'text:alwar_fixture'
reasons={e['id']:e['reason'] for e in out['rejected_edges']}
assert reasons['edge.bad.unverified']=='unknown_or_unverified_node'
assert reasons['edge.bad.unreviewed']=='missing_reviewer'
schema=json.loads((ROOT/'schema/evidence_graph.schema.json').read_text())
errs=list(Draft202012Validator(schema).iter_errors(out['graph'])); assert not errs, errs
assert out['graph']['policy']['silent_harmonization'] is False
print('evidence graph: PASS')
