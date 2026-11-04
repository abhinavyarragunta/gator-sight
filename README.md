# GatorSight
**Dance Dance Revolution Vision Therapy System**  
*CEN4907C / CEN3907C – Computer Engineering Design | University of Florida*

---

## Overview
**GatorSight** is a dual-display gamified vision therapy application inspired by rhythm games like Dance Dance Revolution. It trains and monitors oculomotor functions—specifically **saccadic eye movements** and **smooth visual pursuits**—through dynamic visual stimuli and responsive input tracking. 

The system uses a synchronized two-window architecture:
1. **Doctor Dashboard (`doctor_window`):** Provides clinical administration, session mode selection, real-time telemetry (accuracy, score, streak, attempt history, reaction latencies), and hardware status.
2. **Patient Gameplay (`patient_window`):** Delivers clean, high-contrast visual cues (saccades jumping targets or pursuit continuous movement) controlled via either a standard keyboard or a custom ESP32 capacitive touch finger pad.

---

## Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- (Optional) ESP32 development board running the capacitive touch finger pad firmware

### 1. Font Installation (Important)
GatorSight uses the custom retro font **Pixelify Sans**. To ensure all UI labels, stats, and retro counters align properly:
1. Navigate to [`src/assets/fonts/`](file:///c:/Users/yarra/OneDrive/Documents/UF/Year4/2026_Fall/CEN4907C/gator-sight/src/assets/fonts/).
2. Open `PixelifySans-VariableFont_wght.ttf`.
3. Click **Install** in the Windows font viewer.
*(If not installed, Pyglet falls back to system fonts, which may slightly alter label spacing).*

### 2. Environment Setup
1. Clone the repository and navigate to the project root:
   ```bash
   git clone https://github.com/abhinavyarragunta/gator-sight.git
   cd gator-sight
   ```
2. Create and activate a Python virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Running the Application
Launch the dual-display program:
```bash
python main.py
```

### 4. Controls & Navigation
- **Doctor Window:**
  - `1`: Launch **Saccades** session (60-second exercise).
  - `2`: Launch **Pursuits** session (60-second exercise).
  - `I`: Cycle active input method: `Keyboard` $\to$ `Finger Pad (ESP32)` $\to$ `Both (Keyboard + Finger Pad)`.
  - `Esc`: Exit application cleanly.
- **Patient Window:**
  - `Up`, `Down`, `Left`, `Right` arrows (or matching capacitive pads on ESP32): React to stimulus targets.
  - `Esc`: Abort active session and return to Doctor Configuration home view.

---

## Project Architecture

GatorSight is architected into three primary tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        External Interface Tier                         │
│  ┌───────────────────────────────┐   ┌──────────────────────────────┐  │
│  │   Doctor Dashboard (UI)       │   │   Patient Gameplay (UI)      │  │
│  │   - Configuration & Status    │   │   - High-contrast stimulus   │  │
│  │   - Live Telemetric Graphs    │   │   - Dynamic feedback cue     │  │
│  │   - Real-time 20-attempt log  │   │   - 1280x720 window          │  │
│  │   - 1280x720 window           │   └──────────────▲───────────────┘  │
│  └───────────────▲───────────────┘                  │                  │
└──────────────────┼──────────────────────────────────┼──────────────────┘
                   │                                  │
┌──────────────────┼──────────────────────────────────┼──────────────────┐
│                  │       Internal Processing Tier   │                  │
│  ┌───────────────┴───────────────┐   ┌──────────────┴───────────────┐  │
│  │   Doctor UI Controller        │   │   Game Engines               │  │
│  │   (src/ui/config_screen.py)   │   │   - src/engine/saccades.py   │  │
│  │   - Batch & group management  │   │   - src/engine/pursuits.py   │  │
│  │   - Cached label updates      │   │   - Kinematics & collision   │  │
│  └───────────────▲───────────────┘   │   - Latency & timing math    │  │
│                  │                   └──────────────▲───────────────┘  │
│                  │                                  │                  │
│                  └───────────────┬──────────────────┘                  │
│                                  │                                     │
│                     ┌────────────┴────────────┐                        │
│                     │   GameState / Engine    │                        │
│                     │   (src/ui/displays.py)  │                        │
│                     └────────────▲────────────┘                        │
│                                  │                                     │
│                     ┌────────────┴────────────┐                        │
│                     │   Input Manager         │                        │
│                     │   (src/engine/input_...)│                        │
│                     │   - Serial poller       │                        │
│                     │   - Event filtering     │                        │
│                     │   - Synthetic keypress  │                        │
│                     └────────────▲────────────┘                        │
└──────────────────────────────────┼─────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼─────────────────────────────────────┐
│                          Hardware Tier                                 │
│                     ┌────────────┴────────────┐                        │
│                     │   ESP32 Touch Pad       │                        │
│                     │   - Capacitive touch    │                        │
│                     │   - UART Serial 115200  │                        │
│                     └─────────────────────────┘                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Module Descriptions
- **`main.py`:** Application entry point and central Pyglet event loop dispatcher. Routes render calls and keyboard inputs between active modes.
- **`src/ui/displays.py`:** Initializes the dual 1280x720 windows (`doctor_window`, `patient_window`) and global `GameState` tracking (`CONFIG`, `SACCADES`, `PURSUITS`).
- **`src/ui/config_screen.py`:** Manages doctor view state, including mode selection cards, device polling status, live session dashboards, real-time 20-attempt visual status matrix, and session progress bar.
- **`src/engine/saccades.py`:** Saccadic training engine. Alternates targets across lateral visual zones with randomized directional arrow stimuli, measuring millisecond reaction latency and timeout expirations.
- **`src/engine/pursuits.py`:** Smooth pursuit training engine. Simulates continuous upward target movement along a tracking lane into a fixed hitbox window, calculating millisecond timing error offsets.
- **`src/engine/input_manager.py`:** Abstracted input handler. Discovers ESP32 dev boards by USB VID, polls incoming serial lines asynchronously (115200 baud), and translates capacitive touch events into synthetic Pyglet `on_key_press` events tagged with `TOUCH_FLAG`.
- **`src/engine/arrows.py`:** Asset loader for directional stimulus graphics (`up.png`, `down.png`, `left.png`, `right.png`).
- **`src/storage/session_store.py`:** Persistent state manager. Saves session metrics and telemetry atomically to `data/sessions.json` and `data/sessions/`, and reloads the latest clinical record on doctor dashboard startup.

---

## Completed Work (M1: Pre-Alpha Build)
- [x] **Dual Window Rendering Architecture:** Synchronized multi-window Pyglet environment with batch-optimized draw routines for smooth 60 FPS performance without context thrashing.
- [x] **Persistent State Storage (JSON):**
  - Session archival store located in `data/sessions.json` and timestamped records in `data/sessions/`.
  - Automatic load on Doctor Dashboard initialization displaying previous clinical results across application restarts.
  - Atomic write protection and corrupt data recovery.
- [x] **Saccades Training Engine:**
  - Alternating lateral stimulus boxes (left / right).
  - Randomized arrow directions.
  - Sub-millisecond reaction time logging.
  - 2.0-second timeout detection for missed stimuli.
- [x] **Pursuits Training Engine:**
  - Continuous vertical trajectory simulation with configurable speed.
  - Fixed target hitbox with dynamic proximity highlighting.
  - Timing error calculation relative to arrow velocity and hitbox center.
- [x] **Clinical Doctor Dashboard:**
  - Real-time telemetry: Score, streak, cumulative accuracy %, and level progression.
  - Live 20-attempt visual grid displaying immediate hit/miss history.
  - Elapsed and remaining session countdown with progress bar.
  - Post-session summary banner displaying final targets hit and average reaction latency.
- [x] **Multi-Input Subsystem:**
  - Standard keyboard support.
  - ESP32 capacitive touch integration via non-blocking serial port polling.
  - Input mode toggling (`Keyboard`, `Finger Pad`, `Both`) with strict event filter suppression to prevent cross-input spoofing.
  - Automatic capacitive sensor calibration detection and safety launch lock.

---

## Known Bugs & Current Limitations
*Documented in compliance with M1 Pre-Alpha rubric requirements.*

1. **Independent Window Closure Exception:**
   - *Description:* Closing one window directly using the operating system's title bar close button (`X`) causes an unhandled exception or leaves the other window / background serial poller orphaned.
   - *Workaround / Mitigation:* Exit the application using the `Esc` key on the Doctor Dashboard.
2. **Missing Font Spacing Variance:**
   - *Description:* If `Pixelify Sans` is not manually installed onto the host operating system, Pyglet falls back to Arial or the default system font. Because glyph bounding boxes differ, numerical text within stat cards can appear slightly misaligned.
   - *Workaround / Mitigation:* Install `PixelifySans-VariableFont_wght.ttf` from `src/assets/fonts/` prior to launch.
3. **Multi-Port Serial Collision:**
   - *Description:* `input_manager.py` scans known USB Vendor IDs (CP210x, CH340, FTDI, Espressif) and connects to the first matching device found. If multiple matching microcontrollers or serial adapters are connected to the PC, it may connect to the wrong port.
   - *Workaround / Mitigation:* Set the `SERIAL_PORT` variable manually in `src/engine/input_manager.py` (e.g., `SERIAL_PORT = "COM3"`) if multiple serial boards are attached.
4. **Single Patient Profile Context:**
   - *Description:* All session histories in `data/sessions.json` currently save under a unified global log; multi-patient profile selection, search, and historical trend comparison graphing are slated for the M2 prototype build.
   - *Workaround / Mitigation:* Clinical session records are archived individually in `data/sessions/` with unique ISO timestamps and IDs for manual review.
5. **Single-Axis Pursuits Pathing:**
   - *Description:* Pursuits mode target movement is currently restricted to vertical motion up a single center lane. Multidirectional, circular, and sinusoidal visual tracking paths will be added in upcoming milestones.
