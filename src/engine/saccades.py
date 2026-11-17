import pyglet
from pyglet.window import key
import random
import math
from src.ui.displays import GameState, doctor_window, patient_window
from src.ui import config_screen
from src.engine.arrows import load_arrow_images
from src.engine import input_manager
from src.storage import session_store


# ---------- Aesthetics ---------- NOTEEE 10/28: make sure to add install font on READ.ME
FONT = "Pixelify Sans"          # install this font on the PC; can be found under "/src/assets/fonts/Pixelify Sans.ttf" and click install!
NAVY = (0, 0, 52)
PURPLE = (118, 10, 122)
CARD_FILL = (6, 6, 60)
BORDER = (91, 111, 181)
MAGENTA = (255, 43, 214)
BOX_FILL = (40, 40, 100)        # still used by pursuits.py, don't delete
WHITE = (255, 255, 255, 255)
MUTED = (201, 207, 252, 255)
GOOD = (124, 255, 178, 255)
BAD = (255, 107, 138, 255)

# extra colors for the hit boxes at the bottom
BOX_ACTIVE_FILL = (72, 14, 112)         # box you should answer RIGHT NOW (brighter purple)
BOX_PENDING_BORDER = (178, 82, 206)     # box the NEXT arrow is heading to (softer magenta)

# Pursuits imports these three from this file, so they stay even though saccades no longer draws stat cards
# remove later after i adjust arrows in pursuits.py to not use these and instead be white on the purple background
CARD_W, CARD_H = 208, 150
CARD_POSITIONS = {"Score": (48, 434), "Streak": (48, 264), "Accuracy": (1024, 434), "Level": (1024, 264)}

# difficulty settings
LEVEL_EVERY_HITS = 10   # +1 level every 10 hits
START_STEP = 1.2        # seconds each arrow sits in the hit box on level 1 (slow, comfortable)
MIN_STEP = .7          # fastest it gets
STEP_DECAY = 0.4       # each level shaves this much off the step time
LEAD_IN = 1.0           
LEVEL_COLUMNS = {1: (0, 5), 2: (1, 4), 3: (2, 3)}


# layout constants
patient_window.switch_to()
hud_batch = pyglet.graphics.Batch()
bg_group = pyglet.graphics.Group(order=0)

# creating the bg gradient (unchanged)
STRIPS = 72
strip_height = 720 / STRIPS
background = []
for i in range(STRIPS):
    from_top = 1 - (i + 0.5) / STRIPS
    blend = max(0.0, (from_top - 0.30) / 0.70)      # top 30% stays navy, then fades to purple
    color = tuple(int(a + (b - a) * blend) for a, b in zip(NAVY, PURPLE))
    background.append(pyglet.shapes.Rectangle(0, int(i * strip_height), 1280, math.ceil(strip_height) + 1,
                                              color=color, batch=hud_batch, group=bg_group))

NUM_COLUMNS = 6
NUM_ROWS = 5                      # row 0 = hit row (the boxes), row 4 = where new arrows appear
COLUMN_PITCH = 163
COLUMN_X = [640 + (i - (NUM_COLUMNS - 1) / 2) * COLUMN_PITCH for i in range(NUM_COLUMNS)]
BOX_W, BOX_H = 130, 112
BOX_BOTTOM = 28
BOX_RADIUS = 16
BOX_BORDER = 3
GLOW = 9                          # how far the highlight halo spreads around a box
ROW_PITCH = 104                   # same distance between EVERY row, no gaps
HIT_ROW_Y = BOX_BOTTOM + BOX_H / 2
ARROW_SCALE = 0.66                

WHITE_ARROWS = True              

# arrow opacity by row: the arrow in the hit box is solid
OPACITY_HIT = 255
OPACITY_NEXT = 150                # the row right above next row is faded, so you can see what next is coming
OPACITY_FAR = 95

CALLOUT_X, CALLOUT_Y = 640, 380   # "NICE!" position, as in the Figma frame
CALLOUT_TIME = 0.8
CALLOUT_FADE = 0.35
FLASH_TIME = 0.28                 # how long a box flashes green / red after an answer


def row_y(row):
    return HIT_ROW_Y + row * ROW_PITCH


# ---------- Labels ----------
timer_label = pyglet.text.Label('1:00', font_name=FONT, font_size=32, x=1232, y=674,
                                anchor_x='right', anchor_y='top', color=WHITE)
