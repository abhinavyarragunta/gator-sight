import pyglet

# Initialize the two required windows for Doctor and Patient
doctor_window = pyglet.window.Window(1280, 720, caption="GatorSight - Doctor Dashboard")
patient_window = pyglet.window.Window(1280, 720, caption="GatorSight - Patient Gameplay")

class GameState:
    # Starts on the Configuration Screen / Home Page
    current_mode = "CONFIG"