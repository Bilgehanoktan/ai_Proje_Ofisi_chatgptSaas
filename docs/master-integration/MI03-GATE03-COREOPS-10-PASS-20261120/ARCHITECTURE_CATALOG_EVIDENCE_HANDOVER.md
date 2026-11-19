# AI Company OS — MI03/GATE-03 original Core–OperationsStore CI closure
**Date:** 2026-11-20 (Europe/Istanbul) · **Evidence class:** ACTUAL_GITHUB_HOSTED_ORIGINAL_PRODUCT_SQLITE_TESTS · **Gate:** D0 functional subgate PASS; real owner/security gates HOLD.

## What changed / why / where / how
With explicit user approval limited to PR #6's ten original, synthetic tests, a dedicated read-only GitHub Actions workflow was placed on isolated review branch `review/mi03-gate02-core-positive-20261119`: `.github/workflows/mi03-gate03-pr6-coreops.yml`. It checks out immutable full original source commit `3b59f54eca5246a4989b203e89bee1f1f1d74e93`, validates exact Git blob and SHA-256 pins, initializes Python 3.13.5, installs the existing declared cryptography==46.0.4 plus CI-only version-locked cffi==2.0.0/pycparser==3.0, then executes **only** `python -B -m unittest discover -s tests -p test_core_operations_assignment_mi03.py -v` under `product/ai-company-os-backend`.

### Verifiable actual execution
- **Canonical evidence:** [run 44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705), job `135899290063`, ubuntu-24.04, Python 3.13.5, job conclusion success. All **10/10** unique methods reported `... ok`, summary `Ran 10 tests in 0.849s\nOK`, shell exit 0.
- Checks exercised: (1) original Core Research reader prior to write; (2) persisted Core+OperationsStore write/readback; (3) wrong principal; (4) stale Core version; (5) wrong role; (6) Core member drift; (7) cross-scope rejection; (8) revocation and no reacceptance; (9) persisted Core drift rejects readback; (10) missing Core cursor fails closed.
- Exact test: `product/ai-company-os-backend/tests/test_core_operations_assignment_mi03.py` Git blob `23c2f019a27bc9e16d8de3f2af72c239eefac035`; test SHA-256 `1ef392356f7f605cff573069d77da31d9188f874636d1179eb7a3751a32e636d`. Real Core reader blob `720044a4e4954820b8d298f73b6b75f2189b4f94`; manifest blob `92cbdde64d350e28dd02526b655f90b404f267b2`.
- Initial CI attempts [44619326736](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44619326736), [44619523838](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44619523838), and [44619843185](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44619843185) had **environment/dependency bootstrap problems** (blocked setup, absent cryptography, absent cffi). None is counted as successful original functional test. Other parallel CI runs are not aggregated as new methods.

## Architecture and technical catalog
| Layer | Original symbols/files or resources | This round's production delta |
| --- | --- | --- |
| Core source | `app.core.development_review.research_slice.inspect_research_slice`, `ResearchFixture`, original company/transaction/event readers | **0** |
| ORG source | `durable_ops.OperationsStore.record_assignment_review`, `.assignment_review`, `assignment_lifecycle.verify_core_reference` | **0** |
| Identity | `intent_identity.derive_request`, `AssignmentPin`, `ApprovalObservation`, `Member` | **0** |
| Database | Disposable synthetic Core + ORG SQLite `op_assignment_review`, `run_heads`, company membership and original root `database/01xx` fixture SQL | **0 schemas** |
| API | No newly exposed endpoint or runtime grant | **0** |
| CI/test | New workflow `.github/workflows/mi03-gate03-pr6-coreops.yml`, original 10-method test unchanged | **1 CI workflow; 0 product code** |
| Dependencies | `cryptography==46.0.4` original declared; test-run only `cffi==2.0.0`, `pycparser==3.0` | **0 production requirements** |

Original `OperationsStore` reads actual Core DB through the original reader and commits only to isolated ORG SQLite; it is **not** a single atomic/owner-authenticated distributed transaction. The isolated `ApprovalObservation` has synthetic issuer and custody. All decisions remain `HOLD`; no dispatch/retry/real grant.

## Score and gate disposition
- **Actual test subgate:** previously 0/10 executed, currently **10/10 PASS**; +10 newly executed unique methods under exact owner source.
- **Real GATE-03/02 owner-issuance and authoritativeness:** HOLD; **no product acceptance claim**.
- Existing IAM/ORG development figure **42.5% -> 42.5% (+0 pp)** is carried as a separately recorded historical denominator; re-evaluate only after owner freezes weighted proof criteria. Core product acceptance **12/16 (75%)**, MVP **0/11 (0%)**, acceptance delta 0. Total product development % cannot be calculated from unratified cross-stream denominators.

## Diagnostics, maintenance and rollback / next handover
- To reproduce: inspect frozen PR #6 source SHA; run the exact ten tests on full source checkout with isolated, pinned dependencies. Require `Ran 10 tests\nOK`, explicit negative deny assertions, source SHA checks; preserve CI run/job URLs and immutable test SHA.
- If import fails: distinguish Python bootstrap/package lock, missing full checkout, and actual test failure. Earlier attempted dependency bootstrap failures are diagnostic, not product regression. CI-only dependency versions **are not a fully reviewed/hash-locked production environment**; W8 dependency acceptance remains separate.
- Rollback: normal revert of isolated review-branch CI change, or close PR #6; no rewrite, no product-dev/main modification, no database migration. Preserve successful GitHub run for audit.
- Next owner work: independently verify issuer/registry/member/assignment/role provenance (GATE02), original G2 50/G9 7/Memory T1 10 tests (GATE01), PostgreSQL strict COMMIT/restore witness and nonretry (GATE04), then full W8/native browser/IV and staging (GATE05). No independent security or release approval was granted.
