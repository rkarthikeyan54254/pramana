# Verified-only answer policy

## Moat gate
The retrieval/answer layer exists to expose **verified, cited ground truth**. It must not become a second content-generation corpus.

1. Retrieval candidates MUST satisfy `verified:true` and a non-empty `verification_source`.
2. Every factual/scriptural claim in an answer MUST be supported by one or more returned evidence IDs.
3. Exact quotations MUST come from `text_original` in evidence; never reconstruct from model memory.
4. If no verified evidence matches, REFUSE rather than answer from pretrained knowledge.
5. Preserve `variants[]`; never collapse an attested variant into a single reading silently.
6. The model may summarize/explain retrieved evidence, but generated prose is ephemeral and MUST NOT be fed back into the corpus as source data.
7. Commentary/translation licensing remains independent from source-text verification.

## Semantic retrieval
8. Semantic/vector retrieval MAY improve recall, but the candidate set MUST be restricted to verified rows before embedding/ranking.
9. Similarity is not evidence of truth. Retrieval scores MUST NOT alter verification status.
10. Answer assembly MUST expose claim -> `support_ids` mapping so generated prose remains auditable.
