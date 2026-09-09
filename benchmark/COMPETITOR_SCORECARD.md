# Competitor scorecard protocol

This is a **behavioral benchmark**, not a feature checklist.

## Rules

1. Run the exact prompts in `cases.json` without rewriting them to help the competitor.
2. Capture the full answer, citations/links, and product/date.
3. Score only observable behavior. Marketing claims do not earn points.
4. If sign-in, paywall, unsupported corpus, or UI prevents testing, leave the score `null`.
5. Score 0/1/2 using `RUBRIC.md`.
6. Do not score prose quality, friendliness, number of scriptures, languages, audio, comics, or app polish as moat dimensions.
7. A citation to a verse is **not automatically provenance depth=2**. Full credit requires an auditable route to the source/edition and, where the benchmark asks it, verification/variant status.

## Current public capability reconnaissance

See `competitor_public_capabilities.json`. It records only what is publicly observable as of 2026-09-09 and deliberately does not assign benchmark points.

## Completion criterion

A competitor is considered genuinely moat-competitive if it repeatedly scores near Pramāṇa on:

- authenticity precision,
- refusal discipline,
- provenance depth,
- source separation,
- variant/gap awareness,
- graph auditability,
- overclaim resistance.

If mainstream systems do this consistently, invoke the kill/pivot rule in `RUBRIC.md`.
