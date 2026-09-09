#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rag')); sys.path.insert(0,str(ROOT/'product'))
from cross_text_compare import build_comparison
from common import load_jsonl, load_relations

DEFAULT_SPEC=ROOT/'product/narasimha_compare_spec.json'
def run(spec_path=DEFAULT_SPEC):
    spec=json.loads(Path(spec_path).read_text(encoding='utf-8'))
    out=build_comparison(load_jsonl(),spec)
    out['experience']='compare_sources'
    accepted_rel=[r for r in load_relations() if r.get('status')=='supported' and r.get('concept')==spec.get('concept')]
    out['reviewed_cross_source_relations']=accepted_rel
    out['moat_contract']={
      'sources_kept_separate':True,
      'silent_harmonization':False,
      'semantic_relations_require_review':True,
      'unsupported_dimensions_render_as_gaps':True
    }
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--spec',default=str(DEFAULT_SPEC)); a=ap.parse_args()
    print(json.dumps(run(Path(a.spec)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
