import pyglet
from src.ui.displays import doctor_window, patient_window, GameState
from src.ui import config_screen
from src.engine import saccades, pursuits

@doctor_window.event
def on_draw():
    doctor_window.clear()
    if GameState.current_mode == "CONFIG":
        config_screen.draw_doctor()
    elif GameState.current_mode == "SACCADES":
        saccades.draw_doctor()
    elif GameState.current_mode == "PURSUITS":
        pursuits.draw_doctor()

@patient_window.event
def on_draw():
    patient_window.clear()
    if GameState.current_mode == "CONFIG":
        config_screen.draw_patient()
    elif GameState.current_mode == "SACCADES":
        saccades.draw_patient()
    elif GameState.current_mode == "PURSUITS":
        pursuits.draw_patient()

@doctor_window.event
def on_key_press(symbol, modifiers):
    if GameState.current_mode == "CONFIG":
        config_screen.handle_doctor_input(symbol)
        
        # Trigger the engine clock for whichever mode was selected
        if GameState.current_mode == "PURSUITS":
            pursuits.start_game()
        elif GameState.current_mode == "SACCADES":
            saccades.start_game() 
            
    elif symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()

@patient_window.event
def on_key_press(symbol, modifiers):
    # Route patient inputs (arrow keys) to the active game engine mode
    if GameState.current_mode == "SACCADES":
        saccades.handle_patient_input(symbol)
    elif GameState.current_mode == "PURSUITS":
        pursuits.handle_patient_input(symbol)

    # Return True is used to prevent window from closing on ESC
    if symbol == pyglet.window.key.ESCAPE:
        return True

if __name__ == '__main__':
    pyglet.app.run()