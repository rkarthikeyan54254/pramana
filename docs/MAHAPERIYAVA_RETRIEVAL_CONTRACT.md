# Mahaperiyava V1-V7 retrieval contract

This layer retrieves **public-safe curator metadata** from the completed Deivathin Kural V1-V7 semantic frontier. It does not expose restricted source text and it does not change evidence authority.

## Product contract

- Never speak as Mahaperiyava.
- A retrieved curator summary is not a quotation.
- Every substantive synthesized idea must cite one or more returned `support_id` values.
- Retrieval score is relevance only. It never promotes `dk_attested` to a stronger evidence class.
- If no meaningful record matches, abstain rather than answer from model memory.
- Personal-guidance output must answer the human problem first, then distinguish the attested teaching from any app-generated modern application.
- Broad questions must synthesize themes, not invent a single sweeping prescription.
- Sensitive/historical/hagiographic/scientific/political-social flags remain available to the answer layer for context.
- Exact Deivathin Kural text remains restricted and is never reconstructed from model memory.
- Generated prose is ephemeral product output and must never be fed back into the corpus as evidence.

## Scope

The foundation indexes 3,368 teaching records:

- V1: 927
- V2: 673
- V3: 370
- V4: 457
- V5: 345
- V6: 254
- V7: 342

The deterministic retriever is the CI-safe baseline. Semantic embeddings and LLM synthesis are separate product layers and must preserve the same evidence boundary.
