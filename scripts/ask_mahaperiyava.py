#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import unicodedata
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
EXPECTED_VOLUME_COUNTS = {1: 927, 2: 673, 3: 370, 4: 457, 5: 345, 6: 254, 7: 342}

STOPWORDS = {
    "a","an","and","are","as","at","be","by","did","do","does","for","from",
    "he","his","how","i","in","is","it","maha","mahaperiyava","of","on","or",
    "say","says","said","should","that","the","their","them","there","these",
    "they","this","to","was","were","what","when","where","which","who","why",
    "with","would","about","one","really","teach","teaches","teaching",
    "என்ன","என்றால்","என்று","ஆகும்","இது","அவர்","சொல்கிறார்","சொன்னார்",
    "ஒரு","எப்படி","ஏன்","உள்ள","பற்றி","என்பது","என்பதை","என",
}

ALIASES = {
    "அத்வைதம்": "advaita nonduality nondual brahman",
    "அத்வைத": "advaita nonduality nondual brahman",
    "பக்தி": "bhakti devotion devotional",
    "கர்ம": "karma action duty",
    "கர்மா": "karma action duty",
    "ஞானம்": "jnana knowledge self knowledge",
    "மோக்ஷ": "moksha liberation",
    "மோட்சம்": "moksha liberation",
    "சிவன்": "shiva siva",
    "சிவ": "shiva siva",
    "விஷ்ணு": "vishnu visnu",
    "பெருமாள்": "vishnu perumal",
    "ஒன்றா": "unity same one nonseparate",
    "ஒன்று": "unity same one nonseparate",
    "காமாட்சி": "kamakshi compassion goddess",
    "கருணை": "compassion grace mercy",
    "விநாயகர்": "ganesha vinayaka pillaiyar",
    "பிள்ளையார்": "ganesha vinayaka pillaiyar",
    "வேதம்": "veda vedic",
    "வேத": "veda vedic",
    "தர்மம்": "dharma duty",
    "தர்ம": "dharma duty",
    "கோவில்": "temple worship",
    "கோயில்": "temple worship",
    "பூஜை": "puja worship ritual",
    "வழிபாடு": "worship devotion ritual",
    "அஹிம்சை": "ahimsa nonviolence",
    "சத்தியம்": "truth satya",
    "தியாகம்": "sacrifice renunciation",
    "கண்கள்": "eyes",
    "தமிழ்": "tamil",
    "சமயம்": "religion religious sect",
    "பிரிவு": "division separatism sectarian",
    "siva": "shiva",
    "shiva": "siva",
    "visnu": "vishnu",
    "vishnu": "visnu",
    "bakthi": "bhakti devotion",
    "bhakthi": "bhakti devotion",
    "devotion": "bhakti",
    "nondual": "advaita nonduality",
    "non-dual": "advaita nonduality",
    "liberation": "moksha",
    "pillaiyar": "ganesha vinayaka",
    "vinayaka": "ganesha pillaiyar",
    "mercy": "compassion grace",
    "sectarian": "division separatism religious",
    "separatist": "division separatism sectarian",
    "undertaking": "beginning obstacle work",
    "beginnings": "beginning obstacle work",
    "origins": "origin history dynasty",
}

QUESTION_TYPE_PATTERNS = {
    "source_lookup": (
        "source", "citation", "where does", "which chapter", "chapter", "record",
        "did mahaperiyava say", "did he say", "evidence for",
    ),
    "personal_guidance": (
        "what should i", "how should i", "i am", "i feel", "my life", "my family",
        "my work", "help me", "advice", "guidance",
    ),
    "broad_question": (
        "what does mahaperiyava say about", "what are his teachings on",
        "overall", "in general", "broadly",
    ),
}

CONTEXT_FLAG_TOKENS = (
    "requires_context", "normative", "hagiographic", "supernatural",
    "ritual_effect", "historical_claim", "scientific", "medical",
    "political_social", "caste", "gender", "violence", "social_generalization",
)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _record_files() -> dict[int, list[Path]]:
    out: dict[int, list[Path]] = {
        1: sorted(REVIEW.glob("mahaperiyava_dk_v1_*_teaching_records.jsonl"))
    }
    for volume in range(2, 8):
        path = REVIEW / f"mahaperiyava_deivathin_kural_v{volume}_teaching_records.jsonl"
        if not path.exists():
            raise FileNotFoundError(path)
        out[volume] = [path]
    return out


