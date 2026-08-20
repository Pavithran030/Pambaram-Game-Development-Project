import pygame
import sys
import math
import random
from config import *
from top import Top
from particles import ParticleSystem
from arena import Arena, resolve_top_collision, check_obstacle_collision, check_boost_pad
from ai import AIController
from ui import *

class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False

        self.fullscreen = False
        self._init_display()

        self.clock = pygame.time.Clock()
        self.running = True

        self.state = GameState.MENU
        self.particles = ParticleSystem()

        self.p1_top_name = "Thiruvalluvar"
        self.p2_top_name = "Velu Vettaikaran"
        self.selected_arena = "Gramam Thidal"
        self.p2_is_ai = True
        self.ai_difficulty = Difficulty.MEDIUM

        self.p1 = None
        self.p2 = None
        self.arena = None
        self.ai_controller = None
        self.match_time = MATCH_TIME
        self.winner = None
        self.stats = {}
        self.screen_shake = (0, 0)
        self.shake_decay = 0

        self.drag_p1 = None
        self.drag_p2 = None
        self.countdown = 2
        self.countdown_timer = 0
        self.match_started = False
        self.pause_buttons = []
        self.gameover_buttons = []
        self._build_menu_buttons()
        self._build_top_select_buttons()
        self._build_arena_select_buttons()
        self._build_pause_buttons()
        self._build_gameover_buttons()

    def _init_display(self):
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        try:
            if self.fullscreen:
                self.window = pygame.display.set_mode((0, 0), flags)
            else:
                self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        except:
            self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            self.fullscreen = False
        pygame.display.set_caption("Pambaram: Spinning Top Battle Arena")
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._init_display()

    def _map_mouse_pos(self, pos):
        win_w, win_h = self.window.get_size()
        scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
        scaled_w = int(SCREEN_WIDTH * scale)
        scaled_h = int(SCREEN_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        mx, my = pos
        rx = (mx - offset_x) / max(1, scale)
        ry = (my - offset_y) / max(1, scale)
        return (int(rx), int(ry))

    def _build_menu_buttons(self):
        bw, bh = 340, 65
        cx = SCREEN_WIDTH // 2 - bw // 2
        y_start = 280
        gap = 75
        self.menu_buttons = [
            Button(cx, y_start, bw, bh, "🤖 PLAYER VS AI", self._quick_match, 24),
            Button(cx, y_start + gap, bw, bh, "🎮 PLAYER VS PLAYER (MANUAL)", self._vs_player, 22),
            Button(cx, y_start + gap * 2, bw, bh, "🎯 TOURNAMENT SETUP", self._start_top_select, 24),
            Button(cx, y_start + gap * 3, bw, bh, "⚙ AI DIFFICULTY: " + self.ai_difficulty.name, self._cycle_difficulty, 22),
            Button(cx, y_start + gap * 4, bw, bh, "✖ QUIT", self._quit, 24),
        ]

    def _build_top_select_buttons(self):
        bw, bh = 200, 55
        self.top_select_buttons = [
            Button(SCREEN_WIDTH - 630, SCREEN_HEIGHT - 105, bw, bh, "◀ BACK", self._back_to_menu, 22),
            Button(SCREEN_WIDTH - 420, SCREEN_HEIGHT - 105, bw, bh, "MODE: " + ("VS AI" if self.p2_is_ai else "MANUAL 2P"), self._toggle_ai, 20),
            Button(SCREEN_WIDTH - 210, SCREEN_HEIGHT - 105, bw, bh, "NEXT ▶", self._start_arena_select, 22),
        ]

    def _build_arena_select_buttons(self):
        bw, bh = 200, 55
        self.arena_select_buttons = [
            Button(SCREEN_WIDTH - 430, SCREEN_HEIGHT - 100, bw, bh, "◀ BACK", self._back_to_top_select, 22),
            Button(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 100, bw, bh, "START!", self._start_match, 26,
                   active_color=COLORS["accent_green"]),
        ]

    def _build_pause_buttons(self):
        bw, bh = 320, 65
        cx = SCREEN_WIDTH // 2 - bw // 2
        self.pause_buttons = [
            Button(cx, 320, bw, bh, "▶ RESUME", self._resume, 26),
            Button(cx, 320 + 85, bw, bh, "↻ RESTART", self._restart_match, 26),
            Button(cx, 320 + 170, bw, bh, "🏠 MAIN MENU", self._back_to_menu, 26),
        ]

    def _build_gameover_buttons(self):
        bw, bh = 260, 60
        cx = SCREEN_WIDTH // 2
        self.gameover_buttons = [
            Button(cx - bw - 15, 590, bw, bh, "↻ REMATCH", self._restart_match, 24),
            Button(cx + 15, 590, bw, bh, "🏠 MAIN MENU", self._back_to_menu, 24),
        ]

    def _quick_match(self):
        self.p2_is_ai = True
        self._build_top_select_buttons()
        self._start_top_select()

    def _vs_player(self):
        self.p2_is_ai = False
        self._build_top_select_buttons()
        self._start_top_select()

    def _start_arena_select_from_menu(self):
        self.state = GameState.ARENA_SELECT

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
        self.menu_buttons[3].text = "⚙  AI DIFFICULTY: " + self.ai_difficulty.name

    def _toggle_ai(self):
        self.p2_is_ai = not self.p2_is_ai
        self.top_select_buttons[1].text = "MODE: " + ("VS AI" if self.p2_is_ai else "MANUAL 2P")

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
        self.countdown = 2
        self.countdown_timer = 0
        self.match_started = False
        self.screen_shake = (0, 0)
        self.shake_decay = 0

        if self.p2_is_ai:
            self.ai_controller = AIController(self.p2, self.ai_difficulty)
        else:
            self.ai_controller = None

        self.state = GameState.PLAYING

    def _restart_match(self):
        self._start_match()

    def _resume(self):
        self.state = GameState.PLAYING

    def _quit(self):
        self.running = False

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

    def _handle_menu_events(self, event):
        for b in self.menu_buttons:
            b.handle_event(event)

    def _handle_top_select_events(self, event):
        for b in self.top_select_buttons:
            b.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
            names = list(TOP_PRESETS.keys())
            card_w = 240
            card_h = 290
            gap_x = 20
            cols = 4
            start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
            start_y = 130
            for idx, name in enumerate(names):
                col = idx % cols
                row = idx // cols
                cx = start_x + col * (card_w + gap_x)
                cy = start_y + row * (card_h + gap_x)
                rect = pygame.Rect(cx, cy, card_w, card_h)
                if rect.collidepoint(event.pos):
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.p1_top_name = name
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                        self.p2_top_name = name

    def _handle_arena_select_events(self, event):
        for b in self.arena_select_buttons:
            b.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            card_w = 260
            card_h = 340
            gap_x = 30
            cols = 4
            start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
            start_y = 120
            for idx, key in enumerate(ARENA_PRESETS.keys()):
                col = idx % cols
                row = idx // cols
                cx = start_x + col * (card_w + gap_x)
                cy = start_y + row * (card_h + gap_x)
                rect = pygame.Rect(cx, cy, card_w, card_h)
                if rect.collidepoint(event.pos):
                    self.selected_arena = key

    def _start_launch_drag(self, top, mouse_pos, player_id):
        dx = mouse_pos[0] - top.x
        dy = mouse_pos[1] - top.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < top.radius + 40:
            drag_data = {"start": mouse_pos, "current": mouse_pos, "start_tick": pygame.time.get_ticks()}
            if player_id == 1:
                self.drag_p1 = drag_data
            else:
                self.drag_p2 = drag_data

    def _release_launch_drag(self, top, player_id):
        drag = self.drag_p1 if player_id == 1 else self.drag_p2
        if drag is None:
            return
        sx, sy = drag["start"]
        cx, cy = drag["current"]
        dx = sx - cx
        dy = sy - cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 8:
            dir_x = dx / max(1, dist)
            dir_y = dy / max(1, dist)
            force = min(900, dist * 4.5 + 200)
            spin_factor = min(1.0, 0.5 + dist / 400)
            top.launch(dir_x, dir_y, force, spin_factor)
            self.particles.emit_dust(top.x, top.y, 20)
            self._apply_shake(3)
        else:
            angle = random.uniform(0, math.pi * 2)
            top.launch(math.cos(angle), math.sin(angle), 150, 0.7)
        if player_id == 1:
            self.drag_p1 = None
        else:
            self.drag_p2 = None

    def _ai_auto_launch(self):
        if self.p2_is_ai and self.p2 and not self.p2.is_launched and self.match_started:
            angle = math.atan2(self.p1.y - self.p2.y, self.p1.x - self.p2.x) + random.uniform(-0.4, 0.4)
            force = random.uniform(500, 900)
            self.p2.launch(math.cos(angle), math.sin(angle), force, random.uniform(0.8, 1.0))
            self.particles.emit_dust(self.p2.x, self.p2.y, 20)

    def _handle_playing_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.PAUSED
            if event.key == pygame.K_SPACE and self.match_started and self.p1.is_launched:
                if self.p1.activate_special([self.p1, self.p2]):
                    self.particles.emit_special(self.p1.x, self.p1.y, self.p1.color, 30)
                    self._apply_shake(5)
            if event.key == pygame.K_RETURN and self.match_started and not self.p2_is_ai and self.p2.is_launched:
                if self.p2.activate_special([self.p1, self.p2]):
                    self.particles.emit_special(self.p2.x, self.p2.y, self.p2.color, 30)
                    self._apply_shake(5)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not self.p1.is_launched and self.match_started:
                self._start_launch_drag(self.p1, event.pos, 1)
            if event.button == 3 and not self.p2_is_ai and not self.p2.is_launched and self.match_started:
                self._start_launch_drag(self.p2, event.pos, 2)
            if event.button == 2:
                self._ai_auto_launch()
        elif event.type == pygame.MOUSEMOTION:
            if self.drag_p1:
                self.drag_p1["current"] = event.pos
            if self.drag_p2:
                self.drag_p2["current"] = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.drag_p1:
                self._release_launch_drag(self.p1, 1)
            if event.button == 3 and self.drag_p2:
                self._release_launch_drag(self.p2, 2)

    def _handle_pause_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
            return
        for b in self.pause_buttons:
            b.handle_event(event)

    def _handle_gameover_events(self, event):
        for b in self.gameover_buttons:
            b.handle_event(event)

    def _update_countdown(self, dt):
        self.countdown_timer += dt
        if self.countdown_timer >= 0.5:
            self.countdown_timer = 0
            self.countdown -= 1
            if self.countdown < 0:
                self.match_started = True
                self._ai_auto_launch()

    def _update_gameplay(self, dt):
        if not self.match_started:
            self._update_countdown(dt)
            return

        self.match_time -= dt
        keys = pygame.key.get_pressed()

        if self.p1.is_launched and not self.p1.is_knocked_out:
            sx, sy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]:
                sx = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
                sy = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
                self.p1.steer(sx, sy)
            if keys[pygame.K_LSHIFT] and (sx != 0 or sy != 0):
                self.p1.dash(sx, sy)

        if not self.p2_is_ai and self.p2.is_launched and not self.p2.is_knocked_out:
            sx, sy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                sx = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
                sy = (1 if keys[pygame.K_DOWN] else 0) - (1 if keys[pygame.K_UP] else 0)
                self.p2.steer(sx, sy)
            if keys[pygame.K_RSHIFT] and (sx != 0 or sy != 0):
                self.p2.dash(sx, sy)

        if self.ai_controller and self.p2.is_launched:
            result = self.ai_controller.update(self.p1, dt)
            if result and result[0] is not None:
                steer, dash_do, special_do = result
                if self.p2.is_launched and not self.p2.is_knocked_out:
                    self.p2.steer(steer[0], steer[1])
                    if dash_do:
                        self.p2.dash(steer[0], steer[1])
                    if special_do:
                        if self.p2.activate_special([self.p1, self.p2]):
                            self.particles.emit_special(self.p2.x, self.p2.y, self.p2.color, 30)
                            self._apply_shake(5)

        grip_mod = self.arena.grip_mod

        self.p1.update(dt, grip_mod)
        self.p2.update(dt, grip_mod)

        shake1 = self.p1.check_boundary()
        shake2 = self.p2.check_boundary()
        if shake1 == "bounce":
            self._apply_shake(4)
            self.particles.emit_sparks(self.p1.x, self.p1.y,
                                        (self.p1.x - ARENA_CENTER[0]) / max(1, math.sqrt(
                                            (self.p1.x - ARENA_CENTER[0]) ** 2 + (
                                                        self.p1.y - ARENA_CENTER[1]) ** 2)),
                                        (self.p1.y - ARENA_CENTER[1]) / max(1, math.sqrt(
                                            (self.p1.x - ARENA_CENTER[0]) ** 2 + (
                                                        self.p1.y - ARENA_CENTER[1]) ** 2)), 8)
        if shake1 == "ringout":
            self.particles.emit_ringout(self.p1.x, self.p1.y, 40)
            self._apply_shake(10)
        if shake2 == "bounce":
            self._apply_shake(4)
        if shake2 == "ringout":
            self.particles.emit_ringout(self.p2.x, self.p2.y, 40)
            self._apply_shake(10)

        col_shake = resolve_top_collision(self.p1, self.p2, self.particles)
        if col_shake:
            self._apply_shake(col_shake)

        obs_shake = check_obstacle_collision(self.p1, self.arena.obstacles)
        obs_shake += check_obstacle_collision(self.p2, self.arena.obstacles)
        if obs_shake:
            self._apply_shake(obs_shake)

        check_boost_pad(self.p1, self.arena.boost_pads, self.particles)
        check_boost_pad(self.p2, self.arena.boost_pads, self.particles)

        if self.p1.is_spinning and random.random() < 0.1:
            self.particles.emit_spin(self.p1.x, self.p1.y, 1)
        if self.p2.is_spinning and random.random() < 0.1:
            self.particles.emit_spin(self.p2.x, self.p2.y, 1)

        self.arena.update(dt)
        self.particles.update(dt)
        self._update_shake(dt)

        self._check_win_conditions()

    def _check_win_conditions(self):
        if not self.match_started:
            return

        # Matches only evaluate once BOTH tops have been launched
        if not (self.p1.is_launched and self.p2.is_launched):
            return

        p1_out = self.p1.is_knocked_out and self.p1.knockout_timer > 1.5
        p2_out = self.p2.is_knocked_out and self.p2.knockout_timer > 1.5
        p1_dead = not self.p1.is_spinning and self.p1.spin <= 0 and not self.p1.is_knocked_out
        p2_dead = not self.p2.is_spinning and self.p2.spin <= 0 and not self.p2.is_knocked_out

        reason = ""
        win = None

        if p1_out and not p2_out:
            win = self.p2
            reason = f"RING OUT! {self.p1.name} was knocked out!"
        elif p2_out and not p1_out:
            win = self.p1
            reason = f"RING OUT! {self.p2.name} was knocked out!"
        elif p1_out and p2_out:
            r1 = self.p1.knockout_timer
            r2 = self.p2.knockout_timer
            win = self.p1 if r1 < r2 else self.p2 if r2 < r1 else None
            reason = "DOUBLE RING OUT!"
        elif p1_dead and not p2_dead:
            win = self.p2
            reason = f"SPIN OUT! {self.p1.name} ran out of spin!"
        elif p2_dead and not p1_dead:
            win = self.p1
            reason = f"SPIN OUT! {self.p2.name} ran out of spin!"
        elif p1_dead and p2_dead:
            reason = "DOUBLE SPIN OUT! IT'S A DRAW!"
            win = None
        elif self.match_time <= 0:
            s1 = self.p1.spin / self.p1.max_spin if self.p1.max_spin > 0 else 0
            s2 = self.p2.spin / self.p2.max_spin if self.p2.max_spin > 0 else 0
            if abs(s1 - s2) > 0.02:
                win = self.p1 if s1 > s2 else self.p2
                reason = f"TIME UP! {win.name} has more spin remaining!"
            else:
                reason = "TIME UP! EQUAL SPIN - IT'S A DRAW!"
                win = None

        if win is not None or (self.match_time <= 0 and self.p1.is_launched and self.p2.is_launched) or (p1_dead and p2_dead):
            self.winner = win
            elapsed = MATCH_TIME - max(0, self.match_time)
            
            # Dynamic Score Calculation
            base_points = 0
            if win:
                winning_spin_pct = (win.spin / win.max_spin) * 100 if win.max_spin > 0 else 0
                time_bonus = max(0, int((MATCH_TIME - elapsed) * 2))
                ringout_bonus = 150 if "RING OUT" in reason else 100
                base_points = int(200 + winning_spin_pct * 3 + time_bonus + ringout_bonus)
            
            self.stats = {
                "win_reason": reason,
                "match_time": elapsed,
                "p1_final_spin": self.p1.spin,
                "p2_final_spin": self.p2.spin,
                "points": base_points,
            }
            self.state = GameState.GAME_OVER

    def _draw_background(self):
        self.screen.fill(COLORS["bg_dark"])
        for i in range(8):
            r = 100 + i * 80
            a = 3
            pygame.draw.circle(self.screen, (60 + i * 5, 40 + i * 4, 90 + i * 8), ARENA_CENTER, r, 1)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                    continue

                if hasattr(event, "pos"):
                    event.pos = self._map_mouse_pos(event.pos)

                if self.state == GameState.MENU:
                    self._handle_menu_events(event)
                elif self.state == GameState.TOP_SELECT:
                    self._handle_top_select_events(event)
                elif self.state == GameState.ARENA_SELECT:
                    self._handle_arena_select_events(event)
                elif self.state == GameState.PLAYING:
                    self._handle_playing_events(event)
                elif self.state == GameState.PAUSED:
                    self._handle_pause_events(event)
                elif self.state == GameState.GAME_OVER:
                    self._handle_gameover_events(event)

            self._draw_background()

            if self.state == GameState.MENU:
                draw_menu(self.screen, self.menu_buttons)

            elif self.state == GameState.TOP_SELECT:
                draw_top_select(self.screen, TOP_PRESETS, self.p1_top_name, self.p2_top_name,
                                self.p2_is_ai, self.top_select_buttons, self.ai_difficulty)

            elif self.state == GameState.ARENA_SELECT:
                draw_arena_select(self.screen, ARENA_PRESETS, self.selected_arena, self.arena_select_buttons)

            elif self.state in (GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER):
                if self.arena:
                    self.arena.draw(self.screen, self.screen_shake)
                if self.p1:
                    self.p1.draw(self.screen, self.screen_shake)
                if self.p2:
                    self.p2.draw(self.screen, self.screen_shake)
                self.particles.draw(self.screen, self.screen_shake)

                if self.p1 and self.p2:
                    if self.drag_p1:
                        draw_launch_indicator(self.screen, self.p1, 1, self.drag_p1["start"], self.drag_p1["current"])
                    if self.drag_p2:
                        draw_launch_indicator(self.screen, self.p2, 2, self.drag_p2["start"], self.drag_p2["current"])

                if not self.match_started and self.p1 and self.p2:
                    draw_countdown(self.screen, self.countdown)

                if self.match_started or (self.p1 and self.p2):
                    if self.p1 and self.p2:
                        draw_hud(self.screen, self.p1, self.p2, max(0, self.match_time))

                    if not self.match_started:
                        hint_font = get_font(22, bold=True)
                        if not self.p1.is_launched:
                            hint = hint_font.render(f"LEFT CLICK + DRAG on P1 Top to LAUNCH", True, COLORS["p1_color"])
                            self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)))
                        if not self.p2_is_ai and not self.p2.is_launched:
                            hint2 = hint_font.render(f"RIGHT CLICK + DRAG on P2 Top to LAUNCH", True, COLORS["p2_color"])
                            self.screen.blit(hint2, hint2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)))
                        if self.p2_is_ai and not self.p2.is_launched and self.match_started:
                            pass
                        if self.p2_is_ai and not self.match_started:
                            m = get_font(16).render("Tip: Click MIDDLE MOUSE BUTTON to force AI launch", True, COLORS["text_gray"])
                            self.screen.blit(m, m.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)))

                if self.state == GameState.PLAYING:
                    self._update_gameplay(dt)
                elif self.state == GameState.PAUSED:
                    draw_pause(self.screen, self.pause_buttons)
                elif self.state == GameState.GAME_OVER:
                    draw_game_over(self.screen, self.winner, self.stats, self.gameover_buttons)

            win_w, win_h = self.window.get_size()
            scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
            scaled_w = int(SCREEN_WIDTH * scale)
            scaled_h = int(SCREEN_HEIGHT * scale)
            offset_x = (win_w - scaled_w) // 2
            offset_y = (win_h - scaled_h) // 2

            self.window.fill((10, 10, 15))
            scaled_surf = pygame.transform.smoothscale(self.screen, (scaled_w, scaled_h))
            self.window.blit(scaled_surf, (offset_x, offset_y))
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
