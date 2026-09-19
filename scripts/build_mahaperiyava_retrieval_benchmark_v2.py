#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v2.json"

# Each concept is manually mapped to an existing public-safe teaching record.
# The query variants are deliberately user-like rather than copied from the
# claim_summary.  They test English, Tamil, and Roman-Tamil/mixed input.
CONCEPTS = [
    {
        "id": "advaita_nonduality",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.advaitam.nonduality_of_brahman"
        ],
        "queries": {
            "en": "How does Mahaperiyava explain the idea that ultimate reality is nondual?",
            "en_paraphrase": "If Brahman is one without a second, what does that mean for the apparent many?",
            "ta": "அத்வைதத்தில் பரம்பொருள் ஒன்றே என்று சொல்வதன் பொருள் என்ன?",
            "roman_ta": "Advaitathil Brahman onnu than endraal apparent differences-ai eppadi purinjukanum?",
        },
    },
    {
        "id": "bhakti_karma_jnana",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.mukthikku_munthaiya_nilaiyil_bhakti.karma_bhakti_and_jnana_as_successive_stages"
        ],
        "queries": {
            "en": "How are karma, bhakti and jnana connected on the spiritual path?",
            "en_paraphrase": "Why would disciplined action and devotion come before knowledge?",
            "ta": "கர்மம், பக்தி, ஞானம் மூன்றுக்கும் என்ன தொடர்பு?",
            "roman_ta": "Karmam bhakti jnanam moonum spiritual path-la eppadi connect aagudhu?",
        },
    },
    {
        "id": "shiva_vishnu_unity",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.shiva_vishnu_essential_unity"
        ],
        "queries": {
            "en": "How does Mahaperiyava reconcile Shiva worship and Vishnu worship?",
            "en_paraphrase": "Are Shiva and Vishnu ultimately separate according to this teaching?",
            "ta": "சிவனும் விஷ்ணுவும் இறுதியில் வேறா, ஒன்றா?",
            "roman_ta": "Sivanum Vishnuvum ultimate-a separate-aa illa onna?",
        },
    },
    {
        "id": "kamakshi_compassion",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.karuppum_sivappumana_kamakshi.red_kamakshi_as_compassionate_parashakti"
        ],
        "queries": {
            "en": "Why is Kamakshi associated with compassion in these teachings?",
            "en_paraphrase": "What is the connection between the Goddess Kamakshi and mercy or grace?",
            "ta": "காமாட்சிக்கும் கருணைக்கும் என்ன தொடர்பு?",
            "roman_ta": "Kamakshi-yum karunai-yum eppadi connect pannappadudhu?",
        },
    },
    {
        "id": "kamakshi_eyes",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.kamakshiyin_kangal.kamakshi_eyes_and_brows_as_bow_of_compassion"
        ],
        "queries": {
            "en": "What spiritual symbolism is attached to Kamakshi's eyes and brows?",
            "en_paraphrase": "Why are Kamakshi's eyes described as expressions of compassion?",
            "ta": "காமாட்சியின் கண்களும் புருவங்களும் எந்த ஆன்மிக அர்த்தத்தை குறிக்கின்றன?",
            "roman_ta": "Kamakshi kannum puruvamum compassion-ai eppadi symbolize pannudhu?",
        },
    },
    {
        "id": "ritual_concentration",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.sadangugal.ritual_cultivates_concentration_and_discipline"
        ],
        "queries": {
            "en": "Can ritual practice train concentration and personal discipline?",
            "en_paraphrase": "What inner benefit is supposed to come from regularly following religious rites?",
            "ta": "சடங்குகளை முறையாக செய்வது மன ஒருமைப்பாட்டையும் ஒழுக்கத்தையும் வளர்க்குமா?",
            "roman_ta": "Sadangu regular-a seyyaradhu concentration-um discipline-um valarkkuma?",
        },
    },
    {
        "id": "science_matter_energy_analogy",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.advaitamum_anu_vignaanamum.science_matter_energy_unity_as_analogy"
        ],
        "queries": {
            "en": "How is the scientific relation between matter and energy used as an analogy for unity?",
            "en_paraphrase": "Does the discourse compare modern physics on matter and energy with Advaita?",
            "ta": "பொருளும் சக்தியும் ஒன்றுடன் ஒன்று தொடர்புடையது என்பதை அத்வைதத்திற்கு ஒப்புமையாக பயன்படுத்துகிறாரா?",
            "roman_ta": "Matter energy relation-ai Advaita unity-kku analogy-aa use pannara teaching edhu?",
        },
    },
    {
        "id": "rituals_across_doctrines",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v3.c110.ritual_observances_shared_across_different_doctrines_preparatory"
        ],
        "queries": {
            "en": "Can people with different philosophical doctrines still share preparatory religious observances?",
            "en_paraphrase": "Do doctrinal differences necessarily mean that ritual disciplines must be completely different?",
            "ta": "வேறு தத்துவங்களைப் பின்பற்றினாலும் சில சடங்கு ஒழுக்கங்கள் பொதுவாக இருக்க முடியுமா?",
            "roman_ta": "Different darshanam follow pannalum sila ritual observances common-a irukka mudiyuma?",
        },
    },
    {
        "id": "knowledge_and_character",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v2.c206.knowledge_is_to_be_grounded_in_character_and_religious_discipline_before_broad_intellectual_exploration"
        ],
        "queries": {
            "en": "Why should broad intellectual learning be grounded first in character and discipline?",
            "en_paraphrase": "What is the warning against pursuing knowledge without moral formation?",
            "ta": "பெரிய அறிவைப் பெறுவதற்கு முன் நல்ல குணமும் ஒழுக்கமும் ஏன் அடிப்படையாக வேண்டும்?",
            "roman_ta": "Periya knowledge-ku munnaadi character-um discipline-um base-a venum nu yen?",
        },
    },
    {
        "id": "temple_and_arts_preservation",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.alayamum_deivika_kalaigalum.preserving_temple_presence_and_arts_benefits_society"
        ],
        "queries": {
            "en": "Why does preserving temples together with traditional sacred arts matter to society?",
            "en_paraphrase": "What social value is attributed to keeping temple culture and its arts alive?",
            "ta": "கோவில்களையும் தெய்வீக பாரம்பரிய கலைகளையும் காப்பது சமுதாயத்திற்கு ஏன் முக்கியம்?",
            "roman_ta": "Kovil culture-um traditional kalaigal-um preserve pannina society-kku enna benefit?",
        },
    },
    {
        "id": "ishta_devata_non_denigration",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.bhagavan_yaar_bhagavatpadhar_badhil.ishta_devata_without_denigration_and_reciprocal_worship"
        ],
        "queries": {
            "en": "Can someone be devoted to an ishta-devata without belittling other forms of God?",
            "en_paraphrase": "How should exclusive personal devotion avoid turning into hostility toward other deities?",
            "ta": "தன் இஷ்ட தெய்வத்தை வணங்கும்போது மற்ற தெய்வங்களை இகழாமல் இருக்க வேண்டுமா?",
            "roman_ta": "Ishta deivam mela bhakti irundhaalum other deities-ai kevalama pesa koodatha?",
        },
    },
    {
        "id": "epic_hearing_moral_formation",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v1.maha_bharatham.repeated_epic_hearing_shapes_moral_imagination"
        ],
        "queries": {
            "en": "How can repeatedly hearing the Mahabharata shape a person's moral imagination?",
            "en_paraphrase": "Why is regular listening to the epics treated as character-forming rather than mere entertainment?",
            "ta": "மகாபாரதத்தை மீண்டும் மீண்டும் கேட்பது நல்லொழுக்க மனப்பாங்கை எப்படி உருவாக்கும்?",
            "roman_ta": "Mahabharatam repeated-a kekkaradhu moral character-ai eppadi shape pannum?",
        },
    },
    {
        "id": "education_and_health",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v4.c078.chapter_teaching"
        ],
        "queries": {
            "en": "Should education also protect a student's bodily health and balanced development?",
            "en_paraphrase": "What is wrong with study that ignores the physical well-being of the learner?",
            "ta": "படிப்புடன் மாணவரின் உடல் ஆரோக்கியமும் சமநிலையான வளர்ச்சியும் கவனிக்கப்பட வேண்டுமா?",
            "roman_ta": "Padippoda student-oda udal health-um balanced growth-um care panna venuma?",
        },
    },
    {
        "id": "fearlessness_and_liberation",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v4.c229.chapter_teaching"
        ],
        "queries": {
            "en": "Why is liberation associated with fearlessness while samsara is linked with insecurity?",
            "en_paraphrase": "How does nondual awareness remove fear according to this discourse?",
            "ta": "மோக்ஷம் பயமின்மையுடன், சம்சாரம் பயத்துடன் எப்படி தொடர்புபடுத்தப்படுகிறது?",
            "roman_ta": "Moksham bayam illamai-oda, samsaram insecurity-oda eppadi connect aagudhu?",
        },
    },
    {
        "id": "action_to_nonaction",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v5.c163.chapter_teaching"
        ],
        "queries": {
            "en": "How can disciplined action become a path toward freedom from attachment to action?",
            "en_paraphrase": "Why prescribe duties if the eventual ideal is effortless non-doership?",
            "ta": "செயல்களை ஒழுக்கமாக செய்வது செயல்பற்றை கடந்து செல்லும் வழியாக எப்படி அமையும்?",
            "roman_ta": "Duty seyyaradhu eppadi later attachment-to-action-ai thaandi non-doership-kku kondu pogum?",
        },
    },
    {
        "id": "shankara_seeks_guru",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v5.c259.chapter_teaching"
        ],
        "queries": {
            "en": "Why is Shankara portrayed as seeking a qualified teacher even though he is treated as an avatara?",
            "en_paraphrase": "What does Shankara's search for a guru teach about self-sufficiency in spiritual learning?",
            "ta": "அவதாரமாகக் கருதப்பட்ட சங்கரரும் ஏன் தகுதியான குருவைத் தேடினார்?",
            "roman_ta": "Shankarar avatara-nu sonnalum yen qualified guru-ai thedinaar?",
        },
    },
    {
        "id": "love_self_transcendence",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v6.c110.chapter_teaching"
        ],
        "queries": {
            "en": "How is love described as moving beyond self-centered separateness into service?",
            "en_paraphrase": "What makes genuine love different from simply protecting one's own separate interests?",
            "ta": "அன்பு தனக்கே மையமான பிரிவுணர்வை விட்டுச் சேவையாக மாறுவது எப்படி?",
            "roman_ta": "Anbu self-centered separateness-ai vittutu service-a maarudhu-na enna artham?",
        },
    },
    {
        "id": "liberation_highest_benefit",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v6.c180.liberation_as_highest_benefit"
        ],
        "queries": {
            "en": "Why is liberation ranked above material prosperity as the highest benefit?",
            "en_paraphrase": "How are worldly benefits subordinated to removing ignorance and escaping samsara?",
            "ta": "பொருள் செல்வத்தை விட அறியாமை நீங்கி மோக்ஷம் பெறுவது ஏன் உயர்ந்த பலன்?",
            "roman_ta": "Material prosperity vida ignorance remove aagi moksham varradhu yen highest benefit?",
        },
    },
    {
        "id": "service_without_harming_study",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v7.c171.chapter_teaching"
        ],
        "queries": {
            "en": "How should students do service without neglecting their studies and basic responsibilities?",
            "en_paraphrase": "When can service become an excuse that harms a student's primary duties?",
            "ta": "படிப்பையும் அடிப்படை கடமைகளையும் பாதிக்காமல் மாணவர்கள் சேவை செய்வது எப்படி?",
            "roman_ta": "Padippai affect pannama students sevai eppadi seyyanum?",
        },
    },
    {
        "id": "upadhyaya_vs_guru",
        "expected_any_ids": [
            "mahaperiyava.deivathin_kural.v7.c058.chapter_teaching"
        ],
        "queries": {
            "en": "What is the difference between an upadhyaya's instructional role and the fuller role of a guru or acharya?",
            "en_paraphrase": "Why is an upadhyaya described as a more limited teaching office than a guru?",
            "ta": "உபாத்தியாயரின் பங்கு குரு அல்லது ஆசாரியரின் பங்கில் இருந்து எப்படி வேறுபடுகிறது?",
            "roman_ta": "Upadhyayar role-um guru acharya role-um enna difference?",
        },
    },
]

