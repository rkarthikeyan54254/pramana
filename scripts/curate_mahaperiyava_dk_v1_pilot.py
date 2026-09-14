#!/usr/bin/env python3
'''
Curate the first 56 Mahaperiyava / Deivathin Kural Volume 1 teaching units.

Run from pramana repo root on branch mahaperiyava-dk-v1-corpus.

Recommended:
    python ~/Downloads/curate_mahaperiyava_dk_v1_pilot.py --commit --push

No Deivathin Kural source text is written to tracked files.
'''

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path.cwd()
EXPECTED_BRANCH = "mahaperiyava-dk-v1-corpus"

PRIVATE_PACKET = ROOT / "data/private/mahaperiyava_dk_v1_pilot_review_packet_v3.json"
SCHEMA = ROOT / "schema/teaching_record.schema.json"
CATALOG = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
HISTORICAL_REVIEW = ROOT / "data/review/mahaperiyava_dk_v1_historical_witness_review.json"

TEACHING_RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
CURATION_INDEX = ROOT / "data/review/mahaperiyava_dk_v1_pilot_curation_index.json"
RESEARCH_MD = ROOT / "data/research/mahaperiyava_dk_v1_pilot_teaching_units.md"
TEST = ROOT / "tests/test_mahaperiyava_dk_v1_pilot_teaching_records.py"
CATALOG_TEST = ROOT / "tests/test_mahaperiyava_dk_v1_catalog.py"
REPO_SCRIPT = ROOT / "scripts/curate_mahaperiyava_dk_v1_pilot.py"

