import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import qs.Commons
import qs.Ui

// Oma Top Menu, modified from primo.global-menu (GPL-2.0), 2026-11-07: the bridge
// is run by Service.qml and called through /usr/bin/python3.
// macOS-style app menu bar: shows the focused window's menu strip (from the
// omarchy-global-menu-bridge snapshot) in the bar, with click-to-open popups
// and hover-to-switch submenus. The bar slot renders the strip; a separate
// PopupWindow hosts the open menu so clicking outside dismisses it.
BarWidget {
  id: root
  moduleName: "com.lefteros.somnius.oma-top-menu"

  readonly property var dataLoaderItem: dataLoader.item
  readonly property var record: dataLoaderItem ? dataLoaderItem.record : null
  readonly property var menubar: dataLoaderItem ? dataLoaderItem.menubar : []
  readonly property string appIcon: dataLoaderItem ? dataLoaderItem.icon : ""
  readonly property string appName: dataLoaderItem ? dataLoaderItem.appName : ""
  readonly property string source: dataLoaderItem ? dataLoaderItem.source : ""
  readonly property string statusMessage: dataLoaderItem ? dataLoaderItem.statusMessage : ""

  // Placement decides the role. The bar gives a widget in the left section
  // fixedEdge "start"; anywhere else (right section, tray, centre) it is the
  // options icon. Both share one settings record.
  readonly property bool optionsRole: root.fixedEdge !== "start"
  readonly property bool dividers: root.setting("dividers", false) === true
  readonly property string spacingMode: String(root.setting("spacing", "normal"))
  readonly property real entryPad: root.spacingMode === "compact" ? Style.space(4)
    : (root.spacingMode === "roomy" ? Style.space(14) : Style.space(8))
  readonly property bool showAppIcon: root.setting("showAppIcon", true) !== false
  readonly property bool hideGeneric: root.setting("hideGeneric", false) === true
  readonly property var shownMenubar: (root.hideGeneric && root.source === "desktop-fallback") ? [] : root.menubar

  property int openIndex: -1
  property var openEntry: null
  property string lastAppId: ""

  // The bridge ships with this plugin, so resolve it relative to the
  // plugin directory instead of relying on ~/.local/bin being on PATH.
  readonly property string bridgePath: String(Qt.resolvedUrl("bin/omarchy-global-menu-bridge")).replace(/^file:\/\//, "")

  // Registered with the bar as our popout identity instead of the widget
  // itself: the bar lights its open-panel indicator when activePopout matches
  // the slot's item, which would underline the whole menubar strip. The proxy
  // never matches, so the host indicator stays hidden while every switching
  // contract (closeForPopoutSwitch / popoutSwitchClosing) still works.
  readonly property var popoutOwner: ({
    popoutSwitchClosing: false,
    closeForPopoutSwitch: function() { root.setOpenIndex(-1) }
  })

  function iconSource(icon) {
    var value = String(icon || "")
    if (value.length === 0) return ""
    if (value.indexOf("file://") === 0 || value.indexOf("image://") === 0) return value
    if (value.charAt(0) === "/") return Util.fileUrl(value)
    var themed = Quickshell.iconPath(value, true)
    if (themed.length > 0) return themed
    return ""
  }

  readonly property string appIconUrl: root.iconSource(root.appIcon)

  // This bar's own monitor, found the way Omarchy's workspace widget does it.
  readonly property var monitor: {
    var window = root.QsWindow.window
    var screen = window ? window.screen : null
    return screen ? Hyprland.monitorFor(screen) : Hyprland.focusedMonitor
  }
  readonly property string monitorName: root.monitor ? root.monitor.name : ""

  function setOpenIndex(index) {
    var opening = root.openIndex < 0 && index >= 0
    var closing = root.openIndex >= 0 && index < 0
    root.openEntry = (index >= 0 && entryRepeater && entryRepeater.itemAt) ? entryRepeater.itemAt(index) : null
    root.openIndex = index
    if (root.bar) {
      if (opening) root.bar.requestPopout(root.popoutOwner)
      else if (closing && root.bar.activePopout === root.popoutOwner) root.bar.releasePopout(root.popoutOwner)
    }
    var pop = popupLoader.active ? popupLoader.item : null
    if (pop && pop.visible && pop.anchor) Qt.callLater(function() { pop.anchor.updateAnchor() })
  }

  function activate(item) {
    var action = item && item.action
    if (!action || !action.kind) return
    root.setOpenIndex(-1)
    var kind = action.kind
    if (kind === "exec") {
      Quickshell.execDetached(["sh", "-c", String(action.command || "")])
    } else if (kind === "hypr") {
      Quickshell.execDetached(["hyprctl", "dispatch", String(action.lua || "")])
    } else {
      Quickshell.execDetached(["/usr/bin/python3", root.bridgePath, "activate", "--action-json", JSON.stringify(action)])
    }
  }

  function syncOpenEntry() {
    if (root.openIndex >= 0) {
      if (root.openIndex >= root.menubar.length) {
        root.setOpenIndex(-1)
      } else {
        root.openEntry = entryRepeater.itemAt(root.openIndex)
        var pop = popupLoader.active ? popupLoader.item : null
        if (pop && pop.visible && pop.anchor) Qt.callLater(function() { pop.anchor.updateAnchor() })
      }
    }
  }

  onMenubarChanged: root.syncOpenEntry()

  // The service (one per shell) streams the menu snapshots; fall back to the
  // state file when the shell does not give us a service handle.
  // serviceTick forces a re-check while the service has not mounted yet.
  property int serviceTick: 0
  readonly property var menuService: (root.serviceTick, root.bar && root.bar.shell
    ? root.bar.shell.serviceFor(root.moduleName) : null)

  Timer {
    interval: 1000
    repeat: true
    running: !root.menuService && root.serviceTick < 30
    onTriggered: root.serviceTick += 1
  }

  Loader {
    id: dataLoader
    active: true
    source: Qt.resolvedUrl("GlobalMenuData.qml")
    onLoaded: {
      item.service = Qt.binding(function() { return root.menuService })
      item.monitorName = Qt.binding(function() { return root.monitorName })
    }
  }

  Connections {
    target: dataLoader.item
    function onRecordChanged() {
      var next = dataLoader.item ? dataLoader.item.appId : ""
      if (root.lastAppId !== "" && next !== root.lastAppId) root.setOpenIndex(-1)
      root.lastAppId = next
    }
  }

  function firstSubmenuIndex() {
    for (var i = 0; i < root.menubar.length; i++) {
      var m = root.menubar[i]
      if (m && m.items && m.items.length > 0) return i
    }
    return -1
  }

  function open(): void {
    if (root.optionsRole) { if (optionsLoader.item) optionsLoader.item.open(); return }
    var i = root.openIndex >= 0 ? root.openIndex : firstSubmenuIndex()
    if (i < 0) return
    root.setOpenIndex(i)
  }
  function close(): void {
    if (root.optionsRole) { if (optionsLoader.item) optionsLoader.item.close(); return }
    root.setOpenIndex(-1)
  }
  function toggle(): void {
    if (root.optionsRole) { if (optionsLoader.item) optionsLoader.item.toggle(); return }
    if (root.openIndex >= 0) root.setOpenIndex(-1)
    else root.open()
  }

  // IPC (open/close/toggle) arrives through the service; only the menu strip
  // on the focused monitor answers it.
  Connections {
    target: root.menuService
    ignoreUnknownSignals: true
    function onIpcRequest(action) {
      if (root.optionsRole || !root.monitor || !root.monitor.focused) return
      if (action === "open") root.open()
      else if (action === "close") root.close()
      else if (action === "toggle") root.toggle()
    }
  }

  readonly property bool opened: root.optionsRole && optionsLoader.item ? optionsLoader.item.opened === true : false
  readonly property bool popoutSwitchClosing: root.optionsRole && optionsLoader.item ? optionsLoader.item.popoutSwitchClosing === true : false
  function closeForPopoutSwitch() {
    if (root.optionsRole && optionsLoader.item) optionsLoader.item.closeForPopoutSwitch()
  }

  function openOptions() {
    root.injectOptions()
    if (optionsLoader.item) optionsLoader.item.open()
  }

  // The follow-mouse choice is a widget setting; the service applies it.
  function syncFollowMouse() {
    if (root.menuService && typeof root.menuService.setFollowMouse === "function")
      root.menuService.setFollowMouse(root.setting("followMouse", ""))
  }

  function injectOptions() {
    var p = optionsLoader.item
    if (!p) return
    p.bar = root.bar
    p.anchorItem = root.optionsRole ? optionsButton : strip
    p.hostWidget = root
    p.settings = root.settings
    p.menuService = root.menuService
  }
  onBarChanged: root.injectOptions()
  onSettingsChanged: { root.injectOptions(); root.syncFollowMouse() }
  onMenuServiceChanged: { root.injectOptions(); root.syncFollowMouse() }

  Loader {
    id: optionsLoader
    active: true
    visible: false
    source: Qt.resolvedUrl("OptionsPanel.qml")
    onLoaded: { root.injectOptions(); Qt.callLater(root.injectOptions) }
  }

  implicitWidth: root.optionsRole ? optionsButton.implicitWidth : (root.vertical ? root.barSize : stripRow.implicitWidth)
  implicitHeight: root.barSize

  // The options icon: a bar with three menu stops, drawn in the bar colour.
  WidgetButton {
    id: optionsButton
    visible: root.optionsRole
    anchors.fill: parent
    bar: root.bar
    tooltipText: "Oma Top Menu options"
    hasVisualContent: true
    fixedWidth: root.vertical ? -1 : Style.bar.iconSlot
    onPressed: function(buttonCode) { if (buttonCode === Qt.LeftButton) root.toggle() }
    Item {
      anchors.centerIn: parent
      width: Style.bar.iconSize
      height: Style.bar.iconSize
      readonly property color ink: root.bar ? root.bar.barForeground : Color.foreground
      Rectangle {
        anchors.fill: parent
        radius: width * 0.18
        color: "transparent"
        border.width: Math.max(1, Math.round(parent.width * 0.09))
        border.color: parent.ink
      }
      Row {
        anchors.left: parent.left
        anchors.leftMargin: parent.width * 0.2
        anchors.top: parent.top
        anchors.topMargin: parent.height * 0.22
        spacing: parent.width * 0.1
        Repeater {
          model: 3
          Rectangle { width: parent.parent.width * 0.16; height: Math.max(1, parent.parent.height * 0.09); color: parent.parent.ink }
        }
      }
    }
  }

  Item {
    id: strip
    visible: !root.optionsRole
    anchors.fill: parent

    // Right-click anywhere on the strip opens the options panel, so a default
    // install needs only this one bar entry.
    MouseArea {
      anchors.fill: parent
      acceptedButtons: Qt.RightButton
      onClicked: root.openOptions()
    }

    Row {
      id: stripRow
      anchors.left: parent.left
      anchors.verticalCenter: parent.verticalCenter
      spacing: Style.space(1)

      Item {
        id: iconWrap
        // Non-empty icons that don't resolve to an image (file path or theme
        // icon) are treated as Nerd Font glyphs and rendered as text.
        readonly property bool hasGlyph: String(root.appIcon || "") !== "" && root.appIconUrl === ""
        visible: (root.appIconUrl !== "" || iconWrap.hasGlyph) && !root.vertical && root.showAppIcon && !(root.hideGeneric && root.source === "desktop-fallback")
        width: Style.space(24)
        height: root.barSize
        implicitWidth: Style.space(24)

        Image {
          anchors.centerIn: parent
          width: Style.space(16)
          height: Style.space(16)
          source: root.appIconUrl
          sourceSize.width: Style.space(16) * Screen.devicePixelRatio
          sourceSize.height: Style.space(16) * Screen.devicePixelRatio
          fillMode: Image.PreserveAspectFit
          asynchronous: true
          visible: root.appIconUrl !== ""
        }

        Text {
          anchors.centerIn: parent
          visible: iconWrap.hasGlyph
          text: root.appIcon
          color: root.bar ? root.bar.barForeground : Color.foreground
          font.family: root.bar ? root.bar.fontFamily : Style.font.family
          font.pixelSize: Style.font.body
          renderType: Text.NativeRendering
        }
      }

      Text {
        visible: root.statusMessage !== "" && root.menubar.length === 0
        anchors.verticalCenter: parent.verticalCenter
        text: root.statusMessage
        color: root.bar ? root.bar.barForeground : Color.foreground
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.body
        renderType: Text.NativeRendering
      }

      Repeater {
        id: entryRepeater
        model: root.shownMenubar
        delegate: entryComponent
      }
    }
  }

  Component {
    id: entryComponent

    Item {
      id: entry
      required property int index
      required property var modelData

      property bool hovered: false
      readonly property var entryItem: entry.modelData
      readonly property string label: String(entry.entryItem && entry.entryItem.label || "")
      readonly property bool hasSubmenu: !!(entry.entryItem && entry.entryItem.items && entry.entryItem.items.length > 0)
      readonly property bool hasAction: !!(entry.entryItem && entry.entryItem.action && entry.entryItem.action.kind)
      readonly property bool isOpen: root.openIndex === entry.index
      readonly property bool highlighted: entry.hovered || entry.isOpen

      visible: !root.vertical
      implicitWidth: Math.max(Style.space(8), labelText.implicitWidth + 2 * root.entryPad)
      implicitHeight: root.barSize

      Rectangle {
        visible: entry.highlighted
        anchors.fill: parent
        radius: Math.min(Style.cornerRadius, entry.height / 2)
        color: entry.hovered ? Style.normalFill : Style.selectedFill
      }

      Rectangle {
        visible: root.dividers && entry.index < root.shownMenubar.length - 1
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: 1
        height: Math.round(root.barSize * 0.45)
        color: Qt.alpha(root.bar ? root.bar.barForeground : Color.foreground, 0.25)
      }

      Text {
        id: labelText
        anchors.centerIn: parent
        text: entry.label
        color: entry.highlighted
          ? Color.menu.selectedText
          : (root.bar ? root.bar.barForeground : Color.foreground)
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.body
        renderType: Text.NativeRendering
      }

      MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: {
          entry.hovered = true
          if (root.openIndex >= 0 && root.openIndex !== entry.index && entry.hasSubmenu) root.setOpenIndex(entry.index)
        }
        onExited: entry.hovered = false
        onClicked: {
          if (!entry.hasSubmenu) {
            if (entry.hasAction) root.activate(entry.entryItem)
            return
          }
          if (root.openIndex === entry.index) root.setOpenIndex(-1)
          else root.setOpenIndex(entry.index)
        }
      }
    }
  }

  Loader {
    id: popupLoader
    active: root.openIndex >= 0
    sourceComponent: popupComponent
  }

  Component {
    id: popupComponent

    PopupWindow {
      id: menuPopup

      readonly property var menu: root.menubar[root.openIndex]
      readonly property var anchorItem: root.openEntry !== null ? root.openEntry : strip

      // Height budget for the menu list, derived from screen geometry so tall
      // menus scroll instead of running off-screen (mirrors PopupCard.qml).
      readonly property real maxListHeight: {
        var win = anchorItem && anchorItem.QsWindow ? anchorItem.QsWindow.window : null
        var scr = win && win.screen ? win.screen : null
        if (!scr || scr.height <= 0) return 0
        var margin = Style.space(8)
        var reserved = 0
        if (root.bar && (root.bar.position === "top" || root.bar.position === "bottom") && win) reserved += win.height
        return Math.max(Style.space(160), scr.height - reserved - margin * 2)
      }

      function applyListCap(list) {
        if (!list) return
        list.maxListHeight = Math.max(0, maxListHeight - popupCard.contentTopInset - popupCard.contentBottomInset)
      }

      onMaxListHeightChanged: applyListCap(menuListLoader.item)

      visible: true
      color: "transparent"
      implicitWidth: (menuListLoader.item ? menuListLoader.item.listWidth : Style.space(160))
        + popupCard.contentLeftInset + popupCard.contentRightInset
      implicitHeight: menuListLoader.item
        ? menuListLoader.item.implicitHeight + popupCard.contentTopInset + popupCard.contentBottomInset
        : popupCard.contentTopInset + popupCard.contentBottomInset

      HyprlandFocusGrab {
        active: menuPopup.visible
        windows: (function() {
          var list = [menuPopup]
          if (menuPopup.anchorItem && menuPopup.anchorItem.QsWindow) list.push(menuPopup.anchorItem.QsWindow.window)
          var menu = menuListLoader.item
          if (menu && menu.openFlyouts) list = list.concat(menu.openFlyouts)
          return list
        })()
        onCleared: root.setOpenIndex(-1)
      }

      anchor {
        id: menuAnchor
        window: menuPopup.anchorItem && menuPopup.anchorItem.QsWindow
          ? menuPopup.anchorItem.QsWindow.window : null
        edges: Edges.Bottom | Edges.Left
        gravity: Edges.Bottom | Edges.Right
        adjustment: PopupAdjustment.Slide

        onAnchoring: {
          var target = menuPopup.anchorItem
          if (!target || !target.QsWindow) return
          var win = target.QsWindow.window
          if (!win) return
          var rect = win.contentItem.mapFromItem(target, 0, 0, target.width, target.height)
          menuAnchor.rect.x = Math.round(rect.x)
          menuAnchor.rect.y = Math.round(rect.y)
          menuAnchor.rect.width = Math.round(rect.width)
          menuAnchor.rect.height = Math.round(rect.height)
        }
      }

      BorderSurface {
        id: popupCard
        anchors.fill: parent
        color: Color.popups.background
        borderSpec: Border.localOrSurfaceSpec("popups", "border", Color.popups.border, Color.popups.border, Math.max(1, Style.space(1)))
        padding: Style.space(4)
        radius: Style.cornerRadius
      }

      Loader {
        id: menuListLoader
        anchors.fill: popupCard
        anchors.topMargin: popupCard.contentTopInset
        anchors.rightMargin: popupCard.contentRightInset
        anchors.bottomMargin: popupCard.contentBottomInset
        anchors.leftMargin: popupCard.contentLeftInset
        source: "MenuList.qml"
        onLoaded: {
          menuPopup.applyListCap(item)
          menuPopup.wireMenuList(item)
        }
      }

      function wireMenuList(list) {
        if (!list) return
        list.fontFamily = root.bar ? root.bar.fontFamily : Style.font.family
        list.foreground = Color.popups.text
        list.selectedBackground = Color.menu.selectedBackground
        list.selectedText = Color.menu.selectedText
        list.separatorColor = Qt.rgba(Color.popups.text.r, Color.popups.text.g, Color.popups.text.b, 0.22)
        list.items = (menuPopup.menu && menuPopup.menu.items) ? menuPopup.menu.items : []
        list.activated.connect(function(item) { root.activate(item) })
      }

      onMenuChanged: if (menuListLoader.item) menuListLoader.item.items = (menuPopup.menu && menuPopup.menu.items) ? menuPopup.menu.items : []
    }
  }
}
 