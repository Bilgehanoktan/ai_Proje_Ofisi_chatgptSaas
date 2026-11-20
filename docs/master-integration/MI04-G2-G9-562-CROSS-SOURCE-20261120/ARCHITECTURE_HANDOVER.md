# MI04 — G2/G9 original owner source composition: 72/72 D0 PASS

Date: 2026-11-20. Actual GitHub CI: https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44700495037

## Why and overlap

W8 is active in independent MI01 PR20; Memory MI08 and PG/independent security MI02 are separate. No source, test or permission changes on those workstreams. The already-open MI04 PR19 was extended instead of creating a new prototype.

## Exact product scope

Canonical product-dev @254e0188998d0d245bd8ee4eb901aead02951a66 remains 553 product files / 552 manifest records. Isolated PR19 selected G2 plus G9/G7 original owner blobs produces 562 product files / 561 manifest records, test checkout @93e6c84db1a061ee914aa2c1d543620404515c0b. Exactly 9 owner product paths added, 1 D0 authority path replaced only on isolated review branch, 20 historical fixture paths and 1 G7 pin manifest added.

## Tests and exact limit

At CI #44700495037: 561/561 file SHA256+bytes, 8/8 selected G2 Git blobs, 56/56 original G9 Git blob pins. Existing G2 50 + ORG 15 ran in a single Python process; G9/G7 historical 7 ran in a separate process against the same immutable checkout. Total 72/72 PASS, no errors, failures or skips. G7 original fixture imports historical ORG-05R3 / ORG-06; NOT current canonical ORG authorization or an independent trust verification.

Previous CI run #44700458573 failed because of an incorrectly escaped NUL delimiter in a read-only Git blob test harness. Product code was unchanged. The harness was repaired and the separate new run #44700495037 passed. Preserve both raw GitHub logs.

## Architecture, tech catalog, safety

See TECHNICAL_CATALOG.json for file/classes/functions/DB/API/dep/event. No new HTTP API, production DB migrations, live grants, external effects, secrets, CI workflows in canonical, or lockfile changes. Original 0214 intentionally reproduces rollback replay when product DB, journal and local authority are all restored. True independent root/issuer/custody/sink, protected PostgreSQL and 8 negative IV cases remain HOLD.

## Maintenance, rollback, handover

Owner G2/Authority must decide current intent_authority.py variant; owner G9/ORG must ratify real current ORG contract and historical fixture differences. MI01 owns fresh W8; MI02 owns PG and independent security. Keep PR19 DRAFT, NO MERGE. If source pin changes: HOLD; no silent re-pin. Normal isolated revert or close PR19 if owner rejects. Do not force push, reset consumed claims, modify main or PROD.

## Progress

Previous exact common-candidate G2+ORG 65/65 PASS; current exact same isolated source root 65/65 + G9/G7 7/7 PASS. All are previously authored original tests; new integration evidence is co-location, not new unique methods or accepted product gates. Historical IAM/ORG 42.5% -> 42.5%; global 15/35/20/20/10 uncomputable without ratified denominators. Core 12/16, UI 21/40, MVP 0/11, IV 0/7, product acceptance delta 0.

Machine evidence: EVIDENCE.json and progress/MI04_G2_G9_562_SOURCE_COMPOSITION_20261120.json.