CURATED_UNITS: list[dict[str, Any]] = json.loads('[{"id": "mahaperiyava.deivathin_kural.v1.advaitam.nonduality_of_brahman", "chapter_slug": "advaitam", "unit_slug": "nonduality_of_brahman", "claim_summary": "Ultimate reality is non-dual: Brahman alone is real, while the apparent plurality of jivas arises through maya; jivatman and Paramatman are not ultimately separate.", "question_intents": ["What is Advaita?", "Are jiva and Paramatma ultimately different?", "How does Mahaperiyava explain non-duality?"], "source_paragraph_ids": ["p001", "p002"], "proposed_authority": "earlier_witness_supported", "historical_witness": {"source_key": "acharya-upanyasangal-part2-1957-58-scan", "locus": "எல்லாம் தழுவும் அத்வைதம், printed p. 27 ff.; PDF pp. 38-41", "basis": "same_doctrinal_claim"}, "flags": [], "topics": ["advaita", "brahman", "jiva", "maya"], "source_paragraph_hashes": ["8656c21b3e3099aaa3bee1148e5b236428adf3c452c8fafaf96c61812d0210b0", "23ad4f4a5d2e81d84f4a7e92a1ce221507bb46c9932d89004d1a72e32a6aae10"]}, {"id": "mahaperiyava.deivathin_kural.v1.advaitam.moksha_as_freedom_from_duality", "chapter_slug": "advaitam", "unit_slug": "moksha_as_freedom_from_duality", "claim_summary": "Moksha is freedom from bondage produced by the sense of a second, external reality; this liberation is recognition of the already-unbound Brahman rather than acquisition of a new state.", "question_intents": ["What is moksha in Advaita?", "Why does duality create bondage?", "Is liberation something newly attained?"], "source_paragraph_ids": ["p003", "p004"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["moksha", "bondage", "advaita"], "source_paragraph_hashes": ["08eb6c76add076c2617d4cf2127a2228817ce6e42dfc5f77171a086e09168b8d", "0f06a12800576c09849f8b02532328beb7d7605984e617674df49587f9d9303d"]}, {"id": "mahaperiyava.deivathin_kural.v1.advaitam.karma_upasana_as_steps", "chapter_slug": "advaitam", "unit_slug": "karma_upasana_as_steps", "claim_summary": "Karma and upasana are preparatory disciplines leading toward non-dual realization, while the practitioner should cultivate remembrance that reality is one even before direct experience dawns.", "question_intents": ["What role do karma and upasana play in Advaita?", "How should one practice before direct realization?"], "source_paragraph_ids": ["p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["karma", "upasana", "sadhana", "advaita"], "source_paragraph_hashes": ["505859d0ea4edaae5f2e0cf9a1e166be39dfb547d78d3aab4386d6f46b655885"]}, {"id": "mahaperiyava.deivathin_kural.v1.advaitam.one_self_across_states_and_beings", "chapter_slug": "advaitam", "unit_slug": "one_self_across_states_and_beings", "claim_summary": "The continuity of one subject across waking, dream and changing mental states is used as an analogy for recognizing one underlying Self in apparently different beings.", "question_intents": ["How does Mahaperiyava use waking and dream to explain oneness?", "How can we see the same Self in different beings?"], "source_paragraph_ids": ["p006", "p007", "p008", "p009"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["self", "waking", "dream", "oneness"], "source_paragraph_hashes": ["09601474cdd9da6d3bf11f5b3f0d3ad5151fea0a46b50fcdca6781c1f068f522", "ba338b57785917e1a5fbd18cef8199788d5ac4589cf656c2efb3139840329623", "3491fc5c72adff22b4ab80e635a0644e9efffd15a5b32f0243c8d75cb7553988", "74693a050731a366ef089a15a9e76636f7f0c4b707167b8937d51d783dd2f568"]}, {"id": "mahaperiyava.deivathin_kural.v1.advaitam.single_intelligent_source_of_jada_and_jiva", "chapter_slug": "advaitam", "unit_slug": "single_intelligent_source_of_jada_and_jiva", "claim_summary": "The ordered relation between sentient beings and the material world is presented as pointing to one supreme intelligence that appears as both, rather than two independent sources.", "question_intents": ["How does Mahaperiyava reason from the world to one supreme intelligence?", "What is the source of jada and jiva?"], "source_paragraph_ids": ["p010", "p011", "p012"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["isvara", "creation", "jada", "jiva", "maya"], "source_paragraph_hashes": ["d13b7d86812cb926c3993d4a4a7d85b18502fd7a8fba607c653d4e7efab9df52", "96953aa507a7c9c411550638a94f8456bea72b7f9c70a770bd46358fd83985e0", "7aab77fe90c2e15704ed8c16d6c833e7b7a0cfdde645d860c72ddc60660272ee"]}, {"id": "mahaperiyava.deivathin_kural.v1.advaitam.jivanmukti_and_all_as_self", "chapter_slug": "advaitam", "unit_slug": "jivanmukti_and_all_as_self", "claim_summary": "Non-dual realization culminates in experiencing the whole world as oneself; such knowledge is described as liberation and as possible while embodied.", "question_intents": ["Can moksha be experienced while living?", "What does it mean to see the whole world as oneself?"], "source_paragraph_ids": ["p013"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["jivanmukti", "moksha", "oneness"], "source_paragraph_hashes": ["6cb90b5aac65d22da2e089a2e696fd3738c80d4fcc4ef9c5c94a018df024ad18"]}, {"id": "mahaperiyava.deivathin_kural.v1.dharmame_thalaikakkum.dharma_as_order_for_wellbeing", "chapter_slug": "dharmame_thalaikakkum", "unit_slug": "dharma_as_order_for_wellbeing", "claim_summary": "Dharma is presented as the human form of a wider order or niyati that enables the world and living beings to function in mutual well-being.", "question_intents": ["What is dharma?", "How is dharma related to order in nature?"], "source_paragraph_ids": ["p001", "p002", "p003", "p004", "p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["dharma", "niyati", "world_order"], "source_paragraph_hashes": ["b06bf3b9004aa4084d1d1103a7487e095eee962fc96beabc69fd12fa7be7e475", "3178bebaa36c63aef8ebc764f76321cccb5198e5396375c78ff3cc901a3727a7", "234c7db87d73beffb69a59189be78736e13b6cfbbba1ee6e66f2e0e07c768df7", "0a64eb8351fcc2d59cfeb6af2e4976d8394a5a18bbfa46923e5398deb4a8fa37", "477165b801f3f3d8cb174de5fdb0669742b10216aae1f5e5fe0294d6f80598ad"]}, {"id": "mahaperiyava.deivathin_kural.v1.dharmame_thalaikakkum.religion_redirects_self_interest", "chapter_slug": "dharmame_thalaikakkum", "unit_slug": "religion_redirects_self_interest", "claim_summary": "Religious disciplines are described as reducing ego and self-interest by orienting the person toward God, duty, love, sacrifice and service rather than material gain alone.", "question_intents": ["Why do religions prescribe worship and disciplines?", "How does religion reduce selfishness?"], "source_paragraph_ids": ["p006", "p007", "p008", "p009", "p010"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["religion", "bhakti", "selflessness", "service"], "source_paragraph_hashes": ["89a86511cfdd5510d928cafe8eec6aad8b3eb98b076b8119b05fe698ae9a1f9c", "55c905614becbf4d835c1128920f17e7a7bd06f42a8e08fab51e35930ac4ec75", "49bfad195fe1d38b63712bf89295577575a6f3f66beb92466086a375d6da94bc", "64254f98558dccb1dce3ec61985b778ef0e4c9a2d5200da4de34bf1dd7d41fdb", "2060c9ee3a01da4ee2b9fcdbdf365367ffacf9be160bb20704d585dcd524c2c1"]}, {"id": "mahaperiyava.deivathin_kural.v1.dharmame_thalaikakkum.dharma_benefits_life_and_afterlife", "chapter_slug": "dharmame_thalaikakkum", "unit_slug": "dharma_benefits_life_and_afterlife", "claim_summary": "Dharma is said to support peace and well-being in this life and to remain spiritually beneficial beyond bodily life.", "question_intents": ["How does dharma protect a person?", "Does dharma matter only for this life?"], "source_paragraph_ids": ["p011"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["dharma", "afterlife", "wellbeing"], "source_paragraph_hashes": ["30c82e70afda23c54dd0aff05d4c525c7ab13e493bb6e62eeab5c8c4ffd47154"]}, {"id": "mahaperiyava.deivathin_kural.v1.dharmame_thalaikakkum.inherited_dharma_as_practical_path", "chapter_slug": "dharmame_thalaikakkum", "unit_slug": "inherited_dharma_as_practical_path", "claim_summary": "The chapter recommends practicing the dharma transmitted through one\'s inherited tradition rather than continually inventing an untested path.", "question_intents": ["Which dharma should a person follow?", "Why does Mahaperiyava emphasize inherited practice?"], "source_paragraph_ids": ["p012"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["context_sensitive_traditional_norm"], "topics": ["dharma", "tradition", "practice"], "source_paragraph_hashes": ["f21f3bca3ec7a637223d1f1c3025138f525f017d2e40d13619c405b67eabaf1d"]}, {"id": "mahaperiyava.deivathin_kural.v1.dharmame_thalaikakkum.dharma_protects_through_hardship", "chapter_slug": "dharmame_thalaikakkum", "unit_slug": "dharma_protects_through_hardship", "claim_summary": "Using Rama\'s exile and victory as an illustration, the chapter teaches that hardship should be met within dharma and that dharma ultimately protects the one who protects it.", "question_intents": ["What does \'dharma protects\' mean?", "How does the Ramayana illustrate dharma protecting a person?"], "source_paragraph_ids": ["p013", "p014", "p015", "p016", "p017", "p018", "p019"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["dharma", "ramayana", "rama", "hardship"], "source_paragraph_hashes": ["a968b0a28281412c6fad7df7c88325b77e68c658ad4986869421f999b494ec37", "9af99cb8bc9f1aac83d21729bde9049d4e41ec901c191a93b3d10e29777cceb9", "e6df328fc49cb7e4cdc436c01a6c575472597fc8cd702c84d709b02f0f2025a4", "3cb87c981249c77db497a12130e6268c7a6045625b170018da1a1766f4d94457", "207ccdf76ce7445da3095a110eefd04905cc9285d7247c10b2d8d2b788b3d91d", "f61ecf29ebc7a5b2c8dfbc66f24d30ba28d441f685d5682c36aebfe38083f0b7", "4e644fef1176013e542ddb03e662bbf47780c83fc04a7980c99fb392694e3969"]}, {"id": "mahaperiyava.deivathin_kural.v1.mathathin_payan.religion_and_four_purusharthas", "chapter_slug": "mathathin_payan", "unit_slug": "religion_and_four_purusharthas", "claim_summary": "Religion is presented as a discipline that orders the four purusharthas—dharma, artha, kama and moksha—rather than treating material prosperity or pleasure as the final goal.", "question_intents": ["What are the four purusharthas?", "What is the purpose of religion in relation to dharma, artha, kama and moksha?"], "source_paragraph_ids": ["p001", "p002"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["purusharthas", "dharma", "artha", "kama", "moksha"], "source_paragraph_hashes": ["f6e114a697d0b37fd2d5e88c9290ecb2f54b4d1973b3ad36719a3396397a0322", "b8884a9733828417dd94adcfeb380c821d1c4bc29571e386840f1ef69813f0f0"]}, {"id": "mahaperiyava.deivathin_kural.v1.mathathin_payan.transient_pleasure_vs_moksha", "chapter_slug": "mathathin_payan", "unit_slug": "transient_pleasure_vs_moksha", "claim_summary": "Ordinary pleasures are temporary and repeatedly renew desire, whereas moksha is described as lasting, complete happiness and true freedom.", "question_intents": ["How is moksha different from ordinary happiness?", "Why are worldly pleasures insufficient?"], "source_paragraph_ids": ["p003", "p004", "p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["moksha", "happiness", "desire"], "source_paragraph_hashes": ["97079b0047bca2da5b26e23b7db7132721be57ef7cadf1b9d4caadac88068725", "69ebe4ac2eacecd380491165320b6aa2df8b2316061b2e72c50b86db83d3e6a5", "083d310cb53d8a832510c9157a5111c080868e8fd83e7b1038c1b2bc6f7149f7"]}, {"id": "mahaperiyava.deivathin_kural.v1.mathathin_payan.dharma_supports_artha_and_kama", "chapter_slug": "mathathin_payan", "unit_slug": "dharma_supports_artha_and_kama", "claim_summary": "Dharma is described as the proper foundation for acquiring and using artha and enjoying kama without allowing them to become destructive ends in themselves.", "question_intents": ["How should artha and kama be related to dharma?", "Why is dharma placed first among the purusharthas?"], "source_paragraph_ids": ["p006", "p007"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["dharma", "artha", "kama"], "source_paragraph_hashes": ["7ab5c3c9795295ad5d0d1551bcaee89cfca47b2001eb42a1052b7119f22d5ea3", "bd0228e20365052579891dc3404e5cbbd219babc0f9fdf3bbe2ffe7b7bf0d15c"]}, {"id": "mahaperiyava.deivathin_kural.v1.mathathin_payan.nishkama_dharma_leads_to_moksha", "chapter_slug": "mathathin_payan", "unit_slug": "nishkama_dharma_leads_to_moksha", "claim_summary": "When dharmic action is performed without attachment to its fruits and offered to God, it becomes a means of inner purification and ultimately of moksha.", "question_intents": ["How does nishkama dharma lead toward moksha?", "Why perform dharma without expecting results?"], "source_paragraph_ids": ["p007"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["nishkama_karma", "dharma", "moksha", "purification"], "source_paragraph_hashes": ["bd0228e20365052579891dc3404e5cbbd219babc0f9fdf3bbe2ffe7b7bf0d15c"]}, {"id": "mahaperiyava.deivathin_kural.v1.mathathin_payan.religion_disciplines_desire_toward_moksha", "chapter_slug": "mathathin_payan", "unit_slug": "religion_disciplines_desire_toward_moksha", "claim_summary": "Religion is described as gradually regulating human desires and social life so that a person can move from limited pleasures toward the lasting freedom of moksha.", "question_intents": ["Why does religion regulate desires?", "What is the ultimate aim of religion?"], "source_paragraph_ids": ["p007", "p008", "p009", "p010"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["religion", "desire", "moksha", "dharma"], "source_paragraph_hashes": ["bd0228e20365052579891dc3404e5cbbd219babc0f9fdf3bbe2ffe7b7bf0d15c", "29525fbeedc534695524a8a64a0099e29894488ef62564a7a98522b56f877fdd", "8c84c665d5c48bbf4032534a57bff50ed7730e9b38cd3b494b4c384e5c45c329", "b9edffda9c378e256eedb6224c637fd7def18aaf79872db15140caa1fcaa7c20"]}, {"id": "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.bhakti_common_across_hindu_siddhantas", "chapter_slug": "sakala_mathangalukkum_pothuvana_bhakti", "unit_slug": "bhakti_common_across_hindu_siddhantas", "claim_summary": "Across Advaita, Vishishtadvaita, Dvaita and Saiva Siddhanta, devotion to the divine is presented as a shared spiritual means despite doctrinal differences.", "question_intents": ["What is common across different Hindu philosophical schools?", "Is bhakti common to Advaita, Vishishtadvaita, Dvaita and Saiva Siddhanta?"], "source_paragraph_ids": ["p001"], "proposed_authority": "earlier_witness_supported", "historical_witness": {"source_key": "acharya-upanyasangal-part2-1957-58-scan", "locus": "எல்லாம் தழுவும் அத்வைதம், especially PDF pp. 39-41", "basis": "narrower_hindu_siddhanta_shared_bhakti_claim"}, "flags": [], "topics": ["bhakti", "advaita", "vishishtadvaita", "dvaita", "saiva_siddhanta"], "source_paragraph_hashes": ["9bfbca9c2bfd4023c6e87d6d7aae86225a2e872e4b1814bb5c0709349e0bb6ee"]}, {"id": "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.bhakti_across_religions", "chapter_slug": "sakala_mathangalukkum_pothuvana_bhakti", "unit_slug": "bhakti_across_religions", "claim_summary": "The chapter extends the centrality of devotion beyond Hindu schools and explicitly includes Christianity and Islam among traditions in which surrender to a higher power has a central place.", "question_intents": ["Did Mahaperiyava say bhakti is common to different religions?", "How does the chapter view Christianity and Islam in relation to bhakti?"], "source_paragraph_ids": ["p001"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["bhakti", "religions", "christianity", "islam"], "source_paragraph_hashes": ["9bfbca9c2bfd4023c6e87d6d7aae86225a2e872e4b1814bb5c0709349e0bb6ee"]}, {"id": "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.bhakti_arises_even_when_not_doctrinally_central", "chapter_slug": "sakala_mathangalukkum_pothuvana_bhakti", "unit_slug": "bhakti_arises_even_when_not_doctrinally_central", "claim_summary": "The chapter argues that devotional practice tends to arise naturally even in traditions or movements that formally emphasize inquiry or non-theistic teaching.", "question_intents": ["Why does bhakti arise even where doctrine does not emphasize it?", "What does Mahaperiyava say about devotion among Buddhists or followers of jnana teachers?"], "source_paragraph_ids": ["p002"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["historical_generalization"], "topics": ["bhakti", "buddhism", "devotion"], "source_paragraph_hashes": ["0b012749bd1c912d42e6569244a4a99fb336e79b559940428f60aa6de1852037"]}, {"id": "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.advaita_bhakti_and_abheda", "chapter_slug": "sakala_mathangalukkum_pothuvana_bhakti", "unit_slug": "advaita_bhakti_and_abheda", "claim_summary": "Advaitic devotion should gradually include the recognition that the worshipper and the worshipped are grounded in the same Paramatman, even while devotion begins with an apparent distinction.", "question_intents": ["How does bhakti work in Advaita?", "Can one worship God while holding an Advaitic view?"], "source_paragraph_ids": ["p003", "p004", "p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["advaita", "bhakti", "abheda", "paramatma"], "source_paragraph_hashes": ["a65b109c5518ebb218607e6ab2a5dc48ac830efbbc6ffd8c47da1d5ef7dc5a03", "d5f0199e6f4d14f221bb2f2c280bc46ba5e51853766b969d05c1495af6cdacfe", "71d15447e9777a7302fdba93eb7d1a8aed1103e7044d8ec36ae7647abfa12830"]}, {"id": "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.grace_reveals_divine_nature", "chapter_slug": "sakala_mathangalukkum_pothuvana_bhakti", "unit_slug": "grace_reveals_divine_nature", "claim_summary": "Devotion is said to draw divine grace, through which the nature of God becomes known and the seeker can move from saguna worship toward realization of the nirguna ground.", "question_intents": ["What is the role of grace in bhakti?", "How can saguna upasana lead toward nirguna realization?"], "source_paragraph_ids": ["p006", "p007"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["grace", "saguna", "nirguna", "bhakti"], "source_paragraph_hashes": ["665b765e1e72c84ce601ef55dd9c8b7b205c7e21ff26feaf2cf116ec663109ba", "5d20f02535fefc92b0a6da4635968044506bbc1c7291e42da3f0ed350e424510"]}, {"id": "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.ishta_devata_and_many_forms", "chapter_slug": "sakala_mathangalukkum_pothuvana_bhakti", "unit_slug": "ishta_devata_and_many_forms", "claim_summary": "Sanatana Dharma\'s ishta-devata principle is presented as allowing different temperaments to approach the one divine reality through different forms and methods of worship.", "question_intents": ["What is an ishta devata?", "Why are there many divine forms in Hindu worship?"], "source_paragraph_ids": ["p008", "p009"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["ishta_devata", "murti", "worship", "sanatana_dharma"], "source_paragraph_hashes": ["51db2d248ba346ae3fa8335d4ae5b01e20cd2612be2173b3b2d84f155dc43924", "7341954ac22364228e8b1b80c0989d0dfd3eaae7798b9687bab25ff86c32ff9e"]}, {"id": "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.bhakti_as_common_spiritual_disposition", "chapter_slug": "sakala_mathangalukkum_pothuvana_bhakti", "unit_slug": "bhakti_as_common_spiritual_disposition", "claim_summary": "Whatever the specific form of worship, the devotional disposition itself is presented as a recurring central feature of religious life.", "question_intents": ["What remains common when forms of worship differ?", "What does Mahaperiyava identify as central in religious practice?"], "source_paragraph_ids": ["p010"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["bhakti", "worship", "religion"], "source_paragraph_hashes": ["eef8991e1961f6e9058de9afec709f4b869143fd02bfb17ae3f169bf997f866a"]}, {"id": "mahaperiyava.deivathin_kural.v1.varna_dharmam.religions_as_distinct_spiritual_disciplines", "chapter_slug": "varna_dharmam", "unit_slug": "religions_as_distinct_spiritual_disciplines", "claim_summary": "Different religions are compared to different systems of treatment: their disciplines need not be made identical for each to function as a spiritual path.", "question_intents": ["Why does Mahaperiyava compare religions to different medical systems?", "Must all religious disciplines be made identical?"], "source_paragraph_ids": ["p002", "p003"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["context_sensitive"], "topics": ["religion", "dharma", "pluralism"], "source_paragraph_hashes": ["5a392adbc4dcb0d687ff8627c8b2b977331c8640480225cd3f1fd64055d80799", "d22e833c8e1130e26548b22aeb67745a864c613a0d1e2f6bf14f4791a1ab61c5"]}, {"id": "mahaperiyava.deivathin_kural.v1.varna_dharmam.samanya_and_vishesha_dharma", "chapter_slug": "varna_dharmam", "unit_slug": "samanya_and_vishesha_dharma", "claim_summary": "The chapter distinguishes universal ethical duties such as nonviolence, truthfulness, purity and self-control from special duties assigned within a traditional social order.", "question_intents": ["What are samanya dharmas?", "How does Mahaperiyava distinguish common and special duties?"], "source_paragraph_ids": ["p004", "p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["context_sensitive_social_teaching"], "topics": ["samanya_dharma", "vishesha_dharma", "varna"], "source_paragraph_hashes": ["2b803e224929310fd68a240f00ebc7c6691859fd1f02deaea588d0dc74a2b508", "1fe7a336c44855b20f7df16924ce99b1e6d5be32ae5bb583de0db3e5c14def70"]}, {"id": "mahaperiyava.deivathin_kural.v1.varna_dharmam.follow_ones_own_religion_without_conversion", "chapter_slug": "varna_dharmam", "unit_slug": "follow_ones_own_religion_without_conversion", "claim_summary": "The chapter explicitly says that people of other religions should pursue spiritual welfare within their own traditions and rejects calling them to convert to Hinduism.", "question_intents": ["What did Mahaperiyava say about converting people from other religions?", "Should people stay within their own religion?"], "source_paragraph_ids": ["p006", "p007"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["religious_pluralism", "conversion", "bhakti"], "source_paragraph_hashes": ["95dce75ee6958d149bce2ccc217036740018568edf5ddf825bf26a45d5f4231b", "d1bdad592d0e6cc30f9e9df5b77d2fb137e946bd42817bd19ea5340c6d17cdfc"]}, {"id": "mahaperiyava.deivathin_kural.v1.varna_dharmam.modern_religious_decline_argument", "chapter_slug": "varna_dharmam", "unit_slug": "modern_religious_decline_argument", "claim_summary": "The chapter advances a historical-social argument linking weakening inherited social-religious disciplines with the growth of unbelief; this is an attributed viewpoint, not a verified historical finding in the corpus.", "question_intents": ["What argument does this chapter make about modern religious decline?", "How does the chapter relate social change and loss of religious faith?"], "source_paragraph_ids": ["p008", "p009", "p010", "p011"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["historical_claim_requires_external_verification", "context_sensitive_social_teaching"], "topics": ["religion", "modernity", "varna"], "source_paragraph_hashes": ["44e8466ecdcc28083742e07aeaaf5b93584374777e94729ffb051fb1e01c0a2b", "1b075b5abb67a588048f2af970b0c1c53d07c4f4369dba7971c6e9e132725fad", "230920e5ed6a96090b1be6430a8625e735a66afc8b3c8ec50a6c6a7500c5233c", "1fe0c65bb2c562a85314e022508ef7afa80444fc8ad495dc2298c7f3626d6fae"]}, {"id": "mahaperiyava.deivathin_kural.v1.varna_dharmam.varna_as_explanation_for_traditional_continuity", "chapter_slug": "varna_dharmam", "unit_slug": "varna_as_explanation_for_traditional_continuity", "claim_summary": "The chapter argues that varna-based differentiation contributed to the historical continuity of Sanatana Dharma despite internal divisions and external pressures.", "question_intents": ["Why does Mahaperiyava defend varna dharma?", "What role does this chapter assign to varna in the survival of Sanatana Dharma?"], "source_paragraph_ids": ["p012", "p013", "p014"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["historical_claim_requires_external_verification", "context_sensitive_social_teaching"], "topics": ["varna", "sanatana_dharma", "history"], "source_paragraph_hashes": ["d83c355691852226f281ce043ffe38daf01e78339f7489f9acbda683982b3af3", "b74662fa96a02511a1750f16e34fc75671264bb24c1234ad0c3ddeb12b5d4b4e", "3ba85dbd0fed3667010c1a2afa31dc879debf053fa5992551037adc1aeb8d183"]}, {"id": "mahaperiyava.deivathin_kural.v1.eliya_vazhvu.standard_of_living_is_contentment", "chapter_slug": "eliya_vazhvu", "unit_slug": "standard_of_living_is_contentment", "claim_summary": "A genuinely high standard of living is identified with contentment and sufficiency rather than the multiplication of possessions and conveniences.", "question_intents": ["What is a true high standard of living?", "Does wealth or comfort produce contentment?"], "source_paragraph_ids": ["p001", "p002"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["simple_living", "contentment", "materialism"], "source_paragraph_hashes": ["c7984c8fb9b921d45bf2409d3b8a4e8d8d29f63f22f2303c1c9bd9bb2a4c2fd2", "1aeb0adff10cc5d6203cf4a7eecb7bff484ca6b3f6f40390fbfafa53200e763c"]}, {"id": "mahaperiyava.deivathin_kural.v1.eliya_vazhvu.expanding_wants_create_inner_poverty", "chapter_slug": "eliya_vazhvu", "unit_slug": "expanding_wants_create_inner_poverty", "claim_summary": "Endlessly expanding wants are described as a form of poverty because they prevent contentment even when a person possesses considerable wealth.", "question_intents": ["What does Mahaperiyava mean by poverty amid wealth?", "Why do more possessions not end desire?"], "source_paragraph_ids": ["p002"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["desire", "contentment", "wealth"], "source_paragraph_hashes": ["1aeb0adff10cc5d6203cf4a7eecb7bff484ca6b3f6f40390fbfafa53200e763c"]}, {"id": "mahaperiyava.deivathin_kural.v1.eliya_vazhvu.luxury_harms_spiritual_and_social_wellbeing", "chapter_slug": "eliya_vazhvu", "unit_slug": "luxury_harms_spiritual_and_social_wellbeing", "claim_summary": "Luxury and competitive consumption are portrayed as weakening spiritual aspiration and increasing comparison, jealousy and social friction.", "question_intents": ["How can luxury affect spiritual life?", "How does competitive consumption affect society?"], "source_paragraph_ids": ["p003", "p004"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["social_generalization"], "topics": ["luxury", "spirituality", "social_harmony"], "source_paragraph_hashes": ["af51ea1c76bb2b426859585700503fa1cf423797a4d9a0fa6d07b532548075cf", "340dcf32eb42bdd211aaeb186f998b9d0601c485a942bd083082b0542986a1d3"]}, {"id": "mahaperiyava.deivathin_kural.v1.eliya_vazhvu.affluent_should_model_simplicity", "chapter_slug": "eliya_vazhvu", "unit_slug": "affluent_should_model_simplicity", "claim_summary": "Those with means are urged to live simply, both for their own spiritual good and to reduce envy and social tension around them.", "question_intents": ["Why should wealthy people live simply?", "How can simple living help society?"], "source_paragraph_ids": ["p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["context_sensitive_historical_examples"], "topics": ["simple_living", "wealth", "social_harmony"], "source_paragraph_hashes": ["1ccebde172dabe00eba8a33ae6886d0ae6e793c5c6c5b87d04dc8bbd965b5057"]}, {"id": "mahaperiyava.deivathin_kural.v1.eliya_vazhvu.reduce_needs_and_do_duty", "chapter_slug": "eliya_vazhvu", "unit_slug": "reduce_needs_and_do_duty", "claim_summary": "The practical prescription is to reduce unnecessary needs, fulfill one\'s duties and seek fullness in the mind rather than in consumption.", "question_intents": ["How should one practice simple living?", "What is Mahaperiyava\'s practical advice for contentment?"], "source_paragraph_ids": ["p006"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["simple_living", "duty", "contentment"], "source_paragraph_hashes": ["3cdeeaf37ac185cd4eee2db1cae25aba46f45040decbde817f113e8cb41966d6"]}, {"id": "mahaperiyava.deivathin_kural.v1.tamilnattu_panpin_perumai.temple_and_textual_heritage", "chapter_slug": "tamilnattu_panpin_perumai", "unit_slug": "temple_and_textual_heritage", "claim_summary": "The chapter celebrates Tamil Nadu as exceptionally rich in temples, religious literature and manuscript traditions.", "question_intents": ["What does Mahaperiyava praise about Tamil Nadu\'s religious heritage?", "Why does he highlight temples and manuscripts in Tamil Nadu?"], "source_paragraph_ids": ["p001", "p002"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["quantitative_historical_claim_requires_verification"], "topics": ["tamil_nadu", "temples", "manuscripts", "heritage"], "source_paragraph_hashes": ["c3d2b9489299a26d9bd1e9535eb218023f4ef708c49a0c1789faceccb355ce0c", "dadd2b0be97692f87254afdf5b60001ce50d856e424ddcbfed0738001c1fb917"]}, {"id": "mahaperiyava.deivathin_kural.v1.tamilnattu_panpin_perumai.regional_not_racial_aryan_dravidian_reading", "chapter_slug": "tamilnattu_panpin_perumai", "unit_slug": "regional_not_racial_aryan_dravidian_reading", "claim_summary": "The chapter rejects a racialized Aryan-versus-Dravidian division and presents older regional classifications as geographic rather than racial.", "question_intents": ["What does this chapter say about Aryan and Dravidian identity?", "Does Mahaperiyava treat Aryan and Dravidian as separate races?"], "source_paragraph_ids": ["p003", "p004"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["historical_claim_requires_external_verification", "context_sensitive_identity_claim"], "topics": ["aryan", "dravidian", "history", "identity"], "source_paragraph_hashes": ["a46161b3d83ce8457fe789a1fa902b9ad0b9b28b902adfe1d0d0064c415a1ef0", "50f91359fde1c8f9844066b45d7d9d70103e2263c815686f6dfa938397541818"]}, {"id": "mahaperiyava.deivathin_kural.v1.tamilnattu_panpin_perumai.tamil_capacity_to_absorb_languages_and_customs", "chapter_slug": "tamilnattu_panpin_perumai", "unit_slug": "tamil_capacity_to_absorb_languages_and_customs", "claim_summary": "Tamil people are described as unusually ready to learn and absorb other languages and cultural forms, a capacity the chapter views as both admirable and potentially risky when used without discrimination.", "question_intents": ["What does Mahaperiyava say about Tamils adopting other languages and customs?", "What is both the strength and danger of cultural openness?"], "source_paragraph_ids": ["p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["cultural_generalization"], "topics": ["tamil", "language", "culture"], "source_paragraph_hashes": ["0c563be1e74687a05bac2a10cf4a3d59c52f6e51d15955a9232607768a625912"]}, {"id": "mahaperiyava.deivathin_kural.v1.tamilnattu_panpin_perumai.tamil_nadu_as_preserver_of_plural_traditions", "chapter_slug": "tamilnattu_panpin_perumai", "unit_slug": "tamil_nadu_as_preserver_of_plural_traditions", "claim_summary": "Tamil Nadu is portrayed as allowing migrant communities to preserve their languages and customs while participating in the region\'s wider cultural life.", "question_intents": ["How does Mahaperiyava describe Tamil Nadu\'s treatment of migrant communities?", "Why does he compare Tamil Nadu to a refrigerator preserving cultures?"], "source_paragraph_ids": ["p006"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["historical_generalization"], "topics": ["tamil_nadu", "pluralism", "language", "migration"], "source_paragraph_hashes": ["0a3aac30bc1ad93bc59592255328607a91320bff6600d502cbbdf85c894f881f"]}, {"id": "mahaperiyava.deivathin_kural.v1.tamilnattu_panpin_perumai.vedic_and_bhakti_continuity_in_tamil_nadu", "chapter_slug": "tamilnattu_panpin_perumai", "unit_slug": "vedic_and_bhakti_continuity_in_tamil_nadu", "claim_summary": "The chapter presents Tamil Nadu as a long-standing home of Vedic, bhakti and literary traditions and describes periods of challenge as followed by renewed religious commitment.", "question_intents": ["How does Mahaperiyava connect Tamil Nadu with Vedic and bhakti traditions?", "What does he say about religious renewal in Tamil history?"], "source_paragraph_ids": ["p007", "p008"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["historical_claim_requires_external_verification"], "topics": ["tamil_nadu", "veda", "bhakti", "history"], "source_paragraph_hashes": ["9f477266aa76859b24f2538c14d20a21ad3cf270b0a68501b968c474954ca509", "cac7bf8e62f222fa99f38801411c0d5af54939a00adc239d51b4bbb2767ad90e"]}, {"id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.temple_as_communal_gratitude_and_offering", "chapter_slug": "alaya_vazhipadu", "unit_slug": "temple_as_communal_gratitude_and_offering", "claim_summary": "Temple worship is described as a communal way of expressing gratitude to God by offering back food, clothing and other gifts received through divine grace.", "question_intents": ["Why should we offer food and clothing to God?", "Why are temples needed if people can worship at home?"], "source_paragraph_ids": ["p001"], "proposed_authority": "earlier_witness_supported", "historical_witness": {"source_key": "acharya-upanyasangal-part1-1957-58-scan", "locus": "ஆலய வணக்கம், printed p. 39 ff.; PDF pp. 54-56", "basis": "substantial_doctrinal_and_structural_overlap"}, "flags": [], "topics": ["temple", "gratitude", "naivedya", "offering"], "source_paragraph_hashes": ["3dcd7a16920791d24f76ae2762c04c9539dee54692dbbbcc3ac037d273276136"]}, {"id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.consecrated_murti_as_special_presence", "chapter_slug": "alaya_vazhipadu", "unit_slug": "consecrated_murti_as_special_presence", "claim_summary": "The chapter explains the temple as being built around consecrated murtis in which the all-pervading divine is understood to have a special ritual presence.", "question_intents": ["Why are murtis consecrated in temples?", "What is special sannidhya?"], "source_paragraph_ids": ["p002"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["murti", "consecration", "sannidhya", "temple"], "source_paragraph_hashes": ["b1f12de3f3346935805334b7dc2653b47a860bd6a42d0067cc47219dff9f39a8"]}, {"id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.regular_attendance_sustains_temple_worship", "chapter_slug": "alaya_vazhipadu", "unit_slug": "regular_attendance_sustains_temple_worship", "claim_summary": "Regular temple attendance by the community is presented as necessary to sustain worship, cleanliness, lamps, offerings and proper care of the deity.", "question_intents": ["Why should even people who worship at home go to the temple?", "How does temple attendance help maintain worship?"], "source_paragraph_ids": ["p003"], "proposed_authority": "earlier_witness_supported", "historical_witness": {"source_key": "acharya-upanyasangal-part1-1957-58-scan", "locus": "ஆலய வணக்கம், printed p. 39 ff.; PDF pp. 54-56", "basis": "same_sequence_regular_attendance_and_upkeep"}, "flags": [], "topics": ["temple_attendance", "puja", "cleanliness", "community"], "source_paragraph_hashes": ["4ae402c03893722304ea35c310f7841acacebf46ecac3deab3d6af87b57cddc3"]}, {"id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.temple_cleanliness_and_inner_purity", "chapter_slug": "alaya_vazhipadu", "unit_slug": "temple_cleanliness_and_inner_purity", "claim_summary": "Caring for the cleanliness and dignity of the temple and deity is linked to purification of one\'s own mind and is treated as a communal religious duty.", "question_intents": ["Why is temple cleanliness spiritually important?", "How does caring for the deity relate to purity of mind?"], "source_paragraph_ids": ["p004"], "proposed_authority": "earlier_witness_supported", "historical_witness": {"source_key": "acharya-upanyasangal-part1-1957-58-scan", "locus": "ஆலய வணக்கம், printed p. 39 ff.; PDF pp. 54-56", "basis": "distinctive_cleanliness_and_mind_purification_sequence"}, "flags": [], "topics": ["temple_cleanliness", "mind_purification", "duty"], "source_paragraph_hashes": ["805a32e4ce750b29db4bd255200ed3b925377b16571ab63fad0b78d6fbacc0bb"]}, {"id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.preserve_agama_based_ritual_order", "chapter_slug": "alaya_vazhipadu", "unit_slug": "preserve_agama_based_ritual_order", "claim_summary": "Temple ritual is treated as an established agama-based system that should be repaired where practice has declined rather than freely redesigned according to contemporary preference.", "question_intents": ["Why does Mahaperiyava oppose arbitrary changes to temple ritual?", "What role do Agamas play in temple worship?"], "source_paragraph_ids": ["p005", "p006"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["context_sensitive_ritual_norm"], "topics": ["agama", "ritual", "temple"], "source_paragraph_hashes": ["474bc44524b8afc8a13c7694c42b92840fab8b96ef726cb7457ce846da137178", "ca0da9e56256b3fc17f47671c4d41d5f9253330223130a380571236ef0307e14"]}, {"id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.reform_begins_with_self_discipline_and_loving_explanation", "chapter_slug": "alaya_vazhipadu", "unit_slug": "reform_begins_with_self_discipline_and_loving_explanation", "claim_summary": "The response to temple decline should begin with practitioners correcting themselves, worshipping sincerely and explaining tradition without anger or hostility.", "question_intents": ["How should temple reform be approached?", "How should one respond to critics of traditional temple practice?"], "source_paragraph_ids": ["p007", "p008"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["temple", "reform", "self_discipline", "love"], "source_paragraph_hashes": ["295ca6359326da73e835e38f559ee77c4d5f9edb8a84f07cb3ec632d8face543", "a61841d7d6369c14dbfb5deed5aac9ab98fb478e1b26cf0b9f13e80505fdb8b1"]}, {"id": "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.karma_and_phaladata", "chapter_slug": "bhakti_seyvathu_etharkaga", "unit_slug": "karma_and_phaladata", "claim_summary": "Moral action is presented within a cause-and-effect order in which Isvara is the giver of karmic fruits.", "question_intents": ["Who gives the fruits of karma?", "Why does Mahaperiyava connect cause and effect with Isvara?"], "source_paragraph_ids": ["p001"], "proposed_authority": "earlier_witness_supported", "historical_witness": {"source_key": "acharya-upanyasangal-part1-1957-58-scan", "locus": "ஈசுவர பக்தி ஏன் செய்யவேண்டும்?, printed p. 117 ff.; PDF pp. 132-135", "basis": "substantial_doctrinal_overlap"}, "flags": ["packet_reextract_required"], "topics": ["karma", "phaladata", "isvara"], "source_paragraph_hashes": ["53eac68d3bd06e1ae6f148afde6417d940493611dca1825482029c0319cbf190"]}, {"id": "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.prayer_for_relief_and_acceptance", "chapter_slug": "bhakti_seyvathu_etharkaga", "unit_slug": "prayer_for_relief_and_acceptance", "claim_summary": "Prayer for removal of suffering is treated as understandable, but a higher disposition is to seek the capacity to accept karmic difficulty without being inwardly overwhelmed by it.", "question_intents": ["Should we pray for God to remove suffering?", "What is a higher prayer when facing hardship?"], "source_paragraph_ids": ["p002"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["packet_reextract_required"], "topics": ["prayer", "suffering", "karma"], "source_paragraph_hashes": ["487435a5ea8572145adf6c357e318e8ed454c0486f0069d23e22f35f2b34cab2"]}, {"id": "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.ordinary_prayer_has_partial_value", "chapter_slug": "bhakti_seyvathu_etharkaga", "unit_slug": "ordinary_prayer_has_partial_value", "claim_summary": "Petitionary prayer is not presented as the highest bhakti, yet it can lighten mental burden and weaken the egoistic belief that one can accomplish everything alone.", "question_intents": ["Is asking God for things true bhakti?", "Does ordinary prayer still have value?"], "source_paragraph_ids": ["p003"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["packet_reextract_required"], "topics": ["prayer", "bhakti", "ego"], "source_paragraph_hashes": ["47e8fa4bacb03bbdc9340d7cb752f492f4f5d7edfe23ffc058852a5892f868de"]}, {"id": "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.surrender_as_deeper_bhakti", "chapter_slug": "bhakti_seyvathu_etharkaga", "unit_slug": "surrender_as_deeper_bhakti", "claim_summary": "Deeper bhakti is described as surrendering the claim of personal ownership and accepting the divine will, which quiets anxiety and purifies the mind.", "question_intents": ["What is true surrender in bhakti?", "What does \'let it be as You will\' mean spiritually?"], "source_paragraph_ids": ["p004"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["packet_reextract_required"], "topics": ["surrender", "bhakti", "purification"], "source_paragraph_hashes": ["4cf94469a21a5663988e9dd0fec80b7c73247e681d89c4575ba4f3dba222b646"]}, {"id": "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.love_of_god_as_enduring_love", "chapter_slug": "bhakti_seyvathu_etharkaga", "unit_slug": "love_of_god_as_enduring_love", "claim_summary": "Love is a source of deep joy, but worldly relationships are impermanent; love directed to the enduring divine is therefore presented as a source of lasting joy.", "question_intents": ["Why love God?", "How is divine love different from human attachment?"], "source_paragraph_ids": ["p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["packet_reextract_required"], "topics": ["divine_love", "bhakti", "impermanence"], "source_paragraph_hashes": ["1f2fa866a76f79aae5e05e093146fb9abd6c792f3540d5db5a99b0a00e515137"]}, {"id": "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.mature_love_becomes_universal_love", "chapter_slug": "bhakti_seyvathu_etharkaga", "unit_slug": "mature_love_becomes_universal_love", "claim_summary": "As devotion matures, everything is seen as belonging to or being the divine, reducing partiality and extending love toward all.", "question_intents": ["How does bhakti lead to love for everyone?", "What happens when devotion matures?"], "source_paragraph_ids": ["p005"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["packet_reextract_required"], "topics": ["universal_love", "bhakti", "oneness"], "source_paragraph_hashes": ["1f2fa866a76f79aae5e05e093146fb9abd6c792f3540d5db5a99b0a00e515137"]}, {"id": "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.bhakti_culminates_in_grace_and_moksha", "chapter_slug": "bhakti_seyvathu_etharkaga", "unit_slug": "bhakti_culminates_in_grace_and_moksha", "claim_summary": "Bhakti is described as helping with mental purification, steadiness and divine qualities, and ultimately as opening the way—through grace—to freedom from karmic bondage and non-dual realization.", "question_intents": ["What are the fruits of bhakti?", "How does bhakti lead to moksha or Advaita realization?"], "source_paragraph_ids": ["p006"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["packet_reextract_required"], "topics": ["bhakti", "grace", "moksha", "advaita"], "source_paragraph_hashes": ["63b5c8a5c2fde070c73d5c3c44a5bc1ca9804be78df216a87cee936afa4df59b"]}, {"id": "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.gunas_and_trimurti_symbolism", "chapter_slug": "siva_vishnu_abhedam", "unit_slug": "gunas_and_trimurti_symbolism", "claim_summary": "The three gunas—sattva, rajas and tamas—are used as a symbolic framework for discussing Brahma, Vishnu and Shiva and their cosmic functions.", "question_intents": ["How are the three gunas related to the Trimurti?", "Why are Brahma, Vishnu and Shiva associated with different gunas?"], "source_paragraph_ids": ["p001", "p002", "p003", "p004", "p005", "p006"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["gunas", "trimurti", "brahma", "vishnu", "shiva"], "source_paragraph_hashes": ["747ae5497c771f9c0f3a2ac1c433ccff2d438087a84ffffe790bce9af83a65aa", "41d460664af2e2f80320279361cdec7299ebc4154baf723ebde7d721077e5000", "a579db15d7c47cc4b8d56fba7528b6a3437fd774e06fe022ab0686acd906e06e", "dde33c33e54192a8d1aa4888ff1e2127877eca624f9d80d302f7253df0ca56bc", "4c06ead99674eac63cc9ff39d1b66970453f4e7cc76558ed922d82c52b0041b0", "0e3006cc1df040cd1e80a9d78994226ce6eadfae406d0f5ae07cfb5ad7c3c3aa"]}, {"id": "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.sectarian_readings_of_shiva_and_vishnu", "chapter_slug": "siva_vishnu_abhedam", "unit_slug": "sectarian_readings_of_shiva_and_vishnu", "claim_summary": "The chapter presents contrasting Saiva and Vaishnava interpretations of preservation, dissolution and liberation as examples of sectarian reasoning.", "question_intents": ["Why do Saivas and Vaishnavas argue about which deity is supreme?", "How does the chapter describe their different interpretations?"], "source_paragraph_ids": ["p007"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["descriptive_of_sectarian_views"], "topics": ["saiva", "vaishnava", "shiva", "vishnu"], "source_paragraph_hashes": ["a771d4b914c19aac51d94f8f35def579ae5d3243f7e65982f05ba935136a27eb"]}, {"id": "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.smarta_view_no_higher_or_lower_deity", "chapter_slug": "siva_vishnu_abhedam", "unit_slug": "smarta_view_no_higher_or_lower_deity", "claim_summary": "The Smarta standpoint is stated as seeing Shiva, Vishnu and the other deities as different forms of the one Paramatman, without an ultimate hierarchy among them.", "question_intents": ["What is the Smarta view of Shiva and Vishnu?", "Is one deity higher than another according to this chapter?"], "source_paragraph_ids": ["p008"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["smarta", "shiva", "vishnu", "paramatma", "abheda"], "source_paragraph_hashes": ["0d036fc8b205a816050b91d78a642099bfdc4b1008c1d6dd05bee2d8465686e3"]}, {"id": "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.simple_guna_labels_do_not_separate_shiva_vishnu", "chapter_slug": "siva_vishnu_abhedam", "unit_slug": "simple_guna_labels_do_not_separate_shiva_vishnu", "claim_summary": "The chapter points to features of Vishnu and Shiva that cross simple sattva/tamas assignments, arguing that neither deity can be reduced to a single exclusive guna.", "question_intents": ["Why does Mahaperiyava question simple sattva/tamas labels for Shiva and Vishnu?"], "source_paragraph_ids": ["p009", "p010", "p011"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": [], "topics": ["gunas", "shiva", "vishnu"], "source_paragraph_hashes": ["b294e5abe0a622b8aeb17b804f8f4e258051e70790dd217280a2f65ab452edf4", "4146031c69ea694fab73f39a222e612d5e1bd09b88a9267a3b1c97a33b511e5f", "127bbefd8360ed3c0e5d9f14e51aa3576faef878e9c11edb6a4ca626af86fade"]}, {"id": "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.shiva_vishnu_essential_unity", "chapter_slug": "siva_vishnu_abhedam", "unit_slug": "shiva_vishnu_essential_unity", "claim_summary": "Because sattva and tamas are shown as present in different ways in both Shiva and Vishnu, the chapter concludes that their essential reality is one and that both may be worshipped with devotion.", "question_intents": ["What does Shiva-Vishnu abheda mean?", "Can one worship both Shiva and Vishnu?", "What is the conclusion of this chapter about Shiva and Vishnu?"], "source_paragraph_ids": ["p012"], "proposed_authority": "dk_attested", "historical_witness": null, "flags": ["historical_match_candidate_external_1927"], "topics": ["shiva", "vishnu", "abheda", "bhakti"], "source_paragraph_hashes": ["459ccec100466d47cba8ce687f01fdf3d7e5a44dfdbe8a497342fc5d8952ac52"]}]')

