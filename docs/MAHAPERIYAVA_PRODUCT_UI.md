# Mahaperiyava product UI and voice-input contract

Phase 10 makes the Phase 9 grounded-answer backend usable from a phone-sized browser without weakening the evidence boundary.

The local service serves `/mahaperiyava` with Home, Ask, Explore, and Saved views. Answers keep evidence one tap away with support ID, volume/chapter, authority, and context indicators. Saved answers remain in browser `localStorage`.

Voice is input-only. When browser speech recognition is available, English (India) and Tamil dictation populate the editable question field and never auto-submit. There is deliberately no text-to-speech voice. A local Whisper backend can replace browser dictation later without changing the evidence contract.

No Mahaperiyava portrait is bundled until a real photograph has explicit provenance and reuse rights; no AI-generated likeness is substituted. The UI uses same-origin API calls and no external JavaScript, fonts, images, analytics, or CDNs. Restricted Deivathin Kural source text never enters the UI bundle.
