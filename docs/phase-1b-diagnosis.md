# Phase 1b: why only fallback menus (2026-11-07)

Method: read-only. No focus changes, no window launches or closes by me. I started the test daemon (transient user unit) and stopped it afterwards.

## Findings (verified)
1. While the daemon runs, `org.a11y.Status IsEnabled` is `true`. (Earlier I only read it after stopping the daemon: `false`.) So the daemon's always-on registration works, and the a11y bus is fine.
2. AT-SPI lists 9 app accessibles, and two of them expose a real menu bar: Floorp (File, Edit, View, History, Bookmarks, Profiles, Tools, Help) and KotatogramDesktop (File, Edit, Tools, Help). Menus are available; the earlier fallback results were not caused by a broken accessibility setup.
3. Calling the bridge's own `SnapshotBuilder` directly (no focus change):
   - Floorp: `source=at-spi`, real menus. Works with unpatched primo.
   - Kotatogram: `desktop-fallback`. Cause: the AT-SPI extractor only accepts an app whose pid equals Hyprland's window pid (`discover()`, upstream bridge line about 1187). Kotatogram is sandboxed: Hyprland reports pid 11715, AT-SPI reports 11711, which is an `xdg-dbus-proxy`.
4. Other windows (cliamp, Strata, Quickshell, Orca) have no AT-SPI menu bar here, so the generic fallback is the expected result (cliamp is a terminal UI).

## Fix (in `plugin/`)
`AtspiMenuExtractor.discover()` now, when no accessible has the window's pid, falls back to a name match (`_discover_by_name`): normalised app name, at least 4 characters, substring either way, and only an accessible that actually exposes a menu bar. After the patch, Kotatogram returns `source=at-spi` with File, Edit, Tools, Help. Floorp is unchanged.

## Corrections to earlier notes
- "7 apps": the distinct apps tried were 6 (Orca, Kotatogram, Strata, cliamp, Files, LibreOffice Writer).
- A run showed `soffice` focused while the snapshot said `Foot`: an unexplained timing or attribution mismatch, not investigated.
- The first phase 1 conclusion ("why no real menus is unknown") is now answered for Kotatogram (pid mismatch) and Floorp (works). Not answered: LibreOffice Writer (it was not in the AT-SPI list while I looked, so it exposes no accessibility tree; cause not diagnosed), Files (GTK4, likely no menu bar).

## Open
- The patch is tested by calling the builder directly, not through a focused window in the running daemon and bar widget.
- Name matching could pick the wrong app when two apps have similar names (only the first one with a menu bar is taken). Not tested.
- LibreOffice accessibility, AT-SPI idle cost, and the bar widget (phase 2) remain.