WITNESS_META = {
    "acharya-upanyasangal-part1-1957-58-scan": {
        "url": "https://mahaperiyavaa.blog/wp-content/uploads/2023/04/Acharyaswamigal-Upanyasangal-Part-1.pdf",
        "snapshot_sha256": "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e",
        "rights_status": "restricted_private_research",
        "lineage_note": (
            "1958 publication produced from Ananthan shorthand notes, typed copies, "
            "and editorial arrangement. Earlier witness support is claim-level; "
            "printed wording is not treated as verbatim primary speech."
        ),
    },
    "acharya-upanyasangal-part2-1957-58-scan": {
        "url": "https://mahaperiyavaa.blog/wp-content/uploads/2023/04/Acharyaswamigal-Upanyasangal-Part-2.pdf",
        "snapshot_sha256": "eaf06d8936fb3b160a279b388ec0e2ef408be49c416618bf8bfb9d038f4a31e1",
        "rights_status": "restricted_private_research",
        "lineage_note": (
            "Earlier publication-family witness to 1957-59 discourse material. "
            "Claim-level doctrinal agreement does not establish textual dependence "
            "or verbatim primary wording."
        ),
    },
}

EXPECTED_EARLIER_SUPPORTED = {
    "mahaperiyava.deivathin_kural.v1.advaitam.nonduality_of_brahman",
    "mahaperiyava.deivathin_kural.v1.sakala_mathangalukkum_pothuvana_bhakti.bhakti_common_across_hindu_siddhantas",
    "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.temple_as_communal_gratitude_and_offering",
    "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.regular_attendance_sustains_temple_worship",
    "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.temple_cleanliness_and_inner_purity",
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.karma_and_phaladata",
}

