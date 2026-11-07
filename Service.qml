import QtQuick
import Quickshell
import Quickshell.Io

// Owns the single menu bridge daemon (one per shell, not one per screen).
// Checks python-gobject and AT-SPI first and publishes the result in
// status.json, so the bar widget can say what is wrong instead of staying blank.
Item {
  id: root
  visible: false

  readonly property string python: "/usr/bin/python3"
  readonly property string bridgePath: String(Qt.resolvedUrl("bin/omarchy-global-menu-bridge")).replace(/^file:\/\//, "")
  readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/omarchy/oma-top-menu"
  property int failures: 0

  function writeStatus(state, message) {
    statusFile.setText(JSON.stringify({ state: state, message: message }))
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
    command: [root.python, root.bridgePath, "run"]
    onExited: function(exitCode) {
      if (exitCode === 0) return
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
