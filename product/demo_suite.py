#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from product.verify_claim import run as verify
from product.compare_sources import run as compare
from product.trace_evidence import run as trace

def build():
    return {
      'suite':'pramana_moat_proof_v1',
      'verify_claim':{
        'positive':verify('नरसिंहः स्तम्भमध्याद् निर्गत्य'),
        'negative':verify('Everything happens for a reason')
      },
      'compare_sources':compare(),
      'trace_evidence':trace('person:prahlada',2)
    }
if __name__=='__main__': print(json.dumps(build(),ensure_ascii=False,indent=2))
