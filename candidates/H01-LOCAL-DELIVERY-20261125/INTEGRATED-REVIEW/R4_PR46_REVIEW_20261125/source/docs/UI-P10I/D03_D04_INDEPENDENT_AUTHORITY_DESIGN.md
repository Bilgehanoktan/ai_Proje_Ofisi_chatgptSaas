# D-03/D-04 — independent authority candidate, design only

Existing D0 local journal/witness/claim locks serialize cooperating writers, not independent custody; P10H/P10I original wrapper diagnostics reproduce root path replacement and simultaneous restore of product/journal/authority. D-01/02/03/04 remain open. Do not change default-deny or allow provider calls, real retrieval, grants, spending or effects.

## Trust boundaries and invariant
A separate administrative/restore domain owns the linearizable root and claim ledger. Product identity cannot write, restore or replace that ledger. No root freshness may be inferred from a local file or caller-supplied epoch. Root monotonicity must survive recovery and key rotation via independently retained checkpoint evidence. Claim is durably consumed before journal/T1 attempt, bound to tenant/company/environment/plan/run/principal/intent digest/transaction ref/request digest/expected version and epoch. A later root revision never restores consumed claims. Unknown outcomes quarantine rather than retry. Treat effect-sink acceptance as a separate boundary from product-state commit; sink must validate current fencing epoch and deduplicate an exact effect ID under its own atomic acceptance contract. A signed historical receipt alone is not a grant.

## Options for separate approval
A: independently administered consensus-backed authority + sink-side fenced/idempotent acceptance; recommended design direction, not ratified. B: external immutable checkpoint/append-only ledger + independently enforced serialization service; requires proof of freshness and ordering, append-only alone insufficient. C: keep local D0 read-only diagnostics; no real execution, safest until independent proof. Do not silently choose an implementation or external provider.

## Failure/acceptance matrix
1. Replace root file or redirect path during commit: independent authority must remain unaffected; stale epoch at effect sink denied.
2. Restore product and journal: consumed claim remains, no replay.
3. Restore product, journal and local authority: independent monotonic checkpoint rejects regression; no effect.
4. Split brain/network partition/timeout: fail closed; no alternate authority or automatic retry.
5. Commit response lost: quarantine, exact independent reconciliation; no second effect.
6. Root key rotation/lease expiration: stale proof rejected at sink; consumed claim not erased.
7. Cross-tenant/run/intent binding or direct effect bypass: reject; prove complete mediation and separate credentials.
8. Independent backup/restore drill: establish nonrollbackable checkpoint continuity, test from separately administered environment.

Acceptance requires independent verifier evidence, actual authorized isolation and sink-level tests; SQLite stand-ins and fixture keys do not suffice. No production code or infrastructure change in P10I.
