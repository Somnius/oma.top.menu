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