hint_label = pyglet.text.Label('Press Esc to end the session', font_size=11, weight="bold", x=1232, y=614,
                               anchor_x='right', anchor_y='top', color=MUTED)
# short patient-facing word in the middle ("NICE!"). feedback_label below is kept ONLY as the
# long text the doctor dashboard reads (it starts with HIT / MISS), it is no longer drawn on the patient screen.
callout_label = pyglet.text.Label('NICE!', font_name=FONT, font_size=20, x=CALLOUT_X, y=CALLOUT_Y,
                                  anchor_x='center', anchor_y='center', color=WHITE)
feedback_label = pyglet.text.Label('', font_size=15, weight="bold", x=640, y=34, anchor_x='center', anchor_y='center')
reaction_times = []

# ---------- Game state ----------
score = 0
streak = 0
total_attempts = 0
total_hits = 0
time_remaining = 60.0
attempt_log = []

VALID_DIRECTIONS = [key.UP, key.DOWN, key.LEFT, key.RIGHT]

arrows = []               # every arrow on screen, one dict each (see spawn_arrow)
last_side = "right"       # side of the most recently spawned arrow, so the next one flips
next_step_in = LEAD_IN    # countdown to the next row step
callout_timer = 0.0
flashes = {}              # column -> [color, seconds left]


