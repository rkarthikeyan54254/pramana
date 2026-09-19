#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Protocol

import numpy as np

from ask_mahaperiyava import (
    MahaperiyavaRetriever,
    _attribution_subject,
    _expand,
    _generation_contract,
    _title_key,
    _tokens,
    classify_question,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_REVISION = "383bbb10e05bb8885acd71a7956dc2d823b60305"

ROMAN_TAMIL_ALIASES = {
    "advaitam": "advaita nonduality brahman",
    "brahmam": "brahman nonduality",
    "karmam": "karma action duty",
    "bhakti": "devotion",
    "jnanam": "jnana knowledge",
    "sivan": "shiva siva",
    "sivanum": "shiva siva",
    "vishnu": "vishnu visnu",
    "vishnuvum": "vishnu visnu",
    "onna": "one unity nonseparate",
    "onnu": "one unity nonseparate",
    "kamakshi": "kamakshi goddess",
    "karunai": "compassion grace mercy",
    "sadangu": "ritual observance discipline",
    "darshanam": "philosophical doctrine",
    "arivu": "knowledge learning",
    "gunam": "character virtue",
    "kovil": "temple",
    "kalaigal": "arts traditional arts",
    "ishta deivam": "ishta devata chosen deity",
    "mahabharatam": "mahabharata epic",
    "padippu": "study education",
    "udal": "body physical",
    "moksham": "moksha liberation",
    "bayam": "fear",
    "samsaram": "samsara",
    "seyal": "action karma",
    "shankarar": "shankara",
    "guru": "guru teacher acharya",
    "anbu": "love service",
    "selvam": "prosperity wealth",
    "sevai": "service",
    "upadhyayar": "upadhyaya teacher",
    "pillaiyar": "ganesha vinayaka",
    "suzhi": "symbol mark",
}


class Embedder(Protocol):
    model_name: str
    revision: str | None

    def encode(self, texts: list[str]) -> np.ndarray: ...


def _augment_roman_tamil(text: str) -> str:
    folded = text.casefold()
    additions = []
    for key, value in ROMAN_TAMIL_ALIASES.items():
        if key in folded:
            additions.append(value)
    if not additions:
        return text
    return text + " " + " ".join(additions)


def public_safe_document(record: dict[str, Any]) -> str:
    locus = record["source_locus"]
    pieces = [
        f"claim: {record.get('claim_summary') or ''}",
        "topics: " + " ".join(record.get("topics") or []),
        f"chapter title Tamil: {locus.get('chapter_title_ta') or ''}",
        "identity: " + record["id"].replace(".", " ").replace("_", " "),
    ]
    # Intentionally excludes provenance, URLs, hashes, exact source text,
    # source snapshots, and evidence-depth witness material.
    return "\n".join(pieces)


def corpus_fingerprint(records: list[dict[str, Any]]) -> str:
    payload = [
        {
            "id": r["id"],
            "claim_summary": r.get("claim_summary"),
            "topics": r.get("topics") or [],
            "chapter_title_ta": r["source_locus"].get("chapter_title_ta"),
        }
        for r in records
    ]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class SentenceTransformerEmbedder:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        revision: str | None = DEFAULT_REVISION,
        device: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.revision = revision
        self._model = SentenceTransformer(
            model_name,
            revision=revision,
            device=device,
            trust_remote_code=False,
        )

    def encode(self, texts: list[str]) -> np.ndarray:
        arr = self._model.encode(
            texts,
            batch_size=64,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(arr, dtype=np.float32)


class DeterministicHashEmbedder:
    """Offline test double for hybrid plumbing; not a semantic model."""

    model_name = "deterministic-hash-test-double"
    revision = None

    def __init__(self, dims: int = 128) -> None:
        self.dims = dims

    def encode(self, texts: list[str]) -> np.ndarray:
        rows = []
        for text in texts:
            vec = np.zeros(self.dims, dtype=np.float32)
            for token in _tokens(_expand(_augment_roman_tamil(text))):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % self.dims
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vec[idx] += sign
            norm = float(np.linalg.norm(vec))
            if norm:
                vec /= norm
            rows.append(vec)
        return np.stack(rows, axis=0)


class HybridMahaperiyavaRetriever:
    def __init__(
        self,
        embedder: Embedder | None = None,
        *,
        cache_dir: Path | None = None,
        candidate_pool: int = 80,
    ) -> None:
        self.base = MahaperiyavaRetriever()
        self.records = self.base.records
        self.docs = self.base.docs
        self.embedder = embedder or SentenceTransformerEmbedder()
        self.candidate_pool = max(20, candidate_pool)
        self.fingerprint = corpus_fingerprint(self.records)
        self.doc_texts = [public_safe_document(r) for r in self.records]
        self._component_cache: dict[str, dict[str, Any]] = {}

        if cache_dir is None:
            cache_dir = ROOT / "dist/mahaperiyava/hybrid_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        model_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", self.embedder.model_name)
        revision = (self.embedder.revision or "none")[:12]
        cache_file = cache_dir / f"{model_key}__{revision}__{self.fingerprint[:16]}.npy"

        if cache_file.exists():
            arr = np.load(cache_file)
            if arr.shape[0] != len(self.records):
                raise ValueError("cached embedding row count does not match corpus")
            self.doc_vectors = np.asarray(arr, dtype=np.float32)
        else:
            self.doc_vectors = self.embedder.encode(self.doc_texts)
            if self.doc_vectors.shape[0] != len(self.records):
                raise ValueError("embedding row count does not match corpus")
            np.save(cache_file, self.doc_vectors)

    def _subject_oov_terms(self, query: str) -> list[str]:
        subject = _attribution_subject(query)
        if not subject:
            q = query.casefold().strip(" ?!.,;:")
            extra_patterns = (
                r"\bdid\s+mahaperiyava\s+(?:recommend|configure|advise|teach|say)\s+(?:about\s+|on\s+|for\s+)?(.+)$",
                r"\bwhat\s+did\s+mahaperiyava\s+(?:recommend|teach|say)\s+(?:about\s+|on\s+|for\s+)?(.+)$",
                r"\bwhat\s+was\s+mahaperiyava(?:'s)?\s+(?:view|advice|opinion)\s+(?:about|on)\s+(.+)$",
                r"\bhow\s+did\s+mahaperiyava\s+(?:configure|recommend|advise)\s+(.+)$",
            )
            for pattern in extra_patterns:
                match = re.search(pattern, q)
                if match:
                    subject = match.group(1).strip(" ?!.,;:")
                    break
        if not subject:
            return []
        subject_tokens = list(
            dict.fromkeys(_tokens(_expand(_augment_roman_tamil(subject))))
        )
        return [
            token
            for token in subject_tokens
            if token.isascii()
            and token.isalpha()
            and len(token) >= 5
            and token not in self.base.idf
        ]

    def _components(self, query: str) -> dict[str, Any]:
        cached = self._component_cache.get(query)
        if cached is not None:
            return cached

        augmented = _augment_roman_tamil(query)
        lexical = []
        for idx, doc in enumerate(self.docs):
            score, matched = self.base._score(augmented, doc)
            if score > 0:
                lexical.append((idx, score, matched))
        lexical.sort(
            key=lambda x: (
                -x[1],
                int(self.records[x[0]]["source_locus"]["volume"]),
                self.records[x[0]]["source_locus"].get("chapter_ordinal") or 10**9,
                self.records[x[0]]["id"],
            )
        )

        qvec = self.embedder.encode([augmented])[0]
        sims = np.asarray(self.doc_vectors @ qvec, dtype=np.float32)
        semantic_order = np.argsort(-sims)

        lexical_rank = {idx: rank for rank, (idx, _, _) in enumerate(lexical, 1)}
        lexical_detail = {idx: (score, matched) for idx, score, matched in lexical}
        semantic_rank = {int(idx): rank for rank, idx in enumerate(semantic_order, 1)}

        out = {
            "lexical": lexical,
            "lexical_rank": lexical_rank,
            "lexical_detail": lexical_detail,
            "semantic_order": semantic_order,
            "semantic_rank": semantic_rank,
            "semantic_scores": sims,
            "subject_oov_terms": self._subject_oov_terms(query),
        }
        self._component_cache[query] = out
        return out

    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        *,
        lexical_weight: float = 1.0,
        semantic_weight: float = 1.0,
        min_semantic: float = 0.38,
        rrf_k: int = 60,
    ) -> dict[str, Any]:
        # Preserve the existing deterministic exact-title route.
        if self.base.title_docs.get(_title_key(query)):
            out = self.base.retrieve(query, top_k)
            out["retrieval_mode"] = "exact_title"
            out["hybrid_config"] = None
            return out

        c = self._components(query)
        question_type = classify_question(query)

        # Preserve the existing fail-closed attribution rule.  Semantic
        # similarity is never allowed to invent an attestation for a modern
        # subject that the corpus does not lexically contain.
        if c["subject_oov_terms"]:
            return {
                "query": query,
                "question_type": question_type,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(question_type),
                "retrieval_mode": "hybrid_rrf",
                "hybrid_config": {
                    "lexical_weight": lexical_weight,
                    "semantic_weight": semantic_weight,
                    "min_semantic": min_semantic,
                    "rrf_k": rrf_k,
                },
                "abstention_reason": "explicit_subject_contains_out_of_corpus_terms",
            }

        candidate_indices = set()
        candidate_indices.update(idx for idx, _, _ in c["lexical"][: self.candidate_pool])
        candidate_indices.update(
            int(idx) for idx in c["semantic_order"][: self.candidate_pool]
        )

        fused = []
        for idx in candidate_indices:
            lr = c["lexical_rank"].get(idx)
            sr = c["semantic_rank"].get(idx)
            score = 0.0
            if lr is not None:
                score += lexical_weight / (rrf_k + lr)
            if sr is not None:
                score += semantic_weight / (rrf_k + sr)
            lexical_score, matched = c["lexical_detail"].get(idx, (0.0, []))
            semantic_score = float(c["semantic_scores"][idx])
            fused.append((idx, score, semantic_score, lexical_score, matched, lr, sr))

        fused.sort(
            key=lambda x: (
                -x[1],
                -x[2],
                -x[3],
                int(self.records[x[0]]["source_locus"]["volume"]),
                self.records[x[0]]["source_locus"].get("chapter_ordinal") or 10**9,
                self.records[x[0]]["id"],
            )
        )

        base_out = self.base.retrieve(_augment_roman_tamil(query), top_k=5)
        lexical_answerable = base_out["answerable"]
        best_semantic = float(np.max(c["semantic_scores"])) if len(c["semantic_scores"]) else 0.0

        if not fused or (not lexical_answerable and best_semantic < min_semantic):
            return {
                "query": query,
                "question_type": question_type,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(question_type),
                "retrieval_mode": "hybrid_rrf",
                "hybrid_config": {
                    "lexical_weight": lexical_weight,
                    "semantic_weight": semantic_weight,
                    "min_semantic": min_semantic,
                    "rrf_k": rrf_k,
                },
                "abstention_reason": "hybrid_evidence_below_threshold",
            }

        hits = []
        for idx, score, semantic_score, lexical_score, matched, lr, sr in fused[: max(1, top_k)]:
            hit = self.base._hit(self.records[idx], score, matched)
            hit["retrieval_debug"] = {
                "rrf_score": round(float(score), 8),
                "semantic_similarity": round(semantic_score, 6),
                "lexical_score": round(float(lexical_score), 6),
                "lexical_rank": lr,
                "semantic_rank": sr,
            }
            hits.append(hit)

        return {
            "query": query,
            "question_type": question_type,
            "status": "retrieved_evidence",
            "answerable": True,
            "message": "Evidence candidates retrieved from public-safe curator metadata using lexical+multilingual semantic rank fusion. Claim summaries are not quotations.",
            "hits": hits,
            "generation_contract": _generation_contract(question_type),
            "retrieval_mode": "hybrid_rrf",
            "hybrid_config": {
                "lexical_weight": lexical_weight,
                "semantic_weight": semantic_weight,
                "min_semantic": min_semantic,
                "rrf_k": rrf_k,
            },
        }

    def authority_counts(self) -> dict[str, int]:
        c = Counter(r["evidence_status"]["authority"] for r in self.records)
        return dict(c)