TITLE_CASES = [
    ("v2_c001_title", "கிழவியும் குழவியும்", 2, 1),
    ("v3_c001_title", "பிள்ளையார் சுழி", 3, 1),
    ("v4_c078_title", "ஆரோக்ய வளர்ச்சிக்கும் உதவி", 4, 78),
    ("v4_c229_title", "அபயம் – மோக்ஷம் ; பயம் – ஸம்ஸாரம்", 4, 229),
    ("v4_c376_title", "இருவகைச் சந்தங்கள்", 4, 376),
    ("v5_c163_title", "செயலற்றுப் போக வழியாகவே செயல்களும்!", 5, 163),
    ("v5_c259_title", "அன்னையைப் பிரிந்து ஆசானைத் தேடி..", 5, 259),
    ("v6_c038_title", "பாலசந்த்ரர்", 6, 38),
    ("v6_c110_title", "அன்பு என்பது என்ன ?", 6, 110),
    ("v6_c180_title", "இஹ-பர நலன் தரும் இணையடிப் பொடி", 6, 180),
    ("v7_c058_title", "உபாத்தியாயர்", 7, 58),
    ("v7_c171_title", "படிப்பு பாதிக்காமல் ஸேவை", 7, 171),
    ("v7_c284_title", "ஸத்தும் சித்தும் சேர்ந்த ஆனந்தமே ஸுப்ரஹ்மண்யம்", 7, 284),
    ("v2_c113_title", "வேதாந்த மதங்களும் மீமாம்ஸையும்", 2, 113),
]

