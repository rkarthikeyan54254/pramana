#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

import numpy as np

from ask_mahaperiyava import (
    MahaperiyavaRetriever,
    _generation_contract,
    _title_key,
    _tokens,
    classify_question,
)
from mahaperiyava_hybrid_retrieval import DeterministicHashEmbedder

ROOT = Path(__file__).resolve().parents[1]

MODEL_PROFILES = {
    "minilm_multilingual": {
        "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "revision": "383bbb10e05bb8885acd71a7956dc2d823b60305",
        "query_prefix": "",
        "passage_prefix": "",
        "license": "apache-2.0",
    },
    "multilingual_e5_small": {
        "model": "intfloat/multilingual-e5-small",
        "revision": "fd1525a9fd15316a2d503bf26ab031a61d056e98",
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
        "license": "mit",
    },
}

ROMAN_TAMIL_ALIASES = {
    "advaitam": "advaita nonduality brahman",
    "brahmam": "brahman nonduality",
    "karmam": "karma action duty",
    "bhakti": "devotion",
    "jnanam": "knowledge jnana",
    "sivan": "shiva siva",
    "sivanum": "shiva siva",
    "vishnu": "vishnu visnu",
    "vishnuvum": "vishnu visnu",
    "onna": "one unity nonseparate",
    "onnu": "one unity nonseparate",
    "kamakshi": "kamakshi goddess",
    "karunai": "compassion grace mercy",
    "sadangu": "ritual observance discipline",
    "sadangugal": "ritual observances discipline",
    "arivu": "knowledge learning",
    "gunam": "character virtue",
    "kovil": "temple",
    "kalaigal": "arts traditional arts",
    "ishta deivam": "ishta devata chosen deity",
    "mahabharatam": "mahabharata epic",
    "padippu": "study education",
    "padippai": "study education",
    "udal": "body physical health",
    "moksham": "moksha liberation",
    "bayam": "fear",
    "samsaram": "samsara",
    "seyal": "action karma",
    "seyyaradhu": "action practice duty",
    "seyyanum": "practice do duty",
    "shankarar": "shankara",
    "guru": "guru teacher acharya",
    "acharya": "acharya guru teacher",
    "anbu": "love service selflessness",
    "selvam": "prosperity wealth",
    "sevai": "service",
    "upadhyayar": "upadhyaya teacher instructor",
    "pillaiyar": "ganesha vinayaka",
    "vinayagar": "ganesha vinayaka",
    "suzhi": "symbol mark",
    "chandran": "moon lunar",
    "perumai": "pride",
    "kindal": "mock ridicule",
    "pallavargal": "pallava",
    "origin": "origins history",
    "thodang": "beginning start",
    "start": "beginning undertaking",
    "thadai": "obstacle",
    "samarasam": "reconciliation harmony",
    "alvar": "alvar devotional saint",
    "chandas": "prosody metre meter",
    "chandasil": "prosody metre meter",
    "matra": "mora prosody",
    "subrahmanya": "subrahmanya sat chit bliss",
    "anandham": "bliss ananda",
    "sectarian": "sectarian division separatist",
    "separatist": "sectarian division separatist",
}

