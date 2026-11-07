import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

// Owns the single menu bridge daemon (one per shell, not one per screen).
// Checks python-gobject and AT-SPI first and publishes the result in
// status.json, so the bar widget can say what is wrong instead of staying blank.
Item {
  id: root
  visible: false

  readonly property string python: "/usr/bin/python3"
  readonly property string bridgePath: String(Qt.resolvedUrl("bin/omarchy-global-menu-bridge")).replace(/^file:\/\//, "")
  readonly property string stateDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/oma-top-menu"
  property int failures: 0
  property double startedAt: 0
  property bool manualRestart: false
  // Hyprland focus behaviour (0-3), or "" to leave the user's own config alone.
  // It lives in the widget settings in shell.json, so removing the plugin removes it.
  property string followMouse: ""

  function setFollowMouse(value) {
    var v = String(value === undefined || value === null ? "" : value)
    if (v !== "" && !/^[0-3]$/.test(v)) v = ""
    if (v === root.followMouse) return
    root.followMouse = v
    root.applyFollowMouse()
  }

  property bool followPending: false

  function applyFollowMouse() {
    if (root.followMouse === "") return
    if (followProcess.running) { root.followPending = true; return }
    followProcess.command = ["hyprctl", "eval", "hl.config({ input = { follow_mouse = " + root.followMouse + " } })"]
    followProcess.running = true
  }

  // ---- Lock position -------------------------------------------------------
  // The bar has no lock and no per-widget veto (its drag handler sits above every
  // widget), so the lock is done here: while it is on, the shell.json layout is
  // read every 1.5 s and, if the menu was dragged out of its place in the left
  // section, it is put back with Omarchy's own `omarchy bar move`.
  readonly property string pluginId: "com.lefteros.somnius.oma-top-menu"
  readonly property string layoutPath: (Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config") + "/omarchy/shell.json"
  property bool locked: false
  property int lockIndex: -1
  property bool lockCapture: false
  property int restores: 0
  property bool lockPaused: false                    // true while the panel is moving other widgets
  readonly property bool lockInert: root.locked && root.lockIndex < 0   // menu is not in the left section
  signal lockGaveUp()

  // The panel moves the workspace numbers: do not mistake that for a drag.
  function pauseLock() { root.lockPaused = true }
  function resumeLock() { root.lockPaused = false; if (root.locked) root.recaptureLock() }

  function setLocked(value) {
    var v = value === true
    if (v === root.locked) return
    root.locked = v
    root.restores = 0
    if (v) root.recaptureLock()
  }

  // Remember where the menu is now (also called after the panel moves the workspace numbers).
  function recaptureLock() {
    root.lockCapture = true
    layoutFile.reload()
  }

  function leftIndexIn(text) {
    var config
    try { config = JSON.parse(text) } catch (e) { return -2 }
    var left = config && config.bar && config.bar.layout && config.bar.layout.left ? config.bar.layout.left : []
    for (var i = 0; i < left.length; i++) {
      var entry = left[i]
      if ((entry && typeof entry === "object" ? entry.id : entry) === root.pluginId) return i
    }
    return -1
  }

  function checkLayout(text) {
    var index = root.leftIndexIn(text)
    if (index === -2) return                       // unreadable right now: do nothing
    if (root.lockCapture) { root.lockCapture = false; root.lockIndex = index; return }
    if (root.lockPaused) return
    if (!root.locked || root.lockIndex < 0 || index === root.lockIndex) { root.restores = 0; return }
    if (restoreProcess.running) return
    if (root.restores >= 5) {                      // something keeps moving it: stop fighting
      root.locked = false
      root.lockGaveUp()                              // the widget stores locked=false too
      root.writeStatus("error", "Oma Top Menu: the position lock was switched off because the menu kept being moved")
      return
    }
    root.restores += 1
    restoreProcess.command = ["omarchy", "bar", "move", root.pluginId, "--section", "left", "--index", String(root.lockIndex)]
    restoreProcess.running = true
  }

  Process { id: restoreProcess }

  FileView {
    id: layoutFile
    path: root.layoutPath
    printErrors: false
    onLoaded: root.checkLayout(text())
  }

  Timer {
    interval: 1500
    repeat: true
    running: root.locked
    onTriggered: layoutFile.reload()
  }

  Process {
    id: followProcess
    onExited: function(exitCode) {
      if (root.followPending) { root.followPending = false; root.applyFollowMouse() }
    }
  }

  // One IPC handler for the whole shell (every monitor's widget would
  // otherwise register the same target); the focused monitor's strip answers.
  signal ipcRequest(string action)
  IpcHandler {
    target: "com.lefteros.somnius.oma-top-menu"

    function open(): void { root.ipcRequest("open") }
    function close(): void { root.ipcRequest("close") }
    function toggle(): void { root.ipcRequest("toggle") }
    function options(): void { root.ipcRequest("options") }
  }

  // A Hyprland config reload resets the value, so apply it again.
  Connections {
    target: Hyprland
    function onRawEvent(event) {
      if (event && String(event.name) === "configreloaded") root.applyFollowMouse()
    }
  }
  // Latest menu snapshot, streamed by the daemon; every per-screen widget reads this.
  property var record: null
  property string statusState: ""
  property string statusMessage: ""

  function writeStatus(state, message) {
    root.statusState = state
    root.statusMessage = message
    statusFile.setText(JSON.stringify({ state: state, message: message }))
  }

  function restart() {
    root.failures = 0
    root.manualRestart = true
    daemon.running = false
    restartTimer.restart()
  }

  Component.onCompleted: prepare.running = true

  Process {
    id: prepare
    command: ["mkdir", "-p", "-m", "700", root.stateDir]
    onExited: function(exitCode) { checkDeps.running = true }
  }

  Process {
    id: checkDeps
    command: [root.python, "-c", "import gi; gi.require_version('Atspi', '2.0'); from gi.repository import Atspi"]
    onExited: function(exitCode) {
      if (exitCode === 0) {
        root.writeStatus("ok", "")
        daemon.running = true
      } else {
        root.writeStatus("error", "Oma Top Menu needs python-gobject and at-spi2-core (pacman -S python-gobject)")
      }
    }
  }

  Process {
    id: daemon
    command: [root.python, root.bridgePath, "--stream", "run"]
    stdout: SplitParser {
      onRead: function(line) {
        try {
          var parsed = JSON.parse(line)
          if (parsed && typeof parsed === "object") root.record = parsed
        } catch (e) {}
      }
    }
    onRunningChanged: { if (running) root.startedAt = Date.now() }
    // Restart after any exit (a crash, a kill, a lost lock), but give up after
    // five quick exits in a row so a broken setup does not loop forever.
    onExited: function(exitCode) {
      if (root.manualRestart) { root.manualRestart = false; return }
      if (Date.now() - root.startedAt > 10000) root.failures = 0
      root.failures += 1
      if (root.failures > 5) {
        root.writeStatus("error", "Oma Top Menu daemon keeps stopping (see: journalctl --user -b | grep oma-top-menu)")
        return
      }
      restartTimer.restart()
    }
  }

  Timer {
    id: restartTimer
    interval: 3000
    onTriggered: daemon.running = true
  }

  FileView {
    id: statusFile
    path: root.stateDir + "/status.json"
    atomicWrites: true
    printErrors: false
  }
}
