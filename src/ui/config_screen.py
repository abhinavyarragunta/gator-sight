import math
import pyglet
from pyglet.window import key
from src.ui.displays import GameState, doctor_window, patient_window
from src.engine import input_manager


# Install the keyboard / finger pad filter and serial poller on the patient window (once)
input_manager.install(patient_window)

# ---------- Aesthetics ---------- NOTEEE 10/28: make sure to add install font on READ.ME
FONT = "Pixelify Sans"
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
WARN = (255, 205, 92, 255)         
SESSION_SECONDS = 60.0             
RECENT_COUNT = 20       

# bordered card in same style as the patient stat cards
def _card(x, y, w, h, batch, group):
    return pyglet.shapes.BorderedRectangle(x, y, w, h, border=3, color=CARD_FILL,
                                           border_color=BORDER, batch=batch, group=group)

# only touch a label when its text actually changed (avoids re-layout every frame).
def _set(label, text):
    if label.text != text:
        label.text = text

# only touch a label when its color actually changed (avoids re-layout every frame).
def _set_color(label, color):
    """NEW: same idea as _set, for label colors."""
    if tuple(label.color) != tuple(color):
        label.color = color

# Doctor Window
doctor_window.switch_to()
dash_bg_batch = pyglet.graphics.Batch()
STRIPS = 72
_strip_height = 720 / STRIPS
dash_background = []
for i in range(STRIPS):
    from_top = 1 - (i + 0.5) / STRIPS
    blend = max(0.0, (from_top - 0.30) / 0.70)      # top 30% stays navy gradient into purple
    color = tuple(int(a + (b - a) * blend) for a, b in zip(NAVY, PURPLE))
    dash_background.append(pyglet.shapes.Rectangle(0, int(i * _strip_height), 1280,
                                                   math.ceil(_strip_height) + 1,
                                                   color=color, batch=dash_bg_batch))

# header labels used by both dashboard views
logo_label = pyglet.text.Label('GatorSight', font_name=FONT, font_size=34, x=48, y=674,
                               anchor_y='top', color=WHITE)

# Saccades/Pursits Cards  + Input device/last session cards
config_batch = pyglet.graphics.Batch()
cfg_card_group = pyglet.graphics.Group(order=1)
cfg_chip_group = pyglet.graphics.Group(order=2)

cfg_subtitle = pyglet.text.Label('Doctor Dashboard', font_size=11, weight="bold", x=50, y=614,
                                 anchor_y='top', color=MUTED)
status_label = pyglet.text.Label('READY', font_name=FONT, font_size=30, x=1232, y=674,
                                 anchor_x='right', anchor_y='top', color=GOOD)
cfg_hint = pyglet.text.Label('Choose a session to start the patient screen', font_size=11, weight="bold",
                             x=1232, y=614, anchor_x='right', anchor_y='top', color=MUTED)

# Session Cards (top row)
MODE_W, MODE_H, MODE_Y = 576, 210, 330
MODE_CARDS = [
    # (key label, title, tagline, description, footer)
    ("1", "Saccades", "Quick jumps between two targets",
     "An arrow appears in the left or right box. The patient presses the matching arrow "
     "before it disappears. Tracks hits, reaction time and accuracy.",
     "Press 1 to start"),
    ("2", "Pursuits", "Smooth tracking of a moving target",
     "An arrow glides up the lane toward the box. The patient presses the matching arrow "
     "just as it reaches the box. Tracks hits, timing and accuracy.",
     "Press 2 to start"),
]
mode_cards, mode_chips, mode_labels = [], [], []
for n, (key_text, title, tagline, desc, footer) in enumerate(MODE_CARDS):
    cx = 48 + n * (MODE_W + 32)
    mode_cards.append(_card(cx, MODE_Y, MODE_W, MODE_H, config_batch, cfg_card_group))
    chip_x, chip_y = cx + 24, MODE_Y + MODE_H - 24 - 56
    mode_chips.append(pyglet.shapes.BorderedRectangle(chip_x, chip_y, 56, 56, border=3, color=BOX_FILL,
                                                      border_color=MAGENTA, batch=config_batch,
                                                      group=cfg_chip_group))
    mode_labels.append(pyglet.text.Label(key_text, font_name=FONT, font_size=28, x=chip_x + 28,
                                         y=chip_y + 28, anchor_x='center', anchor_y='center', color=WHITE))
    mode_labels.append(pyglet.text.Label(title, font_name=FONT, font_size=26, x=cx + 104,
                                         y=MODE_Y + MODE_H - 24, anchor_y='top', color=WHITE))
    mode_labels.append(pyglet.text.Label(tagline, font_size=11, weight="bold", x=cx + 106,
                                         y=MODE_Y + MODE_H - 66, anchor_y='top', color=MUTED))
    mode_labels.append(pyglet.text.Label(desc, font_size=12, x=cx + 24, y=MODE_Y + MODE_H - 100,
                                         anchor_y='top', multiline=True, width=MODE_W - 48, color=WHITE))
    mode_labels.append(pyglet.text.Label(footer, font_size=12, weight="bold", x=cx + 24, y=MODE_Y + 20,
                                         anchor_y='bottom', color=MAGENTA))

