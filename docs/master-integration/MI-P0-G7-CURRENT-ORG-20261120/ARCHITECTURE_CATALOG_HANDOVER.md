# AI Company OS — MI-P0 / G7 current ORG requalification runner
2026-11-20 | SOURCE-PINNED TEST DELIVERY / REVIEW ONLY / NOT PRODUCT ACCEPTANCE

## 0. Why this was selected after collision audit
`integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` still contains 553 product files. Owner MI-01 PR #20 is active for W8, MI-04 PR #19 is active for isolated G2/G9 562 source, PR #21 is an existing cross-PR manifest guard, PR #22 is Office Workbench timeout correction, and independent security PR #10 is still in owner review. No competing source, CI or shared runner was edited.

The remaining non-duplicated G7 test gap is **whether the same seven original G7 test methods also pass with the expanded current product-root `durable_ops.OperationsStore`** instead of the historical `candidates/ORG-05R3` implementation. Prior CI #44700495037 ran 72/72 owner-selected D0 tests on immutable `93e6c84db1a061ee914aa2c1d543620404515c0b`; G7's original fixture imported historical ORG. Its test methods are unchanged. Prior historical store blob `43ed448c02904ab44b3cf8665f4aeafb0a38f10a` versus expanded product store blob `619fe224c05d7f7f7efe998583e4730cb2cb4d3e` preserve all 161 previous lines and add 41 lines, but source-level compatibility is not runtime acceptance.

## 1. Actual delivered code (not new product engine)
- `scripts/ci/verify_current_org_g7.py`: standalone Python 3.13.5 standard-library runner outside the exact checkout; Git HEAD must equal `93e6c84db1a061ee914aa2c1d543620404515c0b`; fail if dirty, unexpected paths, symlink or mismatched source. Verify 561 manifest entries and 56 original G7 blobs; pre-import current product-root `durable_ops` before the original G7 runner prepends historical candidate import paths. Assert `test_org_core_checkout.OperationsStore is product.OperationsStore`, verify exact module origin, then invoke seven **unchanged** original method bodies. Reject failure/error/skip/collection drift. Never write to product or modify historical pins.
- `scripts/ci/test_verify_current_org_g7.py`: 16 focused standard-library synthetic guard tests. These validate Git hash, pinned source, path traversal, symlinks, missing paths, malformed manifests and source pin lists, dirty/clean Git checkout, misrouted ORG fixture, old cached module, and fail-closed missing checkout. These are helper tests, not G7 product tests.

**Raw evidence:** local `python -B -m unittest -v test_verify_current_org_g7`: **16/16 PASS**, exit 0, Python 3.13.5 / SQLite 3.46.1. `python -m py_compile` both files PASS. GitHub source Git blobs checked against local byte identity. Full current 562 source archive was unavailable in this execution environment (GitHub DNS failure); actual seven original tests against current ORG: **NOT_RUN**, no fabricated pass. CI workflow created or enabled: **0**.

## 2. Runbook — only an authorized exact checked-out source (never run from arbitrary clone)
On a trusted test machine with private repository access, make **two separate directories**: immutable exact candidate Git checkout `93e6c84...` and this review utility (download the exact verified runner from review branch). Use the owner-approved pinned Python/runtime/dependencies; do not treat these as approved by this delivery.

```bash
python -B -m unittest discover -s scripts/ci -p test_verify_current_org_g7.py -v
python -B scripts/ci/verify_current_org_g7.py --root /path/to/exact/pr19/source --json-out /path/outside/checkout/g7-current-org.json
```
The commands are examples for an **authorized environment only**. They do not authorize any cloud CI scope or owner source promotion. Python >=3.9 is required for `Path.is_relative_to`; Python 3.13.5 is the pinned target. If the source SHA is not exactly `93e6c84...`, the runner must exit 2 and is not allowed to silently re-pin. The current runner assumes the isolated source's existing declared test dependencies are installed; dependency approval is separate. No modifying the PR19 source or Git history.

