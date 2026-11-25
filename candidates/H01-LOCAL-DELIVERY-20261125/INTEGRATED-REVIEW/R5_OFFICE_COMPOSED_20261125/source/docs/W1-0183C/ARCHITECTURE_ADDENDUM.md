# W1-0183C — Smart navigation
Parent 59021b5b9913aa561f26b75cf276c8bafe12e875; isolated W1 branch w1/0183c-smart-navigation. Other branch recovery/0184-outbox-readback at 60c08053169b83c383019f5e34aace6cd7ba669b checked, no overlap in the four source paths. Other Dashboard changed; existing Navigation props and sidebar structure confirmed compatible by source review. No Dashboard or other-branch write.

## Product changes
Three additions, one replacement. The existing thirteen destinations are grouped into four sections, filtered by normalized Turkish labels/group names and English aliases. Search has AND-term matching, clear/no-result states, Ctrl/Cmd+K focus and Escape clear. Compact desktop icon rail and responsive mobile grouping, accessible names retained. No new route: Sanal Ofis remains /office, all others use unchanged callback. Local state only; no dispatch, grants, or backend/network activity. Previous Workflow Studio and Office Gallery retained.

## Verification and boundaries
8/8 standalone helper tests, TSX transpile syntax pass, PostCSS parse pass. Local TypeScript differs from pin; React/Next/Phaser unavailable. Next CSS-module scoping, React rendering, keyboard shortcut/focus and both themes/mobile are NOT_RUN in actual product. CSS :has requires supported browser; layout fallback remains wider. Group names, aliases, compact width and shortcut are presentation choices. No full build, dependency installation, independent acceptance, CI, production, or main merge.

## Maintenance and rollback
Check catalog navigation, then normalization and grouping. If search misses a menu, add reviewed display alias rather than synthetic navigation. If compact shell does not resize, inspect CSS module compilation and :has browser support. Revert exact four source paths, regenerate manifest on destination. Never overwrite another chat's updated Dashboard or tracker.
