# AI Company OS — GATE-02 real IAM/ORG issuer provenance: closure verification and handover

**Date:** 2026-11-20 · **Conclusion:** source contracts **12/12 static matches**, real independently owned and authenticated issuance **NOT PROVEN**, gate **HOLD**. The original Core↔OperationsStore D0 tests are **10/10 actual CI PASS**, distinct evidence [run 44620141705](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620141705).

## Current architecture: source ownership and trust gaps

| Existing source / symbol | What exact source supports | What it does NOT prove |
|---|---|---|
| `app/core/transaction/intent_identity.py :: derive_request` | Core intent + Member identity consistency | `Member` is not an issuer or authenticated current principal |
| `app/core/transaction/identity_binding.py :: review_binding, review_boundary` | D4 typed principal, role, membership, assignment, session observation comparison | Caller-provided `Binding` and `SessionFacts` do not provide actual owner provenance, and decision is always HOLD |
| `assignment_lifecycle.py :: AssignmentPin, ApprovalObservation, validate` | Registry/membership/role hashes, revision shape and distinctness; D0 approval chain | `issuer` and `custody` are synthetic strings; independent custody/signature/current grant absent |
| `durable_ops.py :: record_assignment_review, assignment_review` | Actual Core historical reader and ORG SQLite persistence, readback, fail-closed drift | No live IAM issuer, no atomic Core/ORG snapshot, no protected PostgreSQL COMMIT |
| `app/core/iam_session.py :: D0SessionResolver, SessionClaimCheck` (G2) | Sealed D0 session bootstrap, agent session/revocation and two claim checks in local SQLite | No live owner issuance, D4 Request binding, ORG role or independent external custody; full old-DB+pin restoration residual |
| `app/core/transaction/intent_authority.py :: claim_and_fence` (G2) | Local authority claim consumed before fence, IAM-mode guard | Original execution wrapper does not provide SessionClaimCheck. Protected T1 real commit and external sink fencing are unproven |
| D4 disposable `00_roles.sql` | NOLOGIN, NOBYPASSRLS test roles for dedicated PG test cluster | No authenticated production IAM account/role granting |
| D-03/D-04 independent authority design | Correct negative test and trust boundary matrix | Original design file gave unratified A/B/C options. Subsequently H01 selected **A architecture direction only** in canonical `decisions/ADR/ADR_D03_D04_OPTION_A_20261120.md`; no separate real authority installed |

## Confirmed source-version incompatibility

Existing ORG owner at `integration/mi03-gate03-org-runtime-closure-01@d6b82dc4` retains `intent_authority.py` blob `fa47acd32adb309896f762ec50e47bf26641adbb` and lacks G2 `iam_session.py` and `test_iam_authority_d5g2.py`. D5-G2 owner `workstream/0230-d5g2-durable-iam-authority@9ca667e816dac269084ef8f62051da5fe458eb12` adds `iam_session.py` blob `f3c37428acd475e09c228bce47d534d6584cd944` and changes authority to blob `b28788f46a39c282d79d29c4abd817ed5fc9de99`. This is a **same-file version collision**, not permission to overlay. Avoid overwriting original G9 without source-owner review.

## 10 hard closing criteria

- **P01 Owner issuance: HOLD.** Authenticated server-side issuer and custody, signed or independent administered proof—not ApprovalObservation. Owner: MI-03 IAM / H01 owner.
- **P02 Registry: HOLD.** Owner-issued registry current version and verified independent custody bound to tenant/principal. Owner: MI-03 IAM.
- **P03 Membership: HOLD.** Latest authorized member scope/project/run from protected owner source, no supplied Member alias. Owner: MI-02 Core / MI-06 ORG.
- **P04 Role/assignment: HOLD.** Latest role and assignment owner issuance, revocation and pin equality with ORG Store. Owner: MI-06 ORG / MI-03 IAM.
- **P05 D4↔G2 exact session: HOLD.** Existing signed SessionObservation agent/principal/session tied to original D4 Request and T1 scope, re-read before commit. Owner: MI-03 IAM / MI-04 T1.
- **P06 Owner collision: HOLD.** Compare original intent_authority.py fa47acd... vs G2 b28788...; preserve G9 before controlled merge. Owner: MI-03/MI-04 / G9 owner.
- **P07 Protected COMMIT: HOLD.** Independent authority monotonic root, commit-time principal+role+lease refresh and sink fence; no bypass paths. Owner: MI-04 T1 / Security.
- **P08 Restore safety: FAIL_EXISTING_D0_RESIDUAL.** Old product+old journal+old local authority+old pin cannot reaccept; external checkpoint and destructive restore drill. Owner: Independent Authority / IV.
- **P09 Original security regression: NOT_RUN.** G2 50, G9 7, MemoryT1 0214 10, actual protected PostgreSQL role/RLS tests pass with pinned original sources. Owner: MI-03/MI-04 / MI-02.
- **P10 Independent acceptance: HOLD.** Separate custodian signed IV evidence and W8/native browser build; no synthetic only acceptance. Owner: IV / MI-10.

P08 is an existing demonstrated security failure, not merely `NOT_RUN`: restoring old product + local authority + old owner pin can revive the previously used claim. A standalone D0 signed hash or receipt cannot replace independent monotonic custody or sink-side fence.

## Approved development path vs decision still required

Reuse existing D4, Core `Member`, G2 `SessionClaimCheck`, ORG `AssignmentPin`, and T1 fence. Do **not** add a parallel IAM issuer. **Architecture decision already made: H01 selected Option A (specification/direction only)** as recorded in canonical [ADR D-03/D-04](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/planning/master-integration-governance/decisions/ADR/ADR_D03_D04_OPTION_A_20261120.md). Do **not** repeat the A/B/C user decision. Option A requires an independently administered, consensus-backed root and consumed-claim ledger, plus separate effect-sink freshness/fencing/idempotency. It is **not implemented**: provider, KMS, quorum, issuer, owner custody and sink remain unselected/unproven; independent acceptance **0/8**. Other options are not chosen, but **D0 HOLD is still the only permitted operational behavior**. A1 independent security owner/admin/restore contract review is next; A2–A5 source, negative tests, PG and IV remain HOLD.

Strict high-level requirements: independently issued principal/registry/member/role/assignment evidence; same tenant/company/project/plan/task/run/agent/principal and policy/witness epochs; immutable key/issuer/custody identity, nonrollbackable latest root; session revocation/expiry rechecked within protected commit; fail-close on unknown; no alternative effect path. Preserve ownership and existing CI permissions.

## What/why/where/how; tests and rollback

This audit makes **no product code, API, SQL, credential or CI workflow edit**. An additive non-authoritative review note may be recorded in the central queue without modifying operational security. All 12 checks were exact GitHub source-marker inspections on listed blob pins. They are STATIC source matches, **not** twelve product tests. The **10/10 real Core+ORG D0 tests** remain separate previous evidence, not rerun here. G2 50/G9 7/Memory 0214 10; actual PG, native W8 and independent IV remain **NOT_RUN/HOLD**. IAM/ORG weighted historical progress 42.50 → 42.50 (0 pp). Core 12/16, MVP 0/11, independent security 0/7; overall percentage remains uncomputable without approved denominators.

Next action: owner review of exact G9/G2 conflict and independent issuer/custody selection, then controlled source integration and real fail-closed/revocation/restore trials; preserve raw logs and source manifests, obtain IV sign-off before any authority activation. If rejected, revert only these review records or close draft PR #6. Do not reset persisted consumed claims, bypass revocation, repin stale data or alter `integration/product-dev` / `main`.
