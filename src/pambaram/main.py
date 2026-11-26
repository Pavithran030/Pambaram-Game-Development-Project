import asyncio
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import sys
import math
import random
from . import __version__
from . import settings as settings_store
from .config import *
from .top_art import make_icon
from .top import Top
from .particles import ParticleSystem
from .arena import Arena, resolve_top_collision, check_obstacle_collision, check_boost_pad
from .ai import AIController
from .ui import *
from .sound import SoundManager


def _is_web():
    return sys.platform == "emscripten"


def _enable_dpi_awareness():
    """On Windows with display scaling (125%, 150%...), a non-DPI-aware
    window is bitmap-stretched by the OS, which makes every piece of text
    blurry. Opting in keeps text pixel-sharp."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# Default launch aims: each top fires toward the far side, angled so the
# two paths cross near the centre instead of meeting dead-on.
DEFAULT_AIM = {1: -0.35, 2: math.pi - 0.35}


class Game:
    def __init__(self):
        _enable_dpi_awareness()
        if not pygame.get_init():
            try:
                pygame.mixer.pre_init(44100, -16, 2, 512)
            except Exception:
                pass
            pygame.init()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            self.sound_enabled = True
        except Exception:
            self.sound_enabled = False

        self.sound = SoundManager(self.sound_enabled)

        self.settings = settings_store.load()
        self.muted = self.settings["muted"]
        self._apply_mute()

        self.fullscreen = self.settings["fullscreen"]
        self._init_display()

        self.clock = pygame.time.Clock()
        self.running = True

        self.state = GameState.MENU
        self.particles = ParticleSystem()

        self.p1_top_name = self.settings["p1_top"]
        self.p2_top_name = self.settings["p2_top"]
        self.selected_arena = self.settings["arena"]
        self.p2_is_ai = self.settings["p2_is_ai"]
        self.ai_difficulty = Difficulty[self.settings["difficulty"]]
        self.new_best = False
        self.toast_text = ""
        self.toast_timer = 0.0

        self.p1 = None
        self.p2 = None
        self.arena = None
        self.ai_controller = None
        self.match_time = MATCH_TIME
        self.winner = None
        self.stats = {}
        self.screen_shake = (0, 0)
        self.shake_decay = 0

        self.mouse_pos = (0, 0)
        self.aim = dict(DEFAULT_AIM)
        self.drag_p1 = None
        self.drag_p2 = None
        self.countdown = 3
        self.countdown_timer = 0
        self.match_started = False
        self.fight_banner = 0.0
        self.meter_time = 0.0
        self.launch_lock = {1: None, 2: None}
        self.launch_popups = []
        self.ai_lock_at = None
        self.ai_launch_quality = 0.8
        self.pause_buttons = []
        self.gameover_buttons = []
        self._build_menu_buttons()
        self._build_top_select_buttons()
        self._build_arena_select_buttons()
        self._build_pause_buttons()
        self._build_gameover_buttons()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------
    def _init_display(self):
        if _is_web():
            self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.fullscreen = False
            pygame.display.set_caption("Pambaram: Spinning Top Battle Arena")
            self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            return
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        try:
            if self.fullscreen:
                self.window = pygame.display.set_mode((0, 0), flags)
            else:
                self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        except Exception:
            self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            self.fullscreen = False
        pygame.display.set_caption("Pambaram: Spinning Top Battle Arena")
        try:
            pygame.display.set_icon(make_icon(64))
        except Exception:
            pass
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def _toggle_fullscreen(self):
        if _is_web():
            self._toast("USE BROWSER FULLSCREEN (F11)")
            return
        self.fullscreen = not self.fullscreen
        self._init_display()
        self._save_settings()

    # ------------------------------------------------------------------
    # Settings, sound, toasts
    # ------------------------------------------------------------------
    def _save_settings(self):
        self.settings.update({
            "p1_top": self.p1_top_name,
            "p2_top": self.p2_top_name,
            "arena": self.selected_arena,
            "p2_is_ai": self.p2_is_ai,
            "difficulty": self.ai_difficulty.name,
            "muted": self.muted,
            "fullscreen": self.fullscreen,
        })
        settings_store.save(self.settings)

    def _apply_mute(self):
        self.sound.enabled = self.sound_enabled and bool(self.sound._cache) and not self.muted

    def _toggle_mute(self):
        self.muted = not self.muted
        self._apply_mute()
        self._toast("SOUND OFF" if self.muted else "SOUND ON")
        self._save_settings()

    def _toast(self, text, seconds=1.6):
        self.toast_text = text
        self.toast_timer = seconds

    def _record_result(self):
        """Update lifetime stats once per finished match."""
        st = self.settings["stats"]
        st["matches"] += 1
        if self.winner is None:
            st["draws"] += 1
        elif self.winner.player_id == 1:
            st["p1_wins"] += 1
            if self.p2_is_ai:
                st["wins_vs_ai_by_difficulty"][self.ai_difficulty.name] += 1
        else:
            st["p2_wins"] += 1
        points = self.stats.get("points", 0)
        self.new_best = points > st["best_score"]
        if self.new_best:
            st["best_score"] = points
        self.stats["best_score"] = st["best_score"]
        self.stats["new_best"] = self.new_best
        self._save_settings()

    def _view_transform(self):
        win_w, win_h = self.window.get_size()
        scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
        scaled_w = int(SCREEN_WIDTH * scale)
        scaled_h = int(SCREEN_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2
        return scale, scaled_w, scaled_h, offset_x, offset_y

    def _map_mouse_pos(self, pos):
        scale, _, _, offset_x, offset_y = self._view_transform()
        mx, my = pos
        rx = (mx - offset_x) / max(0.01, scale)
        ry = (my - offset_y) / max(0.01, scale)
        return (int(rx), int(ry))

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def _build_menu_buttons(self):
        bw, bh = 360, 60
        cx = SCREEN_WIDTH // 2 - bw // 2
        y_start = 270
        gap = 74
        self.menu_buttons = [
            Button(cx, y_start, bw, bh, "PLAYER VS AI", self._quick_match, 24, primary=True),
            Button(cx, y_start + gap, bw, bh, "PLAYER VS PLAYER", self._vs_player, 24),
            Button(cx, y_start + gap * 2, bw, bh, "TOURNAMENT SETUP", self._start_top_select, 24),
            Button(cx, y_start + gap * 3, bw, bh, "AI DIFFICULTY: " + self.ai_difficulty.name, self._cycle_difficulty, 22),
            Button(cx, y_start + gap * 4, bw, bh, "QUIT", self._quit, 24),
        ]

    def _build_top_select_buttons(self):
        bw, bh = 200, 54
        y = SCREEN_HEIGHT - 92
        self.top_select_buttons = [
            Button(SCREEN_WIDTH - 650, y, bw, bh, "< BACK", self._back_to_menu, 22),
            Button(SCREEN_WIDTH - 435, y, bw, bh, self._mode_label(), self._toggle_ai, 20),
            Button(SCREEN_WIDTH - 220, y, bw, bh, "NEXT >", self._start_arena_select, 22, primary=True),
        ]

    def _mode_label(self):
        return "MODE: VS AI" if self.p2_is_ai else "MODE: 2 PLAYERS"

    def _build_arena_select_buttons(self):
        bw, bh = 200, 54
        y = SCREEN_HEIGHT - 92
        self.arena_select_buttons = [
            Button(SCREEN_WIDTH - 435, y, bw, bh, "< BACK", self._back_to_top_select, 22),
            Button(SCREEN_WIDTH - 220, y, bw, bh, "START!", self._start_match, 26,
                   primary=True, accent=COLORS["accent_green"]),
        ]

    def _build_pause_buttons(self):
        bw, bh = 320, 60
        cx = SCREEN_WIDTH // 2 - bw // 2
        self.pause_buttons = [
            Button(cx, 290, bw, bh, "RESUME", self._resume, 24, primary=True),
            Button(cx, 290 + 78, bw, bh, "RESTART", self._restart_match, 24),
            Button(cx, 290 + 156, bw, bh, "MAIN MENU", self._back_to_menu, 24),
        ]

    def _build_gameover_buttons(self):
        bw, bh = 260, 60
        cx = SCREEN_WIDTH // 2
        self.gameover_buttons = [
            Button(cx - bw - 15, 610, bw, bh, "REMATCH", self._restart_match, 24, primary=True),
            Button(cx + 15, 610, bw, bh, "MAIN MENU", self._back_to_menu, 24),
        ]

    # ------------------------------------------------------------------
    # Navigation callbacks
    # ------------------------------------------------------------------
    def _quick_match(self):
        self.p2_is_ai = True
        self._build_top_select_buttons()
        self._start_top_select()

    def _vs_player(self):
        self.p2_is_ai = False
        self._build_top_select_buttons()
        self._start_top_select()

    def _start_top_select(self):
        self.state = GameState.TOP_SELECT

    def _start_arena_select(self):
        self.state = GameState.ARENA_SELECT

    def _back_to_top_select(self):
        self.state = GameState.TOP_SELECT

    def _back_to_menu(self):
        self.state = GameState.MENU

    def _cycle_difficulty(self):
        order = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
        idx = order.index(self.ai_difficulty)
        self.ai_difficulty = order[(idx + 1) % len(order)]
        self.menu_buttons[3].text = "AI DIFFICULTY: " + self.ai_difficulty.name
        self._save_settings()

    def _toggle_ai(self):
        self.p2_is_ai = not self.p2_is_ai
        self.top_select_buttons[1].text = self._mode_label()
        self._save_settings()

    def _player_label(self, player_id):
        if player_id == 1:
            return "PLAYER 1"
        return "AI" if self.p2_is_ai else "PLAYER 2"

    # ------------------------------------------------------------------
    # Match lifecycle
    # ------------------------------------------------------------------
    def _start_match(self):
        p1_preset = TOP_PRESETS.get(self.p1_top_name, list(TOP_PRESETS.values())[2])
        p2_preset = TOP_PRESETS.get(self.p2_top_name, list(TOP_PRESETS.values())[0])

        self.p1 = Top(self.p1_top_name, p1_preset, 1, False)
        self.p2 = Top(self.p2_top_name, p2_preset, 2, self.p2_is_ai, self.ai_difficulty)
        self.arena = Arena(self.selected_arena)
        self.match_time = MATCH_TIME
        self.winner = None
        self.stats = {}
        self.particles = ParticleSystem()
        self.drag_p1 = None
        self.drag_p2 = None
        self.countdown = 3
        self.countdown_timer = 0
        self.match_started = False
        self.fight_banner = 0.0
        self.screen_shake = (0, 0)
        self.shake_decay = 0

        if self.p2_is_ai:
            self.ai_controller = AIController(self.p2, self.ai_difficulty)
        else:
            self.ai_controller = None

        self.aim = dict(DEFAULT_AIM)
        self.meter_time = 0.0
        self.launch_lock = {1: None, 2: None}   # locked launch quality per player
        self.launch_popups = []
        self.ai_lock_at = None
        if self.ai_controller:
            self.aim[2] = self.ai_controller.choose_launch_angle(self.p1)
            # The AI "presses launch" at a random moment in the countdown.
            self.ai_lock_at = random.uniform(1.0, 3 * COUNTDOWN_STEP - 0.4)
            self.ai_launch_quality = self.ai_controller.choose_launch_quality()

        self.new_best = False
        self._save_settings()
        self.state = GameState.PLAYING

    # ------------------------------------------------------------------
    # Launch power meter
    # ------------------------------------------------------------------
    def meter_value(self, player_id):
        """0..1 swing; P2's meter is phase-shifted so it's an independent
        timing challenge rather than a copy of P1's."""
        phase = 0.0 if player_id == 1 else 0.37
        t = self.meter_time / LAUNCH_METER_PERIOD + phase
        return 0.5 - 0.5 * math.cos(2 * math.pi * t)

    def _lock_launch(self, player_id, quality=None):
        if self.match_started or self.launch_lock[player_id] is not None:
            return
        q = self.meter_value(player_id) if quality is None else quality
        self.launch_lock[player_id] = q
        self.sound.play("click")

    @staticmethod
    def launch_grade(q):
        for threshold, label in LAUNCH_GRADES:
            if q >= threshold:
                return label
        return LAUNCH_GRADES[-1][1]

    def _restart_match(self):
        self._start_match()

    def _pause(self):
        # Drop any half-finished aim drag: the mouse button may be released
        # while the pause menu is open, and a stale drag would keep steering
        # the aim after resuming.
        self.drag_p1 = None
        self.drag_p2 = None
        self.state = GameState.PAUSED

    def _resume(self):
        self.state = GameState.PLAYING

    def _quit(self):
        if _is_web():
            self._save_settings()
            self._toast("CLOSE TAB TO EXIT")
            return
        self._save_settings()
        self.running = False

    def _launch_top(self, top, angle):
        if top.is_launched:
            return
        q = self.launch_lock.get(top.player_id)
        if q is None:
            q = LAUNCH_UNLOCKED_QUALITY
            self.launch_lock[top.player_id] = q
        force = LAUNCH_FORCE * (0.75 + 0.25 * q)
        top.launch(math.cos(angle), math.sin(angle), force, quality=q)
        self.particles.emit_dust(top.x, top.y, 12 + int(18 * q))
        grade = self.launch_grade(q)
        color = COLORS["accent_gold"] if q >= 0.92 else (
            COLORS["accent_green"] if q >= 0.5 else COLORS["danger"])
        self.launch_popups.append({"pid": top.player_id, "text": grade,
                                   "sub": f"STAMINA {int(round(100 * top.spin / top.max_spin))}%",
                                   "color": color, "t": 1.8})

    def _begin_fight(self):
        """Countdown finished: every top launches on the same frame."""
        self.match_started = True
        self.drag_p1 = None
        self.drag_p2 = None
        if self.ai_controller and self.launch_lock[2] is None:
            self.launch_lock[2] = self.ai_launch_quality
        self._launch_top(self.p1, self.aim[1])
        self._launch_top(self.p2, self.aim[2])
        self.fight_banner = FIGHT_BANNER_TIME
        self._apply_shake(4)
        self.sound.play("launch")

    def _ai_auto_launch(self):
        """Launch the AI top if it somehow hasn't launched yet."""
        if self.p2_is_ai and self.p2 and not self.p2.is_launched and self.match_started:
            self._launch_top(self.p2, self.aim[2])
            self.sound.play("launch")

    # ------------------------------------------------------------------
    # Screen shake
    # ------------------------------------------------------------------
    def _apply_shake(self, amount):
        self.shake_decay = max(self.shake_decay, amount)

    def _update_shake(self, dt):
        if self.shake_decay > 0:
            self.shake_decay -= dt * 40
            if self.shake_decay < 0:
                self.shake_decay = 0
        if self.shake_decay > 0.1:
            sx = random.uniform(-self.shake_decay, self.shake_decay)
            sy = random.uniform(-self.shake_decay, self.shake_decay)
            self.screen_shake = (sx, sy)
        else:
            self.screen_shake = (0, 0)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _handle_menu_events(self, event):
        for b in self.menu_buttons:
            if b.handle_event(event):
                self.sound.play("click")

    def _hovered_top_card(self):
        for name, rect in get_top_card_rects(TOP_PRESETS.keys()).items():
            if rect.collidepoint(self.mouse_pos):
                return name
        return None

    def _hovered_arena_card(self):
        for key, rect in get_arena_card_rects(ARENA_PRESETS.keys()).items():
            if rect.collidepoint(self.mouse_pos):
                return key
        return None

    def _handle_top_select_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._back_to_menu()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._start_arena_select()
            return
        for b in self.top_select_buttons:
            if b.handle_event(event):
                self.sound.play("click")
        if event.type == pygame.MOUSEBUTTONDOWN:
            card_rects = get_top_card_rects(TOP_PRESETS.keys())
            for name, rect in card_rects.items():
                if rect.collidepoint(event.pos):
                    if event.button == 1:
                        self.p1_top_name = name
                        self.sound.play("click")
                    elif event.button == 3:
                        self.p2_top_name = name
                        self.sound.play("click")

    def _handle_arena_select_events(self, event):
        if event.type == pygame.KEYDOWN:
            keys = list(ARENA_PRESETS)
            i = keys.index(self.selected_arena)
            if event.key == pygame.K_ESCAPE:
                self._back_to_top_select()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._start_match()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_arena = keys[(i - 1) % len(keys)]
                self.sound.play("click")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_arena = keys[(i + 1) % len(keys)]
                self.sound.play("click")
            return
        for b in self.arena_select_buttons:
            if b.handle_event(event):
                self.sound.play("click")
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            card_rects = get_arena_card_rects(ARENA_PRESETS.keys())
            for key, rect in card_rects.items():
                if rect.collidepoint(event.pos):
                    self.selected_arena = key
                    self.sound.play("click")

    def _update_drag_aim(self, drag, player_id):
        """Slingshot aim: pull back away from where you want the top to go."""
        sx, sy = drag["start"]
        cx, cy = drag["current"]
        dx, dy = sx - cx, sy - cy
        if dx * dx + dy * dy > 64:  # ignore jitter under 8px
            self.aim[player_id] = math.atan2(dy, dx)

    def _handle_playing_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._pause()
            return

        # Aiming and power-locking only happen before the launch.
        if self.match_started:
            return

        if event.type == pygame.KEYDOWN:
            if event.key in self._keys(1, "launch"):
                self._lock_launch(1)
            elif not self.p2_is_ai and event.key in self._keys(2, "launch"):
                self._lock_launch(2)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.drag_p1 = {"start": event.pos, "current": event.pos}
            elif event.button == 3 and not self.p2_is_ai:
                self.drag_p2 = {"start": event.pos, "current": event.pos}
        elif event.type == pygame.MOUSEMOTION:
            if self.drag_p1:
                self.drag_p1["current"] = event.pos
                self._update_drag_aim(self.drag_p1, 1)
            if self.drag_p2:
                self.drag_p2["current"] = event.pos
                self._update_drag_aim(self.drag_p2, 2)
        elif event.type == pygame.MOUSEBUTTONUP:
            # Pull back and release, like a real launcher: releasing a
            # deliberate drag locks the power meter at that instant.
            if event.button == 1 and self.drag_p1:
                if self._drag_len(self.drag_p1) > 8:
                    self._lock_launch(1)
                self.drag_p1 = None
            elif event.button == 3 and self.drag_p2:
                if self._drag_len(self.drag_p2) > 8:
                    self._lock_launch(2)
                self.drag_p2 = None

    @staticmethod
    def _drag_len(drag):
        return math.hypot(drag["start"][0] - drag["current"][0], drag["start"][1] - drag["current"][1])

    def _keys(self, player_id, action):
        """Key bindings. Against the AI, player 1 may use either WASD or the
        arrow keys (and either SHIFT, SPACE or ENTER)."""
        wasd = {
            "up": [pygame.K_w], "down": [pygame.K_s], "left": [pygame.K_a], "right": [pygame.K_d],
            "dash": [pygame.K_LSHIFT], "launch": [pygame.K_SPACE],
        }
        arrows = {
            "up": [pygame.K_UP], "down": [pygame.K_DOWN], "left": [pygame.K_LEFT], "right": [pygame.K_RIGHT],
            "dash": [pygame.K_RSHIFT], "launch": [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_RCTRL],
        }
        if player_id == 1:
            return wasd[action] + (arrows[action] if self.p2_is_ai else [])
        return arrows[action]

    def _held(self, keys, player_id, action):
        return any(keys[k] for k in self._keys(player_id, action))

    def _handle_pause_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
            return
        for b in self.pause_buttons:
            if b.handle_event(event):
                self.sound.play("click")

    def _handle_gameover_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_r):
                self._restart_match()
            elif event.key == pygame.K_ESCAPE:
                self._back_to_menu()
            return
        for b in self.gameover_buttons:
            if b.handle_event(event):
                self.sound.play("click")

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def _update_aim(self, dt, keys):
        turn = AIM_TURN_SPEED * dt
        players = [(1, self.drag_p1)] + ([] if self.p2_is_ai else [(2, self.drag_p2)])
        for pid, drag in players:
            if drag:
                continue
            if self._held(keys, pid, "left"):
                self.aim[pid] -= turn
            if self._held(keys, pid, "right"):
                self.aim[pid] += turn

        self.meter_time += dt
        if self.ai_lock_at is not None and self.launch_lock[2] is None:
            elapsed = (3 - self.countdown) * COUNTDOWN_STEP + self.countdown_timer
            if elapsed >= self.ai_lock_at:
                self._lock_launch(2, self.ai_launch_quality)

    def _update_countdown(self, dt):
        self.countdown_timer += dt
        if self.countdown_timer >= COUNTDOWN_STEP:
            self.countdown_timer -= COUNTDOWN_STEP
            self.countdown -= 1
            if self.countdown <= 0:
                self.countdown = 0
                self._begin_fight()
            else:
                self.sound.play("click")

    def _steer_player(self, top, keys):
        if not top.is_launched or top.is_knocked_out:
            return
        pid = top.player_id
        sx = int(self._held(keys, pid, "right")) - int(self._held(keys, pid, "left"))
        sy = int(self._held(keys, pid, "down")) - int(self._held(keys, pid, "up"))
        if sx or sy:
            top.steer(sx, sy)
            if self._held(keys, pid, "dash") and top.dash(sx, sy):
                self.sound.play("dash")

    def _handle_boundary(self, top):
        result = top.check_boundary() if top.is_launched else None
        if result == "bounce":
            self._apply_shake(4)
            dx = top.x - ARENA_CENTER[0]
            dy = top.y - ARENA_CENTER[1]
            d = max(1.0, math.hypot(dx, dy))
            self.particles.emit_sparks(top.x, top.y, -dx / d, -dy / d, 8)
        elif result == "ringout":
            self.particles.emit_ringout(top.x, top.y, 40)
            self._apply_shake(10)
            self.sound.play("ringout")

    def _update_gameplay(self, dt):
        keys = pygame.key.get_pressed()

        if not self.match_started:
            self._update_aim(dt, keys)
            self._update_countdown(dt)
            self.particles.update(dt)
            return

        if self.fight_banner > 0:
            self.fight_banner = max(0.0, self.fight_banner - dt)
        for p in self.launch_popups:
            p["t"] -= dt
        self.launch_popups = [p for p in self.launch_popups if p["t"] > 0]

        self.match_time -= dt

        self._steer_player(self.p1, keys)
        if not self.p2_is_ai:
            self._steer_player(self.p2, keys)

        if self.ai_controller and self.p2.is_launched and not self.p2.is_knocked_out:
            steer, dash_do, _ = self.ai_controller.update(self.p1, dt, self.arena.obstacles)
            if steer is not None:
                self.p2.steer(steer[0], steer[1])
                if dash_do and self.p2.dash(steer[0], steer[1]):
                    self.sound.play("dash")

        grip_mod = self.arena.grip_mod
        self.p1.update(dt, grip_mod)
        self.p2.update(dt, grip_mod)

        self._handle_boundary(self.p1)
        self._handle_boundary(self.p2)

        # Knocked-out tops are falling off the stage and can't be hit.
        if (self.p1.is_launched and self.p2.is_launched
                and not self.p1.is_knocked_out and not self.p2.is_knocked_out):
            col_shake = resolve_top_collision(self.p1, self.p2, self.particles)
            if col_shake:
                self._apply_shake(col_shake)
                self.sound.play("collision")

        obs_shake = 0
        for top in (self.p1, self.p2):
            if top.is_launched and not top.is_knocked_out:
                obs_shake += check_obstacle_collision(top, self.arena.obstacles)
                check_boost_pad(top, self.arena.boost_pads, self.particles)
        if obs_shake:
            self._apply_shake(obs_shake)

        if self.p1.is_spinning and random.random() < 0.1:
            self.particles.emit_spin(self.p1.x, self.p1.y, 1)
        if self.p2.is_spinning and random.random() < 0.1:
            self.particles.emit_spin(self.p2.x, self.p2.y, 1)

        self.arena.update(dt)
        self.particles.update(dt)
        self._update_shake(dt)

        self._check_win_conditions()

    # ------------------------------------------------------------------
    # Win conditions
    # ------------------------------------------------------------------
    def _check_win_conditions(self):
        if not self.match_started:
            return

        p1, p2 = self.p1, self.p2
        if not (p1.is_launched and p2.is_launched):
            # Can't happen with the simultaneous launch, but never award a
            # win against a top that never entered the arena.
            if self.match_time > 0:
                return

        reason = ""
        win = None
        game_over = False

        p1_ko, p2_ko = p1.is_knocked_out, p2.is_knocked_out
        p1_ko_done = p1_ko and p1.knockout_timer >= KO_CONFIRM_TIME
        p2_ko_done = p2_ko and p2.knockout_timer >= KO_CONFIRM_TIME

        if p1_ko_done or p2_ko_done:
            game_over = True
            if p1_ko and p2_ko:
                # Both went over the edge. The one that went out later (the
                # smaller timer) survived longer; near-simultaneous = draw.
                if abs(p1.knockout_timer - p2.knockout_timer) < 0.2:
                    reason = "DOUBLE RING OUT! It's a draw!"
                else:
                    win = p1 if p1.knockout_timer < p2.knockout_timer else p2
                    reason = f"DOUBLE RING OUT! {win.name} stayed in longer!"
            elif p1_ko_done:
                win = p2
                reason = f"RING OUT! {p1.name} was knocked out of the arena!"
            else:
                win = p1
                reason = f"RING OUT! {p2.name} was knocked out of the arena!"
        elif (p1_ko or p2_ko) and self.match_time <= 0:
            # Time ran out mid ring-out: the top already over the edge loses.
            game_over = True
            if p1_ko and p2_ko:
                reason = "TIME UP! Both tops left the arena - it's a draw!"
            else:
                win = p2 if p1_ko else p1
                loser = p1 if p1_ko else p2
                reason = f"RING OUT! {loser.name} left the arena as time ran out!"
        elif p1_ko or p2_ko:
            # A ring-out is in progress - let it finish before judging spin.
            return
        else:
            p1_dead = p1.is_launched and p1.spin <= 0
            p2_dead = p2.is_launched and p2.spin <= 0
            if p1_dead and p2_dead:
                game_over = True
                reason = "DOUBLE SPIN OUT! It's a draw!"
            elif p1_dead:
                game_over = True
                win = p2
                reason = f"SPIN OUT! {p1.name} ran out of spin!"
            elif p2_dead:
                game_over = True
                win = p1
                reason = f"SPIN OUT! {p2.name} ran out of spin!"
            elif self.match_time <= 0:
                game_over = True
                if not (p1.is_launched and p2.is_launched):
                    if p1.is_launched:
                        win = p1
                        reason = f"TIME UP! {p2.name} never launched!"
                    elif p2.is_launched:
                        win = p2
                        reason = f"TIME UP! {p1.name} never launched!"
                    else:
                        reason = "TIME UP! Neither top launched - it's a draw!"
                else:
                    s1 = p1.spin / p1.max_spin if p1.max_spin > 0 else 0
                    s2 = p2.spin / p2.max_spin if p2.max_spin > 0 else 0
                    pct1 = int(round(s1 * 100))
                    pct2 = int(round(s2 * 100))
                    if pct1 != pct2:
                        win = p1 if s1 > s2 else p2
                        reason = f"TIME UP! {win.name} has more spin left ({pct1}% vs {pct2}%)"
                    else:
                        reason = f"TIME UP! Equal spin ({pct1}% vs {pct2}%) - it's a draw!"

        if not game_over:
            return

        self.winner = win
        elapsed = MATCH_TIME - max(0, self.match_time)

        base_points = 0
        if win:
            winning_spin_pct = (win.spin / win.max_spin) * 100 if win.max_spin > 0 else 0
            time_bonus = max(0, int((MATCH_TIME - elapsed) * 2))
            reason_bonus = 150 if "RING OUT" in reason else 100
            base_points = int(200 + winning_spin_pct * 3 + time_bonus + reason_bonus)

        p1_max = p1.max_spin if p1.max_spin > 0 else 1.0
        p2_max = p2.max_spin if p2.max_spin > 0 else 1.0

        self.stats = {
            "win_reason": reason,
            "match_time": elapsed,
            "p1_final_spin": p1.spin,
            "p2_final_spin": p2.spin,
            "p1_max_spin": p1.max_spin,
            "p2_max_spin": p2.max_spin,
            "p1_spin_pct": max(0.0, min(1.0, p1.spin / p1_max)),
            "p2_spin_pct": max(0.0, min(1.0, p2.spin / p2_max)),
            "p1_label": self._player_label(1),
            "p2_label": self._player_label(2),
            "p1_name": p1.name,
            "p2_name": p2.name,
            "points": base_points,
        }
        self.drag_p1 = None
        self.drag_p2 = None
        self.state = GameState.GAME_OVER
        self._record_result()
        self.sound.play("victory")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _draw_background(self):
        self.screen.fill(COLORS["bg_dark"])
        for i in range(8):
            r = 100 + i * 80
            pygame.draw.circle(self.screen, (22 + i * 2, 20 + i * 2, 34 + i * 3), ARENA_CENTER, r, 1)

    def _draw_match(self):
        if self.arena:
            self.arena.draw(self.screen, self.screen_shake)
        if self.p1:
            self.p1.draw(self.screen, self.screen_shake)
        if self.p2:
            self.p2.draw(self.screen, self.screen_shake)
        self.particles.draw(self.screen, self.screen_shake)

        if not (self.p1 and self.p2):
            return

        if not self.match_started:
            draw_countdown(self.screen, self.countdown, self.countdown_timer / COUNTDOWN_STEP)
            for top, color, label, drag in ((self.p1, COLORS["p1_color"], "P1", self.drag_p1),
                                            (self.p2, COLORS["p2_color"], "AI" if self.p2_is_ai else "P2",
                                             self.drag_p2)):
                pid = top.player_id
                draw_aim_arrow(self.screen, top, self.aim[pid], color, label, bool(drag))
                locked = self.launch_lock[pid]
                draw_launch_meter(self.screen, top, self.meter_value(pid), locked, color,
                                  self.launch_grade(locked) if locked is not None else None)
            draw_aim_hints(self.screen, self.p2_is_ai)
        elif self.fight_banner > 0:
            draw_fight_banner(self.screen, self.fight_banner / FIGHT_BANNER_TIME)

        for p in self.launch_popups:
            top = self.p1 if p["pid"] == 1 else self.p2
            draw_launch_popup(self.screen, top, p["text"], p["sub"], p["color"], p["t"] / 1.8)

        draw_hud(self.screen, self.p1, self.p2, max(0, self.match_time),
                 self._player_label(1), self._player_label(2))

    def _draw(self):
        self._draw_background()

        if self.state == GameState.MENU:
            draw_menu(self.screen, self.menu_buttons, __version__, self.settings["stats"])
        elif self.state == GameState.TOP_SELECT:
            draw_top_select(self.screen, TOP_PRESETS, self.p1_top_name, self.p2_top_name,
                            self.p2_is_ai, self.top_select_buttons, self.ai_difficulty,
                            hover=self._hovered_top_card())
        elif self.state == GameState.ARENA_SELECT:
            draw_arena_select(self.screen, ARENA_PRESETS, self.selected_arena, self.arena_select_buttons,
                              hover=self._hovered_arena_card())
        elif self.state in (GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER):
            self._draw_match()
            if self.state == GameState.PAUSED:
                draw_pause(self.screen, self.pause_buttons, self.p2_is_ai)
            elif self.state == GameState.GAME_OVER:
                draw_game_over(self.screen, self.winner, self.stats, self.gameover_buttons)

        if self.toast_timer > 0:
            draw_toast(self.screen, self.toast_text, min(1.0, self.toast_timer / 0.3))

        _, scaled_w, scaled_h, offset_x, offset_y = self._view_transform()
        self.window.fill((10, 10, 15))
        if (scaled_w, scaled_h) == (SCREEN_WIDTH, SCREEN_HEIGHT):
            self.window.blit(self.screen, (offset_x, offset_y))
        else:
            scaled_surf = pygame.transform.smoothscale(self.screen, (max(1, scaled_w), max(1, scaled_h)))
            self.window.blit(scaled_surf, (offset_x, offset_y))
        pygame.display.flip()

    def handle_event(self, event):
        """Route one pygame event: global keys/window events first, then the
        handler for the current screen."""
        if event.type == pygame.QUIT:
            self._quit()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self._toggle_fullscreen()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self._toggle_mute()
            return
        if event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
            # Alt-tab / minimise mid-match must not keep the clock running.
            if self.state == GameState.PLAYING:
                self._pause()
            return

        if hasattr(event, "pos"):
            event.pos = self._map_mouse_pos(event.pos)
            self.mouse_pos = event.pos

        handler = {
            GameState.MENU: self._handle_menu_events,
            GameState.TOP_SELECT: self._handle_top_select_events,
            GameState.ARENA_SELECT: self._handle_arena_select_events,
            GameState.PLAYING: self._handle_playing_events,
            GameState.PAUSED: self._handle_pause_events,
            GameState.GAME_OVER: self._handle_gameover_events,
        }.get(self.state)
        if handler:
            handler(event)

    async def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                self.handle_event(event)
                if not self.running:
                    break

            # Update first, then draw, so the frame on screen always shows
            # the state after this tick (and the game-over screen appears on
            # the same frame the match ends).
            if self.state == GameState.PLAYING and self.p1 and self.p2:
                self._update_gameplay(dt)
            elif self.state == GameState.GAME_OVER:
                self.particles.update(dt)
                self._update_shake(dt)

            if self.toast_timer > 0:
                self.toast_timer = max(0.0, self.toast_timer - dt)

            self._draw()
            await asyncio.sleep(0)

        pygame.quit()
        if not _is_web():
            sys.exit(0)


def _show_crash_dialog(message):
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Pambaram crashed", 0x10)
    except Exception:
        pass


async def main():
    try:
        game = Game()
        await game.run()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        pygame.quit()
    except Exception as exc:
        # Never just vanish: log the traceback, tell the player where it is,
        # and exit with an error code.
        log_path = settings_store.write_crash_log(exc)
        pygame.quit()
        msg = f"Sorry - the game hit an unexpected error:\n\n{type(exc).__name__}: {exc}"
        if log_path:
            msg += f"\n\nDetails were saved to:\n{log_path}"
        print(msg, file=sys.stderr)
        _show_crash_dialog(msg)
        if not _is_web():
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
