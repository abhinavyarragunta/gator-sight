import pyglet
from pyglet.window import key
from src.ui.displays import GameState, doctor_window, patient_window

doctor_window.switch_to()
doc_label = pyglet.text.Label('Saccades Mode Active - Monitoring Patient', x=400, y=300, anchor_x='center')

patient_window.switch_to()
patient_label = pyglet.text.Label('Saccades: Press Arrow Keys (Esc to quit)', x=400, y=300, anchor_x='center')
feedback_label = pyglet.text.Label('', x=400, y=200, anchor_x='center')

def draw_doctor():
    doc_label.draw()

def draw_patient():
    patient_label.draw()
    feedback_label.draw()

def handle_patient_input(symbol):
    # Ensure the rebuild happens correctly
    patient_window.switch_to()

    if symbol == key.ESCAPE:
        GameState.current_mode = "CONFIG"
        feedback_label.text = ""
    elif symbol in [key.UP, key.DOWN, key.LEFT, key.RIGHT]:
        feedback_label.text = f"Saccades Hit: {key.symbol_string(symbol)}"