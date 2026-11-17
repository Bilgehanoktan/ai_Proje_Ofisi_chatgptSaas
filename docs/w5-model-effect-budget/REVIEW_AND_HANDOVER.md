# W5 / area 09 — mandatory effect and budget proof review
Baseline 167e5239882dc7b49bd96647412fe6761da0be5e (0227). D08/D14/D21; D30-05A. This is a scoped design checkpoint, not a normative ADR or new grant.
## Findings
- model_gateway/runtime_binding.py pins reservation_ref and ceiling but explicitly does not observe a ledger.
- model_gateway/sample_adapter.py checks a diagnostic effect, skill and gateway; no actual model invocation.
- budget_engine/reservation_review.py checks scope, revision, currency, epochs, UNKNOWN and capacity; it creates no reservation.
- core/policy/gateway_review.py checks grant, lease, witness and effect binding; structural match still DENY (PEP_ISOLATION_NOT_PROVEN).
- model_gateway/gateway.py remains DisabledModelGateway.
## Next implementation contract
Reuse existing owners. Before a model invocation can even be considered for authorization, bind the exact invocation digest to a committed reservation receipt (reservation identity, budget identity, amount/currency, idempotency, scope, policy/witness epochs), current run/lease/fence and exact logical effect identity. Verify against independently obtained current observations, not caller-supplied matching objects. A capacity match is not a reservation receipt. Unknown cost, stale revision, missing receipt, mismatch, revocation or missing independent custody must HOLD/DENY. No provider call or spend from this review. Actual effect remains outside T1; do not add a second authority.
## Acceptance matrix (NOT_RUN)
Missing receipt; wrong reservation id; wrong budget id; wrong scope; wrong currency; insufficient amount; wrong idempotency; stale policy/witness epoch; stale lease/fence; UNKNOWN cost; wrong invocation/effect digest; revoked grant; matching synthetic references still DENY; real receipt without independent custody still HOLD; concurrent revoke/consume and restore residual require independent boundary tests.
## Catalog delta
Documentation only. Existing files above unchanged; no new class/function/API/DB/event/dependency. Source candidate not yet implemented. Design/source scores 50/25 unchanged; no new test or integration gate.
## Isolation and handover
Separate branch from pinned 0227. Historical workstream/0196-memory-model is behind; P10J24b and unified-u2 diverge and touch sample_adapter.py, so do not modify that file or merge those branches. Other active branches not exhaustively diffed. Next: inspect actual committed reservation readback and intent authority contracts, then implement a deny-only binding candidate in a new module with exact-source tests. Do not modify shared runtime, UI, PostgreSQL or current global handover. Rollback: revert this documentation commit on this branch only. Troubleshooting: compare pinned invocation, reservation and effect identity; preserve UNKNOWN and never retry blindly. No network, provider, spend, CI, main or PROD authorization.

## W5 checkpoint — Model Profile Registry / Capability Resolver (2026-11-17)
Previous sections are historical. Current status: partial isolated test pass, no product promotion.
- Why: existing adapter pins do not carry complete model metadata; D30-05A requires pinned policy-aware eligibility before ranking and admission.
- What/where/how: `app/engines/model_gateway/profile_registry.py` defines immutable ModelProfile, validates existing disabled AdapterPin, provider kind, revisions, context/output capacity, data/region/complexity and cost/latency references. Canonical SHA-256 catalog digest is order-independent; duplicate model/adapter identities fail closed. One profile per adapter/revision is a provisional D0 choice, not an approved production cardinality.
- `capability_resolver.py` returns diagnostic candidate digests and exclusion reasons against explicit catalog/allowlist references; no winner, cost calculation, ranking, dispatch, provider call or spending. Existing gateway remains disabled. Run-scoped synthetic references are not authenticated tenant-level policy. No real model IDs/prices/weights approved here.
- `tests/w5/test_model_profile_review.py`: ten actual unit tests passed on Python 3.13.5 Linux using 16 source files with locally recomputed exact Git blob SHA-1 and SHA-256. Direct GitHub checkout still DNS-blocked; only the selected subset was executed. Earlier 9 effect/budget methods remain NOT_RUN. [Evidence](PROFILE_CAPABILITY_TEST_EVIDENCE.json); [catalog](CANDIDATE_CATALOG.json).
- Conflict check: current W5 and seven parallel branch Model Gateway directories read directly; new modules absent on all seven before changes; tests/w5 absent on all seven. Common registry/provider/fallback/runtime blob pins match. sample_adapter.py differs on Office A5R3/A6 and historical memory/model branch; leave untouched. Some compare results capped at 300; not an exhaustive merge test. Core 0227 advanced beyond W5 baseline; no rebase or merge.
- Diagnostics: on catalog pin mismatch compare model profile digest and exact adapter pins; check explicit allowlist and scope; inspect exclusion reason for data/region/capability/token failure; never substitute a hidden fallback. Do not reinterpret D0_CANDIDATES_ONLY as ALLOW.
- Maintenance/extension: version profile digest if shape changes; preserve original profiles and test evidence; cost/latency references are not measured values. Next: recover exact dependencies to execute earlier nine effect/budget tests; develop deny-only policy router and cost-estimation source candidate against explicit approved inputs; no selection weights or production defaults invented.
- Rollback: revert only profile/capability and associated test/catalog/evidence commits on W5; no DB/schema/event/API/dependency or shared source mutations; preserve earlier effect/budget candidate. Global Design Master normative decisions, manifest, TRACK-0227 scores (50/25) and 9/16 gates not promoted. No CI/main/PROD/real spend/provider authorization.

