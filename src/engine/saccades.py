import pyglet
from pyglet.window import key
import random
import math
from src.ui.displays import GameState, doctor_window, patient_window
from src.ui import config_screen
from src.engine.arrows import load_arrow_images


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
# 10/28/26: edited it so it's centered now, based off the new dimensions
doc_label = pyglet.text.Label('Saccades Mode Active - Monitoring Patient', font_size=16,
                              x=640, y=360, anchor_x='center')

patient_window.switch_to()
# 10/28/26: grouped bg gradient + 4 stat cards in one batch so they draw in one call
hud_batch = pyglet.graphics.Batch()
bg_group = pyglet.graphics.Group(order=0)
card_group = pyglet.graphics.Group(order=1)

# creating the bg gradient
STRIPS = 72
strip_height = 720 / STRIPS
background = []
for i in range(STRIPS):
    from_top = 1 - (i + 0.5) / STRIPS
    blend = max(0.0, (from_top - 0.30) / 0.70)      # top 30% stays navy, then fades to purple
    color = tuple(int(a + (b - a) * blend) for a, b in zip(NAVY, PURPLE))
    background.append(pyglet.shapes.Rectangle(0, int(i * strip_height), 1280, math.ceil(strip_height) + 1,
                                              color=color, batch=hud_batch, group=bg_group))

# creating the stat cards
CARD_W, CARD_H = 208, 150
CARD_POSITIONS = {"Score": (48, 434), "Streak": (48, 264), "Accuracy": (1024, 434), "Level": (1024, 264)}
cards = []
card_titles = []
for title, (cx, cy) in CARD_POSITIONS.items():
    cards.append(pyglet.shapes.BorderedRectangle(cx, cy, CARD_W, CARD_H, border=3, color=CARD_FILL,
                                                 border_color=BORDER, batch=hud_batch, group=card_group))
    card_titles.append(pyglet.text.Label(title, font_size=11, weight="bold", x=cx + 20, y=cy + CARD_H - 16,
                                     anchor_y='top', color=MUTED))

logo_label = pyglet.text.Label('GatorSight', font_name=FONT, font_size=34, x=48, y=674, anchor_y='top', color=WHITE)
subtitle_label = pyglet.text.Label('Saccades, Normal Display', font_size=11, weight="bold", x=50, y=614,
                                   anchor_y='top', color=MUTED)
timer_label = pyglet.text.Label('1:00', font_name=FONT, font_size=32, x=1232, y=674,
                                anchor_x='right', anchor_y='top', color=WHITE)
hint_label = pyglet.text.Label('Press Esc to end the session', font_size=11, weight="bold", x=1232, y=614,
                               anchor_x='right', anchor_y='top', color=MUTED)

# big numbers inside the cards
score_label = pyglet.text.Label('0', font_name=FONT, font_size=33, x=68, y=462, color=WHITE)
streak_label = pyglet.text.Label('0', font_name=FONT, font_size=33, x=68, y=292, color=WHITE)
accuracy_label = pyglet.text.Label('0%', font_name=FONT, font_size=33, x=1044, y=462, color=WHITE)
level_label = pyglet.text.Label('1', font_name=FONT, font_size=33, x=1044, y=292, color=WHITE)

feedback_label = pyglet.text.Label('', font_size=15, weight="bold", x=640, y=34, anchor_x='center', anchor_y='center')
reaction_label = pyglet.text.Label('Avg Reaction: --', font_size=11, weight="bold", x=1232, y=34,
                                   anchor_x='right', anchor_y='center', color=MUTED)

# Gameplay and Timer variables
LEFT_BOX_X = 380
RIGHT_BOX_X = 900
BOX_Y = 327
BOX_SIZE = 140
ARROW_SCALE = 0.9      # 128px images drawn at ~115px to fit inside the 140px boxes
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
ARROW_IMAGES = load_arrow_images()
left_box = pyglet.shapes.BorderedRectangle(LEFT_BOX_X - BOX_SIZE // 2, BOX_Y - BOX_SIZE // 2, BOX_SIZE, BOX_SIZE,
                                           border=4, color=BOX_FILL, border_color=BORDER)
right_box = pyglet.shapes.BorderedRectangle(RIGHT_BOX_X - BOX_SIZE // 2, BOX_Y - BOX_SIZE // 2, BOX_SIZE, BOX_SIZE,
                                            border=4, color=BOX_FILL, border_color=BORDER)
arrow_sprite = pyglet.sprite.Sprite(ARROW_IMAGES[key.UP], x=LEFT_BOX_X, y=BOX_Y)
arrow_sprite.scale = ARROW_SCALE

def get_average_reaction():
    return sum(reaction_times) / len(reaction_times) if reaction_times else 0.0

# changed it so that it's easier for the label creation and updating
def set_timer_text():
    seconds = max(0, int(math.ceil(time_remaining)))
    timer_label.text = f"{seconds // 60}:{seconds % 60:02d}"

def set_feedback(text, good):
    feedback_label.text = text
    feedback_label.color = GOOD if good else BAD

def highlight_target_box():
    # The box with the active arrow gets a magenta border
    left_box.border_color = MAGENTA if (target_visible and target_side == "LEFT") else BORDER
    right_box.border_color = MAGENTA if (target_visible and target_side == "RIGHT") else BORDER

def update_labels():
    patient_window.switch_to()
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    score_label.text = f"{score:,}"
    streak_label.text = str(streak)
    accuracy_label.text = f"{accuracy}%"
    level_label.text = str(1 + total_hits // 10)    # +1 level every 10 hits
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
    arrow_sprite.image = ARROW_IMAGES[current_direction]
    arrow_sprite.x = LEFT_BOX_X if target_side == "LEFT" else RIGHT_BOX_X
    highlight_target_box()

def end_target():
    # Hide the arrow and begin the blank gap before the next one appears
    global target_visible, gap_elapsed
    target_visible = False
    gap_elapsed = 0.0
    patient_window.switch_to()
    highlight_target_box()    

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
    set_feedback("", True)
    update_labels()
    set_timer_text()

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
            set_feedback("MISS! No input detected!", False)
            update_labels()
            end_target()
    else:
        gap_elapsed += dt
        if gap_elapsed >= GAP_DURATION:
            show_next_target()

    patient_window.switch_to()
    set_timer_text()

def draw_doctor():
    doc_label.draw()

def draw_patient():
    hud_batch.draw()                       # gradient background + 4 cards
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
    left_box.draw()
    right_box.draw()

    if target_visible:
        arrow_sprite.draw()

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