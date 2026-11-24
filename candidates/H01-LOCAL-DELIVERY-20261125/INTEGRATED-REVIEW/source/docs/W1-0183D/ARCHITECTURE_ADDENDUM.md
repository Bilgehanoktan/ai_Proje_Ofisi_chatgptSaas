# W1-0183D — Office Camera Studio
Parent 2d2bad9906e7662a7ce673a8f263b6ed3d7d1655; branch w1/0183d-office-camera; common base 02e94c07fa8b56668b322184b95f1af2f3e76123. Other branch recovery/0185-provider-admission-contracts @ ba74dd586c6ec4cfc768ae5ceb6b364d901782cb: cumulative 16 W1 frontend paths checked, no content conflict at this pin. No merge.

## Implementation
Two additions and two replacements. Pure gallery camera projects 900×510 validated artwork into clipped viewport at 100–300% zoom; centers constrained, invalid numbers reset safely. Buttons, keyboard pan, mouse/pen drag and explicit 250% station focus use local presentation state. Existing floor/revision remount resets camera and selection. Second floor empty. No touch pinch or touch drag; mobile uses controls. Phaser, validated geometry, artwork, OfficePanel, snapshot JOIN_HOLD and domain policies unchanged. No new dependency, API, DB or contract.

## Evidence and limits
10/10 pure helper tests, TSX syntax pass, 10/10 standalone Chromium checks using compiled camera helper and existing artwork. Standalone DOM adapter is not the React component. Full Next build/typecheck/React browser NOT_RUN; no independent acceptance. Visual max zoom, step sizes and focus factor are design choices. No CI, main merge, PROD, real placement/movement/agent grant or provider calls.

## Maintenance / rollback
Inspect camera bounds and CSS image placement, floor key and pointer capture. No coordinate joins. Revert only four files; regenerate target manifest. To integrate cumulative W1 changes into newer common branch, recheck paths and apply exact slice, preserve updated Dashboard and regenerate destination manifest.