TAMIL_ALIASES = {
    "அத்வைத": "advaita nonduality brahman",
    "பக்தி": "bhakti devotion",
    "கர்ம": "karma action duty",
    "ஞான": "jnana knowledge",
    "சிவ": "shiva siva",
    "விஷ்ணு": "vishnu visnu",
    "காமாட்சி": "kamakshi compassion goddess",
    "கருணை": "compassion grace mercy",
    "சடங்கு": "ritual observance discipline",
    "ஒழுக்க": "discipline character",
    "அறிவு": "knowledge learning",
    "குண": "character virtue",
    "கோவில்": "temple",
    "கோயில்": "temple",
    "கலை": "arts traditional arts",
    "இஷ்ட": "ishta devata chosen deity",
    "தெய்வ": "deity divine",
    "மகாபாரத": "mahabharata epic",
    "படிப்பு": "study education",
    "மாணவர்": "student education",
    "உடல்": "body physical health",
    "ஆரோக்கிய": "health physical well being",
    "மோக்ஷ": "moksha liberation",
    "மோட்ச": "moksha liberation",
    "பயம்": "fear",
    "அபயம்": "fearlessness",
    "சம்ஸார": "samsara",
    "செயல்": "action duty karma",
    "பற்று": "attachment",
    "சங்கர": "shankara",
    "குரு": "guru teacher acharya",
    "ஆசாரிய": "acharya guru teacher",
    "உபாத்தியாய": "upadhyaya instructor teacher",
    "அன்பு": "love selflessness service",
    "சேவை": "service",
    "செல்வ": "wealth prosperity",
    "அறியாமை": "ignorance",
    "விநாயக": "ganesha vinayaka",
    "பிள்ளையார்": "ganesha vinayaka",
    "சந்திர": "moon lunar",
    "பெருமை": "pride",
    "இகழ": "mock ridicule",
    "கிண்டல்": "mock ridicule",
    "பல்லவ": "pallava origins history",
    "தோற்ற": "origin history",
    "தொடங்க": "beginning undertaking",
    "தடை": "obstacle removal",
    "பிரிவினை": "sectarian separatist division",
    "சமயப் பிரிவு": "sectarian religious division",
    "சமரச": "reconciliation harmony",
    "ஆழ்வார்": "alvar devotional saint",
    "சந்த": "prosody metre meter",
    "மாத்திரை": "mora prosody",
    "எழுத்து எண்ணிக்கை": "syllable counted prosody",
    "பாலசந்திர": "bhalachandra moon ganesha",
    "ஸுப்ரஹ்மண்ய": "subrahmanya",
    "சுப்ரமண்ய": "subrahmanya",
    "ஸத்": "sat being",
    "சித்": "chit consciousness",
    "ஆனந்த": "ananda bliss",
}

MODERN_MARKERS = (
    "smartphone", "kubernetes", "bitcoin", "cryptocurrency", "wifi", "wi-fi",
    "gpu", "qr-code", "password manager", "passkey", "postgresql", "5g",
    "crispr", "ray tracing", "usb-c", "thunderbolt", "ransomware", "docker",
    "quantum-comput", "social-media", "generative-ai", "autonomous-drone",
    "service-mesh", "face-recognition", "vector database", "retrieval-augmented",
    "satellite internet", "upi transaction", "staking",
    "செயற்கை நுண்ணறிவு", "சாட்பாட்", "ஸ்மார்ட்போன்", "கிரிப்டோ", "யூபிஐ",
    "செயற்கைக்கோள் இணையம்",
)


def _norm(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text or "").casefold().split())


def _contains_tamil(text: str) -> bool:
    return any("\u0b80" <= ch <= "\u0bff" for ch in text)


def augment_query(text: str) -> str:
    folded = _norm(text)
    additions: list[str] = []
    for key, value in ROMAN_TAMIL_ALIASES.items():
        if key in folded:
            additions.append(value)
    for key, value in TAMIL_ALIASES.items():
        if key in folded:
            additions.append(value)
    if not additions:
        return text
    return text + " " + " ".join(additions)


def _public_claim(record: dict[str, Any]) -> str:
    topics = " ".join(record.get("topics") or [])
    return f"{record.get('claim_summary') or ''}\nTopics: {topics}"


def _public_title_topic(record: dict[str, Any]) -> str:
    locus = record["source_locus"]
    title = locus.get("chapter_title_ta") or ""
    topics = " ".join(record.get("topics") or [])
    return f"Tamil chapter title: {title}\nTopics: {topics}"


def corpus_fingerprint(records: list[dict[str, Any]]) -> str:
    payload = [
        {
            "id": r["id"],
            "claim": r.get("claim_summary"),
            "topics": r.get("topics") or [],
            "title": r["source_locus"].get("chapter_title_ta"),
        }
        for r in records
    ]
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


class SentenceTransformerFieldEmbedder:
    def __init__(self, profile: str, device: str | None = None):
        from sentence_transformers import SentenceTransformer
        if profile not in MODEL_PROFILES:
            raise ValueError(profile)
        self.profile_name = profile
        self.profile = MODEL_PROFILES[profile]
        self.model_name = self.profile["model"]
        self.revision = self.profile["revision"]
        self.query_prefix = self.profile["query_prefix"]
        self.passage_prefix = self.profile["passage_prefix"]
        self._model = SentenceTransformer(
            self.model_name,
            revision=self.revision,
            device=device,
            trust_remote_code=False,
        )

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        values = [self.query_prefix + x for x in texts]
        return np.asarray(
            self._model.encode(
                values,
                batch_size=64,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ),
            dtype=np.float32,
        )

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        values = [self.passage_prefix + x for x in texts]
        return np.asarray(
            self._model.encode(
                values,
                batch_size=64,
                show_progress_bar=len(values) > 100,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ),
            dtype=np.float32,
        )


