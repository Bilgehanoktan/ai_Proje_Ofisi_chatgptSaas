# MI-P0 / NW02 — D0 IAM–Authority–T1 scoped session source repair (2026-11-22)

**Status: DRAFT / OWNER REVIEW HOLD / actual runtime NOT_RUN.** This addendum describes only the existing owner's code paths and their optional D0 integration, not a production authorization feature. No new engine or new trust issuer. H01 Windows-last order remains.

## Scope, source pins and ownership

- **Parent:** MI-03/04 G2 owner draft PR19 at `0a8907f177bb3e9b458aefb3ea3441b15537f542`, shared canonical unchanged `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`.
- **Child:** independent review-only PR46, branch `review/mi-p0-nw02-iam-session-binding-d0-20261122`, base exactly PR19 HEAD; existing owner PR19, combined source PR31 and W8 PR38 untouched.
- **Edited product source** `product/ai-company-os-backend/app/core/transaction/intent_authority.py`: owner original blob `b28788f46a39c282d79d29c4abd817ed5fc9de99`, child blob `d492c6d3ea99214e28c0fa4e772139169bd39a17`, SHA-256 `c1d0cef446a374885054d6cda8852c273297c05f92eed3debcde42e4c5127125`, bytes **10066**.
- **Extended original product regression** `product/ai-company-os-backend/tests/test_authority_wrapper_0213.py`: original blob `f921dbe2abc114cb2b7ff2eb384468a5779eee5b`, new blob `f2176332ebdef0c0b0597977582bab5c5b34c59d`, SHA-256 `d8363de0bab41ed8ee6625d996f8ba63d21ff24d33e831c87ad7a3dc8a993c1f`, bytes **8792**.
- **Updated product manifest** `product/SOURCE_MANIFEST.json`: original blob `566b7210b6edb95a21b999dc1d881a12284d9011`, child blob `15c39d20b2284aa8ce1e7efce5260245e6f3e0f1`, full JSON SHA-256 `c54019d038c8e770ea23918badc1c518f7877f8722f59daaf9c0bc67ae11a018`. Exactly **2** item metadata records changed, existing **561** entries preserved. Owner variant metadata references original owner blob historically, and does **not** represent automatic approval of child source.

## What and why (API, schema, behavior)

Existing `D0IntentAuthority.claim_and_fence(..., *, session_check=None)` already requires exact `SessionClaimCheck` when IAM tables exist. Pre-change `execute_authority_fenced_transition` omitted the check and was therefore **correctly fail-closed** with `D0_IAM_CHECK_REQUIRED_HOLD` in IAM mode. Change the **existing** wrapper to accept `session_check=None` keyword-only (after `result_reader`) and forward the argument to `claim_and_fence`.

Before any claim, when `session_check` is supplied, require exact `SessionClaimCheck` and exact `Scope`; the check's 3-value scope must equal synthetic `D0_SCOPE` and the intent's tenant/company/environment, and the intent's principal and agent IDs must match the check. Failure becomes `D0_AUTHORITY_SESSION_SCOPE_HOLD` *before* writing a claim. The existing `SessionClaimCheck.inspect` additionally requires a resolver on the same authority, exact observation, credential, unexpired nonrevoked AGENT session and persisted IAM pin. The no-check default is **unchanged**: IAM mode continues to refuse a missing check; legacy authority refuses non-None check (`D0_IAM_MODE_HOLD`).

No SQL DDL, migration, event, public API endpoint, env, lock, dependency, CI or provider was changed. Existing `iam_claim_pins`, `claims`, `roots`, `D0IntentJournal` and T1 `CommitReceipt` contracts are reused. All successful D0 results remain `HISTORICAL`/HOLD with `independent_verified=False`, `dispatch_allowed=False`, `retry_allowed=False`; no trust, grant, real spending or production use.

## Test contract / honest evidence state

Six **new methods in the existing** `test_authority_wrapper_0213.py` (not a second test engine):
1. Missing check on IAM mode → HOLD before claim/T1.
2. Scoped real D0 `SessionClaimCheck` → original fixture T1 historical receipt, no dispatch, exactly one claim and IAM pin.
3. Forged principal or agent → HOLD before claim/T1.
4. Revoked exact session → HOLD with no claim.
5. Expired exact session → HOLD with no claim.
6. Legacy/non-IAM authority supplied IAM check → HOLD with no claim.

Preserve the original six wrapped SQL methods, original G2/0211/0212 cases, and separate restore-replay reproducer. **Actual Python tests in this source version: 0 run, NOT_RUN**; no 6/6 or 12/12 runtime PASS. Required later: execute exact original locked suite in full disposable source checkout, Python reviewed dependencies; verify raw output, exit, SHA; ensure original history and D-04 restore residual remain distinct. No Windows requirement is imposed for design/source review; H01 postponed the full Windows chain.

**Static checks done:** GitHub compare exactly three modified product paths (two code/test + manifest), no owner/canonical PR changes; all 561 manifest paths exist, 561 declared sizes match Git tree, no extra paths; 559 unchanged product Git blobs byte-identical to owner PR19, two changed file SHA256 calculated from UTF-8 payload and verified against original owner manifest after a SHA256 implementation self-test. This is not a full 561-payload SHA256 byte audit nor original runtime test.

## Failure diagnoses, ownership gate and rollback

- `D0_AUTHORITY_SESSION_SCOPE_HOLD`: exact scope/principal/agent mismatch before persistent claim. Inspect the request binding and session origin; never bypass by inventing an authorization marker.
- `D0_IAM_CHECK_REQUIRED_HOLD`: missing session on IAM-enabled authority, no fallback. `IAM_CLAIM_HOLD`: observation, credential, clock, revocation, instance or retained pin mismatch. `D0_AUTHORITY_ALREADY_CLAIMED_HOLD`: do not retry; first claim permanently quarantined.
- **Residual:** full DB+journal+local authority store/pin rollback can still replay, so no independent root/monotonic consumed intent/sink-side fence or live authorization is proven. Protected PostgreSQL non-owner RLS/COMMIT and A-AT01..08 independent security tests remain separate **HOLD/NOT_RUN**.
- **Owner to decide:** MI-03/04 Core/ORG confirm binding and test, security/IV confirm separation and scope for any production design, MI-01 manifest/W8 owner reviews new source pin. A source-only child PR cannot self-approve. PR31 566 source is pinned to previous G2 blob and is **not** upgraded by this patch.
- **Rollback:** Close unmerged PR46, or normal revert of child code/test/manifest commits `25f3dca4b8edf3d2eff776486886aaed52bda01e`, `b7a0bc9039a179ea28595a4aed46aba53a307f04`, `38ed3beb0388bbde37ef47357ec712e27170c2a2`; restore parent PR19 exactly. No force-push, source overwrite, automerge or history deletion.

## Metrics / next

Canonical Core 12/16, UI 21/40, MVP 0/11, IV 0/7, W8 3/8; all acceptance delta 0. Overall development weighted 15/35/20/20/10 **HESAPLANAMADI** absent frozen criteria denominators. First owner review PR46 and PR44; later NW04 PostgreSQL trust/restore and NW05 combined source runtime; actual Windows W8 last. New H01 decision is **not** necessary for this isolated review package; independent trust/root/security activation remains a separate gate.
