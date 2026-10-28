import os
import pyglet
from pyglet.window import key

# Arrow images live in src/assets/arrows/ (this file is in src/engine/)
ARROW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'arrows')

ARROW_FILES = {
    key.UP: 'up.png',
    key.DOWN: 'down.png',
    key.LEFT: 'left.png',
    key.RIGHT: 'right.png',
}

def load_arrow_images():
    # Call after a window exists (and ideally after patient_window.switch_to())
    images = {}
    for symbol, filename in ARROW_FILES.items():
        image = pyglet.image.load(os.path.join(ARROW_DIR, filename))
        # Anchor at the center so a sprite's x/y is the middle of the arrow
        image.anchor_x = image.width // 2
        image.anchor_y = image.height // 2
        images[symbol] = image
    return images