import pyglet
from pyglet.window import key
from src.ui.displays import GameState, doctor_window, patient_window
from src.ui import config_screen

doctor_window.switch_to()
doc_label = pyglet.text.Label('Pursuits Mode Active - Monitoring Patient', x=400, y=300, anchor_x='center')

patient_window.switch_to()
patient_label = pyglet.text.Label('Pursuits: Press RIGHT when the block hits the target! (Esc to quit)', 
                                  x=400, y=500, anchor_x='center')
feedback_label = pyglet.text.Label('', x=400, y=400, anchor_x='center')
score_label = pyglet.text.Label('Score: 0', x=400, y=350, anchor_x='center')

# Gameplay variables
hitbox_x = 600
arrow_x = 100
arrow_speed = 300
score = 0
total_attempts = 0

# "Arrow" and "Hitbox" Graphics
patient_window.switch_to()
hitbox_rect = pyglet.shapes.Rectangle(hitbox_x, 200, 60, 60, color=(100, 100, 100))
arrow_rect = pyglet.shapes.Rectangle(arrow_x, 205, 50, 50, color=(200, 50, 200))

def start_game():
    global arrow_x, score, total_attempts
    arrow_x = 100
    score = 0
    total_attempts = 0
    
    patient_window.switch_to()
    feedback_label.text = ""
    score_label.text = f"Score: {score}"
    
    # 60 FPS
    pyglet.clock.schedule_interval(update, 1/60.0)

def stop_game():
    pyglet.clock.unschedule(update)
    
    # Calculate feedback for doctor dashboard
    doctor_window.switch_to()
    accuracy = int((score / total_attempts) * 100) if total_attempts > 0 else 0
    config_screen.doctor_feedback.text = f"Last Session - Pursuits: Score {score}/{total_attempts} ({accuracy}%)"

def update(dt):
    global arrow_x
    arrow_x += arrow_speed * dt
    
    # Loop the block back to the left side if it goes off-screen
    if arrow_x > 800:
        arrow_x = 100 
        
    patient_window.switch_to()
    arrow_rect.x = arrow_x

def draw_doctor():
    doc_label.draw()

def draw_patient():
    patient_label.draw()
    feedback_label.draw()
    score_label.draw()
    hitbox_rect.draw()
    arrow_rect.draw()

def handle_patient_input(symbol):
    global score, total_attempts, arrow_x
    patient_window.switch_to()
    
    if symbol == key.ESCAPE:
        GameState.current_mode = "CONFIG"
        stop_game()
        return
        
    if symbol == key.RIGHT:
        total_attempts += 1
        
        # Check if the moving block is inside the stationary hitbox block
        if abs(arrow_x - hitbox_x) < 40: 
            score += 1
            feedback_label.text = "HIT! Good timing!"
            arrow_x = 100  # Reset position upon a successful hit
        else:
            feedback_label.text = "MISS!"
            
        score_label.text = f"Score: {score}"