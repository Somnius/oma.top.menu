# Notes

## Inspiration and credit
Oma Top Menu (`oma.top.menu`) takes its idea from the **Global Menu GNOME extension** by **Unmade760**
(https://github.com/Unmade760/orbit-global-menu, GPL-3.0). The extension puts the focused app's menus
in the top panel, and builds menus from per-app keyboard-shortcut profiles, with an optional companion
daemon that passes through an app's real menu.

Keep this credit in the README and in any release notes or marketplace listing.

- If we reuse any of its code or shortcut profiles, the GPL-3.0 licence applies. Check the licence and the
  profile format first (not done yet).
- The credit goes to the extension's author, not to the news article that covered it.

## Later
- README tech-stack pills: Lef will supply them. Add them when they arrive. Tracked in ROADMAP.md.
- primo.global-menu (PrimoGameStudio) is the closest existing Omarchy plugin. Credit it too: we fork it.
- Licence: primo's repo ships the GPL-2.0 text (GitHub also reports GPL-2.0) although its manifest and the marketplace catalog say MIT. Our fork is a derivative, so the repo is GPL-2.0 (`manifest.json` says `GPL-2.0-only`; primo's source files carry no version header, so "only" is the conservative reading). Do not mix in GPL-3.0 code (the GNOME extension's profiles) without a licence decision.

## Tools
Built with Claude Code. JEV (TypeSafe) was used to classify the marketplace catalog; Lef OK'd mentioning both (2026-11-07).
