# MI03-GATE02-STORE-CORE-ISOLATED-REPLAY-01

Exact D0 candidate `6efc6714757ebd698d27efd7022afc2c92af70d0`; new source/DB modifications: 0. Actual 16/16 new local SQLite tests ran with the two exact Store extension methods from blob `2765b12863a0fce9410dec1bafafee97a11db339` and original assignment module `9f259e89fd339804292eb6c7fa8e7fd177c71b70`. 20/20 old D0 unit methods reran. Source pins, test SHA256, log SHA256 and ZIP SHA256/CRC in catalog. Runnable source package supplied separately as `MI03_GATE02_STORE_CORE_REPLAY_01.zip`; not uploaded as a GitHub source file in this round.

**Critical interpretation:** Store._current/_team/_history/_connect are harness doubles; Core inspect_research_slice, Member, TaskHistory and derive_request are also doubles. The original GitHub OperationsStore and actual Core reader DID NOT execute. This is real DB path/API-boundary synthetic testing, NOT a full production or owner-issued acceptance test. Original G9 7 and actual P02-A–E NOT_RUN. Do not count repeated 20 as unique. All decisions remain HOLD and no dispatch/commit/retry permissions result.

## Next exact tests
Use existing ORG runtime source package `integration/mi03-gate03-org-runtime-closure-01` (owner selected, 4/4 packaging smoke) in a complete separate checkout. Compare its original ORG-05R3/durable_ops.py blob to assignment candidate blob 619fe224c05d7f7f7efe998583e4730cb2cb4d3e. Owner must approve controlled extension and fix any overlap before candidate transfer. Run original OperationsStore.initialize_ops/record/append_proposal/_history plus assignment wrapper on pinned fresh SQLite file; then actual inspect_research_slice with original shared T1 cursor, Core Member, LogIntent and D4 Request, no injected booleans. Run actual P02-A–E and G9 seven original; IAM registry/role and protected COMMIT independently HOLD.

No main/product-dev source promotion, new CI, PG, credentials, grants or production effects. On failure preserve journal/claim and original checkout; no retry by reset. Governance-only changes revert using reviewed inverse commit.

## Portable package rerun
Latest ZIP SHA256: `3ca547b766d94d61fba7df65268136dcb8ef53a18234cce1082b9a35eb2cec6b`. Script SHA256: `bf4fcd7619e9bb37f1a553c8c10f57f75df932b0d468b159029cd429535fd17c`. Log SHA256: `26f51d7d400121a046aea1b35a92bdaf6cc8bd38063e6bcd894ded7c7868bd1f`. Relative sibling folder fix; same 16/16 replay repeated, no new test count. Supersedes old artifact hashes.
