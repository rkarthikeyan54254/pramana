# Mahaperiyava grounded answer contract

Phase 9 converts the V1-V7 retrieval foundation into a product-safe answer backend.

The backend operates only on **public-safe curator metadata**. It does not send or expose restricted Deivathin Kural source text.

## Answer behavior

1. Never speak as Mahaperiyava.
2. Curator summaries are evidence metadata, not quotations.
3. Every answer claim carries one or more `support_ids`.
4. The evidence drawer carries source locus, authority, context flags, and earlier-witness metadata where available.
5. Retrieval relevance never changes evidence authority.
6. Unsupported questions abstain end-to-end: no answer, no claims, no evidence, and no provider-generation request.
7. Personal-guidance packets expose relevant attested teachings but leave present-day application to a separately labeled `app_generated` layer.
8. Historical, political-social, caste, gender, violence, scientific, medical, supernatural, and hagiographic flags remain visible to downstream synthesis.
9. Generated prose never becomes corpus evidence and never changes publication status.

## Optional model/provider handoff

`generation_request` contains only public-safe metadata summaries and support IDs. A provider may improve prose, but its result must pass `validate_generated_answer()` before display.

That validator is deliberately described as **structural grounding**, not semantic truth verification. It checks support-ID boundaries, attribution rules, quote prohibition, and application labeling. It does not promote generated prose into the corpus.

## API

`POST /v1/mahaperiyava/answer`

```json
{
  "query": "What does Mahaperiyava say about Kamakshi and compassion?",
  "top_k": 8
}
```

The response is an auditable answer packet suitable for the mobile/web UI evidence drawer.