NEGATIVES = [
    "What did Mahaperiyava say about smartphone push notifications?",
    "What did Mahaperiyava teach about Kubernetes autoscaling policies?",
    "Did Mahaperiyava recommend Bitcoin cold-storage wallets?",
    "What was Mahaperiyava's view on React Server Components?",
    "Did Mahaperiyava discuss Wi-Fi 7 router configuration?",
    "What did Mahaperiyava say about GPU tensor cores?",
    "Did Mahaperiyava discuss electric-vehicle battery management systems?",
    "What was Mahaperiyava's advice on QR-code payment fraud?",
    "Did Mahaperiyava recommend password managers and passkeys?",
    "What did Mahaperiyava teach about cloud container orchestration?",
    "What did Mahaperiyava say about PostgreSQL query planners?",
    "Did Mahaperiyava discuss 5G millimeter-wave antennas?",
    "What was Mahaperiyava's view on CRISPR gene-editing protocols?",
    "Did Mahaperiyava advise airlines on dynamic-pricing algorithms?",
    "What did Mahaperiyava say about index funds and exchange-traded funds?",
    "Did Mahaperiyava discuss video-game ray tracing?",
    "What was Mahaperiyava's view on USB-C versus Thunderbolt ports?",
    "What did Mahaperiyava teach about ransomware incident response?",
    "Did Mahaperiyava discuss large-language-model prompt injection?",
    "What did Mahaperiyava recommend for Docker image-layer caching?",
    "Did Mahaperiyava discuss quantum-computing error correction?",
    "What did Mahaperiyava say about social-media engagement algorithms?",
    "Did Mahaperiyava recommend cryptocurrency staking strategies?",
    "What was Mahaperiyava's view on generative-AI copyright licensing?",
    "Did Mahaperiyava discuss autonomous-drone delivery logistics?",
    "What did Mahaperiyava say about cloud-observability SLO dashboards?",
    "Did Mahaperiyava discuss Kubernetes service-mesh routing?",
    "What was Mahaperiyava's advice on smartphone screen-time applications?",
    "Did Mahaperiyava discuss electric-scooter battery swapping?",
    "What did Mahaperiyava say about biometric face-recognition systems?",
]


