from __future__ import annotations
import json
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]

def test_mahaperiyava_lineage_validates():
    schema=json.loads((ROOT/'schema/source_lineage_relation.schema.json').read_text(encoding='utf-8'))
    graph=json.loads((ROOT/'data/review/mahaperiyava_source_lineage.json').read_text(encoding='utf-8'))
    v=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
    for rel in graph['relations']: v.validate(rel)

def test_no_authority_inflation():
    graph=json.loads((ROOT/'data/review/mahaperiyava_source_lineage.json').read_text(encoding='utf-8'))
    assert graph['authority']=='UNVERIFIED_ITEM_LEVEL_PROVENANCE'
    assert graph['policy']['collection_lineage_does_not_propagate_to_claims'] is True
    assert graph['policy']['thematic_antecedent_does_not_imply_textual_dependency'] is True
    assert graph['policy']['no_primary_source_upgrade_without_item_level_evidence'] is True
    for rel in graph['relations']:
        assert rel['authority_effect']=='none_without_item_level_review'
        assert rel['evidence_level']!='exact_text'

def test_same_title_guard():
    graph=json.loads((ROOT/'data/review/mahaperiyava_source_lineage.json').read_text(encoding='utf-8'))
    assert any(g['title']=='The Call of the Jagadguru' and 'P. Sankaranarayanan' in g['wanted'] and 'Sringeri' in g['reject_as_same_work'] for g in graph['disambiguation_guards'])
