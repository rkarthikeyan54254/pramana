#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from ask_mahaperiyava import _generation_contract, classify_question
from mahaperiyava_candidate_reranker_v3 import (
    CandidateReranker,
    concept_query,
)

ROOT = Path(__file__).resolve().parents[1]

CROSS_ENCODER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
CROSS_ENCODER_REVISION = "8008f0154ca2387468013ed439df09d70c122412"

PHASE14_CHECKPOINT = ROOT / "data/review/mahaperiyava_candidate_reranker_checkpoint_v3.json"

ROMAN_TAMIL_SIGNATURES = (
    "eppadi", "yen", "enna", "seyyanum", "seyyaradhu", "padippai", "padippu",
    "sevai", "anbu", "shankarar", "upadhyayar", "moksham", "samsaram",
    "varradhu", "vittutu", "maarudhu", "sonnalum", "thedinaar", "pannama",
    "vida", "aagi", "thaandi", "kondu", "pogum", "artham", "kku", "nu",
)


def contains_tamil(text: str) -> bool:
    return any("\u0b80" <= ch <= "\u0bff" for ch in text)


def detect_language_v4(text: str) -> str:
    if contains_tamil(text):
        return "ta"
    folded = (text or "").casefold()
    hits = sum(1 for marker in ROMAN_TAMIL_SIGNATURES if marker in folded)
    return "roman_ta" if hits >= 1 else "en"


def public_safe_passage(record: dict[str, Any]) -> str:
    locus = record["source_locus"]
    return "\n".join([
        "Teaching summary: " + (record.get("claim_summary") or ""),
        "Topics: " + " ".join(record.get("topics") or []),
        "Tamil chapter title: " + (locus.get("chapter_title_ta") or ""),
    ])


def crossencoder_query_view(query: str, language: str) -> str:
    if language == "en":
        return query
    concepts = concept_query(query)
    if concepts:
        return "Find the teaching about: " + concepts
    return query


