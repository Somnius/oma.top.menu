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
| 3 | Fork decision: forked from primo.global-menu; marketplace dry run (validator, id uniqueness, README deps); Firefox lazy menus | next |
| 4 | Shortcut-profile fallback for apps with no menu bar (check licence and format of the GNOME extension's profiles first) | todo |
| 5 | List on plugins.omarchy.org, release | todo |

## Checklist
- [ ] Ask Lef before moving focus, launching apps or other desktop control
- [ ] README tech-stack pills (Lef supplies them)
- [x] Licence: root is GPL-2.0 because primo's repo ships GPL-2.0 (its catalog entry says MIT)
- [ ] Check licence and format of the GNOME extension's shortcut profiles before reusing anything
- [ ] Credit primo.global-menu (PrimoGameStudio) if we fork it
- [ ] Keep the credit to Unmade760 in the README and listing