MANAGED_PATHS = [
    TEACHING_RECORDS,
    CURATION_INDEX,
    RESEARCH_MD,
    TEST,
    CATALOG,
    QUEUE,
    CATALOG_TEST,
    REPO_SCRIPT,
]


def die(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sh(cmd: list[str], *, capture: bool = False, check: bool = True):
    print("+", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=check,
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    if not path.exists():
        die(f"Missing expected file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        die(f"Missing expected file: {path.relative_to(ROOT)}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_repo_state() -> None:
    if not (ROOT / ".git").exists():
        die("Run this script from the pramana repo root.")

    branch = sh(["git", "branch", "--show-current"], capture=True).stdout.strip()
    if branch != EXPECTED_BRANCH:
        die(f"Expected branch {EXPECTED_BRANCH!r}, currently on {branch!r}.")

    dirty = sh(["git", "status", "--porcelain"], capture=True).stdout.strip()
    if dirty:
        die(
            "Working tree must be clean before curation. "
            "Do not discard anything; inspect first.\n" + dirty
        )

    for path in (PRIVATE_PACKET, SCHEMA, CATALOG, QUEUE, HISTORICAL_REVIEW):
        if not path.exists():
            die(f"Missing required input: {path.relative_to(ROOT)}")


def validate_private_packet(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("packet_version") != "0.3":
        die(
            "Expected private review packet v0.3, found "
            f"{packet.get('packet_version')!r}"
        )
    if packet.get("chapter_count") != 10:
        die("Expected exactly 10 pilot chapters in private packet.")
    if packet.get("rights", {}).get("public_export_allowed") is not False:
        die("Private packet rights gate is not fail-closed.")

    by_slug = {c["slug"]: c for c in packet["chapters"]}
    if len(by_slug) != 10:
        die("Private packet chapter slugs are not unique.")

    bhakti = by_slug.get("bhakti_seyvathu_etharkaga")
    if not bhakti:
        die("Bhakti pilot chapter missing from private packet.")
    semantic = bhakti.get("semantic_completeness_validation", {})
    if (
        semantic.get("complete") is not True
        or semantic.get("anchor_count") != semantic.get("anchor_total")
    ):
        die("Bhakti semantic completeness validation is not GREEN.")

    for unit in CURATED_UNITS:
        chapter = by_slug.get(unit["chapter_slug"])
        if not chapter:
            die(f"Missing private chapter for {unit['id']}")
        para_by_id = {p["id"]: p for p in chapter["paragraphs"]}

        if len(unit["source_paragraph_ids"]) != len(unit["source_paragraph_hashes"]):
            die(f"Paragraph id/hash count mismatch in {unit['id']}")

        for pid, expected_sha in zip(
            unit["source_paragraph_ids"],
            unit["source_paragraph_hashes"],
        ):
            para = para_by_id.get(pid)
            if not para:
                die(f"Missing {unit['chapter_slug']}:{pid} for {unit['id']}")
            if para["sha256"] != expected_sha:
                die(
                    f"Paragraph hash drift for {unit['id']} {pid}: "
                    f"expected {expected_sha}, found {para['sha256']}"
                )

    packet_sha = hashlib.sha256(PRIVATE_PACKET.read_bytes()).hexdigest()
    return {
        "packet_sha256": packet_sha,
        "packet_generated_at": packet.get("generated_at"),
        "chapter_count": packet["chapter_count"],
        "paragraph_count": packet["paragraph_count"],
        "by_slug": by_slug,
    }


def validate_historical_promotions() -> None:
    historical = load_json(HISTORICAL_REVIEW)
    reviews = {r["slug"]: r for r in historical["reviews"]}

    supported = {
        u["id"]
        for u in CURATED_UNITS
        if u["proposed_authority"] == "earlier_witness_supported"
    }
    if supported != EXPECTED_EARLIER_SUPPORTED:
        die(
            "Earlier-witness authority set drifted.\n"
            f"expected={sorted(EXPECTED_EARLIER_SUPPORTED)}\n"
            f"actual={sorted(supported)}"
        )

    for u in CURATED_UNITS:
        authority = u["proposed_authority"]
        witness = u.get("historical_witness")

        if authority == "earlier_witness_supported":
            if not witness:
                die(f"Supported unit has no witness: {u['id']}")
            source_key = witness["source_key"]
            if source_key not in WITNESS_META:
                die(f"Unknown witness source for {u['id']}: {source_key}")

            chapter_review = reviews.get(u["chapter_slug"])
            if not chapter_review:
                die(f"No historical review row for {u['chapter_slug']}")
            if chapter_review.get("witness_source_key") != source_key:
                die(
                    f"Historical review/source mismatch for {u['id']}: "
                    f"{chapter_review.get('witness_source_key')} != {source_key}"
                )

            recommendation = chapter_review.get("authority_recommendation", "")
            if not (
                recommendation.startswith("eligible_for_narrow_claim_level_")
                or recommendation.startswith("strong_candidate_for_claim_level_")
            ):
                die(
                    "Historical review does not permit claim-level promotion "
                    f"for {u['id']}: {recommendation}"
                )
        elif authority != "dk_attested":
            die(
                f"Unexpected authority {authority!r} for {u['id']}. "
                "Pilot permits only dk_attested or earlier_witness_supported."
            )


def make_teaching_records(
    packet_meta: dict[str, Any],
    catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    catalog_by_url = {c["url"]: c for c in catalog["chapters"]}
    packet_by_slug = packet_meta["by_slug"]

    records = []
    for u in CURATED_UNITS:
        chapter = packet_by_slug[u["chapter_slug"]]
        cat = catalog_by_url.get(chapter["url"])
        if not cat:
            die(f"Catalog row not found for {u['id']}")

        earlier = u["proposed_authority"] == "earlier_witness_supported"
        paragraph_ref = ",".join(u["source_paragraph_ids"])
        paragraph_hashes = ",".join(u["source_paragraph_hashes"])

        record = {
            "id": u["id"],
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati",
            "compiler": "ra_ganapathi",
            "language": "tamil",
            "source_locus": {
                "volume": 1,
                "section_title_ta": None,
                "chapter_title_ta": chapter["title_ta"],
                "chapter_ordinal": chapter["catalog_ordinal"],
                "print_edition": None,
                "print_page_start": None,
                "print_page_end": None,
                "digital_url": chapter["url"],
                "digital_anchor": None,
            },
            "claim_summary": u["claim_summary"],
            "topics": u["topics"],
            "attribution": {
                "dk_attestation": "located",
                "wording_status": (
                    "earlier_witness_agrees"
                    if earlier
                    else "dk_wording_only"
                ),
                "compiler_intervention_status": "unknown",
                "note": (
                    "Curator-authored summary, not a quotation. "
                    + (
                        "A pre-DK historical witness supports this narrow claim; "
                        "no verbatim identity or textual dependence is asserted."
                        if earlier
                        else
                        "Official digital Deivathin Kural attests this teaching; "
                        "exact primary wording is not established."
                    )
                ),
            },
            "evidence_status": {
                "digital_attestation": "confirmed",
                "print_check": "not_checked",
                "primary_source_status": "unknown",
                "authority": u["proposed_authority"],
            },
            "provenance": [
                {
                    "source_key": chapter["source_key"],
                    "witness_role": "official_digital",
                    "url": chapter["url"],
                    "locus": (
                        "private review packet v0.3 paragraph(s) "
                        + paragraph_ref
                    ),
                    "snapshot_sha256": chapter["snapshot_sha256"],
                    "lineage_note": (
                        "Official Kanchi digital Deivathin Kural is a "
                        "descendant of the Ra. Ganapathi compilation and is "
                        "not treated as an independent primary witness."
                    ),
                    "rights_status": "restricted_private_research",
                }
            ],
            "rights": {
                "source_text_tier": "restricted",
                "public_export": "metadata_only",
                "terms_url": None,
                "note": (
                    "Exact source wording remains only in private/gitignored "
                    "source snapshots and review packets."
                ),
            },
            "flags": list(u.get("flags", [])),
            "curator_notes": (
                "Private review packet v0.3 refs="
                + paragraph_ref
                + "; paragraph_sha256="
                + paragraph_hashes
                + "; source_packet_sha256="
                + packet_meta["packet_sha256"]
                + ". Summary is metadata, not a quotation."
            ),
        }

        if earlier:
            witness = u["historical_witness"]
            wm = WITNESS_META[witness["source_key"]]
            record["provenance"].append(
                {
                    "source_key": witness["source_key"],
                    "witness_role": "earlier_secondary",
                    "url": wm["url"],
                    "locus": witness["locus"],
                    "snapshot_sha256": wm["snapshot_sha256"],
                    "lineage_note": wm["lineage_note"],
                    "rights_status": wm["rights_status"],
                }
            )

        records.append(record)

    return records


def schema_shape_validate(records: list[dict[str, Any]]) -> None:
    schema = load_json(SCHEMA)
    top_allowed = set(schema["properties"])
    top_required = set(schema["required"])
    id_re = re.compile(schema["properties"]["id"]["pattern"])

    for rec in records:
        missing = top_required - set(rec)
        extra = set(rec) - top_allowed
        if missing:
            die(
                f"Schema required fields missing in {rec.get('id')}: "
                f"{sorted(missing)}"
            )
        if extra:
            die(f"Schema extra fields in {rec.get('id')}: {sorted(extra)}")
        if not id_re.match(rec["id"]):
            die(f"Teaching record id fails schema pattern: {rec['id']}")

        for field in ("source_locus", "attribution", "evidence_status", "rights"):
            spec = schema["properties"][field]
            obj = rec[field]
            required = set(spec.get("required", []))
            allowed = set(spec.get("properties", {}))
            if required - set(obj):
                die(
                    f"{rec['id']}.{field} missing "
                    f"{sorted(required - set(obj))}"
                )
            if spec.get("additionalProperties") is False and set(obj) - allowed:
                die(
                    f"{rec['id']}.{field} extra "
                    f"{sorted(set(obj) - allowed)}"
                )

        authority_allowed = set(
            schema["properties"]["evidence_status"]["properties"]
            ["authority"]["enum"]
        )
        if rec["evidence_status"]["authority"] not in authority_allowed:
            die(f"Invalid authority in {rec['id']}")

        wording_allowed = set(
            schema["properties"]["attribution"]["properties"]
            ["wording_status"]["enum"]
        )
        if rec["attribution"]["wording_status"] not in wording_allowed:
            die(f"Invalid wording_status in {rec['id']}")

        if rec["evidence_status"]["authority"] == "primary_source_verified":
            die("Pilot curation must not contain primary_source_verified.")

        if (
            rec["rights"]["source_text_tier"] == "restricted"
            and rec["rights"]["public_export"] not in {"metadata_only", "none"}
        ):
            die(f"Restricted rights gate violated in {rec['id']}")


def make_curation_index(
    packet_meta: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    authority_counts = Counter(
        r["evidence_status"]["authority"] for r in records
    )
    chapter_counts = Counter(u["chapter_slug"] for u in CURATED_UNITS)

    units = []
    for u in CURATED_UNITS:
        units.append(
            {
                "id": u["id"],
                "chapter_slug": u["chapter_slug"],
                "unit_slug": u["unit_slug"],
                "claim_summary": u["claim_summary"],
                "question_intents": u["question_intents"],
                "source_paragraph_ids": u["source_paragraph_ids"],
                "source_paragraph_hashes": u["source_paragraph_hashes"],
                "topics": u["topics"],
                "flags": u.get("flags", []),
                "authority": u["proposed_authority"],
                "historical_witness": u.get("historical_witness"),
            }
        )

    return {
        "version": "0.1",
        "corpus": "mahaperiyava_teachings",
        "work": "deivathin_kural",
        "volume": 1,
        "phase": "pilot_teaching_units_curated",
        "status": "CURATED_REVIEW_DATA_NOT_PUBLICATION_APPROVED",
        "generated_at": now_iso(),
        "source_packet": {
            "packet_version": "0.3",
            "private_path": (
                "data/private/"
                "mahaperiyava_dk_v1_pilot_review_packet_v3.json"
            ),
            "sha256": packet_meta["packet_sha256"],
            "generated_at": packet_meta["packet_generated_at"],
            "chapter_count": packet_meta["chapter_count"],
            "paragraph_count": packet_meta["paragraph_count"],
            "contains_restricted_source_text": True,
            "tracked": False,
        },
        "policy": {
            "no_exact_source_text_in_tracked_artifacts": True,
            "claim_summaries_are_not_quotes": True,
            "historical_witness_support_is_claim_level": True,
            "collection_lineage_does_not_auto_promote_claims": True,
            "no_print_check_claimed": True,
            "no_primary_source_verified_claimed": True,
            "human_publication_review_still_required": True,
        },
        "unit_count": len(units),
        "authority_counts": dict(sorted(authority_counts.items())),
        "chapter_unit_counts": dict(sorted(chapter_counts.items())),
        "units": units,
    }


def update_queue_and_catalog(catalog: dict[str, Any]) -> None:
    unit_counts = Counter(u["chapter_slug"] for u in CURATED_UNITS)
    packet = load_json(PRIVATE_PACKET)
    pilot_urls = {c["slug"]: c["url"] for c in packet["chapters"]}
    url_to_slug = {url: slug for slug, url in pilot_urls.items()}

    queue_rows = load_jsonl(QUEUE)
    seen_pilot = set()
    for row in queue_rows:
        slug = url_to_slug.get(row["url"])
        if slug:
            row["stage"] = "pilot_teaching_units_curated"
            row["teaching_units_created"] = unit_counts[slug]
            row["review_notes"] = (
                "Curated metadata-only teaching units; exact DK text remains "
                "private. Publication approval and print checks remain pending."
            )
            seen_pilot.add(slug)
        else:
            if row["stage"] != "needs_teaching_unit_review":
                die(
                    f"Unexpected non-pilot queue stage for "
                    f"{row['source_key']}: {row['stage']}"
                )
            if row["teaching_units_created"] != 0:
                die(
                    f"Unexpected non-pilot teaching unit count for "
                    f"{row['source_key']}"
                )

    if seen_pilot != set(unit_counts):
        die(
            "Pilot queue rows missing: "
            + ", ".join(sorted(set(unit_counts) - seen_pilot))
        )
    write_jsonl(QUEUE, queue_rows)

    catalog_seen = set()
    for chapter in catalog["chapters"]:
        slug = url_to_slug.get(chapter["url"])
        if slug:
            chapter["review_status"] = "pilot_teaching_units_curated"
            chapter["teaching_unit_count"] = unit_counts[slug]
            catalog_seen.add(slug)

    if catalog_seen != set(unit_counts):
        die(
            "Pilot catalog rows missing: "
            + ", ".join(sorted(set(unit_counts) - catalog_seen))
        )
    write_json(CATALOG, catalog)


def patch_catalog_test() -> None:
    text = CATALOG_TEST.read_text(encoding="utf-8")
    old = '''    assert all(q["stage"] == "needs_teaching_unit_review" for q in queue)
    assert all(q["teaching_units_created"] == 0 for q in queue)
'''
    new = '''    pilot_rows = [q for q in queue if q["pilot"]]
    nonpilot_rows = [q for q in queue if not q["pilot"]]

    assert len(pilot_rows) == 10
    assert all(
        q["stage"] == "pilot_teaching_units_curated"
        for q in pilot_rows
    )
    assert all(q["teaching_units_created"] > 0 for q in pilot_rows)

    assert all(
        q["stage"] == "needs_teaching_unit_review"
        for q in nonpilot_rows
    )
    assert all(q["teaching_units_created"] == 0 for q in nonpilot_rows)
'''
    if old not in text:
        if new in text:
            print("Catalog queue regression test already patched.")
            return
        die(
            "Could not find expected queue assertions in "
            "tests/test_mahaperiyava_dk_v1_catalog.py"
        )
    CATALOG_TEST.write_text(text.replace(old, new), encoding="utf-8")


def write_tests() -> None:
    TEST.parent.mkdir(parents=True, exist_ok=True)
    TEST.write_text(
        r'''from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_pilot_curation_index.json"
SCHEMA = ROOT / "schema/teaching_record.schema.json"


def _jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_pilot_has_56_unique_teaching_units_across_10_chapters():
    records = _jsonl(RECORDS)
    index = _load(INDEX)

    assert len(records) == 56
    assert index["unit_count"] == 56
    assert len({r["id"] for r in records}) == 56
    assert len(index["chapter_unit_counts"]) == 10

    counts = Counter(
        r["source_locus"]["chapter_title_ta"]
        for r in records
    )
    assert len(counts) == 10


def test_authority_is_fail_closed_and_claim_level():
    records = _jsonl(RECORDS)
    counts = Counter(r["evidence_status"]["authority"] for r in records)

    assert counts == {
        "dk_attested": 50,
        "earlier_witness_supported": 6,
    }
    assert all(
        r["evidence_status"]["print_check"] == "not_checked"
        for r in records
    )
    assert all(
        r["evidence_status"]["primary_source_status"] == "unknown"
        for r in records
    )
    assert not any(
        r["evidence_status"]["authority"] == "primary_source_verified"
        for r in records
    )


def test_earlier_supported_records_have_two_provenance_witnesses():
    records = _jsonl(RECORDS)

    supported = [
        r for r in records
        if r["evidence_status"]["authority"] == "earlier_witness_supported"
    ]
    assert len(supported) == 6

    for r in supported:
        roles = {p["witness_role"] for p in r["provenance"]}
        assert roles == {"official_digital", "earlier_secondary"}
        assert r["attribution"]["wording_status"] == "earlier_witness_agrees"
        assert "verbatim" in r["attribution"]["note"].lower()


def test_dk_only_records_do_not_gain_independent_witnesses():
    records = _jsonl(RECORDS)

    dk_only = [
        r for r in records
        if r["evidence_status"]["authority"] == "dk_attested"
    ]
    assert len(dk_only) == 50

    for r in dk_only:
        assert [p["witness_role"] for p in r["provenance"]] == [
            "official_digital"
        ]
        assert r["attribution"]["wording_status"] == "dk_wording_only"


def test_teaching_records_match_schema_shape_without_new_dependency():
    schema = _load(SCHEMA)
    records = _jsonl(RECORDS)

    top_allowed = set(schema["properties"])
    top_required = set(schema["required"])
    id_re = re.compile(schema["properties"]["id"]["pattern"])

    for r in records:
        assert not (top_required - set(r))
        assert not (set(r) - top_allowed)
        assert id_re.match(r["id"])

        for field in (
            "source_locus",
            "attribution",
            "evidence_status",
            "rights",
        ):
            spec = schema["properties"][field]
            obj = r[field]
            assert not (set(spec.get("required", [])) - set(obj))
            if spec.get("additionalProperties") is False:
                assert not (set(obj) - set(spec["properties"]))

        assert r["evidence_status"]["authority"] in (
            schema["properties"]["evidence_status"]["properties"]
            ["authority"]["enum"]
        )
        assert r["attribution"]["wording_status"] in (
            schema["properties"]["attribution"]["properties"]
            ["wording_status"]["enum"]
        )

        if r["rights"]["source_text_tier"] == "restricted":
            assert r["rights"]["public_export"] in {"metadata_only", "none"}


def test_no_restricted_dk_source_text_is_tracked_in_records_or_index():
    records = _jsonl(RECORDS)
    index = _load(INDEX)

    for r in records:
        assert "exact_text_restricted" not in r
        assert "text" not in r
        assert r["rights"]["source_text_tier"] == "restricted"
        assert r["rights"]["public_export"] == "metadata_only"

    assert index["policy"]["no_exact_source_text_in_tracked_artifacts"] is True
    assert index["source_packet"]["tracked"] is False


def test_curation_index_maps_every_record_to_hashed_private_paragraphs():
    records = _jsonl(RECORDS)
    index = _load(INDEX)

    by_record = {r["id"]: r for r in records}
    by_unit = {u["id"]: u for u in index["units"]}

    assert set(by_record) == set(by_unit)

    for unit_id, unit in by_unit.items():
        assert unit["source_paragraph_ids"]
        assert len(unit["source_paragraph_ids"]) == len(
            unit["source_paragraph_hashes"]
        )
        assert all(
            re.fullmatch(r"[0-9a-f]{64}", h)
            for h in unit["source_paragraph_hashes"]
        )
        assert unit["authority"] == (
            by_record[unit_id]["evidence_status"]["authority"]
        )
        assert unit["question_intents"]


def test_context_sensitive_historical_claims_stay_at_dk_attested():
    records = _jsonl(RECORDS)
    risky_flags = {
        "historical_claim_requires_external_verification",
        "quantitative_historical_claim_requires_verification",
        "context_sensitive_identity_claim",
        "historical_generalization",
        "cultural_generalization",
    }

    for r in records:
        if risky_flags.intersection(r.get("flags", [])):
            assert r["evidence_status"]["authority"] == "dk_attested"
''',
        encoding="utf-8",
    )


def write_research_md(
    packet_meta: dict[str, Any],
    records: list[dict[str, Any]],
) -> None:
    counts = Counter(u["chapter_slug"] for u in CURATED_UNITS)
    authority = Counter(r["evidence_status"]["authority"] for r in records)

    supported = [
        u for u in CURATED_UNITS
        if u["proposed_authority"] == "earlier_witness_supported"
    ]

    lines = [
        "# Mahaperiyava — Deivathin Kural Volume 1 Pilot Teaching Units",
        "",
        "## Result",
        "",
        "- Pilot chapters curated: **10**",
        f"- Teaching units: **{len(records)}**",
        f"- `dk_attested`: **{authority['dk_attested']}**",
        f"- `earlier_witness_supported`: **{authority['earlier_witness_supported']}**",
        "- `dk_print_checked`: **0**",
        "- `primary_source_verified`: **0**",
        f"- Private review-packet paragraphs: **{packet_meta['paragraph_count']}**",
        "",
        "This slice is designed for eventual **Ask Mahaperiyava** retrieval. "
        "Each unit is an answerable teaching claim with a source locus, "
        "evidence state and provenance. Exact Deivathin Kural wording remains "
        "private and is not committed.",
        "",
        "## Evidence discipline",
        "",
        "- Official Kanchi DK proves DK attestation, not verbatim primary speech.",
        "- A historical witness can upgrade only the narrow claim it actually supports.",
        "- Collection-level shorthand provenance does not propagate to every claim.",
        "- No print check is claimed in this milestone.",
        "- No primary-source verification is claimed in this milestone.",
        "- Historical/social assertions remain attributed teachings unless independently verified.",
        "",
        "## Units per pilot chapter",
        "",
    ]

    for slug, count in sorted(counts.items()):
        lines.append(f"- `{slug}`: {count}")

    lines += [
        "",
        "## Narrow claims with earlier-witness support",
        "",
    ]
    for u in supported:
        witness = u["historical_witness"]
        lines.append(
            f"- `{u['id']}` — {witness['source_key']}, {witness['locus']}"
        )

    lines += [
        "",
        "These promotions mean **earlier witness supported**, not "
        "**primary source verified** and not **verbatim wording verified**.",
        "",
        "## Private review packet",
        "",
        "- Version: `0.3`",
        "- Path (gitignored): "
        "`data/private/mahaperiyava_dk_v1_pilot_review_packet_v3.json`",
        f"- SHA-256: `{packet_meta['packet_sha256']}`",
        "",
        "The tracked curation index retains paragraph IDs and paragraph hashes "
        "so the metadata can be audited against the private packet without "
        "publishing copyrighted source text.",
        "",
        "## Next step",
        "",
        "Use this 56-unit slice as the calibration set before scaling curation "
        "through the remaining Volume 1 queue. The next corpus milestone should "
        "focus on repeatable teaching-unit extraction and spot-review, while "
        "keeping authority promotion separate from semantic extraction.",
        "",
    ]

    RESEARCH_MD.parent.mkdir(parents=True, exist_ok=True)
    RESEARCH_MD.write_text("\n".join(lines), encoding="utf-8")


def install_repo_script() -> None:
    REPO_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    if src != REPO_SCRIPT.resolve():
        shutil.copyfile(src, REPO_SCRIPT)
        REPO_SCRIPT.chmod(0o755)


def run_checks() -> None:
    print("\n=== Repo checks ===")
    sh(["git", "diff", "--check"])
    sh([sys.executable, "-m", "pytest", "-q"])
    sh([sys.executable, "scripts/audit_snapshots.py"])
    sh(["git", "diff", "--stat"])
    sh(["git", "status", "--short"])


def commit_changes() -> None:
    paths = [
        str(p.relative_to(ROOT))
        for p in MANAGED_PATHS
        if p.exists()
    ]
    sh(["git", "add", "--", *paths])

    unstaged = sh(["git", "diff", "--name-only"], capture=True).stdout.strip()
    if unstaged:
        die(
            "Unexpected unstaged changes remain; nothing committed.\n"
            + unstaged
        )

    staged = sh(
        ["git", "diff", "--cached", "--name-only"],
        capture=True,
    ).stdout.strip()
    if not staged:
        die("Nothing staged to commit.")

    print("\nStaged files:")
    print(staged)

    sh(
        [
            "git",
            "commit",
            "-m",
            "Curate Mahaperiyava DK V1 pilot teaching units",
        ]
    )


def push_branch() -> None:
    sh(["git", "push", "origin", EXPECTED_BRANCH])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()

    if args.push and not args.commit:
        die("--push requires --commit")

    ensure_repo_state()

    packet = load_json(PRIVATE_PACKET)
    packet_meta = validate_private_packet(packet)
    validate_historical_promotions()

    catalog = load_json(CATALOG)
    records = make_teaching_records(packet_meta, catalog)

    if len(records) != 56:
        die(f"Expected 56 records, built {len(records)}")
    if len({r["id"] for r in records}) != 56:
        die("Teaching record IDs are not unique.")

    schema_shape_validate(records)

    authority_counts = Counter(
        r["evidence_status"]["authority"] for r in records
    )
    if authority_counts != Counter(
        {
            "dk_attested": 50,
            "earlier_witness_supported": 6,
        }
    ):
        die(f"Unexpected authority counts: {authority_counts}")

    write_jsonl(TEACHING_RECORDS, records)
    write_json(CURATION_INDEX, make_curation_index(packet_meta, records))

    update_queue_and_catalog(catalog)
    patch_catalog_test()
    write_tests()
    write_research_md(packet_meta, records)
    install_repo_script()

    print("\n=== Curated pilot summary ===")
    print("Teaching units: 56")
    print("  dk_attested: 50")
    print("  earlier_witness_supported: 6")
    print("  dk_print_checked: 0")
    print("  primary_source_verified: 0")
    print("Tracked exact DK source text: NONE")

    run_checks()

    if args.commit:
        commit_changes()
    else:
        print("\nChanges validated but not committed.")

    if args.push:
        push_branch()

    print("\n=== Final ===")
    sh(["git", "status", "--short"])
    sh(["git", "log", "-5", "--oneline"])
    print(
        "\nPilot curation complete. "
        "The 56-unit evidence slice is ready for the next corpus phase."
    )


if __name__ == "__main__":
    main()
