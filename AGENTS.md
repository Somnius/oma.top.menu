# Working rules for this repo

- Research and specs come before code. Do not guess causes: verify (logs, source, a test) and say what is unknown.
- Keep ROADMAP.md up to date at the end of every phase, in the same commit as the work.
- Commit as often as needed to track the work. Push once at the end of each phase.
- Commit with the repo's git identity as configured. Never override it.
- Lef allowed a short mention of the tools used (Claude Code, JEV) in README and NOTES. Do not add more than that, no "how it was made" sections.
- Credit others: the Global Menu GNOME extension by Unmade760 (see NOTES.md), and primo.global-menu if forked.
- Limit CPU use: nice -n 10 for long jobs, never above 80% of the machine.
- Do not edit `~/.config/omarchy/shell.json` or install plugins without Lef's go-ahead.
- Ask first before anything that takes control of the desktop: moving focus, launching or closing apps, switching workspaces.
- Hyprland here takes Lua dispatch syntax, e.g. `hyprctl dispatch 'hl.dsp.focus({ window = "address:0x..." })'`.
- On this machine the shell's plugin hot-reload does not fire (inotify watches are used up), so after copying files into `~/.config/omarchy/plugins/<id>/` run `omarchy restart shell` (tell Lef first) and check there is exactly one bridge process.
- Do not submit to the Omarchy marketplace (or open any issue on its repo) until Lef says so. Prepare and dry-run only.