# input device card + last session card (bottom row)
INFO_W, INFO_H, INFO_Y = 576, 210, 84
INPUT_X, LAST_X = 48, 48 + INFO_W + 32
_card(INPUT_X, INFO_Y, INFO_W, INFO_H, config_batch, cfg_card_group)
_card(LAST_X, INFO_Y, INFO_W, INFO_H, config_batch, cfg_card_group)
info_titles = [
    pyglet.text.Label('Input Device', font_size=11, weight="bold", x=INPUT_X + 20, y=INFO_Y + INFO_H - 16,
                      anchor_y='top', color=MUTED),
    pyglet.text.Label('Last Session', font_size=11, weight="bold", x=LAST_X + 20, y=INFO_Y + INFO_H - 16,
                      anchor_y='top', color=MUTED),
    pyglet.text.Label('Cycles: Keyboard, Finger Pad, Both', font_size=11, weight="bold", x=INPUT_X + 20,
                      y=INFO_Y + 20, anchor_y='bottom', color=MUTED),
]

doctor_label = pyglet.text.Label('Select a Session: press 1 for Saccades, 2 for Pursuits', font_size=13,
                                 weight="bold", x=48, y=574, anchor_y='top', color=WHITE)  # CHANGED: now a section heading
input_label = pyglet.text.Label('', font_size=14, x=INPUT_X + 20, y=INFO_Y + INFO_H - 56, anchor_y='top',
                                multiline=True, width=INFO_W - 40, color=WHITE)            # CHANGED: lives in the Input card
doctor_feedback = pyglet.text.Label('', font_size=14, x=LAST_X + 20, y=INFO_Y + INFO_H - 56,
                                    anchor_y='top', multiline=True, width=INFO_W - 40,
                                    color=WHITE)                                           # CHANGED: lives in the Last Session card
last_placeholder = pyglet.text.Label('No sessions yet. Pick a session above to begin.', font_size=14,
                                     x=LAST_X + 20, y=INFO_Y + INFO_H - 56, anchor_y='top',
                                     multiline=True, width=INFO_W - 40, color=MUTED)

# warning bow for when dr tries to start session while fingerpad is calibrating/disconnected
doctor_alert = pyglet.text.Label('', font_size=15, weight="bold", x=640, y=40, anchor_x='center',
                                 anchor_y='center', color=BAD)

live_batch = pyglet.graphics.Batch()
live_card_group = pyglet.graphics.Group(order=1)

live_subtitle = pyglet.text.Label('Doctor Dashboard - Live Session', font_size=11, weight="bold", x=50, y=614,
                                  anchor_y='top', color=MUTED)
live_mode_label = pyglet.text.Label('', font_name=FONT, font_size=26, x=640, y=664, anchor_x='center',
                                    anchor_y='top', color=MAGENTA)
live_timer_label = pyglet.text.Label('1:00', font_name=FONT, font_size=32, x=1232, y=674, anchor_x='right',
                                     anchor_y='top', color=WHITE)
live_hint = pyglet.text.Label('Patient: press Esc to end the session', font_size=11, weight="bold", x=1232,
                              y=614, anchor_x='right', anchor_y='top', color=MUTED)

# Score / Streak / Accuracy / Level (row 1)
STAT_W, STAT_H, STAT_Y, STAT_GAP = 281, 150, 410, 20
stat_titles, stat_values = [], []
for n, title in enumerate(["Score", "Streak", "Accuracy", "Level"]):
    sx = 48 + n * (STAT_W + STAT_GAP)
    _card(sx, STAT_Y, STAT_W, STAT_H, live_batch, live_card_group)
    stat_titles.append(pyglet.text.Label(title, font_size=11, weight="bold", x=sx + 20, y=STAT_Y + STAT_H - 16,
                                         anchor_y='top', color=MUTED))
    stat_values.append(pyglet.text.Label('0', font_name=FONT, font_size=33, x=sx + 20, y=STAT_Y + 34,
                                         color=WHITE))

