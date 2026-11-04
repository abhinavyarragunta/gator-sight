import math
import pyglet
from pyglet.window import key
import random
from src.ui.displays import GameState, doctor_window, patient_window
from src.ui import config_screen
from src.engine.arrows import load_arrow_images
from src.engine.saccades import (FONT, NAVY, PURPLE, CARD_FILL, BORDER, MAGENTA, BOX_FILL, WHITE, MUTED,
                                 GOOD, BAD, CARD_W, CARD_H, CARD_POSITIONS)

# ---------- Aesthetics ---------- NOTEEE 10/28: make sure to add install font on READ.ME
FONT = "Pixelify Sans"          # install this font on the PC; can be found under "/src/assets/fonts/Pixelify Sans.ttf" and click install!
NAVY = (0, 0, 52)
PURPLE = (118, 10, 122)
CARD_FILL = (6, 6, 60)
BORDER = (91, 111, 181)
MAGENTA = (255, 43, 214)
BOX_FILL = (40, 40, 100)
WHITE = (255, 255, 255, 255)
MUTED = (201, 207, 252, 255)
GOOD = (124, 255, 178, 255)
BAD = (255, 107, 138, 255)

doctor_window.switch_to()

patient_window.switch_to() 

# Batch and Groups
hud_batch = pyglet.graphics.Batch()
bg_group = pyglet.graphics.Group(order=0)
card_group = pyglet.graphics.Group(order=1)

# Background Gradient
STRIPS = 72
strip_height = 720 / STRIPS
background = []
for i in range(STRIPS):
    from_top = 1 - (i + 0.5) / STRIPS
    blend = max(0.0, (from_top - 0.30) / 0.70)
    color = tuple(int(a + (b - a) * blend) for a, b in zip(NAVY, PURPLE))
    background.append(pyglet.shapes.Rectangle(
        0, int(i * strip_height), 1280, math.ceil(strip_height) + 1,
        color=color, batch=hud_batch, group=bg_group
    ))

# Stat Cards
cards = []
card_titles = []
for title, (cx, cy) in CARD_POSITIONS.items():
    cards.append(pyglet.shapes.BorderedRectangle(
        cx, cy, CARD_W, CARD_H, border=3, color=CARD_FILL,
        border_color=BORDER, batch=hud_batch, group=card_group
    ))
    card_titles.append(pyglet.text.Label(
        title, font_size=11, weight="bold", x=cx + 20, y=cy + CARD_H - 16,
        anchor_y='top', color=MUTED
    ))

# Pursuits Track Lane
LANE_X = 640
LANE_W = 160
LANE_BOTTOM = 96
LANE_TOP = 636
lane = pyglet.shapes.BorderedRectangle(
    LANE_X - LANE_W // 2, LANE_BOTTOM, LANE_W, LANE_TOP - LANE_BOTTOM,
    border=2, color=CARD_FILL, border_color=BORDER,
    batch=hud_batch, group=card_group
)

# Static & State Labels
logo_label = pyglet.text.Label('GatorSight', font_name=FONT, font_size=34, x=48, y=674, anchor_y='top', color=WHITE)
subtitle_label = pyglet.text.Label('Pursuits, Normal Display', font_size=11, weight="bold", x=50, y=614, anchor_y='top', color=MUTED)
timer_label = pyglet.text.Label('1:00', font_name=FONT, font_size=32, x=1232, y=674, anchor_x='right', anchor_y='top', color=WHITE)
hint_label = pyglet.text.Label('Press Esc to end the session', font_size=11, weight="bold", x=1232, y=614, anchor_x='right', anchor_y='top', color=MUTED)

score_label = pyglet.text.Label('0', font_name=FONT, font_size=33, x=68, y=462, color=WHITE)
streak_label = pyglet.text.Label('0', font_name=FONT, font_size=33, x=68, y=292, color=WHITE)
accuracy_label = pyglet.text.Label('0%', font_name=FONT, font_size=33, x=1044, y=462, color=WHITE)
level_label = pyglet.text.Label('1', font_name=FONT, font_size=33, x=1044, y=292, color=WHITE)

feedback_label = pyglet.text.Label('', font_size=15, weight="bold", x=640, y=34, anchor_x='center', anchor_y='center')
reaction_label = pyglet.text.Label('Avg Timing Error: --', font_size=11, weight="bold", x=1232, y=34, anchor_x='right', anchor_y='center', color=MUTED)

# Gameplay & Hitbox Variables
HITBOX_X = 640
HITBOX_Y = 440
BOX_SIZE = 140
HIT_WINDOW = 40
ARROW_EXIT_Y = 650
arrow_y = 0
arrow_speed = 400 
ARROW_SCALE = 0.9

score = 0
streak = 0
total_attempts = 0
total_hits = 0
time_remaining = 60.0
arrow_attempted = False
timing_errors = []
attempt_log = []

VALID_DIRECTIONS = [key.UP, key.DOWN, key.LEFT, key.RIGHT]
current_direction = key.UP

ARROW_IMAGES = load_arrow_images()
hitbox_rect = pyglet.shapes.BorderedRectangle(
    HITBOX_X - BOX_SIZE // 2, HITBOX_Y - BOX_SIZE // 2, BOX_SIZE, BOX_SIZE,
    border=4, color=BOX_FILL, border_color=BORDER
)
arrow_sprite = pyglet.sprite.Sprite(ARROW_IMAGES[key.UP], x=HITBOX_X, y=arrow_y)
arrow_sprite.scale = ARROW_SCALE