class CrossEncoderScorer:
    def __init__(
        self,
        model_name: str = CROSS_ENCODER_MODEL,
        revision: str = CROSS_ENCODER_REVISION,
        *,
        cache_file: Path | None = None,
        device: str | None = None,
    ):
        from sentence_transformers import CrossEncoder

        self.model_name = model_name
        self.revision = revision
        self.model = CrossEncoder(
            model_name,
            revision=revision,
            device=device,
            trust_remote_code=False,
        )
        self.cache_file = cache_file or (
            ROOT / "dist/mahaperiyava/crossencoder_v4_scores.json"
        )
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, dict[str, float]] = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}

    def _key(self, query_view: str) -> str:
        payload = f"{self.model_name}@{self.revision}\n{query_view}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def score(
        self,
        query_view: str,
        ids: list[str],
        passages: list[str],
    ) -> np.ndarray:
        key = self._key(query_view)
        cached = self.cache.get(key, {})
        missing = [
            (i, sid, passage)
            for i, (sid, passage) in enumerate(zip(ids, passages))
            if sid not in cached
        ]
        if missing:
            pairs = [(query_view, passage) for _, _, passage in missing]
            values = self.model.predict(
                pairs,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            values = np.asarray(values, dtype=np.float32).reshape(-1)
            for (_, sid, _), value in zip(missing, values):
                cached[sid] = float(value)
            self.cache[key] = cached
            self.cache_file.write_text(
                json.dumps(self.cache, ensure_ascii=False),
                encoding="utf-8",
            )
        return np.asarray([cached[sid] for sid in ids], dtype=np.float32)


class FakeCrossEncoderScorer:
    """Network-free structural test double; not a semantic model."""
    model_name = "fake-overlap-crossencoder"
    revision = "test"

    @staticmethod
    def _tokens(text: str) -> set[str]:
        import re
        return {
            x for x in re.findall(r"[A-Za-z0-9_\u0b80-\u0bff]+", (text or "").casefold())
            if len(x) >= 3
        }

    def score(self, query_view: str, ids: list[str], passages: list[str]) -> np.ndarray:
        q = self._tokens(query_view)
        vals = []
        for p in passages:
            t = self._tokens(p)
            vals.append(len(q & t) / max(1, len(q)))
        return np.asarray(vals, dtype=np.float32)


class CrossEncoderCandidateReranker:
    def __init__(
        self,
        phase14: CandidateReranker | None = None,
        scorer=None,
        *,
        candidate_cap: int = 140,
    ):
        self.phase14 = phase14 or CandidateReranker()
        self.base = self.phase14.base
        self.records = self.phase14.records
        self.record_by_id = {r["id"]: r for r in self.records}
        self.scorer = scorer or CrossEncoderScorer()
        self.candidate_cap = candidate_cap

        cp = json.loads(PHASE14_CHECKPOINT.read_text(encoding="utf-8"))
        self.phase14_profiles = dict(cp["selected_profiles"])
        # Phase-15 DEV tuning evaluates many fusion configurations for the same
        # query. Cache the expensive Phase-14 candidate-generation result once
        # per query/language/profile; only the cheap rank fusion should repeat.
        self._first_stage_cache: dict[tuple[str, str, str], dict[str, Any]] = {}

    def _phase14_profile(self, language: str) -> str:
        return self.phase14_profiles.get(language, "balanced")

    @staticmethod
    def _rank(scores: np.ndarray, ids: list[str]) -> dict[str, int]:
        order = sorted(
            range(len(ids)),
            key=lambda i: (-float(scores[i]), ids[i]),
        )
        return {ids[idx]: rank for rank, idx in enumerate(order, 1)}

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        *,
        language: str | None = None,
        heuristic_weight: float = 1.0,
        cross_weight: float = 1.0,
        rrf_k: int = 30,
    ) -> dict[str, Any]:
        language = language or detect_language_v4(query)
        p14_profile = self._phase14_profile(language)

        first_key = (query, language, p14_profile)
        if first_key not in self._first_stage_cache:
            self._first_stage_cache[first_key] = self.phase14.retrieve(
                query,
                top_k=self.candidate_cap,
                profile=p14_profile,
            )
        first = self._first_stage_cache[first_key]

        # Preserve exact-title and fail-closed paths verbatim. Cross-encoder
        # ranking is not allowed to convert an abstention into an answer.
        if first["status"] == "insufficient_evidence":
            out = dict(first)
            out["retrieval_mode"] = "phase14_guard_then_crossencoder"
            out["crossencoder_used"] = False
            return out

        if first.get("retrieval_mode") == "exact_title":
            out = dict(first)
            out["retrieval_mode"] = "exact_title"
            out["crossencoder_used"] = False
            return out

        candidates = first["hits"][: self.candidate_cap]
        ids = [h["support_id"] for h in candidates]
        passages = [public_safe_passage(self.record_by_id[sid]) for sid in ids]
        qview = crossencoder_query_view(query, language)
        xscores = self.scorer.score(qview, ids, passages)
        xrank = self._rank(xscores, ids)
        hrank = {sid: rank for rank, sid in enumerate(ids, 1)}

        fused = []
        score_map = {sid: float(score) for sid, score in zip(ids, xscores)}
        for hit in candidates:
            sid = hit["support_id"]
            score = (
                heuristic_weight / (rrf_k + hrank[sid])
                + cross_weight / (rrf_k + xrank[sid])
            )
            fused.append((sid, score, hit))

        fused.sort(
            key=lambda x: (
                -x[1],
                xrank[x[0]],
                hrank[x[0]],
                x[0],
            )
        )

        hits = []
        for sid, score, source_hit in fused[: max(1, top_k)]:
            hit = dict(source_hit)
            debug = dict(hit.get("retrieval_debug") or {})
            debug.update({
                "phase14_rank": hrank[sid],
                "crossencoder_rank": xrank[sid],
                "crossencoder_score": round(score_map[sid], 6),
                "fusion_score": round(float(score), 8),
            })
            hit["retrieval_debug"] = debug
            hits.append(hit)

        return {
            "query": query,
            "question_type": classify_question(query),
            "status": "retrieved_evidence",
            "answerable": True,
            "message": (
                "Evidence candidates were generated by the Phase-14 public-safe "
                "retriever and reranked by a pinned cross-encoder. Restricted "
                "source text was not supplied to the reranker."
            ),
            "hits": hits,
            "generation_contract": _generation_contract(classify_question(query)),
            "retrieval_mode": "phase14_candidates_crossencoder_rrf",
            "crossencoder_used": True,
            "query_language": language,
            "crossencoder_query_view": qview,
            "fusion_config": {
                "heuristic_weight": heuristic_weight,
                "cross_weight": cross_weight,
                "rrf_k": rrf_k,
            },
        }

    def authority_counts(self) -> dict[str, int]:
        return dict(Counter(
            r["evidence_status"]["authority"] for r in self.records
        ))
