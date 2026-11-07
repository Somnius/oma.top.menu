# Working rules for this repo

- Research and specs come before code. Do not guess causes: verify (logs, source, a test) and say what is unknown.
- Keep ROADMAP.md up to date at the end of every phase, in the same commit as the work.
- Commit as often as needed to track the work. Push once at the end of each phase.
- Commit with the repo's git identity as configured. Never override it.
- Mention of tools used to build the project stays to one short line in the README credits and NOTES.md. No "how it was made" sections.
- Credit others: the Global Menu GNOME extension by Unmade760 (see NOTES.md), and primo.global-menu, which this plugin is based on.
- Limit CPU use: `nice -n 10` for long jobs, never above 80% of the machine.
- Do not edit the owner's `~/.config/omarchy/shell.json`, install plugins on their machine, or restart their shell without telling them first.
- Ask first before anything that takes control of the desktop: moving focus, launching or closing apps, switching workspaces. A test window that has keyboard focus receives whatever the owner is typing, so warn first, keep it short, and restore focus right after.
- Never create virtual input devices (uinput, evdev) or inject pointer or keyboard events to test something. Ask the owner to perform the gesture while a watcher logs state.
- Hyprland with a Lua config takes Lua dispatchers, for example `hyprctl dispatch 'hl.dsp.focus({ window = "address:0x..." })'`.
- If the shell's plugin hot-reload does not fire (it relies on inotify watches), run `omarchy restart shell` after copying files into `~/.config/omarchy/plugins/<id>/` and check that exactly one bridge process is running.
- Do not submit to the Omarchy marketplace, or open any issue on its repository, until the owner says so. Preparing and dry-running is fine.
- Test `bin/oma-top-menu-hypr-input` only with both `HOME` and `XDG_CONFIG_HOME` pointed at a temp directory (the owner's shell may export `XDG_CONFIG_HOME`).
- Keep working files (downloads, review evidence, test scripts, screenshots, logs) in the gitignored `.work/` folder, not in `/tmp`, so a reboot does not lose them.
- Screenshots: capture only the panel or bar region, validate the crop before looking at it, delete full-screen captures right away, and never commit an image that shows anything personal.