ARROW_HALF = ARROW_IMAGES[key.UP].height * ARROW_SCALE / 2
VISIBLE_MIN_Y = LANE_BOTTOM + ARROW_HALF
VISIBLE_MAX_Y = LANE_TOP - ARROW_HALF


def get_average_timing_error():
    return sum(timing_errors) / len(timing_errors) if timing_errors else 0.0

def set_timer_text():
    seconds = max(0, int(math.ceil(time_remaining)))
    timer_label.text = f"{seconds // 60}:{seconds % 60:02d}"

def set_feedback(text, good):
    feedback_label.text = text
    feedback_label.color = GOOD if good else BAD

def highlight_hitbox():
    in_window = abs(arrow_y - HITBOX_Y) < HIT_WINDOW and not arrow_attempted
    hitbox_rect.border_color = MAGENTA if in_window else BORDER

def update_labels():
    patient_window.switch_to()
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    score_label.text = f"{score:,}"
    streak_label.text = str(streak)
    accuracy_label.text = f"{accuracy}%"
    level_label.text = str(1 + total_hits // 10)    # +1 level every 10 hits
    if timing_errors:
        reaction_label.text = f"Avg Timing Error: {int(get_average_timing_error() * 1000)} ms"
    else:
        reaction_label.text = "Avg Timing Error: --"

def reset_arrow():
    global arrow_y, current_direction, arrow_attempted
    arrow_y = -50 
    current_direction = random.choice(VALID_DIRECTIONS)
    arrow_attempted = False
    
    patient_window.switch_to()
    arrow_sprite.image = ARROW_IMAGES[current_direction]
    arrow_sprite.y = arrow_y

def start_game():
    global score, total_attempts, total_hits, streak, time_remaining, timing_errors, attempt_log
    pyglet.clock.unschedule(update)

    score = 0
    total_attempts = 0
    total_hits = 0
    streak = 0
    time_remaining = 60.0
    timing_errors = []
    attempt_log = []
    reset_arrow()
    
    patient_window.switch_to()
    set_feedback("", True)
    update_labels()
    set_timer_text()
    highlight_hitbox()
    
    pyglet.clock.schedule_interval(update, 1/60.0)

def stop_game():
    pyglet.clock.unschedule(update)
    
    doctor_window.switch_to()
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    timing_text = f", Avg Timing Error {int(get_average_timing_error() * 1000)} ms" if timing_errors else ""
    config_screen.doctor_feedback.text = (
        f"Last Session - Pursuits: Targets {total_hits}/{total_attempts} ({accuracy}%){timing_text}"
    )

def update(dt):
    global arrow_y, time_remaining, total_attempts, streak, total_hits 
    
    time_remaining -= dt
    if time_remaining <= 0:
        GameState.current_mode = "CONFIG"
        stop_game()
        return
        
    arrow_y += arrow_speed * dt
    
    if arrow_y > ARROW_EXIT_Y:
        if not arrow_attempted:
            total_attempts += 1
            streak = 0
            attempt_log.append(False)
            patient_window.switch_to()
            set_feedback("MISS! No input detected!", False)
            update_labels()
            
        reset_arrow()
        
    patient_window.switch_to()
    arrow_sprite.y = arrow_y
    highlight_hitbox()
    set_timer_text()

def draw_doctor():
    config_screen.draw_live_doctor(
        mode_name="Pursuits",
        score=score,
        streak=streak,
        total_hits=total_hits,
        total_attempts=total_attempts,
        level=1 + total_hits // 10,
        time_remaining=time_remaining,
        last_event=feedback_label.text,
        attempt_log=attempt_log,
        avg_label="Avg Timing Error",
        avg_text=f"{int(get_average_timing_error() * 1000)} ms" if timing_errors else "--",
    )

def draw_patient():
    hud_batch.draw()
    for label in card_titles:
        label.draw()
    logo_label.draw()
    subtitle_label.draw()
    timer_label.draw()
    hint_label.draw()
    score_label.draw()
    streak_label.draw()
    accuracy_label.draw()
    level_label.draw()
    feedback_label.draw()
    reaction_label.draw()
    hitbox_rect.draw()

    if VISIBLE_MIN_Y < arrow_y < VISIBLE_MAX_Y:
        arrow_sprite.draw()

def handle_patient_input(symbol):
    global score, total_attempts, total_hits, streak, arrow_attempted
    patient_window.switch_to()

    if symbol == key.ESCAPE:
        GameState.current_mode = "CONFIG"
        stop_game()
        return

    if symbol in VALID_DIRECTIONS and not arrow_attempted:
        arrow_attempted = True
        total_attempts += 1

        timing_correct = abs(arrow_y - HITBOX_Y) < HIT_WINDOW
        direction_correct = (symbol == current_direction)

        if timing_correct and direction_correct:
            streak += 1
            total_hits += 1
            timing_errors.append(abs(arrow_y - HITBOX_Y) / arrow_speed)
            attempt_log.append(True)

            points_earned = 100 + (25 * (streak // 5))
            score += points_earned

            set_feedback(f"HIT! Perfect {key.symbol_string(symbol)}! (+{points_earned})", True)
            reset_arrow()
        else:
            streak = 0
            attempt_log.append(False)
            if not timing_correct:
                set_feedback("MISS! Bad timing!", False)
            elif not direction_correct:
                set_feedback(f"MISS! Wrong direction. Expected: {key.symbol_string(current_direction)}", False)

        update_labels()