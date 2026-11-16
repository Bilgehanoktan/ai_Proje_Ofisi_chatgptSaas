# 0213 → 0214 — P0 work ordered by verified architectural gates

1. Restore exact authenticated repository checkout locally (not only 55-file slice) and validate 350 product manifest entries, dependency locks and original 154 regressions. Execute the six prepared `test_authority_wrapper_0213.py` tests using original 0209/0210 source; explicitly reproduce D-03/D-04, do not claim security completion.
2. Implement independent monotonic intent claim/head custody external to same restore boundary, with authenticated sequence, key lifecycle, clock, anti-rollback and mandatory authoritative effect fence; perform adversarial crash/recovery tests and independent verification before permission. No local SQLite-only replacement claim.
3. Extend 4/4 two-project shared-budget SQLite cases to actual PostgreSQL and concurrent sessions. Configure isolated PostgreSQL with psycopg and reviewed direct/transitive dependency locks, run prior 13 PG tests and non-owner RLS, cross-tenant read/write negative tests and race/lock-order tests. No PROD schema migration.
4. Full dependency-pinned backend/Next frontend build and browser for read-only CEO Dashboard / multi-floor Office verified historical projections. No fabricated active agents or live permission. Source branch W1 separate; review before any merge.
5. Continue per-domain 24-row ordinal tracking, preserve originals and record exact hashes, test evidence, repair/rollback and full ZIP. Update 16-gate integration status by actual tests only (0213: 6/16, 37.5%).

No CI, main merge, PROD, provider effect, customer data or paid calls without separate approval.
