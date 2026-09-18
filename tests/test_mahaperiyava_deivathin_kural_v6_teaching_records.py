from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'data'/'review'
def _j(n): return json.loads((R/n).read_text(encoding='utf-8'))
def _jl(n): return [json.loads(x) for x in (R/n).read_text(encoding='utf-8').splitlines() if x.strip()]
def test_v6_hardened_contract():
    rows=_jl('mahaperiyava_deivathin_kural_v6_teaching_records.jsonl')
    idx=_j('mahaperiyava_deivathin_kural_v6_curation_index.json')
    audit=_j('mahaperiyava_deivathin_kural_v6_semantic_completion_audit.json')
    assert len(rows)==254
    assert idx['source_coverage']['curation_paragraph_count']==3160
    assert idx['source_coverage']['covered_curation_paragraph_count']==3160
    assert idx['source_coverage']['explicitly_excluded_curation_paragraphs']==0
    assert idx['source_coverage']['unaccounted_curation_paragraphs']==0
    assert audit['result']=='PASS' and audit['checks']['publication_approved'] is False
