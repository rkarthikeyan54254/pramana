#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import unicodedata

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
from mahaperiyava_hybrid_retrieval_v2 import (
    MODERN_MARKERS,
    ROMAN_TAMIL_ALIASES,
    TAMIL_ALIASES,
    SentenceTransformerFieldEmbedder,
    _norm,
    augment_query,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = "minilm_multilingual"

EXTRA_CONCEPT_ALIASES = {
    "கடமை": "duty responsibility",
    "கடமைகள்": "duty responsibility",
    "பொறுப்பு": "responsibility duty",
    "பொறுப்புகள்": "responsibility duty",
    "விடுதலை": "liberation moksha",
    "முக்தி": "liberation moksha",
    "பலன்": "benefit fruit result",
    "உயர்ந்த": "highest superior",
    "பொருள்": "material worldly wealth",
    "உலக": "worldly world",
    "தன்னலம்": "self interest self centered",
    "தனக்கே": "self centered",
    "பிரிவு": "separateness division",
    "பிரிவுணர்வு": "separateness",
    "தியாக": "self sacrifice renunciation",
    "கல்வி": "education study learning",
    "பாடம்": "lesson study",
    "ஆசிரிய": "teacher instructor",
    "கற்பித்தல்": "teaching instruction",
    "உடல்நலம்": "physical health",
    "நலம்": "well being benefit",
    "மனம்": "mind",
    "ஒருமுக": "concentration focus",
    "கவனம்": "attention concentration",
    "பழக்கம்": "practice habit discipline",
    "வழிபாடு": "worship devotion ritual",
    "பூஜை": "worship puja ritual",
    "மதம்": "religion doctrine",
    "சமயம்": "religion sect",
    "ஒற்றுமை": "unity harmony",
    "ஒன்று": "one unity",
    "வேற்றுமை": "difference duality",
    "அவதாரம்": "avatara incarnation",
    "தேடினார்": "sought search",
    "தேட": "seek search",
    "செல்வம்": "wealth prosperity",
    "அறியாமை": "ignorance",
    "நீங்கி": "remove freedom",
    "பாதிக்காமல்": "without harming without neglecting",
    "மாணவர்கள்": "students education",
    "செய்வது": "practice action do",
    "செய்ய": "practice action do",
    "எப்படி": "how",
    "ஏன்": "why",
    "வேறுபாடு": "difference distinction",
    "பங்கு": "role",
    "போதனை": "teaching",
    "பக்தி": "bhakti devotion",
    "அன்பு": "love selflessness service",
    "சேவை": "service",
    "சங்கரர்": "shankara",
    "குரு": "guru teacher",
    "ஆசாரியர்": "acharya teacher",
    "உபாத்தியாயர்": "upadhyaya instructor",
    "மோக்ஷம்": "moksha liberation",
    "மோட்சம்": "moksha liberation",
    "kadami": "duty responsibility",
    "kadamai": "duty responsibility",
    "poruppu": "responsibility duty",
    "viduthalai": "liberation moksha",
    "mukthi": "liberation moksha",
    "palan": "benefit fruit result",
    "uyarntha": "highest superior",
    "porul": "material worldly wealth",
    "thannalam": "self interest self centered",
    "pirivu": "separateness division",
    "kalvi": "education study learning",
    "paadam": "lesson study",
    "aasiriyar": "teacher instructor",
    "udalnalam": "physical health",
    "manam": "mind",
    "gavanam": "attention concentration",
    "vazhipadu": "worship devotion ritual",
    "poojai": "worship puja ritual",
    "madham": "religion doctrine",
    "samayam": "religion sect",
    "otrumai": "unity harmony",
    "ondru": "one unity",
    "avatharam": "avatara incarnation",
    "thedinaar": "sought search",
    "thedi": "seek search",
    "selvam": "wealth prosperity",
    "ariyamai": "ignorance",
    "neengi": "remove freedom",
    "paathikkama": "without harming without neglecting",
    "students": "student education",
    "padippu": "study education",
    "padippai": "study education",
    "sevai": "service",
    "seyyanum": "practice duty do",
    "seyyaradhu": "practice duty action",
    "eppadi": "how",
    "yen": "why",
    "enna": "what",
    "difference": "difference distinction",
    "role": "role",
    "anbu": "love selflessness service",
    "shankarar": "shankara",
    "upadhyayar": "upadhyaya instructor",
    "moksham": "moksha liberation",
    "samsaram": "samsara",
}

GENERIC_CONCEPT_STOP = {
    "how", "why", "what", "do", "practice", "one", "world", "result",
    "teaching", "religious", "divine",
}


def _contains_tamil(text: str) -> bool:
    return any("\u0b80" <= ch <= "\u0bff" for ch in text)


def detect_language(text: str) -> str:
    if _contains_tamil(text):
        return "ta"
    folded = _norm(text)
    roman_hits = sum(1 for key in ROMAN_TAMIL_ALIASES if key in folded)
    roman_hits += sum(
        1 for key in EXTRA_CONCEPT_ALIASES
        if key.isascii() and key in folded
    )
    return "roman_ta" if roman_hits >= 2 else "en"


def _all_alias_items() -> list[tuple[str, str]]:
    merged: dict[str, str] = {}
    merged.update(ROMAN_TAMIL_ALIASES)
    merged.update(TAMIL_ALIASES)
    merged.update(EXTRA_CONCEPT_ALIASES)
    return sorted(merged.items(), key=lambda kv: (-len(kv[0]), kv[0]))


ALIAS_ITEMS = _all_alias_items()


def concept_terms(query: str) -> list[str]:
    folded = _norm(query)
    values: list[str] = []
    for key, gloss in ALIAS_ITEMS:
        if key in folded:
            values.extend(_tokens(_expand(gloss)))

    if not _contains_tamil(query):
        values.extend(
            t for t in _tokens(_expand(query))
            if t.isascii() and t.isalpha() and len(t) >= 3
        )

    out: list[str] = []
    seen = set()
    for token in values:
        if token in GENERIC_CONCEPT_STOP or len(token) < 3:
            continue
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out


def concept_query(query: str) -> str:
    return " ".join(concept_terms(query))


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    value = "".join(
        ch for ch in unicodedata.normalize("NFKC", text or "").casefold()
        if not ch.isspace() and not unicodedata.category(ch).startswith("P")
    )
    if len(value) < n:
        return {value} if value else set()
    return {value[i:i+n] for i in range(len(value) - n + 1)}


def tamil_title_similarity(query: str, title: str) -> float:
    if not _contains_tamil(query) or not title:
        return 0.0
    q = _char_ngrams(query)
    t = _char_ngrams(title)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q | t)


