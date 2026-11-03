import pyglet
from pyglet.window import key
from src.ui.displays import GameState, doctor_window, patient_window
from src.engine import input_manager

# Install the keyboard / finger pad filter and serial poller on the patient window (once)
input_manager.install(patient_window)

doctor_window.switch_to()
doctor_label = pyglet.text.Label('Configuration: Press 1 for Saccades, 2 for Pursuits',
                                   font_size=16, x=640, y=420, anchor_x='center')
input_label = pyglet.text.Label('', font_size=14, x=640, y=360, anchor_x='center')
doctor_feedback = pyglet.text.Label('', font_size=14, x=640, y=300, anchor_x='center')

patient_window.switch_to()
WAITING_TEXT = 'Waiting for Doctor...'
CALIBRATING_TEXT = "Calibrating finger pad - please don't touch the pads"
patient_label = pyglet.text.Label(WAITING_TEXT,
                               font_size=18, x=640, y=360, anchor_x='center')

# Cache of last-shown text so we only touch the labels when something changes
_shown = {"input": None, "patient": None}


def refresh_input_status(dt):
    """Keeps the input mode / calibration status labels current."""
    text = input_manager.mode_text() + "   (press I to change)"
    if text != _shown["input"]:
        doctor_window.switch_to()
        input_label.text = text
        _shown["input"] = text

    patient_text = CALIBRATING_TEXT if is_calibrating() else WAITING_TEXT
    if patient_text != _shown["patient"]:
        patient_window.switch_to()
        patient_label.text = patient_text
        _shown["patient"] = patient_text


def is_calibrating():
    return input_manager.status.startswith("calibrating")


pyglet.clock.schedule_interval(refresh_input_status, 0.25)
refresh_input_status(0)


def draw_doctor():
    doctor_label.draw()
    input_label.draw()
    doctor_feedback.draw()

def draw_patient():
    patient_label.draw()

def handle_doctor_input(symbol):
    if symbol == key.I:
        input_manager.cycle_mode()  # Keyboard -> Finger Pad -> Both
        refresh_input_status(0)
        return

    if symbol in (key._1, key._2):
        if is_calibrating():
            doctor_feedback.text = "Finger pad is still calibrating - wait a moment, then try again"
            return

        if symbol == key._1:
            GameState.current_mode = "SACCADES"
        else:
            GameState.current_mode = "PURSUITS"
        # Reset feedback when starting a new session
        doctor_feedback.text = ""