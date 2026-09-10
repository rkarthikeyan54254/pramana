# Moat & Goal — Non-Negotiable Reminder

## The Moat
**Verified, citation-linked, structured ground truth.**
- Fluency is commoditized; verified ground truth with citations is not.
- Every record: exact source bytes, stable ID, provenance, verification witness.
- Variants tracked, never silently picked. Traditions/recensions kept distinct.
- Refusal boundary: "not in verified corpus" ≠ "model doesn't know."

## The Goal
Build a **durable dataset asset** that outlives any model.
- Corpus first, model second (fungible).
- RAG over verified-only rows. Optional LoRA later.
- Publish milestones: dataset → adapter → demo. Not model outputs.

## Rules We Never Break
1. **No fabrication** — flag `needs_source`, never invent verses/numbers/attributions.
2. **No silent harmonization** — disagreements become `variants[]` or `flags[]`, not resolutions.
3. **No downstream contamination** — vamsha/sandhyakatha/templecircuit are outputs, never sources.
4. **No verification theater** — `verified:true` requires independent 2nd source + exact normalized match.
5. **No authority leakage** — unverified rows never enter retrieval, graph, or benchmark authority.
6. **No push without gates** — all 6 moat checks must pass; `make moat-proof-gate` green is minimum.

## Before Any Push/Commit/Action
Ask:
- Does this add/improve source-backed evidence?
- Can every promoted record trace to exact source + stable ID?
- Is independent verification explicit, disagreements preserved?
- Is the result queryable structured data, not narrative?
- Can the product refuse "not verified"?
- Are generated explanations kept out of authoritative corpus?

**If any answer is NO → stop. Redesign. Do not push.**

---

*The moment you feel tempted to "let the model fill it in" — stop, flag it, source it. The corpus is the asset. The model is fungible.*