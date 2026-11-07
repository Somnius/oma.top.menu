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
  readonly property string monitorsText: {
    if (!root.rec) return "Waiting for a window"
    if (!root.rec.monitors) return "Showing " + root.rec.appName + " (" + root.rec.source + ")"
    var lines = []
    for (var name in root.rec.monitors) {
      var snap = root.rec.monitors[name]
      lines.push((name || "screen") + ": " + (snap ? snap.appName + " (" + snap.source + ")" : "no window"))
    }
    return lines.join("\n")
  }

  property string followMouse: ""
  property string workspaceSection: ""
  property int menuLeftIndex: -1
  property int workspaceIndex: -1
  property string note: ""
  // "edit" is the full settings panel (right-click); "preview" is the small
  // read-only summary shown by a left click on the options icon.
  property string mode: "edit"

  function open() { root.controller.show(); root.refresh() }
  function openEdit() {
    if (root.opened && root.mode === "edit") { root.close(); return }
    root.mode = "edit"
    root.open()
  }
  function openPreview() {
    if (root.opened && root.mode === "preview") { root.close(); return }
    root.mode = "preview"
    root.open()
  }

  readonly property string followLabel: {
    var v = String(root.setting("followMouse", ""))
    return v === "1" ? "Hover" : (v === "2" ? "Click" : (v === "0" ? "Off" : "System (your Hyprland setting)"))
  }
  readonly property string serviceLine: root.menuService
    ? (root.menuService.statusState === "error" ? root.menuService.statusMessage : "Menu service: running")
    : "Menu service: not available"
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

  Process {
    id: mover
    property string targetSection: ""
    stderr: StdioCollector { waitForEnd: true; onStreamFinished: if (text.trim() !== "") root.note = text.trim() }
    onExited: function(exitCode) {
      if (exitCode === 0) {
        root.workspaceSection = mover.targetSection
        root.note = "Workspace numbers moved."
      }
    }
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.hostWidget || root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(root.mode === "edit" ? 300 : 260))
    contentHeight: panel.fittedContentHeight(root.mode === "edit" ? content.implicitHeight : previewContent.implicitHeight)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      Column {
        id: content
        visible: root.mode === "edit"
        width: parent.width
        spacing: Style.space(8)

        Text {
          textFormat: Text.PlainText
          width: parent.width
          text: "Oma Top Menu"
          color: root.barForeground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.subtitle
          font.bold: true
        }
        Row {
          width: parent.width
          spacing: Style.space(8)
          Text {
            width: parent.width - restartButton.width - parent.spacing
            anchors.verticalCenter: parent.verticalCenter
            wrapMode: Text.WordWrap
            textFormat: Text.PlainText
            color: root.menuService && root.menuService.statusState === "error" ? root.barForeground : Qt.darker(root.barForeground, 1.3)
            font.family: root.bar ? root.bar.fontFamily : Style.font.family
            font.pixelSize: Style.font.caption
            text: root.serviceLine
          }
          Button {
            id: restartButton
            text: "Restart service"
            bordered: true
            tooltipText: "Restart the menu service if the menus stop following your windows"
            onClicked: { if (root.menuService && typeof root.menuService.restart === "function") root.menuService.restart() }
          }
        }
        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          textFormat: Text.PlainText
          color: Qt.darker(root.barForeground, 1.3)
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: root.monitorsText
        }

        PanelSectionHeader { text: "Focus behaviour"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "system", label: "System" }, { value: "1", label: "Hover" }, { value: "2", label: "Click" }, { value: "0", label: "Off" }]
          value: (/^[0-3]$/.test(String(root.setting("followMouse", "")))) ? String(root.setting("followMouse", "")) : "system"
          onChanged: function(v) {
            var chosen = v === "system" ? "" : v
            root.persist({ followMouse: chosen })
            if (root.menuService && typeof root.menuService.setFollowMouse === "function")
              root.menuService.setFollowMouse(chosen)
            root.note = chosen === "" ? "Your own Hyprland setting applies from the next Hyprland reload." : ""
          }
        }
        Text {
          textFormat: Text.PlainText
          width: parent.width
          wrapMode: Text.WordWrap
          color: Qt.darker(root.barForeground, 1.3)
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: "Hover moves focus as the pointer crosses windows, so a menu changes on the way to the bar. Click keeps the menu of the window you clicked. Kept in this widget's settings and applied by the plugin (nothing is written to your Hyprland files); if you remove the plugin, your own setting returns at the next Hyprland reload."
        }

        PanelSectionHeader { text: "Workspace numbers"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "left", label: "Left" }, { value: "center", label: "Middle" }, { value: "right", label: "Right" }]
          value: root.workspaceSection
          onChanged: function(v) { root.moveWorkspaces(v) }
        }

        PanelSectionHeader { text: "Position"; foreground: root.barForeground }
        ButtonGroup {
          options: [{ value: "free", label: "Free" }, { value: "locked", label: "Locked" }]
          value: root.setting("locked", false) === true ? "locked" : "free"
          onChanged: function(v) { root.persist({ locked: v === "locked" }) }
        }
        Text {
          textFormat: Text.PlainText
          width: parent.width
          wrapMode: Text.WordWrap
          color: Qt.darker(root.barForeground, 1.3)
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: "Locked: the mouse cannot drag the menu out of its place (it shows a not-allowed cursor). Clicks, hover and right-click work as usual. Omarchy's own commands and the bar editor can still move it."
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
          textFormat: Text.PlainText
          visible: root.note !== ""
          width: parent.width
          wrapMode: Text.WordWrap
          color: root.barForeground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: root.note
        }

        PanelSeparator {}

        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          textFormat: Text.PlainText
          color: Qt.darker(root.barForeground, 1.3)
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: "Oma Top Menu, made by Lef (Somnius). Free software, GPL-2.0."
        }
        Button {
          text: "GitHub: Somnius/oma.top.menu"
          bordered: true
          onClicked: Quickshell.execDetached(["xdg-open", "https://github.com/Somnius/oma.top.menu"])
        }
      }

      // Left click on the options icon: a read-only summary, with a pointer to the editor.
      Column {
        id: previewContent
        visible: root.mode === "preview"
        width: parent.width
        spacing: Style.space(6)

        Text {
          width: parent.width
          textFormat: Text.PlainText
          text: "Oma Top Menu"
          color: root.barForeground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.subtitle
          font.bold: true
        }
        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          textFormat: Text.PlainText
          color: Qt.darker(root.barForeground, 1.3)
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: root.serviceLine + "\n" + root.monitorsText
        }
        Repeater {
          model: [
            { name: "Focus behaviour", value: root.followLabel },
            { name: "Workspace numbers", value: root.workspaceSection === "center" ? "Middle" : (root.workspaceSection === "right" ? "Right" : (root.workspaceSection === "left" ? "Left, before the menu" : (root.workspaceSection === "left-after" ? "Left, after the menu" : "-"))) },
            { name: "Position", value: root.setting("locked", false) === true ? "Locked" : "Free" },
            { name: "Dividers", value: root.setting("dividers", false) === true ? "Shown" : "Hidden" },
            { name: "Spacing", value: String(root.setting("spacing", "normal")).charAt(0).toUpperCase() + String(root.setting("spacing", "normal")).slice(1) },
            { name: "App icon", value: root.setting("showAppIcon", true) === false ? "Hidden" : "Shown" },
            { name: "Apps with no menu", value: root.setting("hideGeneric", false) === true ? "Nothing" : "Generic menu" }
          ]
          delegate: Row {
            required property var modelData
            width: previewContent.width
            spacing: Style.space(6)
            Text {
              width: Math.round(parent.width * 0.55)
              textFormat: Text.PlainText
              text: modelData.name
              color: Qt.darker(root.barForeground, 1.3)
              font.family: root.bar ? root.bar.fontFamily : Style.font.family
              font.pixelSize: Style.font.caption
            }
            Text {
              width: parent.width - Math.round(parent.width * 0.55) - parent.spacing
              wrapMode: Text.WordWrap
              textFormat: Text.PlainText
              text: modelData.value
              color: root.barForeground
              font.family: root.bar ? root.bar.fontFamily : Style.font.family
              font.pixelSize: Style.font.caption
              font.bold: true
            }
          }
        }
        PanelSeparator {}
        Text {
          width: parent.width
          wrapMode: Text.WordWrap
          textFormat: Text.PlainText
          color: root.barForeground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.caption
          text: "Right-click the icon to edit these settings."
        }
      }
    }
  }
}
