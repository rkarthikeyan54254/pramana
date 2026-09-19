#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v2.json"
OUT = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v3.json"


def c(cid, split, language, query, expected_id=None, expected_locus=None, group="phase13_supported"):
    row = {
        "id": cid,
        "group": group,
        "split": split,
        "language": language,
        "query": query,
        "expected_status": "retrieved_evidence",
        "expected_any_ids": [expected_id] if expected_id else [],
        "expected_any_loci": [expected_locus] if expected_locus else [],
    }
    return row


def n(cid, split, language, query):
    return {
        "id": cid,
        "group": "hard_negative",
        "split": split,
        "language": language,
        "query": query,
        "expected_status": "insufficient_evidence",
        "expected_any_ids": [],
        "expected_any_loci": [],
    }


ADDITIONS = [
    # DEV: concepts that are not held out in v2 natural-query evaluation.
    c(
        "p13_prosody_types__en", "dev", "en",
        "How are Sanskrit metres divided between syllable-counted and mora-counted forms?",
        "mahaperiyava.deivathin_kural.v4.c376.prosody_theory",
    ),
    c(
        "p13_prosody_types__ta", "dev", "ta",
        "சமஸ்கிருதச் சந்தங்களில் எழுத்து எண்ணிக்கையையும் மாத்திரை எண்ணிக்கையையும் அடிப்படையாகக் கொண்ட இரு வகைகள் என்ன?",
        "mahaperiyava.deivathin_kural.v4.c376.prosody_theory",
    ),
    c(
        "p13_prosody_types__roman_ta", "dev", "roman_ta",
        "Sanskrita chandasil syllable count-um matra count-um base pannina rendu vagai enna?",
        "mahaperiyava.deivathin_kural.v4.c376.prosody_theory",
    ),
    c(
        "p13_alvar_return__en", "dev", "en",
        "Why does the king seek reconciliation, and how is the deity's earlier act reversed after the Alvar returns?",
        "mahaperiyava.deivathin_kural.v5.c058.return_and_reversal",
    ),
    c(
        "p13_alvar_return__ta", "dev", "ta",
        "ஆழ்வார் திரும்பியபின் அரசன் ஏன் சமரசம் தேடுகிறான், முன்னைய தெய்வச் செயல் எவ்வாறு மாற்றப்படுகிறது?",
        "mahaperiyava.deivathin_kural.v5.c058.return_and_reversal",
    ),
    c(
        "p13_alvar_return__roman_ta", "dev", "roman_ta",
        "Alvar thirumbi vandha pin raja yen samarasam thedaraan, deivathin munnaadiya seyal eppadi reverse aagudhu?",
        "mahaperiyava.deivathin_kural.v5.c058.return_and_reversal",
    ),
    c(
        "p13_bhalachandra__en", "dev", "en",
        "Why is Ganesha called Bhalachandra, and what does the moon on his forehead signify?",
        "mahaperiyava.deivathin_kural.v6.c038.chapter_teaching",
    ),
    c(
        "p13_bhalachandra__ta", "dev", "ta",
        "விநாயகர் ஏன் பாலசந்திரர் என்று அழைக்கப்படுகிறார், நெற்றியில் உள்ள சந்திரன் எதை குறிக்கிறது?",
        "mahaperiyava.deivathin_kural.v6.c038.chapter_teaching",
    ),
    c(
        "p13_bhalachandra__roman_ta", "dev", "roman_ta",
        "Vinayagar yen Bhalachandrar-nu sollappadugirar, netriyil irukkira chandran enna kurikkudhu?",
        "mahaperiyava.deivathin_kural.v6.c038.chapter_teaching",
    ),
    c(
        "p13_subrahmanya_satchit__en", "dev", "en",
        "How is Subrahmanya interpreted as the bliss in which sat and chit come together?",
        "mahaperiyava.deivathin_kural.v7.c284.chapter_teaching",
    ),
    c(
        "p13_subrahmanya_satchit__ta", "dev", "ta",
        "ஸத் மற்றும் சித் ஒன்றாகும் ஆனந்தமாக ஸுப்ரஹ்மண்யம் எப்படி விளக்கப்படுகிறது?",
        "mahaperiyava.deivathin_kural.v7.c284.chapter_teaching",
    ),
    c(
        "p13_subrahmanya_satchit__roman_ta", "dev", "roman_ta",
        "Sat-um chit-um serndha anandham Subrahmanya-nu eppadi vilakkappadudhu?",
        "mahaperiyava.deivathin_kural.v7.c284.chapter_teaching",
    ),

    # TEST: new held-out natural concepts.  None is used by the Phase-13 dev additions.
    c(
        "p13_moon_pride__en", "test", "en",
        "What moral does the Ganesha and moon episode draw about pride and mocking others?",
        "mahaperiyava.deivathin_kural.v4.c033.chapter_teaching",
    ),
    c(
        "p13_moon_pride__ta", "test", "ta",
        "விநாயகரும் சந்திரனும் பற்றிய கதை பெருமை மற்றும் பிறரை இகழ்வது குறித்து என்ன பாடம் கூறுகிறது?",
        "mahaperiyava.deivathin_kural.v4.c033.chapter_teaching",
    ),
    c(
        "p13_moon_pride__roman_ta", "test", "roman_ta",
        "Vinayagar chandran kathai perumaiyum mathavangala kindal panradhu pathiyum enna paadam solludhu?",
        "mahaperiyava.deivathin_kural.v4.c033.chapter_teaching",
    ),
    c(
        "p13_pallava_origins__en", "test", "en",
        "How does the discourse handle conflicting or uncertain traditions about the origins of the Pallavas?",
        "mahaperiyava.deivathin_kural.v5.c055.chapter_teaching",
    ),
    c(
        "p13_pallava_origins__ta", "test", "ta",
        "பல்லவர்களின் தோற்றம் பற்றிய முரண்பட்ட அல்லது உறுதியற்ற மரபுகளை உரை எவ்வாறு அணுகுகிறது?",
        "mahaperiyava.deivathin_kural.v5.c055.chapter_teaching",
    ),
    c(
        "p13_pallava_origins__roman_ta", "test", "roman_ta",
        "Pallavargal origin pathina conflicting traditions-ai urai eppadi handle pannudhu?",
        "mahaperiyava.deivathin_kural.v5.c055.chapter_teaching",
    ),
    c(
        "p13_ganesha_beginning__en", "test", "en",
        "Why is Ganesha invoked before beginning an undertaking or important piece of work?",
        "mahaperiyava.deivathin_kural.v6.c001.obstacle_removal_across_life",
    ),
    c(
        "p13_ganesha_beginning__ta", "test", "ta",
        "ஒரு முக்கியமான செயலைத் தொடங்குவதற்கு முன் விநாயகரை ஏன் நினைத்து வழிபடுகிறோம்?",
        "mahaperiyava.deivathin_kural.v6.c001.obstacle_removal_across_life",
    ),
    c(
        "p13_ganesha_beginning__roman_ta", "test", "roman_ta",
        "Mukkiyamaana velai start panna munnaadi Pillaiyar-ai yen ninaichu vazhipadanum?",
        "mahaperiyava.deivathin_kural.v6.c001.obstacle_removal_across_life",
    ),
    c(
        "p13_ganesha_nonsectarian__en", "test", "en",
        "Why should Tamil devotion to Ganesha avoid becoming sectarian or separatist?",
        "mahaperiyava.deivathin_kural.v7.c002.chapter_teaching",
    ),
    c(
        "p13_ganesha_nonsectarian__ta", "test", "ta",
        "தமிழ் விநாயக பக்தி ஏன் சமயப் பிரிவினையாகவோ தனித்துவப் பிரச்சாரமாகவோ மாறக்கூடாது?",
        "mahaperiyava.deivathin_kural.v7.c002.chapter_teaching",
    ),
    c(
        "p13_ganesha_nonsectarian__roman_ta", "test", "roman_ta",
        "Tamil Pillaiyar bhakti yen sectarian-a illa separatist-a maara koodadhu?",
        "mahaperiyava.deivathin_kural.v7.c002.chapter_teaching",
    ),

    # Multilingual hard negatives strengthen the abstention contract.
    n(
        "p13_negative_rag__en", "dev", "en",
        "Did Mahaperiyava discuss retrieval-augmented generation and vector databases?",
    ),
    n(
        "p13_negative_ai_chatbot__ta", "dev", "ta",
        "மஹாபெரியவா செயற்கை நுண்ணறிவு சாட்பாட்கள் பற்றி என்ன சொன்னார்?",
    ),
    n(
        "p13_negative_crypto__roman_ta", "dev", "roman_ta",
        "Mahaperiyava cryptocurrency staking pathi enna sonnaar?",
    ),
    n(
        "p13_negative_satellite__en", "test", "en",
        "What did Mahaperiyava say about satellite internet constellations?",
    ),
    n(
        "p13_negative_smartphone__ta", "test", "ta",
        "மஹாபெரியவா ஸ்மார்ட்போன் அறிவிப்புகள் பற்றி என்ன சொன்னார்?",
    ),
    n(
        "p13_negative_upi__roman_ta", "test", "roman_ta",
        "Mahaperiyava UPI transaction security pathi enna advise panninaar?",
    ),
]


