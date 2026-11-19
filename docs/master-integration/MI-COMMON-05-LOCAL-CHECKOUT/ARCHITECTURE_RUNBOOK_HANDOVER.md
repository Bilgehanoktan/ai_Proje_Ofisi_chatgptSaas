# MI-COMMON-05 — full Git tree ZIP verification and source handover

**Intent:** User approved running local source transfer on their own Windows PC. Existing `MI-COMMON-04-PINNED-RECOVERY/pinned_source_recovery.py` previously fetched ~145 distinct blobs through `api.github.com`, which can hit the unauthenticated 60 requests/hour cap. This addition does not replace the original helper: it obtains a single immutable commit ZIP, validates the **entire Git tree object SHA** as independently recorded at source commit, then calls the original exact helper in offline mode for immutable 114+55 staging.

## Exact source and symbols

- `mi05_verified_local_checkout.py`: `read_archive` checks ZIP member paths, symlink modes, duplication and size budget; `tree_sha` computes Git tree SHA-1 recursively using canonical `100644` file blobs and `40000` subtrees; `seed_cache` checks pinned raw rows including optional SHA256 and preserves historical overlay paths; `run` verifies source and atomically renames a fresh new `.partial` checkout; `main` reports HOLD or `SOURCE_RECOVERED_TESTS_NOT_RUN`.
- Exact commit `87272b6aebd1ce4b26d3a789b2ea75e4310cf60a`; root Git tree `187f652f1b1ff8604981833f634c4531a33f8a47`, 1,953 100644 files / 22,342,956 bytes. No symlink, submodules or executable files in the recorded source tree.
- Product manifest blob `03af243e8683f92c5d9c0b24e90b70d2bd6af29f`; original pin locks `fb1a73c86eda928409c371359056e79ef43665e4` Model and `223f6fbd28cf4c428c07eb60dda4a36f644fa58c` Core; existing helper blob `70c9c0970632834a2c4ba9cd4e4d718bfc14c2b4`.
- `POWERSHELL_KOPYALA_YAPISTIR.txt`: paste only; no execution policy bypass or administrator privilege. Download static ZIP from this conversation to `Downloads`; new C:\AIOS\MI05_<timestamp> stage. Alternative user-selected drive path allowed. No package install.

## Tests actually performed

`python -m unittest -v test_mi05_verified_local_checkout.py`: 12/12 actual isolated helper controls on Python 3.13.5, no failures/skips. Independent `git write-tree` reference compared with internal Git hashing, valid ZIP verification, wrong root/tree, traversal, symlink, duplicate, oversize, overwrite/disk guards, synthetic 114/55 distinct stage and two historic blob alternatives. Real 1953-file ZIP was **not downloaded in this container**. This test set is not Model344 or Core29.

## Deployment / diagnostics

User PC must have Python >=3.10 (3.13.5 needed for later original 344) and an HTTPS route to github.com/codeload.github.com. ZIP download can be performed manually via GitHub signed-in browser and supplied using `--archive` when private; even then full SHA proof is required. Minimum free disk 130 MB. On failure `.partial/TRANSFER_HOLD.json` is preserved, never mark complete; do not reuse stage with different source pin. Stage output roots and `TRANSFER_REPORT.json` are user's proof. No GitHub credential is requested in chat.

`GIT_TREE_PIN_MISMATCH`: ZIP metadata or file bytes differ from pinned Git tree; refuse without repinning. `ARCHIVE_SCOPE_HOLD`: not 1953 files / 22,342,956 bytes; inspect exact commit source and URL. `PINNED_FILE_CHANGED`: source lock unexpected; do not overwrite with historical candidate. `INSUFFICIENT_DISK_SPACE_130MB`: choose another drive before retry. `ARCHIVE_DOWNLOAD_FAILED`: access/network or private repository; use manually downloaded exact-commit ZIP, not an arbitrary branch archive. `HISTORICAL_OVERLAY_*`: preserve two known alternate core sources, owner review if pin changes.

## Next P0 gates and rollback

After user submits success report, run original `run_combined.py` 344 using exact Python/SQLite/Cryptography environment; historical Core 29 using reviewed direct/transitive dependency pins, never unpinned; then W8 `w8_mi_common_02.py` fresh review/immutable npm lock, complete Next build and browser. Existing exact ORG31/Skill41/projection25 selected 97 PASS is historical for that turn, not repeated in this one. All protected COMMIT, real IAM/provider/DB grants, CI/main/PROD and IV still HOLD. `product-dev` unchanged. Rollback only the new local staging folder or normal revert of helper-only source commit, never force push.
