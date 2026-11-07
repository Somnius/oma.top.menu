# Omarchy marketplace guidelines we must follow

Source: https://plugins.omarchy.org/publish.html and /develop.html (read in full, 2026-11-07). The official reference is the Omarchy Quattro plugin docs; the marketplace repo is github.com/omacom/omarchy-plugin-marketplace.

## Listing requirements
- Public GitHub repository.
- Valid `manifest.json` in the repository root. Required fields: schemaVersion, id, name, version (max 64 chars), author, description, kinds, entryPoints.
- README and a license.
- Safe install and removal.
- Optional preview image (optimised by the marketplace).
- Submit through the issue form with repo link, category and tags. Automated validation checks the current commit, then a maintainer approves.
- The marketplace validates listings, not plugin security. Plugins run unsandboxed in the shared Omarchy shell process.

## Rules from the development guide
- Kinds: bar-widget (`BarWidget.qml`), panel, overlay, menu, service (`Service.qml`, headless singleton), bar. Entry points are safe relative paths.
- A bar widget loads its panel internally; do not add a second kind for a nested panel. Keep the same `moduleName` in both files.
- Third-party ids cannot start with `omarchy.`. Choose a permanent namespaced id before publishing.
- No symlinks inside the plugin folder.
- Never start a second Quickshell process for a plugin.
- Validate with `omarchy plugin validate <dir>` and `qmllint -I "$OMARCHY_PATH/shell" <qml files>`.
- Check with `omarchy plugin list --json`; `omarchy-shell shell rescanPlugins` forces discovery.
- Avoid unnecessary privileges; review every dependency and command.

## What this means for oma.top.menu
1. The repo root must be the plugin: `manifest.json`, QML and the daemon at the root. The current `plugin/` subfolder layout does not fit and has to move to the root before submission.
2. primo.global-menu is listed as "Manual setup" (`installAvailable: false`) because its daemon needs symlinks and a systemd unit. A listing that installs cleanly should start and stop its daemon from the plugin itself (a service kind or a Process in the widget), with no symlinks, no files outside its folder, and no systemd step.
3. primo's optional `~/.config/environment.d` a11y file and its writing of `IsEnabled` are changes outside the plugin; the AT-SPI side effect must be documented in the README and be reversible on removal.
4. Pick a namespaced id (not `omarchy.*`), e.g. `<author>.top-menu`. Not decided.
5. Licence: primo's repo ships GPL-2.0, so our fork is GPL-2.0 (root LICENSE). GPL-3.0 code from the GNOME extension cannot be mixed into GPL-2.0-only code.
6. Fill in a preview image, category and tags for the listing.
