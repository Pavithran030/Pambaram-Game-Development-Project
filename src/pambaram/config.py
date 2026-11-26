import pygame
import pygame.font
from enum import Enum

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
ARENA_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
ARENA_RADIUS = 280
RINGOUT_RADIUS = 320
MATCH_TIME = 180
TOP_LIFETIME = 180.0  # matches MATCH_TIME fallback

# --- Match start / launch -------------------------------------------------
# Both players aim during the countdown and every top launches at the same
# instant on "FIGHT!", so neither side gets a head start.
COUNTDOWN_STEP = 1.2        # seconds per countdown number (3, 2, 1)
LAUNCH_FORCE = 700.0        # launch speed (px/s) for a perfect launch
AIM_TURN_SPEED = 2.6        # keyboard aim rotation (rad/s)
FIGHT_BANNER_TIME = 0.9     # how long "FIGHT!" stays on screen after launch

# Launch power meter: swings 0 -> 1 -> 0 during the countdown. Locking it near
# the top of the swing is a perfect launch.
LAUNCH_METER_PERIOD = 1.1   # seconds for one full swing (0 -> 1 -> 0)
LAUNCH_UNLOCKED_QUALITY = 0.35  # quality if a player never locks the meter
LAUNCH_MIN_SPIN = 0.5       # starting stamina (fraction of max spin) at quality 0
LAUNCH_WEAK_DECAY = 0.6     # a quality-0 launch drains stamina 60% faster
LAUNCH_GRADES = [           # (min quality, label)
    (0.92, "PERFECT!"),
    (0.75, "GREAT"),
    (0.50, "GOOD"),
    (0.00, "WEAK"),
]

# --- Movement ---------------------------------------------------------------
STEER_ACCEL = 750.0         # px/s^2 steering push at full spin (scaled by grip)
BOWL_ACCEL = 170.0          # pull toward the centre at the rim (stadium slope)
PRECESSION_RATE = 0.5       # rad/s of path curving while spinning
FLOOR_FRICTION = 0.16       # per-second speed loss while spinning fast

# --- Combat / ring-out ----------------------------------------------------
KO_CONFIRM_TIME = 0.8       # seconds a top must stay out before the KO counts
HIT_WINDOW = 0.6            # a top counts as "just hit" for this long
RINGOUT_ESCAPE_SPEED = 700  # outward speed at the wall that carries a hit top over the edge
COLLISION_RESTITUTION = 0.8
MIN_IMPACT_SPEED = 90       # closing speed below this is a soft push, not a hit
WALL_SPIN_COST = 0.015       # fraction of max spin lost per wall or pillar bounce
COLLISION_SPIN_DAMAGE = 0.03  # spin lost per px/s of closing speed (before mass/spin weighting)
COLLISION_KNOCKBACK = 0.12    # extra push given to the weaker top
ATTACKER_BONUS = 1.5         # clash power bonus for the top ramming into the contact

class GameState(Enum):
    MENU = 1
    TOP_SELECT = 2
    ARENA_SELECT = 3
    PLAYING = 4
    PAUSED = 5
    GAME_OVER = 6

class TopType(Enum):
    ATTACK = "Attack"
    DEFENSE = "Defense"
    BALANCE = "Balance"
    SPEED = "Speed"

class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3

COLORS = {
    "bg_dark": (10, 11, 16),
    "bg_mid": (19, 21, 30),
    "bg_deep": (6, 7, 11),
    "arena_floor": (210, 195, 175),
    "arena_ring": (100, 90, 80),
    "arena_void": (12, 14, 18),
    "accent_gold": (245, 185, 71),
    "accent_red": (230, 70, 82),
    "accent_blue": (66, 148, 245),
    "accent_green": (72, 201, 130),
    "accent_purple": (162, 109, 235),
    "accent_cyan": (66, 224, 214),
    "text_white": (238, 241, 248),
    "text_gray": (144, 151, 168),
    "text_dim": (95, 101, 118),
    "p1_color": (66, 148, 245),
    "p2_color": (230, 70, 82),
    "spin_full": (72, 201, 130),
    "spin_mid": (245, 185, 71),
    "spin_low": (230, 70, 82),
    "special_ready": (245, 185, 71),
    "ui_panel": (16, 18, 26, 235),
    "panel_border": (58, 63, 84),
    "glow_gold": (245, 185, 71, 60),
    "danger": (235, 60, 70),
    "button_idle": (30, 33, 45),
    "button_hover": (44, 49, 66),
    "button_active": (58, 65, 86),
    "shadow": (0, 0, 0, 120),
}