## W5 checkpoint — Policy-aware Router / Cost Estimator / recovered Effect & Budget Review (2026-11-17)
Prior NOT_RUN entries are historical. Both independent W5 tasks completed at isolated synthetic unit-test level, not production acceptance.
- Why: D30-05A requires central policy-aware eligibility and explicit cost/latency controls before ranking or admission; effect authority remains independently proven under D30-06A.
- What/where/how: `app/engines/model_gateway/cost_estimator.py` adds CostProfile, CostEstimate, valid_currency, cost_digest, estimate_cost. Explicit profile/rate/reference/currency pins, integer token counts and minor-unit arithmetic; upward rounding per component plus fixed amount, bounds and overflow rejection. This rounding is a provisional D0 choice, not the approved billing formula; actual charge remains absent.
- `router.py` adds RouteMetric, RoutePolicy, RouteCandidate, RoutingReview, _digest, metrics_digest, policy_digest, inspect_route. Reuses CapabilityQuery and resolver. Validates supplied scope/epochs, policy/catalog/metrics pins, allowlist, currency, profile-specific cost and upper-latency references and ceilings; missing/invalid metrics or limits exclude. Only SAMPLE is eligible; digest order is not ranking. No final model selection, fallback execution, provider call, token charge or spend. No production prices, weights, SLA or defaults invented. Diagnostic pins are caller-supplied, not independent authenticated policy.
- Exact test recovery: immutable commit 76d3997f70bbe80117304557b6576dfa07ba32bb; 42 exact source files recovered from GitHub connector with recomputed Git blob SHA-1 and SHA-256. Direct clone remains DNS blocked. Linux Python 3.13.5: 29/29 passed, including 9 previously NOT_RUN effect/budget tests unchanged, 10 profile/capability regression methods and 10 new router/cost methods. [Raw logs and file hashes](ROUTER_COST_EFFECT_TEST_EVIDENCE.json). No DB/provider/network integration or concurrency/revocation/restore proof.
- Conflict review: inspected latest core 0228-d3-rls-fixture, unified-u3a-product-acceptance, org-04-candidate-scale, p10j24b-source-recovery and Office A5R3/A6 Model Gateway directories before edits. New router/cost paths absent on all six; shared files left unchanged. sample_adapter.py divergence deferred. No merge/rebase, exhaustive merge proof or global product promotion.
- Catalog: two new source modules, six classes, seven functions (including private digest helper), one test module. No API, database, schema, event, worker or external dependency changes. [Updated catalog](CANDIDATE_CATALOG.json). W5 baseline TRACK-0227 scores 50/25 retained; no global gate change by W5.
- Diagnostics: check canonical query/profile/policy/metrics digests, scope/epochs, explicit rates and currency, token bounds and latency references; inspect exclusion reason. No candidates means HOLD; a candidate is not a winner or effect authorization. For effect review compare exact receipt identity/lease/fence; UNKNOWN remains unknown, never retry blindly.
- Maintenance and next: independently develop immutable RoutingDecisionRecord and Token Accounting with distinct estimated/reserved/actual/reconciled states. Bind query/policy/catalog/metrics and diagnostic outcome, preserve revisioned evidence; do not infer actual cost. Recheck active branches; rerun 29 tests plus new tests. Real reservation receipt per invocation, independent custody/readback, quota/risk/revocation and DB/provider acceptance remain HOLD.
- Rollback: revert this round's six commits on isolated W5 branch only; retain earlier profile and effect candidates and historical evidence. No shared runtime edits, CI, main, PROD, real credentials, spend or provider authorization.


---

# W5 — Routing Decision Record / Token Accounting (2026-11-17)