# Hit boxes: six rounded boxes along the bottom, each with a halo, border and fill
def whiten(image):
    # arrow PNGs are solid yellow, I set RGB to 255 so it's white (need to add for pursuits.py too)
    data = image.get_image_data()
    raw = bytearray(data.get_data('RGBA', data.width * 4))
    raw[0::4] = b'\xff' * (len(raw) // 4)
    raw[1::4] = b'\xff' * (len(raw) // 4)
    raw[2::4] = b'\xff' * (len(raw) // 4)
    white = pyglet.image.ImageData(data.width, data.height, 'RGBA', bytes(raw), pitch=data.width * 4)
    white.anchor_x, white.anchor_y = image.anchor_x, image.anchor_y
    return white

patient_window.switch_to()
ARROW_IMAGES = load_arrow_images()
if WHITE_ARROWS:
    ARROW_IMAGES = {k: whiten(v) for k, v in ARROW_IMAGES.items()}
box_batch = pyglet.graphics.Batch()
glow_group = pyglet.graphics.Group(order=0)
border_group = pyglet.graphics.Group(order=1)
fill_group = pyglet.graphics.Group(order=2)


class LaneBox:
    def __init__(self, cx):
        x = cx - BOX_W / 2
        y = BOX_BOTTOM
        self.glow = pyglet.shapes.RoundedRectangle(x - GLOW, y - GLOW, BOX_W + 2 * GLOW, BOX_H + 2 * GLOW,
                                                   BOX_RADIUS + GLOW, color=(*MAGENTA, 0),
                                                   batch=box_batch, group=glow_group)
        self.border = pyglet.shapes.RoundedRectangle(x, y, BOX_W, BOX_H, BOX_RADIUS, color=BORDER,
                                                     batch=box_batch, group=border_group)
        self.fill = pyglet.shapes.RoundedRectangle(x + BOX_BORDER, y + BOX_BORDER, BOX_W - 2 * BOX_BORDER,
                                                   BOX_H - 2 * BOX_BORDER, BOX_RADIUS - BOX_BORDER,
                                                   color=CARD_FILL, batch=box_batch, group=fill_group)
        self._style = None

    def set_style(self, border, fill, glow):
        # only touch when something actually changed
        style = (border, fill, glow)
        if style != self._style:
            self.border.color = border
            self.fill.color = fill
            self.glow.color = glow
            self._style = style


boxes = [LaneBox(cx) for cx in COLUMN_X]

# The 3 looks a box can have
STYLE_IDLE = (BORDER, CARD_FILL, (*MAGENTA, 0))
STYLE_ACTIVE = (MAGENTA, BOX_ACTIVE_FILL, (*MAGENTA, 110))        # answer this one now
STYLE_PENDING = (BOX_PENDING_BORDER, CARD_FILL, (*MAGENTA, 35))   # the next arrow is heading here

# One sprite per possible on-screen arrow
arrow_sprites = [pyglet.sprite.Sprite(ARROW_IMAGES[key.UP]) for _ in range(NUM_ROWS)]
for s in arrow_sprites:
    s.scale = ARROW_SCALE


# Difficulty helpers: level, columns, step time
def current_level():
    return 1 + total_hits // LEVEL_EVERY_HITS

def columns_for_level(level):
    return LEVEL_COLUMNS[min(level, max(LEVEL_COLUMNS))]

def step_for_level(level):
    return max(MIN_STEP, START_STEP - STEP_DECAY * (level - 1))


def get_average_reaction():
    return sum(reaction_times) / len(reaction_times) if reaction_times else 0.0

# changed it so that it's easier for the label creation and updating
def set_timer_text():
    seconds = max(0, int(math.ceil(time_remaining)))
    timer_label.text = f"{seconds // 60}:{seconds % 60:02d}"

def set_feedback(text, good):
    feedback_label.text = text
    feedback_label.color = GOOD if good else BAD

# Words for performance feedback
def show_callout(text, color):
    global callout_timer
    patient_window.switch_to()      
    callout_label.text = text
    callout_label.color = color
    callout_timer = CALLOUT_TIME

def flash_box(column, color):
    flashes[column] = [color, FLASH_TIME]


# arrow spawning, movement, and scoring
def spawn_arrow(row):
    # One arrow per row, alternating left / right towards the middle column as level goes up
    # Columns come from the current level, so higher levels spawn arrows closer to the middle.
    global last_side
    last_side = "left" if last_side == "right" else "right"
    left_col, right_col = columns_for_level(current_level())
    arrows.append({
        "row": row,
        "side": last_side,
        "col": left_col if last_side == "left" else right_col,
        "dir": random.choice(VALID_DIRECTIONS),
        "since": 0.0,       # seconds it has been waiting in the hit box (for reaction time)
    })

def arrow_at_row(row):
    for a in arrows:
        if a["row"] == row:
            return a
    return None

def register_miss(arrow, text):
    global total_attempts, streak
    total_attempts += 1
    streak = 0
    attempt_log.append(False)
    flash_box(arrow["col"], BAD)
    set_feedback(text, False)
    show_callout("MISS", BAD)

def advance_step():
    # Everything moves down exactly one row
    global next_step_in

    # whatever sat in the hit box and wasn't answered is a miss, then it's gone
    a = arrow_at_row(0)
    if a:
        register_miss(a, "MISS! No input detected!")
        arrows.remove(a)

    # the rest hop down one row (no sliding so it's purely saccades
    for a in arrows:
        a["row"] -= 1

    # a fresh arrow appears at the top, on the opposite side of the one below it
    spawn_arrow(NUM_ROWS - 1)

    # rhythm for the next step depends on the level, will probably increase the spee in future iterations
    next_step_in = step_for_level(current_level())

def refresh_boxes():
    styles = [STYLE_IDLE] * NUM_COLUMNS
    upcoming = arrow_at_row(1)
    if upcoming:
        styles[upcoming["col"]] = STYLE_PENDING
    current = arrow_at_row(0)
    if current:
        styles[current["col"]] = STYLE_ACTIVE
    for col, (color, _) in flashes.items():
        styles[col] = (color[:3], BOX_ACTIVE_FILL if color == GOOD else (90, 14, 60), (*color[:3], 130))
    for box, style in zip(boxes, styles):
        box.set_style(*style)

def start_game():
    global score, total_attempts, total_hits, streak, time_remaining, reaction_times, attempt_log
    global next_step_in, callout_timer, last_side

    # Safeguard against stacked clock callbacks
    pyglet.clock.unschedule(update)
    patient_window.switch_to()

    score = 0
    total_attempts = 0
    total_hits = 0
    streak = 0
    time_remaining = 60.0
    reaction_times = []
    attempt_log = []          

    # Start with the board already populated so the patient isn't staring at nothing for sev secs
    arrows.clear()
    flashes.clear()
    last_side = random.choice(["left", "right"])
    for row in range(1, NUM_ROWS):          # bottom-up, so the alternation continues correctly at the top
        spawn_arrow(row)
    next_step_in = LEAD_IN
    callout_timer = 0.0

    callout_label.text = ""
    set_feedback("", True)
    set_timer_text()
    refresh_boxes()

    pyglet.clock.schedule_interval(update, 1/60.0)

def stop_game():
    pyglet.clock.unschedule(update)

    doctor_window.switch_to()
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    if reaction_times:
        reaction_text = f", Avg Reaction {int(get_average_reaction() * 1000)} ms"
    else:
        reaction_text = ""
    summary = f"Targets {total_hits}/{total_attempts} ({accuracy}%){reaction_text}"

    if total_attempts > 0:
        session_store.save_session({
            "mode": "SACCADES",
            "input_mode": input_manager.mode,
            "duration_seconds": round(60.0 - max(0.0, time_remaining), 1),
            "score": score,
            "streak": streak,
            "level": current_level(),
            "total_attempts": total_attempts,
            "total_hits": total_hits,
            "accuracy_percent": accuracy,
            "avg_metric_label": "Avg Reaction",
            "avg_metric_value_ms": int(get_average_reaction() * 1000) if reaction_times else None,
            "summary_text": summary,
            "attempt_log": attempt_log,
        })
    config_screen.load_last_session()

def update(dt):
    global time_remaining, next_step_in, callout_timer

    time_remaining -= dt
    if time_remaining <= 0:
        GameState.current_mode = "CONFIG"
        stop_game()
        return

    patient_window.switch_to() 

    # reaction clock for the arrow that's waiting in the boxes
    a = arrow_at_row(0)
    if a:
        a["since"] += dt

    next_step_in -= dt
    if next_step_in <= 0:
        advance_step()

    # box flashes and the callout fade out on their own
    for col in list(flashes):
        flashes[col][1] -= dt
        if flashes[col][1] <= 0:
            del flashes[col]
    if callout_timer > 0:
        callout_timer -= dt
        alpha = 255 if callout_timer > CALLOUT_FADE else int(255 * max(0.0, callout_timer) / CALLOUT_FADE)
        callout_label.color = (*callout_label.color[:3], alpha)

    refresh_boxes()
    set_timer_text()

def draw_doctor():
   # draws live dashboard for doctor window
   config_screen.draw_live_doctor(
        mode_name="Saccades",
        score=score,
        streak=streak,
        total_hits=total_hits,
        total_attempts=total_attempts,
        level=current_level(),                   
        time_remaining=time_remaining,
        last_event=feedback_label.text,
        attempt_log=attempt_log,
        avg_label="Avg Reaction",
        avg_text=f"{int(get_average_reaction() * 1000)} ms" if reaction_times else "--",
    )

def draw_patient():
    hud_batch.draw()                       # gradient background
    box_batch.draw()                       # the six hit boxes (bottom)

    # arrows: solid in the boxes, faded everywhere above
    for sprite, a in zip(arrow_sprites, arrows):
        if a["row"] == 0:
            sprite.opacity = OPACITY_HIT
        elif a["row"] == 1:
            sprite.opacity = OPACITY_NEXT
        else:
            sprite.opacity = OPACITY_FAR
        image = ARROW_IMAGES[a["dir"]]
        if sprite.image is not image:
            sprite.image = image
        sprite.x = COLUMN_X[a["col"]]
        sprite.y = row_y(a["row"])
        sprite.draw()

    timer_label.draw()
    hint_label.draw()
    if callout_timer > 0:
        callout_label.draw()

def handle_patient_input(symbol):
    global score, total_attempts, total_hits, streak
    patient_window.switch_to()

    if symbol == key.ESCAPE:
        GameState.current_mode = "CONFIG"
        stop_game()
        return

    # Only process input while an arrow is sitting in the boxes
    a = arrow_at_row(0)
    if symbol in VALID_DIRECTIONS and a:
        level_before = current_level()
        total_attempts += 1

        if symbol == a["dir"]:
            streak += 1
            total_hits += 1
            reaction_times.append(a["since"])
            attempt_log.append(True)
            points_earned = 100 + (25 * (streak // 5))
            score += points_earned

            feedback_label.text = (f"HIT! {key.symbol_string(symbol)} in {int(a['since'] * 1000)} ms "
                                   f"(+{points_earned})")
            flash_box(a["col"], GOOD)
            show_callout("NICE!", WHITE)
            if current_level() > level_before:
                show_callout(f"LEVEL {current_level()}!", (*MAGENTA, 255))
        else:
            streak = 0
            attempt_log.append(False)
            feedback_label.text = f"MISS! Wrong direction. Expected: {key.symbol_string(a['dir'])}"
            flash_box(a["col"], BAD)
            show_callout("MISS", BAD)

        arrows.remove(a)        # answered: it leaves the box, the next one arrives on the next step
        refresh_boxes()