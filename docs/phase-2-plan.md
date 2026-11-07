# Phase 2 plan: make it marketplace-ready (draft for review)

Sources: docs/marketplace-guidelines.md plus omacom/omarchy-plugin-marketplace SUBMISSION.md, VERIFICATION.md and SECURITY.md (read 2026-11-07).

## Extra rules found in the marketplace repo
- Repo root is the plugin; root README must have installation AND removal instructions; root LICENSE; document external dependencies.
- ID must be globally unique and permanent; prefer `io.github.<user>.<name>`. Not `omarchy.*`. Search the marketplace first.
- Category (one): Appearance, Desktop, Developer Tools, Hardware, Kids, Productivity, System, Widgets, Other. Tags (1-3): ai, bar, education, games, hyprland, kids, launcher, media, power-management, quickshell, security, system, vpn, workspaces.
- Checklist: "does not overwrite user configuration without explicit consent".
- An automated static security baseline scans the exact commit. `service-management` (systemd unit files, `systemctl`, `systemd-run`) is a "review capability": not a failure, but needs maintainer review and is why primo is listed as manual setup. Download-and-execute, unpinned external git, and sudoers changes are blocking findings.
- Install is `omarchy plugin add` (clones mutable HEAD). Listing is approved per exact commit; later upstream commits show "Update unverified" until re-verified.
- Preview: optional root `preview.png|jpg|jpeg|webp|avif`.
- Precedent: many "Available" bar widgets and services run helper processes (e.g. hendkai.omarchy-mercedes, jacob.omawake). I did not yet read how any of them start their helper.

## Baseline today
- `omarchy plugin validate plugin/` exits 0 (manifest id `primo.global-menu`, still primo's).
- `qmllint` exits 255 with no output on BarWidget.qml, and also on an installed known-good plugin (ilyazar.btop), so not treated as a failure; meaning unverified.
- `python-gobject` is not a dependency of Omarchy base: `pactree -r python-gobject` lists other apps (flatpak, lutris, nautilus-python...), so it must be documented as an external dependency (not verified whether Omarchy pulls it in some other way).

## Proposed design
1. Layout: `git mv` the contents of `plugin/` to the repo root so `manifest.json` is at the root. Keep primo's copyright: ship its MIT notice (our LICENSE currently only names Lef).
2. New id (permanent, unique): proposal `io.github.somnius.top-menu`. Not decided; needs Lef and a marketplace search.
3. Daemon lifecycle: the plugin starts and stops the bridge itself (a Quickshell `Process` in the bar widget or a `service` kind) with `/usr/bin/python3`; no systemd unit, no symlinks, no `environment.d`, no files outside the plugin folder and `$XDG_RUNTIME_DIR` / the state dir. Must be tested: child dies when the widget is removed, the plugin is disabled, or the shell restarts. Open: whether a manifest can declare two kinds (bar-widget + service) and whether a service runs independently of the bar position.
4. Failure visibility: if `gi`/Atspi is missing or the daemon dies, the widget shows a clear message instead of an empty bar.
5. Removal: stopping the daemon ends AT-SPI always-on (`IsEnabled` goes back to false, verified). Remove the state dir on exit. README documents both.
6. Layout move: the widget goes in the left section by default; moving `omarchy.workspaces` to the right is a `shell.json` change that the plugin must NOT do silently (checklist: no overwriting user config). Document it in the README, or offer it as an explicit user action.
7. Dev flow: sync files to `~/.config/omarchy/plugins/<id>/` (no symlinks allowed in plugin folders), `omarchy plugin validate`, `qmllint`, `omarchy-shell shell rescanPlugins`.
8. Later: shortcut-profile fallback for apps with no menu bar; check licence and format of the GNOME extension's profiles first.

## Gates that need Lef
`shell.json` edit, making the repo public, choosing the id, the marketplace submission.

## Questions for reviewers
- Is running the daemon from the plugin the right way to avoid "Manual setup", and is a `Process` child safe w.r.t. the guideline "never start a second Quickshell process"?
- Are any of the marketplace's blocking patterns or review capabilities triggered by the bridge's existing code (it uses `sh -c`, `gdbus`, `hyprctl`)?
- Anything missing in this plan?
