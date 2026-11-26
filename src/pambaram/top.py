import pygame
import pygame.gfxdraw
import math
import random
from .config import *
from .top_art import render_top


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

        # Seconds since this top took a strong hit (counts down from
        # HIT_WINDOW). Only a top that was just hit can be carried over the
        # rim; a top that steers or launches itself into the wall bounces.
        self.hit_timer = 0.0
        self.escaping = False

        self.launch_quality = 1.0
        self.decay_mult = 1.0
        # P1 spins one way, P2 the other, so their paths curve oppositely.
        self.spin_dir = 1 if self.player_id == 1 else -1

        self.trail_points = []

    def launch(self, direction_x, direction_y, force, initial_spin_factor=1.0, quality=None):
        """quality (0..1) is how well the launch was timed. A weak launch
        starts with less stamina (spin) and also burns it faster, because the
        top comes off the launcher wobbling. quality=None keeps the old
        behaviour (initial_spin_factor decides the spin, normal decay)."""
        self.is_launched = True
        self.is_spinning = True
        if quality is not None:
            q = max(0.0, min(1.0, quality))
            self.launch_quality = q
            initial_spin_factor = LAUNCH_MIN_SPIN + (1.0 - LAUNCH_MIN_SPIN) * q
            self.decay_mult = 1.0 + LAUNCH_WEAK_DECAY * (1.0 - q)
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

        if self.hit_timer > 0:
            self.hit_timer = max(0.0, self.hit_timer - dt)

        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt

        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False

        decay_mod = self.decay_mult
        if self.is_dashing:
            decay_mod *= 2.5
        # Floor grip scales spin decay (design doc 4.1): slick floors such as
        # the River Bed sap less spin than grippy ones.
        self.spin -= self.spin_decay * decay_mod * arena_grip_mod * dt
        if self.spin <= 0:
            self.spin = 0
            self.is_spinning = False
            self.vx *= 0.85
            self.vy *= 0.85
            if abs(self.vx) < 3 and abs(self.vy) < 3:
                self.vx = 0
                self.vy = 0

        self.wobble = max(0.0, (1.0 - spin_ratio) * 15)
        if spin_ratio < 0.2:
            self.wobble += math.sin(pygame.time.get_ticks() * 0.02) * (5 - spin_ratio * 25)

        effective_grip = self.grip * arena_grip_mod

        # Player / AI steering: a responsive push that weakens as the top
        # loses spin (a dying top is hard to control).
        steer_power = STEER_ACCEL * effective_grip * (0.35 + spin_ratio * 0.65)
        if self.is_dashing:
            steer_power *= 2.0
        if self.is_spinning and (self.steer_x != 0 or self.steer_y != 0):
            mag = math.sqrt(self.steer_x ** 2 + self.steer_y ** 2)
            if mag > 0:
                self.vx += (self.steer_x / mag) * steer_power * dt
                self.vy += (self.steer_y / mag) * steer_power * dt

        # The stadium is a shallow bowl: the slope always pulls a top back
        # toward the centre, so it keeps rolling and circling instead of
        # coasting to a dead stop wherever it happens to be.
        if self.is_spinning:
            cdx = ARENA_CENTER[0] - self.x
            cdy = ARENA_CENTER[1] - self.y
            self.vx += cdx / ARENA_RADIUS * BOWL_ACCEL * dt
            self.vy += cdy / ARENA_RADIUS * BOWL_ACCEL * dt

            # Gyroscopic precession: a spinning top's path curves slightly
            # sideways, which turns straight runs into arcs and orbits.
            speed = math.hypot(self.vx, self.vy)
            if speed > 20:
                ang = PRECESSION_RATE * self.spin_dir * (0.3 + 0.7 * spin_ratio) * dt
                c, s = math.cos(ang), math.sin(ang)
                self.vx, self.vy = self.vx * c - self.vy * s, self.vx * s + self.vy * c

        # Rolling friction: tiny while the tip spins fast, heavy once the top
        # slows down and starts scraping the floor.
        friction = FLOOR_FRICTION * effective_grip * (1.0 + 3.0 * (1.0 - spin_ratio) ** 2)
        if not self.is_spinning:
            friction = 3.0
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > 0:
            new_speed = max(0.0, speed * (1.0 - friction * dt))
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
            self.special_timer = 3.0
            self.grip = self.base_grip * 1.5
            self.spin_decay = self.preset["spin_decay"] * 0.4

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

        if self.is_knocked_out:
            return None

        if dist >= RINGOUT_RADIUS:
            self.is_knocked_out = True
            self.knockout_timer = 0
            self.escaping = False
            return "ringout"

        if dist < ARENA_RADIUS:
            self.escaping = False
            return None

        nx = dx / dist
        ny = dy / dist
        dot = self.vx * nx + self.vy * ny

        # A top that was just smashed toward the rim fast enough sails over
        # it instead of bouncing. Without this, the wall always reflected the
        # top and pushed it back inside, so a ring-out could never happen.
        if not self.escaping and self.hit_timer > 0 and dot > RINGOUT_ESCAPE_SPEED:
            self.escaping = True
        if self.escaping:
            if dot > 0:
                return None
            self.escaping = False

        if dot > 0:
            self.vx -= 2 * dot * nx
            self.vy -= 2 * dot * ny
            self.vx *= 0.65
            self.vy *= 0.65
            self.spin = max(0, self.spin - self.max_spin * WALL_SPIN_COST)
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

        spin_ratio = self.spin / self.max_spin if self.max_spin > 0 else 0

        if self.is_knocked_out:
            # Falling off the stage: shrink and fade out.
            k = max(0.0, 1.0 - self.knockout_timer / 1.2)
            if k > 0.05:
                art = render_top(max(4, int(r * (0.4 + 0.6 * k))), self.color, self.accent, self.type,
                                 self.rotation, spin_ratio)
                art.set_alpha(int(255 * k))
                surface.blit(art, art.get_rect(center=(px, py)))
            return

        wobble_dx = math.sin(self.rotation * 3) * self.wobble * 0.5
        wobble_dy = math.cos(self.rotation * 2) * self.wobble * 0.3
        cx = px + int(wobble_dx)
        cy = py + int(wobble_dy)

        # Team ring on the floor (blue = P1, red = P2/AI) so each player can
        # always find their own top. It replaces the old corner badge dot.
        team = COLORS["p1_color"] if self.player_id == 1 else COLORS["p2_color"]
        ring_r = r + 7
        ring = pygame.Surface((ring_r * 2 + 6, ring_r * 2 + 6), pygame.SRCALPHA)
        rc = ring_r + 3
        pygame.draw.circle(ring, (*team, 55), (rc, rc), ring_r)
        for rr in (ring_r, ring_r - 1):
            pygame.gfxdraw.aacircle(ring, rc, rc, rr, (*team, 230))
        surface.blit(ring, (px - rc, py - rc))

        if self.invincible and (pygame.time.get_ticks() // 80) % 2 == 0:
            pygame.draw.circle(surface, (255, 255, 255), (px, py), r + 10, 2)

        # Soft contact shadow, offset down-right (light comes from top-left).
        shadow_r = max(1, int(r * 0.95))
        shadow = pygame.Surface((shadow_r * 2 + 4, shadow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(shadow, (0, 0, 0, 85), (shadow_r + 2, shadow_r + 2), shadow_r)
        surface.blit(shadow, (cx - shadow_r - 2 + 4, cy - shadow_r - 2 + 6))

        art = render_top(r, self.color, self.accent, self.type, self.rotation * self.spin_dir, spin_ratio)
        surface.blit(art, art.get_rect(center=(cx, cy)))