def build() -> dict:
    cases = []
    variant_order = ["en", "en_paraphrase", "ta", "roman_ta"]
    language = {
        "en": "en",
        "en_paraphrase": "en",
        "ta": "ta",
        "roman_ta": "roman_ta",
    }

    for concept_index, concept in enumerate(CONCEPTS):
        split = "dev" if concept_index < 14 else "test"
        for variant in variant_order:
            case = {
                "id": f"{concept['id']}__{variant}",
                "group": "natural_supported",
                "split": split,
                "language": language[variant],
                "query": concept["queries"][variant],
                "expected_status": "retrieved_evidence",
                "expected_any_ids": concept["expected_any_ids"],
                "expected_any_loci": [],
            }
            cases.append(case)

    for i, (cid, title, volume, ordinal) in enumerate(TITLE_CASES):
        cases.append({
            "id": cid,
            "group": "exact_title_lookup",
            "split": "dev" if i < 10 else "test",
            "language": "ta",
            "query": title,
            "expected_status": "retrieved_evidence",
            "expected_any_ids": [],
            "expected_any_loci": [{"volume": volume, "chapter_ordinal": ordinal}],
        })

    for i, query in enumerate(NEGATIVES):
        cases.append({
            "id": f"unsupported_modern_{i+1:02d}",
            "group": "hard_negative",
            "split": "dev" if i < 20 else "test",
            "language": "en",
            "query": query,
            "expected_status": "insufficient_evidence",
            "expected_any_ids": [],
            "expected_any_loci": [],
        })

    assert len(CONCEPTS) == 20
    assert len(TITLE_CASES) == 14
    assert len(NEGATIVES) == 30
    assert len(cases) == 124
    assert len({c["id"] for c in cases}) == len(cases)

    return {
        "version": "2.0",
        "checkpoint": "MAHAPERIYAVA_RETRIEVAL_BENCHMARK_V2",
        "status": "CURATED_QUERY_SET_FOR_HYBRID_RETRIEVAL_EVALUATION",
        "corpus_scope": "Deivathin Kural V1-V7 public-safe teaching metadata only",
        "case_count": len(cases),
        "design": {
            "natural_supported": 80,
            "exact_title_lookup": 14,
            "hard_negative": 30,
            "languages": ["en", "ta", "roman_ta"],
            "split_policy": "concept-level dev/test split so language variants of one concept do not cross splits",
            "authority_effect": "none",
            "restricted_source_text_included": False,
        },
        "cases": cases,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(OUT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    payload = build()
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path = Path(args.output)
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != rendered:
            raise SystemExit("benchmark file is missing or out of sync with builder")
        print("mahaperiyava retrieval benchmark v2: synchronized (124 cases)")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    print(path)
    print("cases: 124 (80 supported + 14 exact-title + 30 hard-negative)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
