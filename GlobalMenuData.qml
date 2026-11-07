import QtQuick
import Quickshell
import Quickshell.Io

// Oma Top Menu, modified from primo.global-menu (GPL-2.0), 2026-11-07: renamed state
// directory and a status.json reader.
// Watches the bridge's snapshot of the focused window's menu. The daemon
// owns the file; this component only discovers and parses it, so any record
// that appears in the state directory is rendered, whoever wrote it.
Item {
  id: root
  visible: false

  property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/omarchy/oma-top-menu"
  property string path: root.stateDir + "/active.json"
  property var status: null
  readonly property string statusMessage: service && service.statusState !== "" ? (service.statusState === "error" ? String(service.statusMessage || "Oma Top Menu: error") : "") : (status && status.state === "error" ? String(status.message || "Oma Top Menu: error") : "")
  // The service streams snapshots (no file watch needed); the file is the fallback.
  property var service: null
  property var fileRecord: null
  readonly property var record: service && service.record ? service.record : fileRecord
  property string lastText: ""
  property string lastStatusText: ""

  readonly property var menubar: record && Array.isArray(record.menubar) ? record.menubar : []
  readonly property string appId: record ? String(record.appId || "") : ""
  readonly property string appName: record ? String(record.appName || "") : ""
  readonly property string icon: record ? String(record.icon || "") : ""
  readonly property string title: record ? String(record.title || "") : ""
  readonly property string source: record ? String(record.source || "") : ""

  FileView {
    path: root.path
    watchChanges: true
    printErrors: false
    id: activeFile
    onFileChanged: reload()
    onLoaded: root.parse(text())
    onLoadFailed: { root.lastText = ""; root.fileRecord = null }
  }

  FileView {
    id: statusView
    path: root.stateDir + "/status.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      var t = String(text() || "")
      if (t === root.lastStatusText) return
      root.lastStatusText = t
      try { root.status = JSON.parse(t) } catch (e) { root.status = null }
    }
    onLoadFailed: root.status = null
  }

  // Safety net: if the inotify watch limit is exhausted the watches above
  // never fire, so re-read every second. Unchanged content is ignored.
  Timer {
    interval: 1000
    running: !(root.service && root.service.record)
    repeat: true
    onTriggered: { activeFile.reload(); statusView.reload() }
  }

  function parse(content) {
    if (String(content || "") === root.lastText) return
    root.lastText = String(content || "")
    try {
      var parsed = JSON.parse(String(content || ""))
      root.fileRecord = parsed && typeof parsed === "object" ? parsed : null
    } catch (e) {
      console.warn("oma-top-menu", "Ignoring bad menu record", root.path, e)
      root.fileRecord = null
    }
  }
}
