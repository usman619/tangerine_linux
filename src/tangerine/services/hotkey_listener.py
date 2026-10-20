import math
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard, mouse


class HotkeyBridge(QObject):
    summon_wheel = pyqtSignal(str)   # "CONVERT", "TOOLS", or "ACTIONS"
    dismiss_wheel = pyqtSignal()


class GlobalModifierMonitor:
    DRAG_THRESHOLD_PX = 12

    def __init__(self, bridge: HotkeyBridge):
        self.bridge = bridge
        self.left_mouse_held = False
        self.is_dragging = False
        self.wheel_visible = False
        self.press_origin: tuple[int, int] | None = None

        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move
        )
        self._kb_listener = keyboard.Listener(
            on_press=self._on_key_press
        )

    def start(self) -> None:
        self._mouse_listener.start()
        self._kb_listener.start()

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button == mouse.Button.left:
            self.left_mouse_held = pressed
            if pressed:
                self.press_origin = (x, y)
                self.is_dragging = False
            else:
                self.press_origin = None
                self.is_dragging = False
                if self.wheel_visible:
                    self.wheel_visible = False
                    # Slight delay so Qt dropEvent finishes before hiding
                    threading.Timer(0.18, self.bridge.dismiss_wheel.emit).start()

    def _on_move(self, x: int, y: int) -> None:
        if self.left_mouse_held and not self.is_dragging and self.press_origin is not None:
            dx = x - self.press_origin[0]
            dy = y - self.press_origin[1]
            if math.hypot(dx, dy) >= self.DRAG_THRESHOLD_PX:
                self.is_dragging = True

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        # Must be actively holding left click (dragging) to summon or switch wheels
        if not self.left_mouse_held:
            return

        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.wheel_visible = True
            self.bridge.summon_wheel.emit("CONVERT")

        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            self.wheel_visible = True
            self.bridge.summon_wheel.emit("TOOLS")

        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.wheel_visible = True
            self.bridge.summon_wheel.emit("ACTIONS")