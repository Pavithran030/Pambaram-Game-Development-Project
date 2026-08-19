import pygame
from enum import Enum

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
ARENA_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
ARENA_RADIUS = 280
RINGOUT_RADIUS = 320
MATCH_TIME = 180

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
    "bg_dark": (20, 15, 30),
    "bg_mid": (40, 35, 55),
    "arena_floor": (222, 184, 135),
    "arena_ring": (139, 69, 19),
    "arena_void": (15, 10, 20),
    "accent_gold": (255, 215, 0),
    "accent_red": (220, 50, 50),
    "accent_blue": (50, 120, 220),
    "accent_green": (50, 200, 100),
    "accent_purple": (180, 80, 220),
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 180),
    "p1_color": (60, 140, 240),
    "p2_color": (240, 80, 80),
    "spin_full": (80, 255, 120),
    "spin_mid": (255, 220, 50),
    "spin_low": (255, 80, 80),
    "special_ready": (255, 200, 50),
    "ui_panel": (30, 25, 45, 220),
    "button_idle": (60, 55, 80),
    "button_hover": (90, 85, 115),
    "button_active": (120, 100, 160),
}

TOP_PRESETS = {
    "Velu Vettaikaran": {
        "type": TopType.ATTACK,
        "mass": 3.5,
        "spin_speed": 1800,
        "spin_decay": 90,
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
        "spin_decay": 50,
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
        "spin_decay": 70,
        "grip": 1.3,
        "color": (80, 180, 100),
        "accent": (200, 255, 200),
        "special": "Spin Boost",
        "desc": "Balanced stats for all situations",
    },
    "Puyal Kaalai": {
        "type": TopType.SPEED,
        "mass": 1.8,
        "spin_speed": 2200,
        "spin_decay": 110,
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
        "spin_decay": 65,
        "grip": 1.4,
        "color": (255, 140, 50),
        "accent": (255, 220, 150),
        "special": "Spin Boost",
        "desc": "Stable and reliable all-rounder",
    },
    "Sooravali": {
        "type": TopType.SPEED,
        "mass": 1.6,
        "spin_speed": 2400,
        "spin_decay": 120,
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
        "spin_decay": 45,
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
        "spin_decay": 100,
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

pygame.font.init()
def get_font(size, bold=False):
    try:
        if bold:
            return pygame.font.SysFont("arial, georgia, sans-serif", size, bold=True)
        return pygame.font.SysFont("arial, georgia, sans-serif", size)
    except:
        return pygame.font.Font(None, size)