class HashFieldEmbedder:
    """Network-free test double.  Not a semantic model."""
    profile_name = "hash_test_double"
    model_name = "deterministic-hash-test-double"
    revision = None
    query_prefix = ""
    passage_prefix = ""

    def __init__(self, dims: int = 128):
        self._base = DeterministicHashEmbedder(dims=dims)

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return self._base.encode(texts)

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        return self._base.encode(texts)


class FieldedHybridRetriever:
    def __init__(
        self,
        embedder,
        *,
        cache_dir: Path | None = None,
        candidate_pool: int = 120,
    ):
        self.base = MahaperiyavaRetriever()
        self.records = self.base.records
        self.docs = self.base.docs
        self.embedder = embedder
        self.candidate_pool = max(40, candidate_pool)
        self.fingerprint = corpus_fingerprint(self.records)
        self.claim_docs = [_public_claim(r) for r in self.records]
        self.title_docs_text = [_public_title_topic(r) for r in self.records]
        self._component_cache: dict[str, dict[str, Any]] = {}

        if cache_dir is None:
            cache_dir = ROOT / "dist/mahaperiyava/hybrid_cache_v2"
        cache_dir.mkdir(parents=True, exist_ok=True)

        model_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", self.embedder.model_name)
        revision = (self.embedder.revision or "none")[:12]
        prefix = f"{model_key}__{revision}__{self.fingerprint[:16]}"

        self.claim_vectors = self._load_or_build(
            cache_dir / f"{prefix}__claim.npy", self.claim_docs
        )
        self.title_vectors = self._load_or_build(
            cache_dir / f"{prefix}__title_topics.npy", self.title_docs_text
        )

    def _load_or_build(self, path: Path, texts: list[str]) -> np.ndarray:
        if path.exists():
            arr = np.load(path)
            if arr.shape[0] != len(self.records):
                raise ValueError(f"cached row count mismatch: {path}")
            return np.asarray(arr, dtype=np.float32)
        arr = self.embedder.encode_passages(texts)
        if arr.shape[0] != len(self.records):
            raise ValueError("embedding row count mismatch")
        np.save(path, arr)
        return arr

    def _modern_marker(self, query: str) -> str | None:
        q = _norm(query)
        for marker in MODERN_MARKERS:
            if marker in q:
                return marker
        return None

    def _title_overlap(self, query: str, idx: int) -> float:
        title = self.records[idx]["source_locus"].get("chapter_title_ta") or ""
        q = _norm(query)
        t = _norm(title)
        if not q or not t:
            return 0.0
        if t in q or q in t:
            return 1.0
        qt = {x for x in _tokens(q) if len(x) >= 3}
        tt = {x for x in _tokens(t) if len(x) >= 3}
        if not qt or not tt:
            return 0.0
        shared = qt & tt
        return len(shared) / max(1, min(len(qt), len(tt)))

    def _components(self, query: str):
        if query in self._component_cache:
            return self._component_cache[query]

        augmented = augment_query(query)

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

        qvec = self.embedder.encode_queries([augmented])[0]
        claim_sims = np.asarray(self.claim_vectors @ qvec, dtype=np.float32)
        title_sims = np.asarray(self.title_vectors @ qvec, dtype=np.float32)
        claim_order = np.argsort(-claim_sims)
        title_order = np.argsort(-title_sims)

        c = {
            "augmented": augmented,
            "lexical": lexical,
            "lexical_rank": {idx: rank for rank, (idx, _, _) in enumerate(lexical, 1)},
            "lexical_detail": {idx: (score, matched) for idx, score, matched in lexical},
            "claim_order": claim_order,
            "claim_rank": {int(idx): rank for rank, idx in enumerate(claim_order, 1)},
            "claim_sims": claim_sims,
            "title_order": title_order,
            "title_rank": {int(idx): rank for rank, idx in enumerate(title_order, 1)},
            "title_sims": title_sims,
        }
        self._component_cache[query] = c
        return c

    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        *,
        lexical_weight: float = 1.0,
        claim_weight: float = 1.0,
        title_weight: float = 0.5,
        overlap_weight: float = 0.3,
        min_semantic: float = 0.45,
        rrf_k: int = 60,
    ):
        if self.base.title_docs.get(_title_key(query)):
            out = self.base.retrieve(query, top_k)
            out["retrieval_mode"] = "exact_title"
            out["hybrid_config"] = None
            return out

        question_type = classify_question(query)
        marker = self._modern_marker(query)
        if marker is not None:
            return {
                "query": query,
                "question_type": question_type,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(question_type),
                "retrieval_mode": "fielded_hybrid_rrf",
                "hybrid_config": None,
                "abstention_reason": f"modern_subject_marker:{marker}",
            }

        c = self._components(query)
        candidate_indices = set()
        candidate_indices.update(idx for idx, _, _ in c["lexical"][: self.candidate_pool])
        candidate_indices.update(int(x) for x in c["claim_order"][: self.candidate_pool])
        candidate_indices.update(int(x) for x in c["title_order"][: self.candidate_pool])

        rows = []
        for idx in candidate_indices:
            lr = c["lexical_rank"].get(idx)
            cr = c["claim_rank"].get(idx)
            tr = c["title_rank"].get(idx)
            lexical_score, matched = c["lexical_detail"].get(idx, (0.0, []))
            claim_sim = float(c["claim_sims"][idx])
            title_sim = float(c["title_sims"][idx])
            overlap = self._title_overlap(query, idx)

            score = 0.0
            if lr is not None:
                score += lexical_weight / (rrf_k + lr)
            if cr is not None:
                score += claim_weight / (rrf_k + cr)
            if tr is not None:
                score += title_weight / (rrf_k + tr)
            if overlap:
                score += overlap_weight * overlap / (rrf_k + 1)

            rows.append(
                (idx, score, claim_sim, title_sim, overlap, lexical_score, matched, lr, cr, tr)
            )

        rows.sort(
            key=lambda x: (
                -x[1], -max(x[2], x[3]), -x[5],
                int(self.records[x[0]]["source_locus"]["volume"]),
                self.records[x[0]]["source_locus"].get("chapter_ordinal") or 10**9,
                self.records[x[0]]["id"],
            )
        )

        base_out = self.base.retrieve(augment_query(query), top_k=5)
        lexical_answerable = base_out["answerable"]
        best_semantic = max(
            float(np.max(c["claim_sims"])) if len(c["claim_sims"]) else 0.0,
            float(np.max(c["title_sims"])) if len(c["title_sims"]) else 0.0,
        )

        if not rows or (not lexical_answerable and best_semantic < min_semantic):
            return {
                "query": query,
                "question_type": question_type,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(question_type),
                "retrieval_mode": "fielded_hybrid_rrf",
                "hybrid_config": {
                    "lexical_weight": lexical_weight,
                    "claim_weight": claim_weight,
                    "title_weight": title_weight,
                    "overlap_weight": overlap_weight,
                    "min_semantic": min_semantic,
                    "rrf_k": rrf_k,
                },
                "abstention_reason": "hybrid_evidence_below_threshold",
            }

        hits = []
        for idx, score, claim_sim, title_sim, overlap, lexical_score, matched, lr, cr, tr in rows[: max(1, top_k)]:
            hit = self.base._hit(self.records[idx], score, matched)
            hit["retrieval_debug"] = {
                "rrf_score": round(float(score), 8),
                "claim_similarity": round(claim_sim, 6),
                "title_topic_similarity": round(title_sim, 6),
                "title_overlap": round(overlap, 6),
                "lexical_score": round(float(lexical_score), 6),
                "lexical_rank": lr,
                "claim_rank": cr,
                "title_rank": tr,
            }
            hits.append(hit)

        return {
            "query": query,
            "question_type": question_type,
            "status": "retrieved_evidence",
            "answerable": True,
            "message": "Evidence candidates retrieved from public-safe curator metadata using field-separated lexical and multilingual semantic rank fusion.",
            "hits": hits,
            "generation_contract": _generation_contract(question_type),
            "retrieval_mode": "fielded_hybrid_rrf",
            "hybrid_config": {
                "lexical_weight": lexical_weight,
                "claim_weight": claim_weight,
                "title_weight": title_weight,
                "overlap_weight": overlap_weight,
                "min_semantic": min_semantic,
                "rrf_k": rrf_k,
            },
        }

    def authority_counts(self):
        return dict(Counter(r["evidence_status"]["authority"] for r in self.records))
