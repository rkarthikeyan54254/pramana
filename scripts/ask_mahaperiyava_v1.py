#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"

STOPWORDS = {
    "a","an","and","are","as","at","be","by","did","do","does","for","from",
    "he","his","how","i","in","is","it","maha","mahaperiyava","of","on","or",
    "say","says","said","should","that","the","their","them","there","these",
    "they","this","to","ultimately","was","were","what","when","where","which",
    "who","why","with","would","about","one","really","teach","teaches",
    "என்ன","என்றால்","என்று","ஆகும்","இது","அவர்","சொல்கிறார்","சொன்னார்",
}

TAMIL_ALIASES = {
    "சிவன்": "shiva siva",
    "சிவ": "shiva siva",
    "விஷ்ணு": "vishnu",
    "பெருமாள்": "vishnu",
    "அத்வைதம்": "advaita nonduality",
    "அத்வைத": "advaita nonduality",
    "பக்தி": "bhakti devotion",
    "கர்ம": "karma",
    "கர்மா": "karma",
    "மோக்ஷ": "moksha liberation",
    "மோட்சம்": "moksha liberation",
    "காமாட்சி": "kamakshi",
    "அம்பாள்": "ambal devi goddess",
    "தேவி": "devi goddess",
    "வேதம்": "veda vedic",
    "வேத": "veda vedic",
    "ஞானம்": "jnana knowledge",
    "நவராத்திரி": "navaratri",
    "கண்கள்": "eyes",
    "கருணை": "compassion grace",
}

