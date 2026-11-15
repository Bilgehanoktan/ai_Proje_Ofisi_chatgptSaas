# W1-0183B — Isometric Office Gallery
Parent e885fd51e3cc013ded11307fe6abd42f4b6ed7ee; isolated W1 branch w1/0183b-office-gallery. Checked target paths against 0184 head 60c08053169b83c383019f5e34aace6cd7ba669b; no conflict at read time. Prior W1 Workflow Studio retained. Other chat's branch not modified or merged.

## Product changes
Four new files, one replacement. Gallery uses existing validated 6x6 demo floor and renders deterministic SVG art with room surfaces, decorative partial walls/window bands, desks, monitors, chair blocks and role-initial badges. Local station selection highlights the art and shows the room; floor/revision key resets selection. Second floor remains unoccupied. No agent instance, movement, collision, door routing or snapshot coordinate join. OfficeScene (Phaser) unchanged; old static fallback explicitly historical. Snapshot station list separate. JOIN_HOLD retained.

## Boundaries and verification
CEO-0174 and CEO-0179=B; no new dependencies, runtime authority, API, DB, contract changes, CI, main merge, external effects or PROD. 8/8 artwork helper tests, 8/8 previous workflow regression, 3/3 TS/TSX syntax-only, 7/7 standalone preview browser checks. Chromium installed executable; file:// blocked; page.set_content used for standalone HTML. No full Next build, current React/browser or product typecheck. Mobile canvas labels are small; text buttons and context remain available; zoom/pan and full accessibility/contrast review outstanding. Decorative furniture style, colors and geometry are UI decisions only. No independent acceptance.

## Maintenance and rollback
Check geometry guard and selected floor/revision, then generated SVG/data URI/CSP. Unknown or invalid geometry -> HOLD/fallback. Do not infer physical walls or real agents from art. Revert only five product paths and rebuild target manifest; when integrating with newer common base, compare exact paths and regenerate manifest against that base. See catalog/scope/evidence.
