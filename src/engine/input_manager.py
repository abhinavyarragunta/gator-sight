"""
Input manager: keyboard and/or ESP32 finger pad (capacitive touch over serial).

Put this file at src/engine/input_manager.py

How it works
------------
The ESP32 prints lines like "Left:1" (touched) / "Left:0" (released) at 115200 baud.
This module polls the serial port without blocking and re-dispatches each touch as a
normal pyglet on_key_press event on the patient window, tagged with TOUCH_FLAG in the
modifiers field. A handler pushed onto the window then blocks arrow keys from whichever
source is not allowed by the current mode, so the existing game code
(handle_patient_input) needs no changes.

Usage
-----
    from src.engine import input_manager

    input_manager.install(patient_window)    # once, right after the window is created
    input_manager.set_mode(input_manager.FINGERPAD)   # or KEYBOARD / BOTH
    input_manager.cycle_mode()               # handy for a config-screen button
    input_manager.mode_text()                # label text for the config screen
"""
import pyglet
from pyglet.window import key

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pyserial not installed: keyboard mode still works
    serial = None
    list_ports = None

# ---- Settings ---------------------------------------------------------------
KEYBOARD = "KEYBOARD"
FINGERPAD = "FINGERPAD"
BOTH = "BOTH"
MODES = [KEYBOARD, FINGERPAD, BOTH]

SERIAL_PORT = None   # e.g. "COM3" or "/dev/ttyUSB0". None = auto-detect
BAUD = 115200

# USB vendor IDs of common ESP32 dev board serial chips (CP210x, CH340, FTDI, Espressif)
KNOWN_VIDS = {0x10C4, 0x1A86, 0x0403, 0x303A}

PAD_TO_KEY = {
    "Left": key.LEFT,
    "Right": key.RIGHT,
    "Up": key.UP,
    "Down": key.DOWN,
}
ARROWS = set(PAD_TO_KEY.values())
TOUCH_FLAG = 1 << 20  # unused high bit in pyglet's modifiers; marks synthetic touch events

# ---- State ------------------------------------------------------------------
mode = KEYBOARD
status = ""
_ser = None
_buf = b""
_window = None


def _set_status(text):
    global status
    status = text


def mode_text():
    """Short text for a config screen label."""
    names = {KEYBOARD: "Keyboard", FINGERPAD: "Finger Pad (ESP32)", BOTH: "Keyboard + Finger Pad"}
    text = f"Input: {names[mode]}"
    if mode != KEYBOARD and status:
        text += f" - {status}"
    return text


def is_connected():
    return _ser is not None


# ---- Serial handling --------------------------------------------------------
def _find_port():
    if list_ports is None:
        return None
    for p in list_ports.comports():
        if p.vid in KNOWN_VIDS:
            return p.device
    return None


def _open():
    """Open the serial port. Note: this resets the ESP32, which then recalibrates (~1.5 s)."""
    global _ser, _buf
    _close()
    if serial is None:
        _set_status("pyserial not installed (pip install pyserial)")
        return False
    port = SERIAL_PORT or _find_port()
    if not port:
        _set_status("ESP32 not found")
        return False
    try:
        _ser = serial.Serial(port, BAUD, timeout=0)  # timeout=0 -> non-blocking reads
    except (OSError, serial.SerialException) as e:
        _ser = None
        _set_status(f"could not open {port}: {e}")
        return False
    _buf = b""
    _set_status(f"calibrating on {port} - don't touch the pads")
    return True


def _close():
    global _ser
    if _ser is not None:
        try:
            _ser.close()
        except Exception:
            pass
        _ser = None


def _poll(dt):
    global _buf
    if _ser is None:
        return
    try:
        _buf += _ser.read(_ser.in_waiting)
    except (OSError, serial.SerialException):
        _close()
        _set_status("disconnected")
        return
    while b"\n" in _buf:
        line, _buf = _buf.split(b"\n", 1)
        _handle_line(line.decode(errors="ignore").strip())


def _handle_line(line):
    if line == "Ready.":
        _set_status("ready")
        return

    # Accepts "Left:1" (new sketch) and plain "Left" (original sketch)
    name, sep, state = line.partition(":")
    if name not in PAD_TO_KEY:
        return  # calibration chatter etc.
    if sep and state != "1":
        return  # release events aren't needed by the game
    _set_status("ready")
    if _window is not None:
        _window.dispatch_event("on_key_press", PAD_TO_KEY[name], TOUCH_FLAG)


# ---- Window filter ----------------------------------------------------------
def _on_key_press(symbol, modifiers):
    """Pushed onto the window, so it runs before the game's own handler."""
    if symbol not in ARROWS:
        return None
    from_pad = bool(modifiers & TOUCH_FLAG)
    allowed = (mode in (FINGERPAD, BOTH)) if from_pad else (mode in (KEYBOARD, BOTH))
    return None if allowed else pyglet.event.EVENT_HANDLED  # swallow disallowed source


# ---- Public API -------------------------------------------------------------
def install(window):
    """Call once with the patient window."""
    global _window
    _window = window
    window.push_handlers(on_key_press=_on_key_press)
    window.push_handlers(on_close=lambda: _close())
    pyglet.clock.schedule_interval(_poll, 1 / 120)


def set_mode(new_mode):
    global mode
    if new_mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    mode = new_mode
    if mode == KEYBOARD:
        _close()
        _set_status("")
    elif not is_connected():
        _open()


def cycle_mode():
    set_mode(MODES[(MODES.index(mode) + 1) % len(MODES)])
    return mode