Parent: 6167e4c593a11bf9fcacfdb5d5b7572db0d6e7c8. Isolated W5; D08/D14/D21, D30-05A, phase 3. CEO-0174 / 0179=B source and synthetic local-test scope only.

RoutingDecisionRecord captures query, policy/catalog/metrics pins and screened outcomes. Replay against exact supplied references rejects tampering even if rehashed. Token Accounting keeps estimate, reservation, usage and reconciliation observations distinct, bound to run/attempt/profile/invocation/currency/epochs; no inferred zero or actual authorization. All execution/finance gates HOLD.

Tests: 41/41 (21 new + 20 regression); 19 exact existing source files verified. Prior 9 effect/budget tests not rerun. Full evidence and file pins in local ZIP; repository summary in DECISION_ACCOUNTING_TEST_EVIDENCE.json.

Parallel: 169 branch names inventoried; 13 active peer trees checked, A5R3 folder checked (commit-tree 404). No matching new paths found. Includes Core 0229-D4R2, ORG-05R5, W5-EXT02, Unified U3A, P10J24B. No exhaustive merge/future-chat guarantee. No shared Runtime, DB, API, UI or global manifest/tracker edits.

Maintenance: compare exact replay and supplied reference pins; inspect scope/attempt/invocation/profile and independent receipt/content pins. UNKNOWN remains unknown; never release based on estimate. Reconciliation match is not settlement. Preserve evidence and digest version; revert only W5 commit if needed, no migration.

Open: Full repository checkout DNS blocked; exact isolated source subset only; Previous nine effect/budget tests historical PASS; not rerun here; No independent security, actual receipts, runtime lease/fence binding, live provider, real spend, PG/RLS or full build; Frozen records are not durable append-only storage; SHA-256 is not a signature; No shared manifest promotion or new execution grant; scores 50/25 unchanged.

Next: Bind exact invocation envelope to route/profile and current run/attempt/lease/fence; Define per-invocation reservation and usage receipt port with existing T1/Budget/PEP owners; do not implement a second ledger; Recheck Core, Unified, W5-EXT and other active branches before shared edits.

Full local handover SHA-256: 96a104528bce6cbbd4700faa3bed9b78abb072dff0f2df3cc790eb7c1012fb07. This repository handover is a concise counterpart, not byte-identical to local document.


---

# W5 — Invocation route binding and reservation/usage receipt port

Parent: db38b65dc1120cf5cc25222774295662f9d7d120. Only W5 source additions, no shared owner edits or merge. D0 review only.

InvocationRouteContext replays the exact routing record and existing invocation envelope against supplied run, lease, clock, raw bytes and catalog/metrics pins. It checks caller-nominated primary and alternate profiles, input/output token limits, capability and cost ceilings, then derives UsageBinding. A match is HOLD, never selection or dispatch. Input token count is an explicit synthetic reference, not a trusted tokenizer measurement.

ReceiptLookup binds the invocation idempotency and reservation identity. ReceiptReadback carries pinned reservation, usage and reconciliation observations and budget revision/source pin. ReservationUsageReceiptPort is an owner-supplied read-only Protocol with no implementation. Existing run-level admission CommitReceipt/sample_reservations and aggregate budget balances cannot establish per-invocation membership; do not reinterpret failure-only sample_settlements as actual model usage. The review checks supplied pins, exact identities, unknown-cost state and arithmetic/ceiling consistency, and retains HOLD even when everything matches. There is no ledger, schema, write path, API or provider integration.

Evidence: 62/62 actual isolated tests (21 new + 41 prior); 25 parent-exact files and 3 new file pins. Original 9 Effect & Budget tests were not rerun; exact dependency recovery blocked by incomplete transfer. Full regression PARTIAL. Source catalog and full local log hashes in companion records. No product score or authority changes.

Collision scope: current W5 plus seven active peer branches inspected (Core 0229-D4R2, Unified U3A, ORG-05R5, UI P10J24B, Office A5R3/A6, W5-EXT03); no matching new paths. No global tracker, shared Runtime, Budget, T1, DB, UI or sample_adapter mutation.

Maintenance: compare invocation/route/profile and scope/attempt/lease/fence pins, then budget source revision and independent receipt pins. Treat unknown result/cost and missing custody as HOLD, never synthesize evidence or retry blindly. Roll back only the W5 delta commit, no migration. Strict dual-candidate eligibility and reservation covering invocation ceiling are provisional D0 choices, not ranking/billing policy. Next: exact full regression and owner-approved durable receipt adapter contract, then integration review; no real provider calls, grants, spend or independent acceptance.