def load_corpus() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    counts: Counter[int] = Counter()
    for volume, paths in _record_files().items():
        for path in paths:
            for row in _jsonl(path):
                rid = row["id"]
                if rid in seen:
                    raise ValueError(f"duplicate teaching-record id: {rid}")
                seen.add(rid)
                actual_volume = int(row["source_locus"]["volume"])
                if actual_volume != volume:
                    raise ValueError(f"{rid}: volume mismatch {actual_volume} != {volume}")
                counts[volume] += 1
                rows.append(row)
    actual = dict(sorted(counts.items()))
    if actual != EXPECTED_VOLUME_COUNTS:
        raise ValueError(f"unexpected V1-V7 corpus counts: {actual}")
    if len(rows) != 3368:
        raise ValueError(f"unexpected teaching-record total: {len(rows)}")
    return rows


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").casefold()
    text = text.replace("_", " ").replace("-", " ").replace(".", " ")
    return " ".join(text.split())


def _expand(text: str) -> str:
    base = _norm(text)
    additions: list[str] = []
    for key, value in ALIASES.items():
        if key in base:
            additions.append(value)
    return _norm(" ".join([base, *additions]))


def _tokens(text: str) -> list[str]:
    toks = re.findall(r"[^\W_]+", _norm(text), flags=re.UNICODE)
    return [t for t in toks if len(t) > 1 and t not in STOPWORDS]


def classify_question(query: str) -> str:
    q = _norm(query)
    for kind in ("source_lookup", "personal_guidance", "broad_question"):
        if any(p in q for p in QUESTION_TYPE_PATTERNS[kind]):
            return kind
    return "doctrinal"


