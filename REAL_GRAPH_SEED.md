# Real Evidence Graph Seed

This checkpoint replaces fixture-only graph testing with the first real certified evidence tranche.

## Certified evidence rows

Primary: GRETIL Mārkaṇḍeyapurāṇa 1–93 (CC BY-NC-SA 4.0)
Second witness: Ved Path Durga Saptashati chapter 2 (verification use; modern meanings/commentary are not imported)

Rows:
- `purana.devi_mahatmya.82.1` ↔ Ved Path 2.2
- `purana.devi_mahatmya.82.2` ↔ Ved Path 2.3
- `purana.devi_mahatmya.82.12` ↔ Ved Path 2.13
- `purana.devi_mahatmya.82.13` ↔ Ved Path 2.14

The +1 numbering offset occurs because the liturgical witness counts `ṛṣiruvāca` as 2.1 while GRETIL does not.

## Graph nodes
- Devī Māhātmya
- Mārkaṇḍeya Purāṇa
- Mahiṣāsura conflict
- Mahiṣāsura
- Devī
- combined divine tejas
- Śākta tradition

## Verified graph edges
1. Devī Māhātmya → contains evidence for → Mahiṣāsura conflict
2. Mahiṣāsura → central antagonist in → Mahiṣāsura conflict
3. combined divine tejas → manifests as → Devī
4. Devī Māhātmya → curated under tradition → Śākta

Edges 3–4 are explicitly curator-reviewed because they contain semantic/taxonomic interpretation. They are not promoted by model inference.

## Moat rule
The graph is an evidence-backed index. It does not create facts. Every edge must resolve to verified corpus IDs, and interpretive edges require explicit review.

## Expansion checkpoint — Narasiṃha cluster across three Purāṇic witnesses

The global evidence graph now includes certified rows from:
- Śrīmad Bhāgavata Purāṇa (Prahlāda–Narasiṃha seed)
- Viṣṇu Purāṇa (Prahlāda/Narasiṃha + genealogy seed)
- Narasiṃha Purāṇa chapter 44
- Devī Māhātmya chapter 82

The Narasiṃha Purāṇa tranche adds a scripture-backed place node for **Śrīśaila**, but the graph deliberately limits the claim to what the passage supports: Narasiṃha reaches/remains at Śrīśaila. It does not identify a specific modern temple without a separate historical/temple evidence layer.

Current global graph: **21 nodes / 30 edges**. All node and edge evidence IDs resolve to certified corpus rows, and all semantic `relation_ids` resolve to accepted reviewed relation artifacts.

## Expanded evidence branches
The current global graph now includes:
- deeper Daitya genealogy: Prahlāda → Virocana → Bali;
- a generic scriptural Hari/Keśava temple node backed by Vāmana Purāṇa 68.37, 68.46 and 68.59;
- lamp-offering and upavāsa ritual nodes;
- Devī Māhātmya tithi-recitation and annual autumn mahāpūjā evidence.

Current materialized graph: **30 nodes / 41 edges**. The modern-temple identity layer remains intentionally separate: a text saying `Keśava temple`, `Vāsudeva-ālaya`, or `Viṣṇu-gṛha` is not enough to identify a present-day temple without additional historical evidence.