#recent attempts (row 2 left)
RECENT_X, RECENT_Y, RECENT_W, RECENT_H = 48, 190, 736, 190
_card(RECENT_X, RECENT_Y, RECENT_W, RECENT_H, live_batch, live_card_group)
recent_title = pyglet.text.Label('Recent Attempts (newest on the right)', font_size=11, weight="bold",
                                 x=RECENT_X + 20, y=RECENT_Y + RECENT_H - 14, anchor_y='top', color=MUTED)
SQUARE, SQUARE_GAP = 56, 12
attempt_squares = []
for i in range(RECENT_COUNT):
    row, col = divmod(i, 10)
    attempt_squares.append(pyglet.shapes.Rectangle(RECENT_X + 20 + col * (SQUARE + SQUARE_GAP),
                                                   RECENT_Y + 94 - row * (SQUARE + SQUARE_GAP),
                                                   SQUARE, SQUARE, color=BOX_FILL))

# session details (row 2 right)
DETAIL_X, DETAIL_Y, DETAIL_W, DETAIL_H = 816, 190, 416, 190
_card(DETAIL_X, DETAIL_Y, DETAIL_W, DETAIL_H, live_batch, live_card_group)
detail_title = pyglet.text.Label('Session Details', font_size=11, weight="bold", x=DETAIL_X + 20,
                                 y=DETAIL_Y + DETAIL_H - 16, anchor_y='top', color=MUTED)
hits_caption = pyglet.text.Label('Hits / Attempts', font_size=12, weight="bold", x=DETAIL_X + 20,
                                 y=DETAIL_Y + 124, color=MUTED)
hits_value = pyglet.text.Label('0 / 0', font_name=FONT, font_size=18, x=DETAIL_X + DETAIL_W - 20,
                               y=DETAIL_Y + 122, anchor_x='right', color=WHITE)
avg_caption = pyglet.text.Label('Avg Reaction', font_size=12, weight="bold", x=DETAIL_X + 20,
                                y=DETAIL_Y + 86, color=MUTED)
avg_value = pyglet.text.Label('--', font_name=FONT, font_size=18, x=DETAIL_X + DETAIL_W - 20,
                              y=DETAIL_Y + 84, anchor_x='right', color=WHITE)
event_caption = pyglet.text.Label('Last Event', font_size=12, weight="bold", x=DETAIL_X + 20,
                                  y=DETAIL_Y + 50, color=MUTED)
event_value = pyglet.text.Label('', font_size=12, weight="bold", x=DETAIL_X + 20, y=DETAIL_Y + 40,
                                anchor_y='top', multiline=True, width=DETAIL_W - 40, color=MUTED)

# time progress bar
BAR_X, BAR_Y, BAR_W, BAR_H = 48, 100, 1184, 20
progress_caption = pyglet.text.Label('Session Progress', font_size=11, weight="bold", x=BAR_X, y=BAR_Y + 30,
                                     color=MUTED)
progress_time = pyglet.text.Label('', font_size=11, weight="bold", x=BAR_X + BAR_W, y=BAR_Y + 30,
                                  anchor_x='right', color=MUTED)
progress_track = pyglet.shapes.Rectangle(BAR_X, BAR_Y, BAR_W, BAR_H, color=BOX_FILL)
progress_fill = pyglet.shapes.Rectangle(BAR_X, BAR_Y, 1, BAR_H, color=MAGENTA)
live_footer = pyglet.text.Label('Read-only view. The patient plays with the arrow keys / finger pad.',
                                font_size=11, weight="bold", x=640, y=44, anchor_x='center',
                                anchor_y='center', color=MUTED)

# Patient Window
patient_window.switch_to()
WAITING_TEXT = 'Waiting for Doctor...'
CALIBRATING_TEXT = "Calibrating finger pad - please don't touch the pads"
patient_label = pyglet.text.Label(WAITING_TEXT,
                               font_size=18, x=640, y=360, anchor_x='center')

# cache of last-shown text so we labels is only changed when something act changes
_shown = {"input": None, "patient": None, "status": None}

