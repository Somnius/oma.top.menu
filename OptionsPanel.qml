import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// Oma Top Menu options. Every change here happens only on a click, and the
// two that touch system files go through a documented command:
//   Workspace numbers -> `omarchy bar move omarchy.workspaces --section ...`
//   Focus behaviour   -> `hyprctl eval` (live) and bin/oma-top-menu-hypr-input
//                        (saved, with a backup of ~/.config/hypr/input.lua)
Panel {
  id: root
  moduleName: "com.lefteros.somnius.oma-top-menu"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  property var menuService: null

  readonly property var rec: root.menuService && root.menuService.record ? root.menuService.record : null
  readonly property string helperPath: String(Qt.resolvedUrl("bin/oma-top-menu-hypr-input")).replace(/^file:\/\//, "")

  property string followMouse: ""
  property string workspaceSection: ""
  property int menuLeftIndex: -1
  property int workspaceIndex: -1
  property string note: ""

  function open() { root.controller.show(); root.refresh() }
  function close() { root.controller.hide() }
  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.hostWidget || root, direction)
    return false
  }

  function refresh() {
    readFollow.running = true
    readSection.running = true
  }

  // Settings are shared by every instance of this widget (the bar writes one
  // entry per widget id), so the menu strip and this icon always agree.
  function persist(values) {
    var entry = { id: root.moduleName }
    for (var existing in root.settings) if (existing !== "id") entry[existing] = root.settings[existing]
    for (var key in values) entry[key] = values[key]
    root.settings = entry
    if (root.hostWidget && "settings" in root.hostWidget) root.hostWidget.settings = entry
    if (root.bar && root.bar.shell && typeof root.bar.shell.updateEntryInline === "function")
      root.bar.shell.updateEntryInline(root.moduleName, entry)
  }

  function applyFollow(value) {
    if (!/^[0-3]$/.test(String(value))) return
    root.followMouse = String(value)
    runner.command = ["hyprctl", "eval", "hl.config({ input = { follow_mouse = " + value + " } })"]
    root.note = "Applied now. Use Save to keep it after a restart."
    runner.running = true
  }

  function saveFollow() {
    if (!/^[0-3]$/.test(root.followMouse)) return
    saver.command = ["/usr/bin/python3", root.helperPath, "follow_mouse", root.followMouse]
    saver.running = true
  }

  function moveWorkspaces(section) {
    if (["left", "center", "right"].indexOf(section) < 0) return
    // Left goes just before the menu strip, middle and right go at the start
    // of their section; without an index the bar appends at the end.
    if (section === "left" && root.menuLeftIndex >= 0)
      mover.command = ["omarchy", "bar", "move", "omarchy.workspaces", "--before", root.moduleName]
    else
      mover.command = ["omarchy", "bar", "move", "omarchy.workspaces", "--section", section, "--index", "0"]
    mover.targetSection = section
    mover.running = true
  }

  Process {
    id: readFollow
    command: ["hyprctl", "getoption", "input:follow_mouse"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: { var m = text.match(/int:\s*([0-3])/); root.followMouse = m ? m[1] : "" }
    }
  }

  Process {
    id: readSection
    command: ["/usr/bin/python3", "-c",
      "import json,os\n" +
      "d=json.load(open(os.path.expanduser('~/.config/omarchy/shell.json')))\n" +
      "for s,l in d.get('bar',{}).get('layout',{}).items():\n" +
      "    for i,e in enumerate(l):\n" +
      "        n=e.get('id') if isinstance(e,dict) else e\n" +
      "        if n=='omarchy.workspaces': print('ws', s, i)\n" +
      "        if n=='" + root.moduleName + "' and s=='left': print('menu', i)\n"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var lines = text.trim().split("\n")
        root.workspaceSection = ""
        root.menuLeftIndex = -1
        for (var i = 0; i < lines.length; i++) {
          var parts = lines[i].split(" ")
          if (parts[0] === "ws") { root.workspaceSection = parts[1]; root.workspaceIndex = parseInt(parts[2]) }
          else if (parts[0] === "menu") root.menuLeftIndex = parseInt(parts[1])
        }
        // "Left" means just before the menu strip. Left but after it, or in a
        // centre sub-section, is shown accordingly so that clicking the
        // intended option is a real change.
        if (root.workspaceSection === "left" && root.menuLeftIndex >= 0 && root.workspaceIndex > root.menuLeftIndex)
          root.workspaceSection = "left-after"
        else if (root.workspaceSection.indexOf("center") === 0)
          root.workspaceSection = "center"
      }
    }
  }

  Process { id: runner }

  Process {
    id: saver
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.note = text.trim() }
    stderr: StdioCollector { waitForEnd: true; onStreamFinished: if (text.trim() !== "") root.note = text.trim() }
  }

  Process {
    id: mover
    property string targetSection: ""
    stderr: StdioCollector { waitForEnd: true; onStreamFinished: if (text.trim() !== "") root.note = text.trim() }
    onExited: function(exitCode) {
      if (exitCode === 0) { root.workspaceSection = mover.targetSection; root.note = "Workspace numbers moved." }
    }
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.hostWidget || root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(300))
    contentHeight: panel.fittedContentHeight(content.implicitHeight)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      Column {
        id: content
        width: parent.width
        spacing: Style.space(8)

        Text {
          width: parent.width
          text: "Oma Top Menu"
          color: root.barForeground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.subtitle
          font.bold: true
        }
        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          color: Qt.darker(root.barForeground, 1.3)
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: root.menuService && root.menuService.statusState === "error"
            ? root.menuService.statusMessage
            : (root.rec ? ("Showing " + root.rec.appName + " (" + root.rec.source + ")") : "Waiting for a window")
        }

        PanelSectionHeader { text: "Focus behaviour"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "1", label: "Hover" }, { value: "2", label: "Click" }, { value: "0", label: "Off" }]
          value: root.followMouse
          onChanged: function(v) { root.applyFollow(v) }
        }
        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          color: Qt.darker(root.barForeground, 1.3)
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: "Hover moves focus as the pointer crosses windows, so the menu changes on the way to the bar. Click keeps the menu of the window you clicked."
        }
        Button {
          text: "Save to ~/.config/hypr/input.lua"
          bordered: true
          onClicked: root.saveFollow()
        }

        PanelSectionHeader { text: "Workspace numbers"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "left", label: "Left" }, { value: "center", label: "Middle" }, { value: "right", label: "Right" }]
          value: root.workspaceSection
          onChanged: function(v) { root.moveWorkspaces(v) }
        }

        PanelSectionHeader { text: "Dividers"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "off", label: "Hidden" }, { value: "on", label: "Shown" }]
          value: root.setting("dividers", false) === true ? "on" : "off"
          onChanged: function(v) { root.persist({ dividers: v === "on" }) }
        }

        PanelSectionHeader { text: "Spacing"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "compact", label: "Compact" }, { value: "normal", label: "Normal" }, { value: "roomy", label: "Roomy" }]
          value: String(root.setting("spacing", "normal"))
          onChanged: function(v) { root.persist({ spacing: v }) }
        }

        PanelSectionHeader { text: "App icon"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "show", label: "Shown" }, { value: "hide", label: "Hidden" }]
          value: root.setting("showAppIcon", true) === false ? "hide" : "show"
          onChanged: function(v) { root.persist({ showAppIcon: v === "show" }) }
        }

        PanelSectionHeader { text: "Apps without a menu bar"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "show", label: "Generic menu" }, { value: "hide", label: "Nothing" }]
          value: root.setting("hideGeneric", false) === true ? "hide" : "show"
          onChanged: function(v) { root.persist({ hideGeneric: v === "hide" }) }
        }

        Text {
          visible: root.note !== ""
          width: parent.width
          wrapMode: Text.WordWrap
          color: root.barForeground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: root.note
        }

        Button {
          text: "Restart menu service"
          bordered: true
          onClicked: { if (root.menuService && typeof root.menuService.restart === "function") root.menuService.restart() }
        }
      }
    }
  }
}
