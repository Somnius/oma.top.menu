# Moving the menu, and locking it in place

![Dragging the menu along the bar and back](media/moving-the-menu.gif)

*(The recording as a video: [moving-the-menu.mp4](media/moving-the-menu.mp4).)*

## What the recording shows
The menu strip can be picked up and moved, using Omarchy's own bar drag-and-drop (the plugin does nothing special for this):

1. Press the strip with the left mouse button and move the pointer a few pixels (or press and hold). A boxed copy of the strip lifts off and follows the pointer.
2. Drag it along the bar. The other widgets slide out of the way as it passes over them.
3. Let go to drop it in the new place. In the recording it is carried across the bar to the right and then dragged back to its original spot on the left.

A plain click, without moving, still opens the menu under it, so clicking and dragging do not get in each other's way. The workspace numbers and the other widgets are moved the same way.

## Where it can go
- **Left section**: the menu strip (the default place).
- **Right section, or the tray drawer**: the widget becomes the small options icon instead of the strip, because where a copy sits decides what it is. So dragging the strip to the right turns it into the options icon; drag it back to the left to get the menu again.
- **Centre sections** are not supported (the bar gives a widget no reliable signal there).

## Locking it in place
Right-click the strip to open the options and choose **Position: Locked**. The bar has no lock of its own and no way for a widget to refuse a drag (its drag handler sits on top of every widget), so the plugin does the locking:

- While locked, the service reads the bar layout from `shell.json` every 1.5 seconds. If the menu is no longer at its place in the left section, it runs `omarchy bar move com.lefteros.somnius.oma-top-menu --section left --index <its place>`, Omarchy's own command, and the menu snaps back (about two seconds in the test below).
- If something keeps moving it (more than five restores in a row), the lock switches itself off and the bar says so, instead of fighting.
- When you move the workspace numbers from the options panel, the lock notes the menu's new index so it does not undo that.
- If you rearrange the bar yourself, unlock first, rearrange, then lock again (the lock remembers the place where you locked).
- The setting is stored with the widget in `shell.json` (`locked`), so it is removed with the plugin.

What it cannot do: stop the drag itself (you will see the menu lift off and snap back), or hold a place when the plugin is not running.

## Tested (2026-11-07, Omarchy 4.5.0-3)
- Locked: the menu was moved to `centerBegin` with `omarchy bar move` (the same layout change a drag makes) at 0.3 s and was back in the left section at the same place at 2.3 s.
- Unlocked: the same move stayed where it was.
- Not tested: a real mouse drag against the lock (the recording is a drag without the lock); the layout restore when the optional second copy of the widget sits in the right section was checked only through the CLI, where the first copy found is the one moved.
