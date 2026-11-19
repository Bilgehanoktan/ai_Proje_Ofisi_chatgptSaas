# MI-03-GATE01-AUTHORITY-API-REVIEW-01

Static readback on 2026-11-19. Existing owner task MI03-GATE-01, not a new engine, task assignment or approval. Common product candidate remains bf87d5c48c7fee97fe12d0a28df3be80249f7306. See [catalog and evidence](CATALOG_AND_EVIDENCE.json).

## What / why / where
G2 and G7 have identical authority and IAM blobs. Common authority lacks IAM bootstrap/session-check; the legacy wrapper in G2/G6A/R8 calls claim_and_fence without session_check. This is intentional fail-closed for IAM stores, not a working protected transaction. G6A explicit entry is NoReturn and rejects before any claim; R8 optional protected_org is not equivalent to an explicit route. Do not alter historical legacy semantics or turn diagnostic IAM/ORG observations into a grant.

## Tests / diagnosis / maintenance
G2 log 33 PASS historical; original 50 remains NOT_RUN as a complete run. Four existing historical test files match the common tree, while G1/G2 IAM tests are absent. G3 exact recovery and original G2 runner remain authoritative; no copy, lock regeneration, or rerun was performed here. G6A local preclaim 6 historical, fullchain 2 NOT_RUN. On a future reviewed exact checkout, run the existing pinned owner runners; inspect missing blob/dependency and preserve raw evidence on failure. No retry on consumed claim or UNKNOWN. No Windows action requested now.

## Next / rollback
Gate01 source-owner concurrence and Gate02 owner-issued assignment/role provenance in parallel. Retain G6A explicit entry recommendation (not ratification), then existing G9, publication, strict COMMIT and W8 gates. No product, API, DB, event, dependency or permission change. Revert governance-only commit if needed; no product branch or data rollback. D5-G 42.5% -> 42.5%, Core 12/16, MVP 0/11 unchanged.
