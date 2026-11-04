"""
Persistent storage manager for GatorSight therapy sessions using JSON.

Handles saving, retrieving, and validating clinical session records across
application restarts, connecting internal game engine metrics to the doctor UI.
"""

import os
import json
import datetime
import tempfile

# Root data directory: gator-sight/data/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
ARCHIVE_DIR = os.path.join(DATA_DIR, "sessions")


def _ensure_dirs():
    """Ensure data storage directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)


def _load_all():
    """
    Load all session records from data/sessions.json.
    Includes error handling for corrupted files.
    """
    _ensure_dirs()
    if not os.path.exists(SESSIONS_FILE):
        return []

    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError) as e:
        # Resilience: Backup corrupted file and recover gracefully
        corrupt_backup = os.path.join(DATA_DIR, f"sessions.corrupt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            if os.path.exists(SESSIONS_FILE):
                os.rename(SESSIONS_FILE, corrupt_backup)
        except OSError:
            pass
        return []


def _save_all(sessions):
    """
    Atomically write the sessions list to data/sessions.json.
    Uses a temporary file before renaming to ensure data integrity.
    """
    _ensure_dirs()
    # Write to a temp file in the same directory first
    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, prefix="sessions_", suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # Replace target file atomically
        os.replace(temp_path, SESSIONS_FILE)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise


def save_session(session_data):
    """
    Persist a newly completed session to JSON storage.
    
    Args:
        session_data (dict): Session metrics from saccades or pursuits engine.

    Returns:
        dict: The normalized, saved session object with timestamps and id.
    """
    _ensure_dirs()
    now = datetime.datetime.now()
    mode = session_data.get("mode", "UNKNOWN").upper()
    session_id = f"{mode.lower()}_{now.strftime('%Y%m%d_%H%M%S')}"

    record = {
        "session_id": session_id,
        "timestamp": now.isoformat(),
        "date_formatted": now.strftime("%m/%d/%Y %I:%M %p"),
        "mode": mode,
        "input_mode": session_data.get("input_mode", "KEYBOARD"),
        "duration_seconds": session_data.get("duration_seconds", 60.0),
        "score": session_data.get("score", 0),
        "streak": session_data.get("streak", 0),
        "level": session_data.get("level", 1),
        "total_attempts": session_data.get("total_attempts", 0),
        "total_hits": session_data.get("total_hits", 0),
        "accuracy_percent": session_data.get("accuracy_percent", 0),
        "avg_metric_label": session_data.get("avg_metric_label", ""),
        "avg_metric_value_ms": session_data.get("avg_metric_value_ms"),
        "summary_text": session_data.get("summary_text", ""),
        "attempt_log": session_data.get("attempt_log", []),
    }

    # 1. Update the master sessions.json list
    sessions = _load_all()
    sessions.append(record)
    _save_all(sessions)

    # 2. Save individual session archive file in data/sessions/
    archive_file = os.path.join(ARCHIVE_DIR, f"{session_id}.json")
    try:
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
    except OSError:
        pass

    return record


def get_last_session():
    """
    Retrieve the most recent session from persistent storage.

    Returns:
        dict or None: The latest session dictionary if available, else None.
    """
    sessions = _load_all()
    if sessions:
        return sessions[-1]
    return None


def get_all_sessions():
    """
    Retrieve all recorded sessions.

    Returns:
        list[dict]: List of session dictionaries, ordered chronologically.
    """
    return _load_all()


def get_session_by_id(session_id):
    """
    Retrieve a specific session by its session_id.
    """
    sessions = _load_all()
    for s in sessions:
        if s.get("session_id") == session_id:
            return s
    return None

