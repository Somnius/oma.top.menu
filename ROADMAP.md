# Roadmap

Updated at the end of every phase. One push per phase.

| Phase | What | Status |
|---|---|---|
| 0 | Research: catalog scan, GNOME extension, primo.global-menu review | done (2026-11-07) |
| 1 | Re-test primo.global-menu with the system Python; read quickshell log and `active.json`; test GTK, Qt, Electron (Ghostty if installed); click a menu item; try `/usr/bin/python3` in the unit; measure AT-SPI always-on cost | partly done (2026-11-07), see [phase 1 notes](docs/phase-1-primo-test.md): daemon runs with system Python, only fallback menus seen so far; needs restarted apps and Lef at the keyboard |
| 2 | With Lef's go-ahead: move workspaces right and add the menu widget (primo id or fork id) on the left in `shell.json`; confirm the layout | todo |
| 3 | Decide: use primo as is, or fork it as Oma Top Menu (add a shortcut-profile fallback) | todo |
| 4 | Build/fork, package as an Omarchy plugin with the daemon unit installed | todo |
| 5 | List on plugins.omarchy.org, release | todo |

## Checklist
- [ ] Ask Lef before moving focus, launching apps or other desktop control
- [ ] README tech-stack pills (Lef supplies them)
- [ ] Check licence and format of the GNOME extension's shortcut profiles before reusing anything
- [ ] Credit primo.global-menu (PrimoGameStudio) if we fork it
- [ ] Keep the credit to Unmade760 in the README and listing
