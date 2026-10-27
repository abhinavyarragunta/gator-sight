import pyglet
from pyglet.window import key
import random
from src.ui.displays import GameState, doctor_window, patient_window
from src.ui import config_screen

doctor_window.switch_to()
doc_label = pyglet.text.Label('Pursuits Mode Active - Monitoring Patient', x=400, y=300, anchor_x='center')

patient_window.switch_to()
patient_label = pyglet.text.Label('Pursuits: Match direction when arrow hits the box! (Esc to quit)', 
                                  x=400, y=550, anchor_x='center')
feedback_label = pyglet.text.Label('', x=400, y=100, anchor_x='center')

score_label = pyglet.text.Label('Score: 0', font_size=16, x=50, y=500, anchor_x='left')
streak_label = pyglet.text.Label('Streak: 0', font_size=16, x=50, y=450, anchor_x='left')
accuracy_label = pyglet.text.Label('Accuracy: 0%', font_size=16, x=750, y=450, anchor_x='right')
timer_label = pyglet.text.Label('Time: 60', font_size=18, x=750, y=500, anchor_x='right')

# Gameplay and Timer variables
hitbox_y = 450
arrow_y = 0
arrow_speed = 400 
score = 0
streak = 0
total_attempts = 0
total_hits = 0
time_remaining = 60.0
arrow_attempted = False

VALID_DIRECTIONS = [key.UP, key.DOWN, key.LEFT, key.RIGHT]
current_direction = key.UP

patient_window.switch_to()
hitbox_rect = pyglet.shapes.Rectangle(x=370, y=hitbox_y - 30, width=60, height=60, color=(100, 100, 100))
arrow_label = pyglet.text.Label('UP', font_size=20, x=400, y=arrow_y, 
                                anchor_x='center', anchor_y='center', color=(255, 255, 0, 255))

def reset_arrow():
    global arrow_y, current_direction, arrow_attempted
    arrow_y = -50  
    current_direction = random.choice(VALID_DIRECTIONS)
    arrow_attempted = False
    
    patient_window.switch_to()
    arrow_label.text = key.symbol_string(current_direction)
    arrow_label.y = arrow_y

def start_game():
    global score, total_attempts, total_hits, streak, time_remaining
    score = 0
    total_attempts = 0
    total_hits = 0
    streak = 0
    time_remaining = 60.0
    reset_arrow()
    
    patient_window.switch_to()
    feedback_label.text = ""
    score_label.text = "Score: 0"
    streak_label.text = "Streak: 0"
    accuracy_label.text = "Accuracy: 0%"
    timer_label.text = "Time: 1:00"
    
    pyglet.clock.schedule_interval(update, 1/60.0)

def stop_game():
    pyglet.clock.unschedule(update)
    
    doctor_window.switch_to()
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    config_screen.doctor_feedback.text = f"Last Session - Pursuits: Targets {total_hits}/{total_attempts} ({accuracy}%)"

def update(dt):
    # Add total_hits to the global declaration here
    global arrow_y, time_remaining, total_attempts, streak, total_hits 
    
    time_remaining -= dt
    if time_remaining <= 0:
        GameState.current_mode = "CONFIG"
        stop_game()
        return
        
    arrow_y += arrow_speed * dt
    
    if arrow_y > 650:
        if not arrow_attempted:
            patient_window.switch_to()
            total_attempts += 1
            streak = 0
            feedback_label.text = "MISS! No input detected!"
            
            # Recalculate and update the accuracy label
            accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
            accuracy_label.text = f"Accuracy: {accuracy}%"
            streak_label.text = f"Streak: {streak}"
            
        reset_arrow() 
        
    patient_window.switch_to()
    arrow_label.y = arrow_y
    
    minutes = int(time_remaining) // 60
    seconds = int(time_remaining) % 60
    timer_label.text = f"Time: {minutes}:{seconds:02d}"

def draw_doctor():
    doc_label.draw()

def draw_patient():
    patient_label.draw()
    feedback_label.draw()
    score_label.draw()
    streak_label.draw()
    accuracy_label.draw()
    timer_label.draw()
    hitbox_rect.draw()

    if 130 < arrow_y < 530:
        arrow_label.draw()

def handle_patient_input(symbol):
    global score, total_attempts, total_hits, streak, arrow_attempted
    patient_window.switch_to()
    
    if symbol == key.ESCAPE:
        GameState.current_mode = "CONFIG"
        stop_game()
        return
        
    # Only process the input if the current arrow hasn't been attempted yet
    if symbol in VALID_DIRECTIONS and not arrow_attempted:
        arrow_attempted = True
        total_attempts += 1
        
        timing_correct = abs(arrow_y - hitbox_y) < 40 
        direction_correct = (symbol == current_direction)
        
        if timing_correct and direction_correct: 
            streak += 1
            total_hits += 1
            
            points_earned = 100 + (25 * (streak // 5))
            score += points_earned
            
            feedback_label.text = f"HIT! Perfect {key.symbol_string(symbol)}! (+{points_earned})"
            reset_arrow()  
        else:
            streak = 0
            if not timing_correct:
                feedback_label.text = "MISS! Bad timing!"
            elif not direction_correct:
                feedback_label.text = f"MISS! Wrong direction. Expected: {key.symbol_string(current_direction)}"
                
        accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
        
        score_label.text = f"Score: {score}"
        streak_label.text = f"Streak: {streak}"
        accuracy_label.text = f"Accuracy: {accuracy}%"