class MahaperiyavaRetriever:
    FIELD_WEIGHTS = {"claim": 5.0, "topics": 4.5, "title": 3.0, "identity": 2.0, "flags": 1.25}

    def __init__(self) -> None:
        self.records = load_corpus()
        self.docs: list[dict[str, Any]] = []
        df: Counter[str] = Counter()
        for record in self.records:
            locus = record["source_locus"]
            fields = {
                "claim": record.get("claim_summary") or "",
                "topics": " ".join(record.get("topics") or []),
                "title": locus.get("chapter_title_ta") or "",
                "identity": record["id"].replace(".", " "),
                "flags": " ".join(record.get("flags") or []),
            }
            counts = {name: Counter(_tokens(_expand(text))) for name, text in fields.items()}
            unique: set[str] = set()
            for c in counts.values():
                unique.update(c)
            df.update(unique)
            self.docs.append({"record": record, "fields": fields, "counts": counts})
        n = len(self.docs)
        self.idf = {t: math.log((n + 1) / (freq + 1)) + 1.0 for t, freq in df.items()}

    def _score(self, query: str, doc: dict[str, Any]) -> tuple[float, list[str]]:
        expanded = _expand(query)
        qtokens = list(dict.fromkeys(_tokens(expanded)))
        if not qtokens:
            return 0.0, []
        score = 0.0
        matched: set[str] = set()
        for field, counts in doc["counts"].items():
            weight = self.FIELD_WEIGHTS[field]
            for token in qtokens:
                freq = counts.get(token, 0)
                if not freq:
                    continue
                matched.add(token)
                score += weight * self.idf.get(token, 1.0) * (1.0 + 0.12 * min(freq - 1, 3))
        if not matched:
            return 0.0, []
        qwords = _tokens(expanded)
        bigrams = [" ".join(qwords[i:i+2]) for i in range(len(qwords) - 1)]
        for field, raw in doc["fields"].items():
            ftext = _expand(raw)
            weight = self.FIELD_WEIGHTS[field]
            for bg in bigrams:
                if bg and bg in ftext:
                    score += 0.45 * weight
            if len(expanded) >= 10 and expanded in ftext:
                score += 3.0 * weight
        coverage = len(matched) / max(1, len(qtokens))
        score *= 0.80 + 0.40 * coverage
        return score, sorted(matched)

    @staticmethod
    def _hit(record: dict[str, Any], score: float, matched: list[str]) -> dict[str, Any]:
        earlier = []
        for p in record.get("provenance", []):
            if p.get("witness_role") == "earlier_secondary":
                earlier.append({
                    "source_key": p.get("source_key"),
                    "locus": p.get("locus"),
                    "url": p.get("url"),
                    "snapshot_sha256": p.get("snapshot_sha256"),
                })
        flags = record.get("flags") or []
        context_required = any(
            token in " ".join(flags).casefold()
            for token in CONTEXT_FLAG_TOKENS
        )
        locus = record["source_locus"]
        return {
            "support_id": record["id"],
            "score": round(score, 6),
            "matched_terms": matched,
            "claim_summary": record.get("claim_summary"),
            "source": {
                "work": "Deivathin Kural",
                "volume": locus["volume"],
                "chapter_ordinal": locus.get("chapter_ordinal"),
                "chapter_title_ta": locus.get("chapter_title_ta"),
                "digital_url": locus.get("digital_url"),
            },
            "evidence_status": {
                "authority": record["evidence_status"]["authority"],
                "digital_attestation": record["evidence_status"].get("digital_attestation"),
                "print_check": record["evidence_status"].get("print_check"),
                "primary_source_status": record["evidence_status"].get("primary_source_status"),
                "wording_status": record["attribution"].get("wording_status"),
            },
            "flags": flags,
            "context_required": context_required,
            "earlier_witnesses": earlier,
            "safe_attribution": "This teaching is attested in Deivathin Kural as a teaching of Mahaperiyava.",
            "exact_source_text_exposed": False,
        }

    def retrieve(self, query: str, top_k: int = 8) -> dict[str, Any]:
        scored: list[tuple[float, list[str], dict[str, Any]]] = []
        for doc in self.docs:
            score, matched = self._score(query, doc)
            if score > 0:
                scored.append((score, matched, doc))
        scored.sort(key=lambda x: (
            -x[0],
            int(x[2]["record"]["source_locus"]["volume"]),
            x[2]["record"]["source_locus"].get("chapter_ordinal") or 10**9,
            x[2]["record"]["id"],
        ))
        question_type = classify_question(query)

        # Fail closed on weak lexical accidents. Multi-token questions need
        # at least two meaningful matched concepts in the best candidate.
        query_tokens = list(dict.fromkeys(_tokens(_expand(query))))
        if scored:
            best_matched = scored[0][1]
            min_matches = 1 if len(query_tokens) <= 1 else 2
            weak_match = len(best_matched) < min_matches
        else:
            weak_match = True

        if not scored or weak_match:
            return {
                "query": query,
                "question_type": question_type,
                "status": "insufficient_evidence",
                "answerable": False,
                "message": "No sufficiently strong V1-V7 teaching-record match was found. Do not answer from model memory.",
                "hits": [],
                "generation_contract": _generation_contract(question_type),
            }
        hits = [self._hit(doc["record"], score, matched) for score, matched, doc in scored[:max(1, top_k)]]
        return {
            "query": query,
            "question_type": question_type,
            "status": "retrieved_evidence",
            "answerable": True,
            "message": "Evidence candidates retrieved from public-safe curator metadata. Claim summaries are not quotations.",
            "hits": hits,
            "generation_contract": _generation_contract(question_type),
        }


def _generation_contract(question_type: str) -> dict[str, Any]:
    base = {
        "never_speak_as_mahaperiyava": True,
        "every_substantive_answer_idea_requires_support_ids": True,
        "retrieval_score_never_changes_authority": True,
        "raw_retrieval_is_not_advice": True,
        "exact_source_text_may_not_be_reconstructed": True,
        "generated_text_may_not_enter_corpus": True,
        "weak_or_missing_evidence_requires_abstention": True,
        "modern_application_must_be_labeled_app_generated": True,
        "evidence_drawer_required": True,
    }
    if question_type == "broad_question":
        base["synthesis_shape"] = "themes_not_single_prescription"
    elif question_type == "personal_guidance":
        base["synthesis_shape"] = "human_problem_first_then_supported_teaching_then_app_generated_application"
    elif question_type == "source_lookup":
        base["synthesis_shape"] = "source_and_evidence_first"
    else:
        base["synthesis_shape"] = "doctrinal_explanation_with_support_ids"
    return base


def main() -> int:
    ap = argparse.ArgumentParser(description="Evidence-first retrieval over Mahaperiyava / Deivathin Kural Volumes 1-7.")
    ap.add_argument("query")
    ap.add_argument("--top", type=int, default=8, dest="top_k")
    args = ap.parse_args()
    print(json.dumps(MahaperiyavaRetriever().retrieve(args.query, args.top_k), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