def _record_concept_tokens(record: dict[str, Any]) -> set[str]:
    locus = record["source_locus"]
    text = " ".join([
        record.get("claim_summary") or "",
        " ".join(record.get("topics") or []),
        locus.get("chapter_title_ta") or "",
        record["id"].replace(".", " ").replace("_", " "),
    ])
    return set(_tokens(_expand(augment_query(text))))


def _modern_marker(query: str) -> str | None:
    q = _norm(query)
    for marker in MODERN_MARKERS:
        if marker in q:
            return marker
    return None


def _strong_oov_subject_terms(base: MahaperiyavaRetriever, query: str) -> list[str]:
    subject = _attribution_subject(query)
    if not subject:
        return []
    toks = _tokens(_expand(subject))
    return [
        t for t in toks
        if t.isascii() and t.isalpha() and len(t) >= 5 and t not in base.idf
    ]


@dataclass(frozen=True)
class RankProfile:
    name: str
    lexical_original: float
    lexical_augmented: float
    lexical_concept: float
    semantic_claim: float
    semantic_title: float
    concept_coverage: float
    tamil_title_char: float
    rrf_k: int = 40


PROFILES: dict[str, RankProfile] = {
    "lexical_guarded": RankProfile(
        "lexical_guarded", 2.5, 1.0, 0.8, 0.45, 0.15, 0.35, 0.10
    ),
    "balanced": RankProfile(
        "balanced", 1.5, 1.2, 1.3, 0.9, 0.35, 0.65, 0.20
    ),
    "concept_heavy": RankProfile(
        "concept_heavy", 0.8, 1.1, 2.5, 1.0, 0.35, 1.20, 0.20
    ),
    "concept_semantic": RankProfile(
        "concept_semantic", 0.7, 0.9, 2.0, 1.5, 0.50, 1.00, 0.25
    ),
    "tamil_concept_title": RankProfile(
        "tamil_concept_title", 0.35, 0.75, 2.4, 1.25, 0.90, 1.30, 0.80
    ),
    "semantic_guarded": RankProfile(
        "semantic_guarded", 1.1, 0.8, 1.0, 1.8, 0.60, 0.50, 0.20
    ),
}


