"""Persistent settings, stats and crash logs.

Files live in a per-user folder:
    Windows: %APPDATA%\\Pambaram
    others : ~/.pambaram

Set PAMBARAM_NO_SAVE=1 to disable all reading/writing (the test suite does
this so it never touches a player's real save data). Every read is
validated, so a missing, corrupt or hand-edited file falls back to defaults
instead of crashing the game.
"""
import json
import os
import sys
import tempfile
import traceback
from datetime import datetime

from .config import TOP_PRESETS, ARENA_PRESETS, Difficulty

DEFAULTS = {
    "p1_top": "Thiruvalluvar",
    "p2_top": "Velu Vettaikaran",
    "arena": "Gramam Thidal",
    "p2_is_ai": True,
    "difficulty": "MEDIUM",
    "muted": False,
    "fullscreen": False,
    "stats": {
        "matches": 0,
        "p1_wins": 0,
        "p2_wins": 0,
        "draws": 0,
        "best_score": 0,
        "wins_vs_ai_by_difficulty": {"EASY": 0, "MEDIUM": 0, "HARD": 0},
    },
}


def persistence_enabled():
    return os.environ.get("PAMBARAM_NO_SAVE", "") not in ("1", "true", "yes")


def data_dir():
    base = os.environ.get("APPDATA") if sys.platform == "win32" else None
    if base:
        return os.path.join(base, "Pambaram")
    return os.path.join(os.path.expanduser("~"), ".pambaram")


def _settings_path():
    return os.path.join(data_dir(), "settings.json")


def _deepcopy(d):
    return json.loads(json.dumps(d))


def _validate(raw):
    s = _deepcopy(DEFAULTS)
    if not isinstance(raw, dict):
        return s
    if raw.get("p1_top") in TOP_PRESETS:
        s["p1_top"] = raw["p1_top"]
    if raw.get("p2_top") in TOP_PRESETS:
        s["p2_top"] = raw["p2_top"]
    if raw.get("arena") in ARENA_PRESETS:
        s["arena"] = raw["arena"]
    if raw.get("difficulty") in Difficulty.__members__:
        s["difficulty"] = raw["difficulty"]
    for key in ("p2_is_ai", "muted", "fullscreen"):
        if isinstance(raw.get(key), bool):
            s[key] = raw[key]
    stats = raw.get("stats")
    if isinstance(stats, dict):
        for key in ("matches", "p1_wins", "p2_wins", "draws", "best_score"):
            v = stats.get(key)
            if isinstance(v, int) and v >= 0:
                s["stats"][key] = v
        by_diff = stats.get("wins_vs_ai_by_difficulty")
        if isinstance(by_diff, dict):
            for d in s["stats"]["wins_vs_ai_by_difficulty"]:
                v = by_diff.get(d)
                if isinstance(v, int) and v >= 0:
                    s["stats"]["wins_vs_ai_by_difficulty"][d] = v
    return s


def load():
    if not persistence_enabled():
        return _deepcopy(DEFAULTS)
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            return _validate(json.load(f))
    except (OSError, ValueError):
        return _deepcopy(DEFAULTS)


def save(settings):
    """Atomic write (temp file + replace) so a crash mid-save can't corrupt
    the file. Failures are ignored: losing a save must never crash the game."""
    if not persistence_enabled():
        return False
    try:
        folder = data_dir()
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, prefix="settings-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        os.replace(tmp, _settings_path())
        return True
    except OSError:
        return False


def write_crash_log(exc):
    """Append a traceback to crash.log; returns the path (or None)."""
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        folder = data_dir()
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "crash.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.now().isoformat(timespec='seconds')} =====\n{text}")
        return path
    except OSError:
        return None