TOP_PRESETS = {
    "Velu Vettaikaran": {
        "type": TopType.ATTACK,
        "mass": 3.5,
        "spin_speed": 1800,
        "spin_decay": 15,
        "grip": 1.2,
        "color": (220, 60, 60),
        "accent": (255, 200, 50),
        "special": "Ram Strike",
        "desc": "High mass, strong collision damage",
    },
    "Kottai Veeran": {
        "type": TopType.DEFENSE,
        "mass": 4.5,
        "spin_speed": 1400,
        "spin_decay": 9,
        "grip": 1.5,
        "color": (60, 100, 180),
        "accent": (150, 180, 220),
        "special": "Iron Wall",
        "desc": "Heavy, resistant to knockback",
    },
    "Thiruvalluvar": {
        "type": TopType.BALANCE,
        "mass": 2.5,
        "spin_speed": 1700,
        "spin_decay": 12,
        "grip": 1.3,
        "color": (80, 180, 100),
        "accent": (200, 255, 200),
        "special": "Gyro Balance",
        "desc": "Balanced stats for all situations",
    },
    "Puyal Kaalai": {
        "type": TopType.SPEED,
        "mass": 1.8,
        "spin_speed": 2200,
        "spin_decay": 18,
        "grip": 1.0,
        "color": (200, 80, 200),
        "accent": (255, 180, 255),
        "special": "Whirlwind",
        "desc": "Fast and agile, quick direction changes",
    },
    "Maruthuvar": {
        "type": TopType.BALANCE,
        "mass": 2.8,
        "spin_speed": 1600,
        "spin_decay": 6.5,
        "grip": 1.4,
        "color": (255, 140, 50),
        "accent": (255, 220, 150),
        "special": "Gyro Balance",
        "desc": "Stable and reliable all-rounder",
    },
    "Sooravali": {
        "type": TopType.SPEED,
        "mass": 1.6,
        "spin_speed": 2400,
        "spin_decay": 12,
        "grip": 0.9,
        "color": (0, 200, 220),
        "accent": (180, 255, 255),
        "special": "Whirlwind",
        "desc": "Blazing fast, hardest to control",
    },
    "Kallazhagar": {
        "type": TopType.DEFENSE,
        "mass": 4.8,
        "spin_speed": 1300,
        "spin_decay": 4.5,
        "grip": 1.6,
        "color": (100, 80, 60),
        "accent": (200, 180, 120),
        "special": "Iron Wall",
        "desc": "Immovable object, slow decay",
    },
    "Veerapandiya": {
        "type": TopType.ATTACK,
        "mass": 3.8,
        "spin_speed": 1900,
        "spin_decay": 10,
        "grip": 1.1,
        "color": (180, 20, 20),
        "accent": (255, 100, 50),
        "special": "Ram Strike",
        "desc": "Aggressive, devastating strikes",
    },
}

ARENA_PRESETS = {
    "Gramam Thidal": {
        "name": "Village Ground",
        "floor_color": (222, 184, 135),
        "ring_color": (139, 69, 19),
        "void_color": (50, 30, 20),
        "grip_mod": 1.0,
        "hazards": [],
        "desc": "Flat, no hazards - pure skill",
    },
    "Kovil Prangaram": {
        "name": "Temple Courtyard",
        "floor_color": (200, 170, 150),
        "ring_color": (160, 80, 30),
        "void_color": (40, 20, 10),
        "grip_mod": 1.05,
        "hazards": ["pillars"],
        "desc": "Stone pillars at center",
    },
    "Aaru Paarai": {
        "name": "River Bed",
        "floor_color": (210, 190, 160),
        "ring_color": (150, 120, 80),
        "void_color": (100, 150, 200),
        "grip_mod": 0.7,
        "hazards": [],
        "desc": "Sandy terrain, low grip",
    },
    "Neon Arangam": {
        "name": "Neon Arena",
        "floor_color": (30, 20, 60),
        "ring_color": (255, 50, 200),
        "void_color": (10, 5, 30),
        "grip_mod": 1.1,
        "hazards": ["boost_pads"],
        "desc": "Cyberpunk with speed boost zones",
    },
}

TYPE_COLORS = {
    TopType.ATTACK: (230, 70, 82),
    TopType.DEFENSE: (66, 148, 245),
    TopType.BALANCE: (72, 201, 130),
    TopType.SPEED: (162, 109, 235),
}

# --- Typography -------------------------------------------------------------
# "display" is for titles, buttons, names and numbers; "body" for running
# text; "semibold" for small labels that must stay readable. Each family
# falls back to Arial and then pygame's built-in font on other systems.
FONT_FAMILIES = {
    "display": ("bahnschrift", "segoeuisemibold", "dejavusans", "liberationsans", "arial"),
    "body": ("segoeui", "calibri", "dejavusans", "liberationsans", "arial"),
    "semibold": ("segoeuisemibold", "segoeui", "dejavusans", "liberationsans", "arial"),
}

pygame.font.init()
_FONT_PATHS = {}
_FONT_CACHE = {}


def _resolve_font_path(family):
    if family not in _FONT_PATHS:
        path = None
        for name in FONT_FAMILIES.get(family, FONT_FAMILIES["body"]):
            path = pygame.font.match_font(name)
            if path:
                break
        _FONT_PATHS[family] = path
    return _FONT_PATHS[family]


def get_font(size, bold=False, family=None):
    """Cached font lookup. Creating a SysFont is slow, and the UI asks for
    dozens of fonts every frame, so each (family, size, bold) is built once."""
    family = family or ("display" if bold else "body")
    key = (family, size, bold)
    font = _FONT_CACHE.get(key)
    if font is None:
        path = _resolve_font_path(family)
        try:
            font = pygame.font.Font(path, size)
        except Exception:
            font = pygame.font.Font(None, size)
        if bold and family == "display":
            font.set_bold(True)
        _FONT_CACHE[key] = font
    return font
