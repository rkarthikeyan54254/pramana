# Local Platform Checkpoint — 2026-09-09

This session intentionally focused on work that can be completed without external network access.

## Delivered
1. **Queryable evidence substrate** — `dist/pramana.sqlite` indexes only independently verified rows and evidence-backed graph nodes/edges.
2. **Pramāṇa service contract** — JSON operations for health, claim verification, source comparison and evidence tracing.
3. **Local HTTP surface** — dependency-light endpoints that can run directly on a MacBook Air.
4. **Quality dashboard** — corpus depth, verification status, graph coverage, license mix and moat-benchmark status.
5. **Competitor benchmark workflow** — reproducible provider scorecards with answer capture and validation.

## Current checkpoint numbers
- Verified materialized records: **24**
- Evidence graph: **30 nodes / 41 edges**
- Native moat benchmark: **25/25 cases; 82/82 checks**
- Already mapped Tamil target: **12,240 units** (4,000 Divya Prabandham + 8,240 Tevaram)
- Materialized vs mapped Tamil depth: **0.2%**

That last figure is intentional: it prevents infrastructure maturity from being confused with corpus maturity.

## Laptop commands
```bash
make local-platform-focused-gate
make sqlite-store
python product/http_server.py
make quality-dashboard
```
Then open `dist/dashboard/index.html`.

## Next major unblock
On a network-enabled laptop, run:
```bash
python scripts/network_materialize.py --group core-materialization --fetch --materialize
```
After real source materialization, the next priority is **verification throughput**, not additional platform infrastructure.

## Moat statement
**Retrieval/index/UI layers may broaden access; they never broaden authority.** Authority remains independently verified corpus evidence with provenance.