def refresh_input_status(dt):
    """Keeps the input mode / calibration status labels current."""
    text = input_manager.mode_text() + "   (press I to change)"
    if text != _shown["input"]:
        doctor_window.switch_to()
        input_label.text = text
        _shown["input"] = text

    # top-right status word on the home view
    if is_calibrating():
        status = ("CALIBRATING", WARN)
    elif input_manager.mode != input_manager.KEYBOARD and not input_manager.is_connected():
        status = ("CHECK INPUT", BAD)
    else:
        status = ("READY", GOOD)
    if status != _shown["status"]:
        doctor_window.switch_to()
        status_label.text = status[0]
        status_label.color = status[1]
        _shown["status"] = status

    patient_text = CALIBRATING_TEXT if is_calibrating() else WAITING_TEXT
    if patient_text != _shown["patient"]:
        patient_window.switch_to()
        patient_label.text = patient_text
        _shown["patient"] = patient_text


def is_calibrating():
    return input_manager.status.startswith("calibrating")


pyglet.clock.schedule_interval(refresh_input_status, 0.25)
refresh_input_status(0)


def draw_doctor():
    # temp home view meant for demo while not everything is functional
    dash_bg_batch.draw()
    config_batch.draw()
    logo_label.draw()
    cfg_subtitle.draw()
    status_label.draw()
    cfg_hint.draw()
    doctor_label.draw()
    for label in mode_labels:
        label.draw()
    for label in info_titles:
        label.draw()
    input_label.draw()
    if doctor_feedback.text:
        doctor_feedback.draw()
    else:
        last_placeholder.draw()
    doctor_alert.draw()

def draw_live_doctor(mode_name, score, streak, total_hits, total_attempts, level, time_remaining,
                     last_event, attempt_log, avg_label, avg_text):
    accuracy = int((total_hits / total_attempts) * 100) if total_attempts > 0 else 0
    time_left = max(0.0, time_remaining)
    seconds = int(math.ceil(time_left))

    # header
    _set(live_mode_label, f"{mode_name.upper()} - LIVE")
    _set(live_timer_label, f"{seconds // 60}:{seconds % 60:02d}")

    # stat cards
    _set(stat_values[0], f"{score:,}")
    _set(stat_values[1], str(streak))
    _set(stat_values[2], f"{accuracy}%")
    _set(stat_values[3], str(level))

    # details card
    _set(hits_value, f"{total_hits} / {total_attempts}")
    _set(avg_caption, avg_label)
    _set(avg_value, avg_text)
    _set(event_value, last_event if last_event else "Waiting for the first attempt...")
    if last_event.startswith("HIT"):
        _set_color(event_value, GOOD)
    elif last_event.startswith("MISS"):
        _set_color(event_value, BAD)
    else:
        _set_color(event_value, MUTED)

    recent = attempt_log[-RECENT_COUNT:]
    for i, square in enumerate(attempt_squares):
        if i < len(recent):
            square.color = GOOD[:3] if recent[i] else BAD[:3]
        else:
            square.color = BOX_FILL

    # progress bar (+ remaining time text)
    elapsed_fraction = min(1.0, max(0.0, 1.0 - time_left / SESSION_SECONDS))
    progress_fill.width = max(1, int(BAR_W * elapsed_fraction))
    _set(progress_time, f"{seconds // 60}:{seconds % 60:02d} remaining")

    # draw everything
    dash_bg_batch.draw()
    live_batch.draw()
    logo_label.draw()
    live_subtitle.draw()
    live_mode_label.draw()
    live_timer_label.draw()
    live_hint.draw()
    for label in stat_titles:
        label.draw()
    for label in stat_values:
        label.draw()
    recent_title.draw()
    for square in attempt_squares:
        square.draw()
    detail_title.draw()
    hits_caption.draw()
    hits_value.draw()
    avg_caption.draw()
    avg_value.draw()
    event_caption.draw()
    event_value.draw()
    progress_caption.draw()
    progress_time.draw()
    progress_track.draw()
    progress_fill.draw()
    live_footer.draw()
def draw_patient():
    patient_label.draw()

def handle_doctor_input(symbol):
    if symbol == key.I:
        input_manager.cycle_mode()  # Keyboard -> Finger Pad -> Both
        refresh_input_status(0)
        return

    if symbol in (key._1, key._2):
        if is_calibrating():
            doctor_feedback.text = "Finger pad is still calibrating - wait a moment, then try again"
            return

        if symbol == key._1:
            GameState.current_mode = "SACCADES"
        else:
            GameState.current_mode = "PURSUITS"
        # Reset feedback when starting a new session
        doctor_feedback.text = ""