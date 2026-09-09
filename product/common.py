from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_PATHS = [
    ROOT/'data/public/bhagavatam/prahlada_narasimha_certified_seed.jsonl',
    ROOT/'data/public/purana/devi_mahatmya_certified_seed.jsonl',
    ROOT/'data/public/purana/devi_mahatmya_ritual_seed.jsonl',
    ROOT/'data/public/purana/narasimha_purana_44_certified_seed.jsonl',
    ROOT/'data/public/purana/vamana_purana_temple_ritual_seed.jsonl',
    ROOT/'data/public/purana/vishnu_purana_genealogy_seed.jsonl',
    ROOT/'data/public/purana/vishnu_purana_prahlada_certified_seed.jsonl',
]
GRAPH_PATH = ROOT/'data/public/graph/global_evidence_graph.json'
RELATION_PATHS = [
    ROOT/'data/public/relations/narasimha_bhagavata_vishnu_purana_relations.json',
    ROOT/'data/public/relations/narasimha_three_text_relations.json',
]

def load_jsonl(paths=DEFAULT_CORPUS_PATHS):
    rows=[]
    for p in paths:
        if not Path(p).exists():
            continue
        with open(p,encoding='utf-8') as f:
            for line in f:
                line=line.strip()
                if line: rows.append(json.loads(line))
    return rows

def evidence_index(rows=None):
    rows = rows if rows is not None else load_jsonl()
    return {r['id']:r for r in rows if r.get('verified') is True and r.get('verification_source')}

def load_graph(path=GRAPH_PATH):
    raw=json.loads(Path(path).read_text(encoding='utf-8'))
    return raw.get('graph',raw)

def load_relations(paths=RELATION_PATHS):
    out=[]
    for p in paths:
        if not Path(p).exists(): continue
        raw=json.loads(Path(p).read_text(encoding='utf-8'))
        out.extend(raw.get('relations',[]))
    return out
