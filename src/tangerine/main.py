import sys
from PyQt6.QtWidgets import QApplication
from tangerine.ui.radial_overlay import RadialDropOverlay
from tangerine.ui.tray_icon import TangerineTray
from tangerine.services.hotkey_listener import HotkeyBridge, GlobalModifierMonitor

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    overlay = RadialDropOverlay()
    tray = TangerineTray(app, on_summon_callback=lambda: overlay.summon("CONVERT"))
    tray.show()

    overlay.action_completed.connect(tray.notify_success)

    bridge = HotkeyBridge()
    bridge.summon_wheel.connect(overlay.summon)
    bridge.dismiss_wheel.connect(overlay.hide)

    monitor = GlobalModifierMonitor(bridge)
    monitor.start()

    print("🍊 Open-Tangerine (Pro UI Edition) running in system tray.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()