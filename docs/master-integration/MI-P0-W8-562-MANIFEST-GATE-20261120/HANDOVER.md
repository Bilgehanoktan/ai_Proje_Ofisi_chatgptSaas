# MI-P0 W8 553–562 manifest compatibility — architecture, catalog and handover

2026-11-20. Review-only integration QA. Preserve Design Master, WORKING_STANDARD, REPORTING_STANDARD_20261118, CEO-0174/0179=B and independent safety HOLD.

## Observed original source difference

Canonical integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66: 553 product files / 552 manifest entries; manifest Git blob 27b4eb5816265d4e6e6d2458acb6220db7dd0c76.

PR19@0a8907f177bb3e9b458aefb3ea3441b15537f542: 562 files / 561 entries; manifest blob 566b7210b6edb95a21b999dc1d881a12284d9011. 9 added files, 0 deleted, 1 changed existing intent_authority.py. Full path/hash data: progress/reviews/MI_P0_W8_562_MANIFEST_GATE_20261120.json.

PR20@99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542: W8 adapter blob b4043035e75c5a18b7b19a9f18eecfef8e8fe677, still pins canonical 27b4eb5816265d4e6e6d2458acb6220db7dd0c76. Direct 562 use is U3_MANIFEST_HOLD; no combined W8 run performed.

## Actual changes and scope

- Added scripts/ci/mi_p0_w8_manifest_gate.py; functions git_blob, _unique_object, _files, _w8_pin_and_guard, assess, main; class GateHold. Readonly CLI compares three immutable source files and Git blob pins, checks fail-closed AST guard, and emits HOLD or MANIFEST_PRECHECK_MATCH_ONLY.

- Added scripts/ci/test_mi_p0_w8_manifest_gate.py; 16/16 actual local Python synthetic fixture unittests PASS, no failures/skips. Tests include tamper, duplicate JSON paths, added/removed/modified files, missing/inverted/late guard, invalid UTF-8 and non-acceptance semantics.

- Added versioned progress/reviews evidence JSON and this handover. New support source Git blobs abd1306246f38dc4f612cbb94e92d8de448f7d3a / ab16361322417d9ef23c245a83565fc899b9d424 independently read back identical to tested local files.

- No product source/class/API/database/event, dependency, security grant, CI workflow, product-dev or main modification. Original full W8 C04-C08 and native Chromium NOT_RUN. Real protected PG/independent security HOLD.

## Maintenance and execution

Obtain the exact three original files using the pinned refs and invoke Python CLI with --canonical, --candidate, --adapter, --canonical-blob, --candidate-blob and --adapter-blob. Current PR19 candidate should exit 2/U3_MANIFEST_HOLD. This exact three-file CLI combination was NOT_RUN locally; the source manifest comparison was performed via GitHub metadata and complete JSON, and the local helper was tested with synthetic fixtures. Never auto-repin to produce PASS.

Rollback: close/revert isolated review PR; the working owner PR19/PR20 and canonical product-dev are unchanged. Do not claim a static match is build, security or release acceptance.

## Owners and next ordered work

MI-01 owner PR20: complete exact 553 W8 dependency fingerprint, C04 prepare, C05 review, C06 install, C07 tests and C08 native browser proof. MI-04 owner PR19 and independent security: ratify G2/G9 authority variant and real issuer/root/restore/sink, then allow a separately reviewed 562 repin and full W8 rerun. No auto merge. Strict PostgreSQL and IV remain HOLD.

## Progress (15/35/20/20/10)

W8 old 3/8 -> current 3/8, Δ0. Core 12/16, UI 21/40, MVP 0/11, independent security 0/7. Overall weighted development HESAPLANAMADI (no frozen cross-stream denominator). Product acceptance delta 0. This review closes only diagnostic implementation; central queue owner must ratify any status promotion.
