import pyglet
from pyglet.window import key
import random
from src.ui.displays import GameState, doctor_window, patient_window
from src.ui import config_screen

doctor_window.switch_to()
doc_label = pyglet.text.Label('Saccades Mode Active - Monitoring Patient', x=400, y=300, anchor_x='center')

patient_window.switch_to()
patient_label = pyglet.text.Label('Saccades: Match the arrow in the box! (Esc to quit)',
                                  x=400, y=550, anchor_x='center')
feedback_label = pyglet.text.Label('', x=400, y=100, anchor_x='center')

score_label = pyglet.text.Label('Score: 0', font_size=16, x=50, y=500, anchor_x='left')
streak_label = pyglet.text.Label('Streak: 0', font_size=16, x=50, y=450, anchor_x='left')
accuracy_label = pyglet.text.Label('Accuracy: 0%', font_size=16, x=750, y=450, anchor_x='right')
timer_label = pyglet.text.Label('Time: 60', font_size=18, x=750, y=500, anchor_x='right')
reaction_label = pyglet.text.Label('Avg Reaction: --', font_size=16, x=750, y=400, anchor_x='right')

# Gameplay and Timer variables
LEFT_BOX_X = 200
RIGHT_BOX_X = 600
BOX_Y = 300
BOX_SIZE = 100
TARGET_TIMEOUT = 2.0   # Seconds the arrow stays visible before counting as a miss
GAP_DURATION = 0.5     # Seconds of blank screen between targets

score = 0
streak = 0
total_attempts = 0
total_hits = 0
time_remaining = 60.0
reaction_times = []

target_side = "LEFT"
target_visible = False
target_elapsed = 0.0
gap_elapsed = 0.0

VALID_DIRECTIONS = [key.UP, key.DOWN, key.LEFT, key.RIGHT]
current_direction = key.UP

patient_window.switch_to()
left_box = pyglet.shapes.Rectangle(x=LEFT_BOX_X - BOX_SIZE // 2, y=BOX_Y - BOX_SIZE // 2,
                                   width=BOX_SIZE, height=BOX_SIZE, color=(100, 100, 100))
right_box = pyglet.shapes.Rectangle(x=RIGHT_BOX_X - BOX_SIZE // 2, y=BOX_Y - BOX_SIZE // 2,
                                    width=BOX_SIZE, height=BOX_SIZE, color=(100, 100, 100))
arrow_label = pyglet.text.Label('UP', font_size=20, x=LEFT_BOX_X, y=BOX_Y,
                                anchor_x='center', anchor_y='center', color=(255, 255, 0, 255))

def get_average_reaction():
    return sum(reaction_times) / len(reaction_times) if reaction_times else 0.0

def update_labels():
    patient_window.switch_to()
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    score_label.text = f"Score: {score}"
    streak_label.text = f"Streak: {streak}"
    accuracy_label.text = f"Accuracy: {accuracy}%"
    if reaction_times:
        reaction_label.text = f"Avg Reaction: {int(get_average_reaction() * 1000)} ms"
    else:
        reaction_label.text = "Avg Reaction: --"

def show_next_target():
    # Alternate sides each time, and pick a random arrow direction
    global target_side, current_direction, target_visible, target_elapsed
    target_side = "RIGHT" if target_side == "LEFT" else "LEFT"
    current_direction = random.choice(VALID_DIRECTIONS)
    target_visible = True
    target_elapsed = 0.0

    patient_window.switch_to()
    arrow_label.text = key.symbol_string(current_direction)
    arrow_label.x = LEFT_BOX_X if target_side == "LEFT" else RIGHT_BOX_X

def end_target():
    # Hide the arrow and begin the blank gap before the next one appears
    global target_visible, gap_elapsed
    target_visible = False
    gap_elapsed = 0.0

def start_game():
    global score, total_attempts, total_hits, streak, time_remaining, reaction_times, target_side
    # Safeguard against stacked clock callbacks
    pyglet.clock.unschedule(update)

    score = 0
    total_attempts = 0
    total_hits = 0
    streak = 0
    time_remaining = 60.0
    reaction_times = []

    # Start on a random side; show_next_target() flips it, so pre-flip here
    target_side = random.choice(["LEFT", "RIGHT"])
    show_next_target()

    patient_window.switch_to()
    feedback_label.text = ""
    score_label.text = "Score: 0"
    streak_label.text = "Streak: 0"
    accuracy_label.text = "Accuracy: 0%"
    reaction_label.text = "Avg Reaction: --"
    timer_label.text = "Time: 1:00"

    pyglet.clock.schedule_interval(update, 1/60.0)

def stop_game():
    pyglet.clock.unschedule(update)

    doctor_window.switch_to()
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    if reaction_times:
        reaction_text = f", Avg Reaction {int(get_average_reaction() * 1000)} ms"
    else:
        reaction_text = ""
    config_screen.doctor_feedback.text = (
        f"Last Session - Saccades: Targets {total_hits}/{total_attempts} ({accuracy}%){reaction_text}"
    )

def update(dt):
    global time_remaining, total_attempts, streak, target_elapsed, gap_elapsed

    time_remaining -= dt
    if time_remaining <= 0:
        GameState.current_mode = "CONFIG"
        stop_game()
        return

    if target_visible:
        target_elapsed += dt
        if target_elapsed >= TARGET_TIMEOUT:
            # Arrow expired with no input
            total_attempts += 1
            streak = 0
            patient_window.switch_to()
            feedback_label.text = "MISS! No input detected!"
            update_labels()
            end_target()
    else:
        gap_elapsed += dt
        if gap_elapsed >= GAP_DURATION:
            show_next_target()

    patient_window.switch_to()
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
    reaction_label.draw()
    left_box.draw()
    right_box.draw()

    if target_visible:
        arrow_label.draw()

def handle_patient_input(symbol):
    global score, total_attempts, total_hits, streak
    patient_window.switch_to()

    if symbol == key.ESCAPE:
        GameState.current_mode = "CONFIG"
        stop_game()
        return

    # Only process input while an arrow is on screen
    if symbol in VALID_DIRECTIONS and target_visible:
        total_attempts += 1

        if symbol == current_direction:
            streak += 1
            total_hits += 1
            reaction_times.append(target_elapsed)

            points_earned = 100 + (25 * (streak // 5))
            score += points_earned

            feedback_label.text = (f"HIT! {key.symbol_string(symbol)} in {int(target_elapsed * 1000)} ms "
                                   f"(+{points_earned})")
        else:
            streak = 0
            feedback_label.text = f"MISS! Wrong direction. Expected: {key.symbol_string(current_direction)}"

        end_target()
        update_labels()