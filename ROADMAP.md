# Roadmap

Updated at the end of every phase. One push per phase.

| Phase | What | Status |
|---|---|---|
| 0 | Research: catalog scan, GNOME extension, primo.global-menu review | done (2026-11-07) |
| 1 | Re-test primo.global-menu with the system Python | done (2026-11-07), see [phase 1 notes](docs/phase-1-primo-test.md): daemon runs, but only fallback menus in the 6 apps tried then; why no real menus is unknown |
| 1b | Diagnose extraction | done (2026-11-07), see [diagnosis](docs/phase-1b-diagnosis.md): menus exist in AT-SPI; Floorp works, Kotatogram fixed by a name-match patch in the repo root; LibreOffice and cost still open |
| 2a | Marketplace readiness plan, reviewed ([plan](docs/phase-2-plan.md), [guidelines](docs/marketplace-guidelines.md)) | done (2026-11-07) |
| 2b | Restructure to repo root, new id, `service` + `bar-widget`, singleton lock, status message, snapshots streamed by the service | done (2026-11-07), see [testing](docs/testing.md) |
| 2c | Live bar test | done on this machine (Floorp, Kotatogram, Omamail verified by screenshot); several monitors untested |
| 2d | Fixed: Firefox-style AT-SPI menus, titled shell windows (Omamail), stale snapshots; recommended `follow_mouse = 2` | done (2026-11-07) |
| 2e | Options icon and panel (focus behaviour, workspace position, dividers, spacing, app icon, generic menu); the icon or menu role comes from where the widget is placed | built and shown in the bar (2026-11-07); workspace move fixed after Lef's report; confirmed by Lef: follow-mouse Click, dividers, spacing, workspace Left/Middle/Right; not yet: App icon and generic-menu buttons, tray drawer, several monitors | 
| 2f | Multi-monitor menus (per-monitor window planning, event-driven, per-window cache, frame matching), removal-clean design (state in the runtime dir, focus behaviour as a widget setting, uninstall helper), internals and actions docs | done (2026-11-07), tested with a virtual monitor and a real removal; see docs/compatibility.md |
| 2g | Position lock, GitHub button and creator note, recording documented (docs/moving-the-menu.md), options IPC command | done (2026-11-07); right-click = editor, left-click on the icon = preview, Restart service moved to the top; lock redesigned as a shield above the bar's drag handler (no snap-back), hand-tested by Lef; second Floorp window and Chromium tests done; GitHub button click and a real mouse drag against the lock not yet confirmed by Lef |
| 2h | Plain-text hardening (every Text, sanitized and bounded snapshots, argument-list launches), translations (English catalog), rebuild of lazy menus after a click, history rewritten to remove old screenshots | done (2026-11-07); lazy-menu rebuild unit-tested, not yet seen live |
| 2i | Marketplace dry run with the marketplace's own scripts (commit 56481dc): validation passes; security baseline `review-required`, 0 findings, one capability (`installer`: the optional uninstall helper) | done; submission text drafted, NOT posted (waiting for Lef) |
| 3 | Fork decision: forked from primo.global-menu | done |
| 4 | Own shortcut-profile fallback for apps with no menu bar and for lazy Firefox menus (written here; nothing is taken from the GNOME extension, whose licence therefore does not apply) | not started |
| 5 | List on plugins.omarchy.org, release | waiting for Lef's go (text drafted in .work/drafts) |

## Checklist
- [ ] Marketplace submission only when Lef says so (he wants it polished first)
- [ ] Ask Lef before moving focus, launching apps or other desktop control
- [ ] README tech-stack pills (Lef supplies them)
- [x] Licence: root is GPL-2.0 because primo's repo ships GPL-2.0 (its catalog entry says MIT)
- [x] GNOME extension: inspiration only, no code or data copied, so its GPL-3.0 does not apply (Lef, 2026-11-07)
- [ ] Credit primo.global-menu (PrimoGameStudio) if we fork it
- [ ] Keep the credit to Unmade760 in the README and listing
