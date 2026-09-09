# Pramāṇa Local Platform

This layer is intentionally laptop-first. It does **not** make the local store authoritative; authority remains the verified JSONL corpus.

## Build indexed store
```bash
make sqlite-store
```
Creates `dist/pramana.sqlite` with verified records, evidence nodes/edges, and evidence joins.

## Run the local API
```bash
python product/http_server.py
```
Endpoints:
- `GET /v1/health`
- `POST /v1/verify` with `{ "claim": "..." }`
- `POST /v1/compare` with `{}`
- `POST /v1/trace` with `{ "node": "person:prahlada", "depth": 2 }`

## Quality dashboard
```bash
make quality-dashboard
open dist/dashboard/index.html
```

## Competitor scorecards
```bash
python benchmark/new_scorecard.py Vedapath
python benchmark/capture_answer.py benchmark/results/vedapath.json verify.unsupported.popular_quote --answer-file answer.txt
python benchmark/validate_external_scorecard.py benchmark/results/vedapath.json
python benchmark/score_external.py benchmark/results/vedapath.json
```

## Moat boundary
SQLite, HTTP, embeddings, and UI are delivery/index layers only. They may never promote an unverified row or generated edge into authority.
