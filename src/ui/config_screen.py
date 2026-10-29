import pyglet
from pyglet.window import key
from src.ui.displays import GameState, doctor_window, patient_window

doctor_window.switch_to()
doctor_label = pyglet.text.Label('Configuration: Press 1 for Saccades, 2 for Pursuits',
                                   font_size=16, x=640, y=420, anchor_x='center')
doctor_feedback = pyglet.text.Label('', font_size=14, x=640, y=300, anchor_x='center')

patient_window.switch_to()
patient_label = pyglet.text.Label('Waiting for Doctor...',
                               font_size=18, x=640, y=360, anchor_x='center')

def draw_doctor():
    doctor_label.draw()
    doctor_feedback.draw()

def draw_patient():
    patient_label.draw()

def handle_doctor_input(symbol):
    if symbol == key._1:
        GameState.current_mode = "SACCADES"
        # Reset feedback when starting a new session
        doctor_feedback.text = "" 
    elif symbol == key._2:
        GameState.current_mode = "PURSUITS"
        doctor_feedback.text = ""