def build():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    assert len(base["cases"]) == 124, len(base["cases"])
    ids = {x["id"] for x in base["cases"]}
    for row in ADDITIONS:
        if row["id"] in ids:
            raise ValueError(f"duplicate case id: {row['id']}")
        ids.add(row["id"])

    cases = base["cases"] + ADDITIONS
    assert len(cases) == 154

    spec = {
        "version": "3.0",
        "checkpoint_family": "MAHAPERIYAVA_RETRIEVAL_BENCHMARK_V3",
        "scope": (
            "154 retrieval cases over public-safe Mahaperiyava/Deivathin Kural metadata. "
            "Phase 13 adds new held-out concepts and multilingual hard negatives without changing authority."
        ),
        "quality_target": {
            "test_top1": 0.75,
            "test_top5": 0.90,
            "test_abstention": 1.0,
            "test_tamil_top5": 0.75,
            "test_roman_tamil_top5": 0.80,
        },
        "split_policy": (
            "Phase-13 parameters are selected on dev only. Test metrics are computed after the config is locked. "
            "The 12 new test supported cases use concepts not present in the Phase-13 dev additions."
        ),
        "cases": cases,
    }
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    spec = build()
    cases = spec["cases"]
    print("cases:", len(cases))
    print("groups:", dict(Counter(x["group"] for x in cases)))
    print("languages:", dict(Counter(x["language"] for x in cases)))
    print("splits:", dict(Counter(x["split"] for x in cases)))
    if not args.check:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
