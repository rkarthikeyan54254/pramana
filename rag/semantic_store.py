#!/usr/bin/env python3
"""Semantic retrieval over VERIFIED corpus rows only.

Embeddings improve recall, never authority. This module refuses to embed or return
rows that do not pass the verified-only gate.

Backends:
- sentence_transformers: optional, when installed locally.
- precomputed: deterministic JSON vectors for tests/offline pipelines.
"""
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from verified_store import verified_only, searchable_text


def cosine(a: List[float], b: List[float]) -> float:
    if len(a) != len(b) or not a:
        return -1.0
    dot=sum(x*y for x,y in zip(a,b))
    na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    if na == 0 or nb == 0: return -1.0
    return dot/(na*nb)


def load_precomputed(path: str|Path) -> Dict[str,List[float]]:
    obj=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(obj,dict):
        raise ValueError('precomputed embeddings must be a JSON object')
    return obj


def sentence_transformer_embed(texts: List[str], model_name: str) -> List[List[float]]:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError('sentence-transformers backend unavailable; install locally or use --precomputed') from e
    model=SentenceTransformer(model_name)
    vecs=model.encode(texts, normalize_embeddings=True)
    return [list(map(float,v)) for v in vecs]


def semantic_search(rows, query: str, limit: int=8, *, model_name: str|None=None,
                    precomputed: Dict[str,List[float]]|None=None,
                    query_vector: List[float]|None=None,
                    min_score: float=0.15) -> List[Tuple[float,dict]]:
    candidates=verified_only(rows)  # AUTHORITY GATE BEFORE EMBEDDING
    if not candidates: return []

    if precomputed is not None:
        if query_vector is None:
            query_vector=precomputed.get('__query__')
        if query_vector is None:
            raise ValueError('precomputed mode requires query_vector or __query__ vector')
        scored=[]
        for r in candidates:
            v=precomputed.get(r['id'])
            if v is None: continue
            s=cosine(query_vector,v)
            if s >= min_score: scored.append((s,r))
    else:
        if not model_name:
            raise ValueError('model_name required when precomputed embeddings are not supplied')
        texts=[query]+[searchable_text(r) for r in candidates]
        vecs=sentence_transformer_embed(texts,model_name)
        qv=vecs[0]
        scored=[(cosine(qv,v),r) for v,r in zip(vecs[1:],candidates)]
        scored=[x for x in scored if x[0] >= min_score]

    scored.sort(key=lambda x:(-x[0],x[1].get('id','')))
    return scored[:limit]