## 3. Architecture, symbol/API/DB/dependency catalog
| Item | Role | New behavior / delta |
|---|---|---|
| `git_blob(raw)` | Source Git blob identity | Computes Git SHA1 blob envelope, not a security signature |
| `safe_file(root,path)` / `pinned_bytes` | Fail-closed path & source preflight | Reject symlinks, traversal and mismatching original source bytes |
| `check_commit(root)` | Immutable Git checkout gate | Requires exact revision and clean tree |
| `verify_manifest(root)` | Product source integrity | 561 manifest metadata entries, 562 total product files |
| `verify_original_pins(root)` | Original owner provenance | 56 unchanged G9/G7 historical references; no repin |
| `product_import_first(root)` | Runtime module resolution | Preload product `durable_ops.py`, avoid historical `sys.path` fallback |
| `assert_fixture_uses_product(...)` | Runtime class identity | Require ORG-06 fixture to reference the exact current product OperationsStore class |
| `run_g7(root)` | Seven original D0 methods | Invokes existing source, no new grants or T1 COMMIT |
| `main(argv)` | CLI / local JSON evidence | Exit 0 only on seven actual methods; exit 2 on failed preflight or tests |

**No new product API / DB tables / events / external network dependencies / frontend / service workers / business logic / npm lock / authorized CI workflow.** Standard library only; CLI is review/test scope. Script-side checks do not establish independent issuer/provenance, PostgreSQL commit/restore, sink fencing or IV.

## 4. Repair, maintenance, regression and rollback
- If `IMMUTABLE_COMMIT_MISMATCH`, refresh **owner decision** and create a separately reviewed new source pin set; never change expected SHA to make a broken run pass.
- If `G7_ORG_IMPORT_ORIGIN_CHANGED` or `FIXTURE_HAS_HISTORICAL_OPERATIONSSTORE`, inspect `durable_ops.__file__`, `sys.modules` and historical fixture `sys.path` ordering. Do not edit original seven tests for a forced green result.
- If `MANIFEST_CONTENT_MISMATCH`, stop; compare `product/SOURCE_MANIFEST.json` and the immutable commit's source with owner; don't overwrite.
- If `G7_CURRENT_PRODUCT_ORG_RUNTIME_NOT_PASS`, retain exact failure log and raise owner G2/G9/ORG review; **do not grant authority**.
- Rollback: close the draft review PR or normal revert of its six scoped files. Historical owner PR19/20/21/22, central product-dev/main and security claims unchanged. Never force push, replay claims or auto-merge.

## 5. Progress & handover
- General weighted design/source/function/integration/final `15/35/20/20/10`: **previous/current HESAPLANAMADI** (0/10 approved denominators), delta not computable.
- Canonical acceptance unchanged: Core **12/16**, UI **21/40**, MVP **0/11**, IV **0/7**, delta **0 pp**. W8 operational **3/8** unchanged, not a product-acceptance percentage.
- New helper test methods 16; executed local 16 PASS, original G7 current-store tests 0/7 NOT_RUN. Prior 72/72 original cross-source CI remains historical and is not counted again.
- Next real owner task: exact 562 checkout on an authorized machine, run this unchanged-method/current-store import-root requalification (7/7 target) with full original owner dependencies, capture raw evidence. Owner MI-01 completes original 553 W8 C04-C08 separately; MI-04/G2/G9 ratify authority variant; MI-02 independent root/issuer/sink/PG/IV gates remain HOLD. No additional CEO choice is requested for review-only runner; any new hosted CI or production authorization needs its own policy decision.

## Delivery identity
Branch `review/mi-p0-g7-current-org-requal-20261120` based on `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`. New files only; owner source change 0. Script blob `48bc0a7c6582defac61a5e346fd923af200d1d88`, test blob `7313cf0160c006eaa5eb7ebc2381712daa26a14a`. Source hashes, exact local runtime and helper raw log are recorded in `EVIDENCE.json` and local delivery bundle. This architecture/catalog delta preserves previous versions rather than replacing Design Master.
