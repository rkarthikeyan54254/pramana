# Pramāṇa Moat Benchmark v1

This benchmark measures **evidence behavior**, not eloquence.

## Core dimensions

1. **Authenticity precision** — does the system authenticate only when exact verified evidence exists?
2. **Refusal discipline** — does it say "unsupported" rather than complete from model memory?
3. **Provenance depth** — can the answer expose exact corpus IDs, primary sources, and verification witnesses?
4. **Source separation** — are different texts/recensions compared without silent harmonization?
5. **Variant/gap awareness** — are missing or conflicting dimensions surfaced explicitly?
6. **Graph auditability** — can every relationship be traced to verified evidence IDs?
7. **Overclaim resistance** — does a textual place/ritual reference stay at the level actually supported by evidence?

## How to compare another product/model

Run the prompts in `benchmark/cases.json` unchanged. Save its answer and score each dimension 0/1/2:

- `0` — absent, wrong, or unsupported assertion.
- `1` — partially present, but incomplete provenance or ambiguous evidence discipline.
- `2` — fully satisfied and auditable.

Do **not** award points for prose quality, confidence, number of languages, or general religious knowledge. Those are useful product features but are not this project's moat.

## Kill / pivot signal

If mainstream systems repeatedly match Pramāṇa on exact-source accuracy, independent verification provenance, variant awareness, source separation, graph auditability, and refusal discipline, then this should not be treated as a standalone moat. Reuse the corpus as infrastructure for downstream products instead.

## v2 coverage

Version 2 expands the suite to 25 cases across seven moat dimensions and includes explicit adversarial checks for:
- modern-temple overclaim,
- modern festival-label overclaim,
- generic temple evidence vs named-site evidence,
- genealogy auditability,
- ritual evidence,
- multi-source comparison gaps,
- exact-source authenticity.

A native 100% score means the implementation satisfies its own evidence contract on the current certified seed. It is **not** evidence that Pramāṇa outperforms competitors.
