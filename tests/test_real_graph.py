#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'graph/build_all.py')],check=True,cwd=ROOT)
subprocess.run([
    sys.executable,str(ROOT/'graph/audit_graph.py'),str(ROOT/'data/public/graph/global_evidence_graph.json'),
    str(ROOT/'data/public/purana/devi_mahatmya_certified_seed.jsonl'),
    str(ROOT/'data/public/bhagavatam/prahlada_narasimha_certified_seed.jsonl'),
    str(ROOT/'data/public/purana/vishnu_purana_prahlada_certified_seed.jsonl'),
    str(ROOT/'data/public/purana/narasimha_purana_44_certified_seed.jsonl'),
    str(ROOT/'data/public/purana/vishnu_purana_genealogy_seed.jsonl'),
    str(ROOT/'data/public/purana/devi_mahatmya_ritual_seed.jsonl'),
    str(ROOT/'data/public/purana/vamana_purana_temple_ritual_seed.jsonl'),
    '--relations',str(ROOT/'data/public/relations/narasimha_bhagavata_vishnu_purana_relations.json'),
    str(ROOT/'data/public/relations/narasimha_three_text_relations.json')
],check=True,cwd=ROOT)
x=json.loads((ROOT/'data/public/graph/global_evidence_graph.json').read_text())['graph']
assert len(x['nodes'])==26, len(x['nodes'])
assert len(x['edges'])==35, len(x['edges'])
assert any(n['id']=='avatar:narasimha' for n in x['nodes'])
assert any(n['id']=='person:prahlada' for n in x['nodes'])
assert any(n['id']=='lineage:daitya' for n in x['nodes'])
assert any(n['id']=='place:srisaila' for n in x['nodes'])
assert any(n['id']=='text:narasimha_purana' for n in x['nodes'])
assert any(e['predicate']=='father_of' and e['subject']=='person:hiranyakashipu' and e['object']=='person:prahlada' for e in x['edges'])
assert any(e['kind']=='textual_relation' and e.get('relation_ids') for e in x['edges'])

assert any(n['id']=='person:virocana' for n in x['nodes'])
assert any(n['id']=='person:bali' for n in x['nodes'])
assert any(n['id']=='temple:hari_kesava_generic' for n in x['nodes'])
assert any(n['id']=='ritual:temple_lamp_offering' for n in x['nodes'])
assert any(n['id']=='festival:annual_autumn_mahapuja' for n in x['nodes'])
assert any(e['predicate']=='father_of' and e['subject']=='person:virocana' and e['object']=='person:bali' for e in x['edges'])
assert any(e['kind']=='temple_link' for e in x['edges'])
assert not any('purana.devi_mahatmya.92.3' in e['evidence_ids'] for e in x['edges'])
assert all(n.get('evidence_ids') for n in x['nodes'])
assert all(e.get('evidence_ids') for e in x['edges'])
print('real graph: PASS')