class CandidateReranker:
    def __init__(
        self,
        embedder=None,
        *,
        cache_dir: Path | None = None,
        lexical_pool: int = 60,
        semantic_pool: int = 50,
        candidate_cap: int = 140,
    ):
        self.base = MahaperiyavaRetriever()
        self.records = self.base.records
        self.docs = self.base.docs
        self.embedder = embedder or SentenceTransformerFieldEmbedder(DEFAULT_PROFILE)
        self.lexical_pool = lexical_pool
        self.semantic_pool = semantic_pool
        self.candidate_cap = candidate_cap

        from mahaperiyava_hybrid_retrieval_v2 import FieldedHybridRetriever
        self.fielded = FieldedHybridRetriever(
            self.embedder,
            cache_dir=cache_dir or ROOT / "dist/mahaperiyava/hybrid_cache_v2",
            candidate_pool=max(120, candidate_cap),
        )
        self.record_concepts = [_record_concept_tokens(r) for r in self.records]

    @staticmethod
    def _rank_map(scored: list[tuple[int, float, list[str]]]) -> dict[int, int]:
        return {idx: rank for rank, (idx, _, _) in enumerate(scored, 1)}

    def _lexical_ranking(self, query: str) -> list[tuple[int, float, list[str]]]:
        if not query.strip():
            return []
        rows = []
        for idx, doc in enumerate(self.docs):
            score, matched = self.base._score(query, doc)
            if score > 0:
                rows.append((idx, score, matched))
        rows.sort(
            key=lambda x: (
                -x[1],
                int(self.records[x[0]]["source_locus"]["volume"]),
                self.records[x[0]]["source_locus"].get("chapter_ordinal") or 10**9,
                self.records[x[0]]["id"],
            )
        )
        return rows

    def components(self, query: str) -> dict[str, Any]:
        original = self._lexical_ranking(query)
        augmented_text = augment_query(query)
        augmented = self._lexical_ranking(augmented_text)
        concepts = concept_query(query)
        concept_ranked = self._lexical_ranking(concepts) if concepts else []

        q_for_semantic = concepts if concepts else augmented_text
        qvec = self.embedder.encode_queries([q_for_semantic])[0]
        claim_sims = np.asarray(self.fielded.claim_vectors @ qvec, dtype=np.float32)
        title_sims = np.asarray(self.fielded.title_vectors @ qvec, dtype=np.float32)
        claim_order = np.argsort(-claim_sims)
        title_order = np.argsort(-title_sims)

        candidates: set[int] = set()
        for ranking in (original, augmented, concept_ranked):
            candidates.update(idx for idx, _, _ in ranking[: self.lexical_pool])
        candidates.update(int(x) for x in claim_order[: self.semantic_pool])
        candidates.update(int(x) for x in title_order[: max(20, self.semantic_pool // 2)])

        concept_set = set(_tokens(concepts))
        orig_rank = self._rank_map(original)
        aug_rank = self._rank_map(augmented)
        con_rank = self._rank_map(concept_ranked)
        claim_rank = {int(idx): r for r, idx in enumerate(claim_order, 1)}
        title_rank = {int(idx): r for r, idx in enumerate(title_order, 1)}

        prelim = []
        for idx in candidates:
            cov = (
                len(concept_set & self.record_concepts[idx]) / len(concept_set)
                if concept_set else 0.0
            )
            score = (
                1.0 / (40 + orig_rank.get(idx, 10**6))
                + 1.0 / (40 + aug_rank.get(idx, 10**6))
                + 1.2 / (40 + con_rank.get(idx, 10**6))
                + 0.8 / (40 + claim_rank.get(idx, 10**6))
                + 0.3 / (40 + title_rank.get(idx, 10**6))
                + 0.02 * cov
            )
            prelim.append((idx, score))
        prelim.sort(key=lambda x: (-x[1], self.records[x[0]]["id"]))
        candidates = {idx for idx, _ in prelim[: self.candidate_cap]}

        return {
            "language": detect_language(query),
            "augmented": augmented_text,
            "concept_query": concepts,
            "concept_set": concept_set,
            "candidates": candidates,
            "original": original,
            "augmented_ranked": augmented,
            "concept_ranked": concept_ranked,
            "original_rank": orig_rank,
            "augmented_rank": aug_rank,
            "concept_rank": con_rank,
            "claim_rank": claim_rank,
            "title_rank": title_rank,
            "claim_sims": claim_sims,
            "title_sims": title_sims,
        }

    def candidate_ids(self, query: str) -> set[str]:
        c = self.components(query)
        return {self.records[i]["id"] for i in c["candidates"]}

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        *,
        profile: str = "balanced",
    ) -> dict[str, Any]:
        if profile not in PROFILES:
            raise ValueError(f"unknown profile: {profile}")

        exact = self.base.title_docs.get(_title_key(query))
        if exact:
            out = self.base.retrieve(query, top_k=top_k)
            out["retrieval_mode"] = "exact_title"
            out["rerank_profile"] = profile
            return out

        qtype = classify_question(query)
        marker = _modern_marker(query)
        if marker is not None:
            return {
                "query": query,
                "question_type": qtype,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(qtype),
                "retrieval_mode": "candidate_then_rerank",
                "rerank_profile": profile,
                "abstention_reason": f"modern_marker:{marker}",
            }

        oov = _strong_oov_subject_terms(self.base, query)
        if oov:
            return {
                "query": query,
                "question_type": qtype,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(qtype),
                "retrieval_mode": "candidate_then_rerank",
                "rerank_profile": profile,
                "abstention_reason": "explicit_subject_contains_out_of_corpus_terms",
            }

        c = self.components(query)
        p = PROFILES[profile]
        concept_set = c["concept_set"]
        rows = []

        for idx in c["candidates"]:
            def rr(rank_map, weight):
                rank = rank_map.get(idx)
                return weight / (p.rrf_k + rank) if rank else 0.0

            coverage = (
                len(concept_set & self.record_concepts[idx]) / len(concept_set)
                if concept_set else 0.0
            )
            title = self.records[idx]["source_locus"].get("chapter_title_ta") or ""
            title_char = tamil_title_similarity(query, title)

            score = (
                rr(c["original_rank"], p.lexical_original)
                + rr(c["augmented_rank"], p.lexical_augmented)
                + rr(c["concept_rank"], p.lexical_concept)
                + rr(c["claim_rank"], p.semantic_claim)
                + rr(c["title_rank"], p.semantic_title)
                + (0.025 * p.concept_coverage * coverage)
                + (0.020 * p.tamil_title_char * title_char)
            )

            lexical_score = 0.0
            matched: list[str] = []
            for ranking in (c["concept_ranked"], c["augmented_ranked"], c["original"]):
                found = next((row for row in ranking if row[0] == idx), None)
                if found:
                    lexical_score = max(lexical_score, float(found[1]))
                    matched = sorted(set(matched) | set(found[2]))

            rows.append((
                idx,
                score,
                coverage,
                float(c["claim_sims"][idx]),
                float(c["title_sims"][idx]),
                title_char,
                lexical_score,
                matched,
            ))

        rows.sort(
            key=lambda x: (
                -x[1], -x[2], -x[3], -x[4], -x[6],
                int(self.records[x[0]]["source_locus"]["volume"]),
                self.records[x[0]]["source_locus"].get("chapter_ordinal") or 10**9,
                self.records[x[0]]["id"],
            )
        )

        base_out = self.base.retrieve(augment_query(query), top_k=5)
        concepts = c["concept_query"]
        concept_out = self.base.retrieve(concepts, top_k=5) if concepts else {
            "answerable": False
        }
        best_claim = float(np.max(c["claim_sims"])) if len(c["claim_sims"]) else 0.0

        if not rows or (
            not base_out["answerable"]
            and not concept_out["answerable"]
            and best_claim < 0.48
        ):
            return {
                "query": query,
                "question_type": qtype,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(qtype),
                "retrieval_mode": "candidate_then_rerank",
                "rerank_profile": profile,
                "abstention_reason": "candidate_evidence_below_threshold",
            }

        hits = []
        for idx, score, coverage, claim_sim, title_sim, title_char, lex_score, matched in rows[:max(1, top_k)]:
            hit = self.base._hit(self.records[idx], score, matched)
            hit["retrieval_debug"] = {
                "rerank_score": round(float(score), 8),
                "concept_coverage": round(float(coverage), 4),
                "claim_similarity": round(claim_sim, 6),
                "title_similarity": round(title_sim, 6),
                "tamil_title_char_similarity": round(title_char, 6),
                "best_lexical_score": round(lex_score, 6),
            }
            hits.append(hit)

        return {
            "query": query,
            "question_type": qtype,
            "status": "retrieved_evidence",
            "answerable": True,
            "message": "Evidence candidates retrieved from public-safe curator metadata using language-aware candidate generation followed by constrained reranking.",
            "hits": hits,
            "generation_contract": _generation_contract(qtype),
            "retrieval_mode": "candidate_then_rerank",
            "rerank_profile": profile,
            "query_language": c["language"],
            "concept_query": c["concept_query"],
        }

    def authority_counts(self) -> dict[str, int]:
        return dict(Counter(
            r["evidence_status"]["authority"] for r in self.records
        ))
