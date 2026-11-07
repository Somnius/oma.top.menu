# Roadmap

Updated at the end of every phase. One push per phase.

| Phase | What | Status |
|---|---|---|
| 0 | Research: catalog scan, GNOME extension, primo.global-menu review | done (2026-11-07) |
| 1 | Re-test primo.global-menu with the system Python | done (2026-11-07), see [phase 1 notes](docs/phase-1-primo-test.md): daemon runs, but only fallback menus in 7 apps; why no real menus is unknown |
| 1b | Diagnose extraction | done (2026-11-07), see [diagnosis](docs/phase-1b-diagnosis.md): menus exist in AT-SPI; Floorp works, Kotatogram fixed by a name-match patch in `plugin/`; LibreOffice and cost still open |
| 2a | Marketplace readiness plan, reviewed ([plan](docs/phase-2-plan.md), [guidelines](docs/marketplace-guidelines.md)) | done (2026-11-07), local, not pushed yet |
| 2b | Restructure to repo root, new unique id, plugin starts/stops the daemon itself (no systemd, symlinks or environment.d), README install/removal/deps, run `omarchy plugin validate` + `qmllint` | todo |
| 2c | Test the bar widget live: with Lef's go-ahead, back up and edit `shell.json` (menu widget left, workspaces right) | todo |
| 3 | Fork decision: leaning to fork (`plugin/` already patched); add a shortcut-profile fallback for apps without a menu bar | in progress |
| 4 | Build/fork, package as an Omarchy plugin with the daemon unit installed | todo |
| 5 | List on plugins.omarchy.org, release | todo |

## Checklist
- [ ] Ask Lef before moving focus, launching apps or other desktop control
- [ ] README tech-stack pills (Lef supplies them)
- [x] Licence: root is GPL-2.0 because primo's repo ships GPL-2.0 (its catalog entry says MIT)
- [ ] Check licence and format of the GNOME extension's shortcut profiles before reusing anything
- [ ] Credit primo.global-menu (PrimoGameStudio) if we fork it
- [ ] Keep the credit to Unmade760 in the README and listing
