# DOC-REV-0198-UL — lifecycle source integration / W1 baseline

Pinned parents: 0197-U 0bcfd8d4cdcd8ef5f5af3af85f0b34f9b68ea841; 0196-L a7c4f417faf17959e3165193aa247815954bfa42; common 0195 9ece621baaadd160b3f90d4c8071d6a74d697604. Source commit 3e34c178796e247559259ae2733e5bdb70e633f7. User directs GitHub development now, Windows later. CEO-0174 / CEO-0179=B unchanged. Main and original branches preserved.

## What / why / where / how
21 disjoint new paths imported as exact Git blobs, including three backend product files, candidate SQL, original catalog and logs. Eight overlapping metadata files reconciled from 0197-U; both original sets archived byte-exact. 25 prerequisite Git blob pins from lifecycle BASE_PINS matched (test_base aliases resolved to product paths). Manifest union 272 entries / 273 product files; all 107 frontend blobs unchanged; no product deletions. Existing UI routes, themes, office engine and projections preserved; no new API or dependency. Lifecycle mapping is explicit D0 only, not wired into runtime or UI. See [0196-L](../0196L/ARCHITECTURE_AND_CATALOG.md) and [0197-U](../0197-U/ARCHITECTURE_AND_CATALOG.md).

Windows runner on this branch pins new manifest and fifth candidate SQL fixture so SQLite lifecycle tests can find it. Launcher requires explicitly reviewed new lock fingerprint via --approve; previous 0197 digest is not approval for new manifest. Windows execution deferred; no new dependency pins.

## Interfaces / W1 next
0196-L verifies immutable admission and reservation links, same-holder lease/heartbeat renewal and D0 local terminal failure with zero recognized cost; no success, cancel, takeover, external effect or canonical authority. Model Gateway binding still requires persisted admission/lease/reservation validation. W1 next: implement a read-only D0 lifecycle projection with explicit scope/revision/causal readback and HOLD, then connect CEO and Office through strict shared schema/parser; preserve STATIC_ONLY geometry JOIN_HOLD, never infer active agents or move avatars from historical samples. Skill/Tool and Memory integration remain independent; no provider calls. No live runtime binding in this turn.

## Evidence / rollback
Historical 26 new +79 regressions and 10 PG skips are 0196-L evidence, not additive to 0195 or 0197-U. Remote source tree and manifest path/size readback PASS. Full combined SHA256/tests/build/browser, new runner preflight and PG NOT_RUN. R03, real grants, independent acceptance, CI, PROD, spend and main merge HOLD. Roll back by returning to pinned 0197-U; no migration or data change. If missing SQL, verify auxiliary blob pins; if lock mismatch, HOLD and review new inventory, never use old digest.