ENGLISH_ALIASES = {
    "siva": "shiva",
    "shiva": "siva",
    "visnu": "vishnu",
    "vishnu": "visnu",
    "bakthi": "bhakti",
    "bhakthi": "bhakti",
    "devotion": "bhakti",
    "liberation": "moksha",
    "nondual": "advaita nonduality",
    "non-dual": "advaita nonduality",
    "kamakshi": "kamakshi kamakshi",
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").casefold()
    text = text.replace("_", " ").replace("-", " ").replace(".", " ")
    return " ".join(text.split())


def _expand_query(text: str) -> str:
    base = _normalize_text(text)
    additions: list[str] = []
    for key, value in TAMIL_ALIASES.items():
        if key in base:
            additions.append(value)
    for key, value in ENGLISH_ALIASES.items():
        if key in base:
            additions.append(value)
    return _normalize_text(" ".join([base, *additions]))


def _tokens(text: str) -> list[str]:
    toks = re.findall(r"[^\W_]+", _normalize_text(text), flags=re.UNICODE)
    return [t for t in toks if len(t) > 1 and t not in STOPWORDS]


def _discover_record_files() -> list[Path]:
    return sorted(REVIEW.glob("mahaperiyava_dk_v1_*_teaching_records.jsonl"))


def load_corpus() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in _discover_record_files():
        for row in _load_jsonl(path):
            rid = row["id"]
            if rid in seen:
                raise ValueError(f"Duplicate teaching-record id: {rid}")
            seen.add(rid)
            rows.append(row)
    return rows


def _load_review_metadata() -> tuple[dict[str, dict[str, Any]], dict[int, str]]:
    unit_meta: dict[str, dict[str, Any]] = {}
    chapter_title_ta: dict[int, str] = {}

    for path in sorted(REVIEW.glob("mahaperiyava_dk_v1_*_curation_index.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for unit in data.get("units", []):
            uid = unit.get("id")
            if not uid:
                continue
            current = unit_meta.setdefault(uid, {})
            for key in ("question_intents", "topics", "chapter_slug"):
                if unit.get(key):
                    current[key] = unit[key]

    for path in sorted(REVIEW.glob("mahaperiyava_dk_v1_*_curator_manifest.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for chapter in data.get("chapters", []):
            ordinal = chapter.get("ordinal")
            title = chapter.get("title_ta")
            if isinstance(ordinal, int) and title:
                chapter_title_ta[ordinal] = title

    return unit_meta, chapter_title_ta


class V1Retriever:
    FIELD_WEIGHTS = {
        "claim": 4.0,
        "topics": 4.5,
        "intents": 3.0,
        "identity": 2.5,
        "title": 2.5,
    }

    def __init__(self) -> None:
        self.records = load_corpus()
        self.unit_meta, self.chapter_title_ta = _load_review_metadata()
        self.docs: list[dict[str, Any]] = []
        doc_freq: Counter[str] = Counter()

        for record in self.records:
            uid = record["id"]
            meta = self.unit_meta.get(uid, {})
            ordinal = record["source_locus"]["chapter_ordinal"]

            fields = {
                "claim": record.get("claim_summary", ""),
                "topics": " ".join(record.get("topics", [])),
                "intents": " ".join(meta.get("question_intents", [])),
                "identity": uid.replace(".", " "),
                "title": " ".join([
                    self.chapter_title_ta.get(ordinal, ""),
                    record.get("source_locus", {}).get("chapter_title_ta", "") or "",
                ]),
            }

            field_tokens = {
                name: Counter(_tokens(text))
                for name, text in fields.items()
            }
            unique = set()
            for counts in field_tokens.values():
                unique.update(counts)
            doc_freq.update(unique)

            self.docs.append({
                "record": record,
                "meta": meta,
                "fields": fields,
                "field_tokens": field_tokens,
            })

        n = len(self.docs)
        self.idf = {
            token: math.log((n + 1) / (df + 1)) + 1.0
            for token, df in doc_freq.items()
        }

    def _score(self, query: str, doc: dict[str, Any]) -> tuple[float, list[str]]:
        expanded = _expand_query(query)
        qtokens = list(dict.fromkeys(_tokens(expanded)))
        if not qtokens:
            return 0.0, []

        score = 0.0
        matched: set[str] = set()
        for field_name, counts in doc["field_tokens"].items():
            weight = self.FIELD_WEIGHTS[field_name]
            for token in qtokens:
                freq = counts.get(token, 0)
                if not freq:
                    continue
                matched.add(token)
                score += weight * self.idf.get(token, 1.0) * (1.0 + 0.12 * min(freq - 1, 3))

        # Small phrase/bigram bonus. This improves precision without changing
        # authority: relevance and evidence strength remain separate dimensions.
        qnorm = _expand_query(query)
        qwords = _tokens(qnorm)
        bigrams = [" ".join(qwords[i:i+2]) for i in range(len(qwords) - 1)]
        for field_name, raw in doc["fields"].items():
            fnorm = _normalize_text(raw)
            weight = self.FIELD_WEIGHTS[field_name]
            for bg in bigrams:
                if bg and bg in fnorm:
                    score += 0.55 * weight
            if len(qnorm) >= 8 and qnorm in fnorm:
                score += 4.0 * weight

        # Require at least one meaningful lexical/concept match.
        if not matched:
            return 0.0, []
        return score, sorted(matched)

    def retrieve(self, query: str, top_k: int = 5) -> dict[str, Any]:
        scored: list[tuple[float, list[str], dict[str, Any]]] = []
        for doc in self.docs:
            score, matched = self._score(query, doc)
            if score > 0:
                scored.append((score, matched, doc))

        scored.sort(
            key=lambda x: (
                -x[0],
                x[2]["record"]["source_locus"]["chapter_ordinal"],
                x[2]["record"]["id"],
            )
        )

        if not scored:
            return {
                "query": query,
                "status": "insufficient_evidence",
                "note": "No meaningful V1 metadata match was found. This checkpoint does not invent an answer.",
                "hits": [],
            }

        hits = []
        for score, matched, doc in scored[:top_k]:
            r = doc["record"]
            ordinal = r["source_locus"]["chapter_ordinal"]
            earlier = [
                {
                    "source_key": p.get("source_key"),
                    "locus": p.get("locus"),
                    "url": p.get("url"),
                }
                for p in r.get("provenance", [])
                if p.get("witness_role") == "earlier_secondary"
            ]
            hits.append({
                "id": r["id"],
                "score": round(score, 4),
                "matched_terms": matched,
                "claim_summary": r["claim_summary"],
                "volume": 1,
                "chapter_ordinal": ordinal,
                "chapter_title_ta": self.chapter_title_ta.get(ordinal),
                "authority": r["evidence_status"]["authority"],
                "wording_status": r["attribution"]["wording_status"],
                "digital_url": r["source_locus"].get("digital_url"),
                "earlier_witnesses": earlier,
            })

        return {
            "query": query,
            "status": "retrieved_evidence",
            "note": (
                "Retrieval checkpoint only. Claim summaries are curator-authored metadata, "
                "not verbatim quotations from Mahaperiyava."
            ),
            "hits": hits,
        }


def format_text(result: dict[str, Any]) -> str:
    lines = [
        f"Query: {result['query']}",
        f"Status: {result['status']}",
        result["note"],
    ]
    if not result["hits"]:
        return "\n".join(lines)

    for i, hit in enumerate(result["hits"], 1):
        label = hit["authority"]
        lines.extend([
            "",
            f"{i}. {hit['claim_summary']}",
            f"   Evidence: {label}",
            f"   Deivathin Kural V1, chapter {hit['chapter_ordinal']}"
            + (f" — {hit['chapter_title_ta']}" if hit.get("chapter_title_ta") else ""),
            f"   Record: {hit['id']}",
            f"   Source: {hit.get('digital_url') or 'not recorded'}",
        ])
        if hit["earlier_witnesses"]:
            for witness in hit["earlier_witnesses"]:
                lines.append(
                    f"   Earlier witness: {witness['source_key']} — {witness['locus']}"
                )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evidence-first lexical retrieval checkpoint for Mahaperiyava DK V1."
    )
    parser.add_argument("query", help="Question or concept to retrieve")
    parser.add_argument("--top", type=int, default=5, dest="top_k")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = V1Retriever().retrieve(args.query, max(1, args.top_k))
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
