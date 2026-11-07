# Specs (draft)

## Goal
On the Omarchy (Hyprland + Quickshell) top bar, show the focused window's application menu on the left,
and show the workspace indicators on the right.

## Requirements
1. Left bar section shows the focused app's menu items, clickable with the mouse.
2. Workspace numbers are on the right section (built-in `omarchy.workspaces`, moved in `shell.json`).
3. Apps without an exportable menu get a fallback menu (see 4).
4. Fallback: a per-app shortcut profile or a generic App/File/Edit/View/Window/Help menu.
5. Installable as an Omarchy plugin (`manifest.json` schema 1, bar widget, default section `left`).
6. No manual setup beyond what the install step does (daemon unit is installed and started for the user).

## Menu sources (cascade, first hit wins)
`org.gtk.Menus`, `com.canonical.dbusmenu`, AT-SPI, then the fallback profile.

## Open questions
- Does primo.global-menu render menus here with the system Python? (Phase 1)
- What does Ghostty expose? (not installed here yet)
- CPU/memory cost of keeping AT-SPI always on.
- Reuse of the GNOME extension's shortcut profiles: licence (GPL-3.0) and format not checked.

## Non-goals (for now)
Replacing the whole bar, other compositors, non-Omarchy setups.
