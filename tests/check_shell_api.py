#!/usr/bin/env python3
"""Local compatibility check: does the installed Omarchy shell still provide what this plugin uses?

Run after every Omarchy update:  python3 tests/check_shell_api.py
It greps the installed shell source (default /usr/share/omarchy/shell) for each name below.
It needs Omarchy installed, so it is not part of CI.
"""
import re
import subprocess
import sys
from pathlib import Path

SHELL = Path(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/omarchy/shell")

UI_FILES = ["BarWidget", "Panel", "KeyboardPanel", "PanelKeyCatcher", "PanelSectionHeader",
            "ButtonGroup", "Button", "WidgetButton", "BorderSurface", "PanelSeparator"]
# (description, regex that must match somewhere under the shell source)
SYMBOLS = [
    ("bar requestPopout(owner)", r"function requestPopout\(\w+\)"),
    ("bar releasePopout(owner)", r"function releasePopout\(\w+\)"),
    ("bar activePopout", r"activePopout"),
    ("bar switchPanelFrom", r"switchPanelFrom"),
    ("shell serviceFor(pluginId)", r"function serviceFor\(pluginId\)"),
    ("shell updateEntryInline(moduleName, settings)", r"function updateEntryInline\((moduleName|id), settings\)"),
    ("widget fixedEdge", r"property string fixedEdge"),
    ("WidgetButton hasVisualContent", r"property bool hasVisualContent"),
    ("manifest barWidget defaults/schema", r"meta\.schema"),
    ("manifest allowMultiple", r"allowMultiple"),
    ("Hyprland.monitorFor(screen)", r"Hyprland\.monitorFor\(screen\)"),
    ("Hyprland rawEvent handler", r"function onRawEvent\(event\)"),
    ("QsWindow.window", r"QsWindow\.window"),
    ("Style.bar.iconSlot", r"iconSlot"),
    ("Style.font.caption", r"property (real|int) caption"),
    ("Color.menu.selectedText", r"selectedText"),
]
CLI = [["omarchy", "bar", "move", "--help"]]
import os
if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
    CLI.append(["hyprctl", "getoption", "input:follow_mouse"])


def main():
    bad = 0
    if not SHELL.is_dir():
        print(f"shell source not found at {SHELL}")
        return 2
    for name in UI_FILES:
        if not (SHELL / "Ui" / f"{name}.qml").exists():
            print(f"MISSING Ui/{name}.qml"); bad += 1
    text = "\n".join(p.read_text(errors="ignore") for p in SHELL.rglob("*.qml"))
    text += "\n" + "\n".join(p.read_text(errors="ignore") for p in SHELL.rglob("*.js"))
    for label, rx in SYMBOLS:
        if not re.search(rx, text):
            print(f"MISSING {label}  ({rx})"); bad += 1
    for cmd in CLI:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"CLI failed: {' '.join(cmd)}"); bad += 1
    r = subprocess.run(["omarchy", "bar", "move", "--help"], capture_output=True, text=True)
    text_help = r.stdout + r.stderr
    for flag in ("--before", "--index", "--section"):
        if flag not in text_help and flag not in subprocess.run(["omarchy-bar", "--help"], capture_output=True, text=True).stdout:
            print(f"MISSING omarchy bar move flag {flag} in --help (check manually)")
    print("omarchy:", subprocess.run(["omarchy", "version"], capture_output=True, text=True).stdout.strip())
    print("OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
