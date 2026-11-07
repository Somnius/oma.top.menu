# Roadmap

Updated at the end of every phase. One push per phase.

| Phase | What | Status |
|---|---|---|
| 0 | Research: catalog scan, GNOME extension, primo.global-menu review | done (2026-11-07) |
| 1 | Re-test primo.global-menu with the system Python | done (2026-11-07), see [phase 1 notes](docs/phase-1-primo-test.md): daemon runs, but only fallback menus in 7 apps; why no real menus is unknown |
| 1b | Diagnose extraction | done (2026-11-07), see [diagnosis](docs/phase-1b-diagnosis.md): menus exist in AT-SPI; Floorp works, Kotatogram fixed by a name-match patch in `plugin/`; LibreOffice and cost still open |
| 2 | With Lef's go-ahead: move workspaces right and add the menu widget (primo id or fork id) on the left in `shell.json`; confirm the layout | todo |
| 3 | Fork decision: leaning to fork (`plugin/` already patched); add a shortcut-profile fallback for apps without a menu bar | in progress |
| 4 | Build/fork, package as an Omarchy plugin with the daemon unit installed | todo |
| 5 | List on plugins.omarchy.org, release | todo |

## Checklist
- [ ] Ask Lef before moving focus, launching apps or other desktop control
- [ ] README tech-stack pills (Lef supplies them)
- [ ] Check licence and format of the GNOME extension's shortcut profiles before reusing anything
- [ ] Credit primo.global-menu (PrimoGameStudio) if we fork it
- [ ] Keep the credit to Unmade760 in the README and listing
