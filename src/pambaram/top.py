import pygame
import pygame.gfxdraw
import math
import random
from .config import *


def _shade(color, factor):
    """Lighten (factor > 0) or darken (factor < 0) an RGB tuple."""
    if factor >= 0:
        return tuple(min(255, int(c + (255 - c) * factor)) for c in color)
    return tuple(max(0, int(c * (1 + factor))) for c in color)

class Top:
    def __init__(self, name, preset, player_id, is_ai=False, difficulty=Difficulty.MEDIUM):
        self.name = name
        self.preset = preset
        self.player_id = player_id
        self.is_ai = is_ai
        self.difficulty = difficulty

        self.type = preset["type"]
        self.base_mass = preset["mass"]
        self.mass = preset["mass"]
        self.base_max_spin = preset["spin_speed"]
        self.max_spin = preset["spin_speed"]
        self.spin_decay = preset["spin_decay"]
        self.base_grip = preset["grip"]
        self.grip = preset["grip"]
        self.color = preset["color"]
        self.accent = preset["accent"]
        self.special_name = preset["special"]

        self.radius = 22 + (self.mass - 1.8) * 3

        self.reset()

    def reset(self):
        self.x = ARENA_CENTER[0] + (-200 if self.player_id == 1 else 200)
        self.y = ARENA_CENTER[1]
        self.vx = 0
        self.vy = 0
        self.spin = 0
        self.rotation = random.uniform(0, math.pi * 2)
        self.is_spinning = False
        self.is_launched = False
        self.is_knocked_out = False
        self.knockout_timer = 0

        self.special_meter = 0
        self.special_active = False
        self.special_timer = 0

        self.dash_cooldown = 0
        self.is_dashing = False
        self.dash_timer = 0

        self.wobble = 0
        self.invincible = False
        self.invincible_timer = 0

        self.steer_x = 0
        self.steer_y = 0

        self.lifetime = TOP_LIFETIME  # seconds remaining before auto-stop
        self.active = True

        self.trail_points = []

    def launch(self, direction_x, direction_y, force, initial_spin_factor=1.0):
        self.is_launched = True
        self.is_spinning = True
        self.spin = self.max_spin * initial_spin_factor
        self.vx = direction_x * force
        self.vy = direction_y * force
        self.lifetime = TOP_LIFETIME
        self.active = True

    def update(self, dt, arena_grip_mod=1.0):
        if self.is_knocked_out:
            self.knockout_timer += dt
            self.vx *= 0.95
            self.vy *= 0.95
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.spin > 0:
                self.spin -= self.spin_decay * 3 * dt
            return


        # Auto-stop timer: if lifetime expires, the top stops spinning and moving.
        self.lifetime -= dt
        if self.lifetime <= 0 and self.active:
            self.active = False
            self.spin = 0
            self.is_spinning = False
            self.vx = 0
            self.vy = 0
            # Do not return immediately; allow one frame of zero state to be processed.
            # The win condition will catch spin=0 on the next evaluation.
            # Keep updating position (which is already zero velocity) and continue.
        if not self.is_launched:
            return

        spin_ratio = self.spin / self.max_spin if self.max_spin > 0 else 0

        if self.special_active:
            self.special_timer -= dt
            if self.special_timer <= 0:
                self.special_active = False
                self._end_special()

        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False

        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt

        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False

        decay_mod = 1.0
        if self.is_dashing:
            decay_mod *= 2.5
        self.spin -= self.spin_decay * decay_mod * dt
        if self.spin <= 0:
            self.spin = 0
            self.is_spinning = False

        self.wobble = max(0.0, (1.0 - spin_ratio) * 15)
        if spin_ratio < 0.2:
            self.wobble += math.sin(pygame.time.get_ticks() * 0.02) * (5 - spin_ratio * 25)

        effective_grip = self.grip * arena_grip_mod
        steer_power = 250 * effective_grip * (0.3 + spin_ratio * 0.7)
        if self.is_dashing:
            steer_power *= 2.5

        if self.is_spinning and (self.steer_x != 0 or self.steer_y != 0):
            mag = math.sqrt(self.steer_x ** 2 + self.steer_y ** 2)
            if mag > 0:
                nx = self.steer_x / mag
                ny = self.steer_y / mag
                resistance = 1.0 + (1.0 - spin_ratio) * 0.5
                self.vx += (nx * steer_power) * dt / resistance
                self.vy += (ny * steer_power) * dt / resistance

        friction = 0.4 * effective_grip
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > 0:
            drag = friction * dt * (1 + (1 - spin_ratio) * 0.5)
            new_speed = max(0, speed - drag * speed)
            if speed > 0:
                self.vx *= new_speed / speed
                self.vy *= new_speed / speed

        max_speed = 800 * (0.7 + spin_ratio * 0.5)
        if self.type == TopType.SPEED:
            max_speed *= 1.25
        if self.is_dashing:
            max_speed *= 2.0

        cur_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if cur_speed > max_speed:
            scale = max_speed / cur_speed
            self.vx *= scale
            self.vy *= scale

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.is_spinning:
            self.rotation += (spin_ratio * 18) * dt
            self.special_meter = min(100, self.special_meter + spin_ratio * 8 * dt)

        self.trail_points.append((self.x, self.y, self.spin / self.max_spin if self.max_spin > 0 else 0))
        if len(self.trail_points) > 20:
            self.trail_points.pop(0)

        self.steer_x = 0
        self.steer_y = 0

    def steer(self, dx, dy):
        self.steer_x = dx
        self.steer_y = dy

    def dash(self, dx, dy):
        if self.dash_cooldown > 0 or not self.is_spinning:
            return False
        mag = math.sqrt(dx * dx + dy * dy)
        if mag == 0:
            return False
        self.vx += (dx / mag) * 600
        self.vy += (dy / mag) * 600
        self.is_dashing = True
        self.dash_timer = 0.25
        self.dash_cooldown = 1.5
        self.spin = max(0, self.spin - self.max_spin * 0.08)
        self.special_meter = min(100, self.special_meter + 5)
        return True

    def activate_special(self, all_tops=None):
        if self.special_meter < 100 or not self.is_spinning:
            return False

        self.special_meter = 0
        self.special_active = True

        if self.type == TopType.ATTACK:
            self.special_timer = 0.8
            self.invincible = True
            self.invincible_timer = 0.8
            speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
            if speed > 0:
                self.vx *= 2.5
                self.vy *= 2.5
            else:
                angle = self.rotation
                self.vx = math.cos(angle) * 800
                self.vy = math.sin(angle) * 800

        elif self.type == TopType.DEFENSE:
            self.special_timer = 3.0
            self.invincible = True
            self.invincible_timer = 3.0
            self.mass = self.base_mass * 2.0
            self.grip = self.base_grip * 1.5

        elif self.type == TopType.BALANCE:
            self.special_timer = 0.5
            self.spin = min(self.max_spin, self.spin + self.max_spin * 0.4)

        elif self.type == TopType.SPEED:
            self.special_timer = 2.5
            if all_tops:
                for other in all_tops:
                    if other is not self and other.is_launched and not other.is_knocked_out:
                        dx = self.x - other.x
                        dy = self.y - other.y
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist < 250 and dist > 0:
                            pull = (250 - dist) * 4
                            other.vx += (dx / dist) * pull
                            other.vy += (dy / dist) * pull
            self.grip = self.base_grip * 0.5
            self.spin_decay = self.preset["spin_decay"] * 0.5

        return True

    def _end_special(self):
        self.mass = self.base_mass
        self.grip = self.base_grip
        self.spin_decay = self.preset["spin_decay"]

    def check_boundary(self):
        dx = self.x - ARENA_CENTER[0]
        dy = self.y - ARENA_CENTER[1]
        dist = math.sqrt(dx * dx + dy * dy)

        # Recovery check: if top drifts back inside ringout threshold, cancel knockout state
        if dist <= RINGOUT_RADIUS and self.is_knocked_out:
            self.is_knocked_out = False
            self.knockout_timer = 0

        if dist >= RINGOUT_RADIUS and not self.is_knocked_out:
            self.is_knocked_out = True
            self.knockout_timer = 0
            return "ringout"

        if dist >= ARENA_RADIUS and not self.is_knocked_out and dist < RINGOUT_RADIUS:
            nx = dx / dist
            ny = dy / dist
            dot = self.vx * nx + self.vy * ny
            if dot > 0:
                self.vx -= 2 * dot * nx
                self.vy -= 2 * dot * ny
                self.vx *= 0.65
                self.vy *= 0.65
                self.spin = max(0, self.spin - self.max_spin * 0.03)
                push = (ARENA_RADIUS - dist - 2)
                if push < 0:
                    self.x += nx * push
                    self.y += ny * push
                return "bounce"
        return None

    def draw(self, surface, shake=(0, 0)):
        sx = shake[0]
        sy = shake[1]

        if len(self.trail_points) > 1:
            for i in range(1, len(self.trail_points)):
                alpha = i / len(self.trail_points)
                px, py, sr = self.trail_points[i]
                color = (
                    int(self.color[0] * sr * 0.7),
                    int(self.color[1] * sr * 0.7),
                    int(self.color[2] * sr * 0.7),
                )
                r = int(self.radius * 0.3 * alpha)
                pygame.draw.circle(surface, color, (int(px + sx), int(py + sy)), max(1, r))

        px = int(self.x + sx)
        py = int(self.y + sy)
        r = int(self.radius)

        if not self.is_launched:
            # Pulsing ring cue so it's obvious this top can be grabbed and
            # flung - a top never has both is_launched=False and
            # is_knocked_out=True, so this can't collide with the KO fade below.
            pulse = (math.sin(pygame.time.get_ticks() * 0.004) + 1) * 0.5
            ring_r = r + 12 + int(pulse * 7)
            ring_alpha = 90 + int(pulse * 90)
            ring_surf = pygame.Surface((ring_r * 2 + 8, ring_r * 2 + 8), pygame.SRCALPHA)
            ring_col = tuple(min(255, c + 50) for c in self.accent)
            for rr in (ring_r - 1, ring_r, ring_r + 1):
                pygame.gfxdraw.aacircle(ring_surf, ring_r + 4, ring_r + 4, rr, (*ring_col, ring_alpha))
            surface.blit(ring_surf, (px - ring_r - 4, py - ring_r - 4))

        if self.is_knocked_out:
            fade_r = max(2, r - int(self.knockout_timer * 15))
            pygame.gfxdraw.filled_circle(surface, px, py, fade_r, self.color)
            pygame.gfxdraw.aacircle(surface, px, py, fade_r, self.color)
            return

        wobble_dx = math.sin(self.rotation * 3) * self.wobble * 0.5
        wobble_dy = math.cos(self.rotation * 2) * self.wobble * 0.3
        cx = px + int(wobble_dx)
        cy = py + int(wobble_dy)

        if self.special_active:
            if self.type == TopType.ATTACK:
                for i in range(3):
                    glow = 20 - i * 6
                    pygame.draw.circle(surface, (255, 150 + i * 30, 50), (px, py), r + glow, 2)
            elif self.type == TopType.DEFENSE:
                pygame.draw.circle(surface, (100, 180, 255), (px, py), r + 15, 3)
            elif self.type == TopType.SPEED:
                for ang in range(0, 360, 30):
                    rad = math.radians(ang + pygame.time.get_ticks() * 0.5)
                    ex = px + math.cos(rad) * (r + 15)
                    ey = py + math.sin(rad) * (r + 15)
                    pygame.draw.line(surface, (255, 150, 255), (px, py), (int(ex), int(ey)), 2)

        if self.invincible and not self.special_active:
            blink = (pygame.time.get_ticks() // 80) % 2 == 0
            if blink:
                pygame.draw.circle(surface, (255, 255, 255), (px, py), r + 5, 2)

        rim_color = _shade(self.color, -0.32)
        light_color = _shade(self.color, 0.30)

        # Soft grounded shadow, offset slightly for a hint of depth.
        shadow_r = max(1, int(r * 0.92))
        shadow_surf = pygame.Surface((shadow_r * 2 + 4, shadow_r * 2 + 4), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(shadow_surf, shadow_r + 2, shadow_r + 2, shadow_r, (0, 0, 0, 80))
        surface.blit(shadow_surf, (px - shadow_r - 2 + 4, py - shadow_r - 2 + 5))

        # Domed body: concentric shaded rings from a dark rim to a lit core,
        # instead of one flat fill, so it reads as a rounded toy top.
        steps = 5
        for i in range(steps, -1, -1):
            t = i / steps
            rad = max(1, int(r * (0.32 + 0.68 * t)))
            col = tuple(int(rim_color[k] * t + light_color[k] * (1 - t)) for k in range(3))
            pygame.gfxdraw.filled_circle(surface, cx, cy, rad, col)
        pygame.gfxdraw.aacircle(surface, cx, cy, r, rim_color)

        # Accent cap, offset slightly as spin winds down, shaded the same way.
        inner_r = max(2, int(r * 0.58))
        spin_r = 1 - (self.spin / self.max_spin if self.max_spin > 0 else 0)
        acx = int(cx + math.cos(self.rotation) * spin_r * 4)
        acy = int(cy + math.sin(self.rotation) * spin_r * 4)
        accent_rim = _shade(self.accent, -0.22)
        accent_light = _shade(self.accent, 0.28)
        for i in range(3, -1, -1):
            t = i / 3
            rad = max(1, int(inner_r * (0.42 + 0.58 * t)))
            col = tuple(int(accent_rim[k] * t + accent_light[k] * (1 - t)) for k in range(3))
            pygame.gfxdraw.filled_circle(surface, acx, acy, rad, col)
        pygame.gfxdraw.aacircle(surface, acx, acy, inner_r, accent_rim)

        # Spin blades: crisp and thick once it's slowing down, thin and
        # bright while spinning fast (reads like motion blur).
        spin_ratio = self.spin / self.max_spin if self.max_spin > 0 else 0
        center_r = max(3, int(r * 0.22))
        if spin_ratio < 0.15:
            blade_w, blade_col = 3, rim_color
        elif spin_ratio < 0.5:
            blade_w, blade_col = 2, rim_color
        else:
            blade_w, blade_col = 1, tuple(min(255, c + 50) for c in rim_color)
        for i in range(4):
            ang = self.rotation + i * (math.pi / 2)
            x1 = cx + math.cos(ang) * center_r
            y1 = cy + math.sin(ang) * center_r
            x2 = cx + math.cos(ang) * (r - 3)
            y2 = cy + math.sin(ang) * (r - 3)
            pygame.draw.line(surface, blade_col, (int(x1), int(y1)), (int(x2), int(y2)), blade_w)

        # Center hub: small metal-bearing look.
        pygame.gfxdraw.filled_circle(surface, cx, cy, center_r, rim_color)
        pygame.gfxdraw.aacircle(surface, cx, cy, center_r, rim_color)
        hub_hl_r = max(2, center_r - 3)
        pygame.gfxdraw.filled_circle(surface, cx, cy, hub_hl_r, (250, 250, 252))
        pygame.gfxdraw.aacircle(surface, cx, cy, hub_hl_r, (250, 250, 252))

        # Small player badge, tucked at the bottom-right of the body.
        badge_col = COLORS["p1_color"] if self.player_id == 1 else COLORS["p2_color"]
        bx, by = px + int(r * 0.74), py + int(r * 0.74)
        pygame.gfxdraw.filled_circle(surface, bx, by, 7, badge_col)
        pygame.gfxdraw.aacircle(surface, bx, by, 7, (18, 19, 24))
