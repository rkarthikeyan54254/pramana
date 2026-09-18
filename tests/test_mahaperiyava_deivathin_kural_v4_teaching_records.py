from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'data'/'review'
def _j(n): return json.loads((R/n).read_text(encoding='utf-8'))
def _jl(n): return [json.loads(x) for x in (R/n).read_text(encoding='utf-8').splitlines() if x.strip()]
def test_v4_hardened_contract():
    rows=_jl('mahaperiyava_deivathin_kural_v4_teaching_records.jsonl')
    idx=_j('mahaperiyava_deivathin_kural_v4_curation_index.json')
    audit=_j('mahaperiyava_deivathin_kural_v4_semantic_completion_audit.json')
    assert len(rows)==457
    assert idx['source_coverage']['curation_paragraph_count']==3208
    assert idx['source_coverage']['covered_curation_paragraph_count']==3139
    assert idx['source_coverage']['explicitly_excluded_curation_paragraphs']==69
    assert idx['source_coverage']['unaccounted_curation_paragraphs']==0
    assert audit['result']=='PASS' and audit['checks']['publication_approved'] is False
