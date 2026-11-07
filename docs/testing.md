# How the lifecycle is tested

The daemon runs as a child of the shell's service. These tests answer "does it die with the service, and is there only one".

## Without touching the desktop (done 2026-11-07, all passed)
Run from the repo, with `/usr/bin/python3 bin/omarchy-global-menu-bridge`:
1. Single instance: start one daemon, start a second one. Expected: the second prints "another oma-top-menu daemon is running; exiting" and exits 0 without touching AT-SPI. Result: as expected.
2. Stops on SIGTERM and cleans up: `kill -TERM` the daemon. Expected: it exits and `~/.local/state/omarchy/oma-top-menu` is empty. Result: stopped, directory empty.
3. Exits with its parent: start it from a `bash -c` that is then killed with `kill -9`. Expected: the daemon exits within about 2 s. Result: it exited.
4. `org.a11y.Status IsEnabled` returns to false after the daemon is gone (read once after the tests: false).

## With the plugin loaded in the shell (needs shell.json to list the plugin)
5. Install, then check `omarchy plugin list --json` shows it enabled with kinds `service` and `bar-widget`.
6. Exactly one bridge process exists with one monitor, and still one with several (the bar makes one widget per screen; the service is one).
7. Remove the widget from the bar layout: the bridge process should stop. Re-add it: it should start again.
8. `omarchy-shell shell rescanPlugins` and a shell restart: no orphan bridge process afterwards.
9. Dependency message: make the check fail (for example point `python` at an interpreter without `gi` in a test copy) and confirm the bar shows the message instead of staying blank.
