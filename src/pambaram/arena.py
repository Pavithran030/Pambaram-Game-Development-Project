import pygame
import math
import random
from config import *
from particles import ParticleSystem

class Arena:
    def __init__(self, preset_key="Gramam Thidal"):
        self.preset_key = preset_key
        self.preset = ARENA_PRESETS[preset_key]
        self.floor_color = self.preset["floor_color"]
        self.ring_color = self.preset["ring_color"]
        self.void_color = self.preset["void_color"]
        self.grip_mod = self.preset["grip_mod"]
        self.hazards = self.preset["hazards"]

        self.obstacles = []
        self.boost_pads = []
        self._setup_hazards()

    def _setup_hazards(self):
        if "pillars" in self.hazards:
            for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
                r = 80
                ox = ARENA_CENTER[0] + math.cos(angle) * r
                oy = ARENA_CENTER[1] + math.sin(angle) * r
                self.obstacles.append({"x": ox, "y": oy, "r": 25})
        if "boost_pads" in self.hazards:
            for angle in [math.pi/4, 3*math.pi/4, 5*math.pi/4, 7*math.pi/4]:
                r = 160
                ox = ARENA_CENTER[0] + math.cos(angle) * r
                oy = ARENA_CENTER[1] + math.sin(angle) * r
                self.boost_pads.append({"x": ox, "y": oy, "r": 35, "cooldown": 0})

    def update(self, dt):
        for pad in self.boost_pads:
            if pad["cooldown"] > 0:
                pad["cooldown"] -= dt

    def draw(self, surface, shake=(0, 0)):
        sx, sy = shake
        cx = ARENA_CENTER[0] + sx
        cy = ARENA_CENTER[1] + sy

        void_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(void_surf, (0, 0, 0, 0), (cx, cy), RINGOUT_RADIUS + 60)
        void_surf.fill((self.void_color[0], self.void_color[1], self.void_color[2], 255), None, pygame.BLEND_RGBA_MAX)
        surface.blit(void_surf, (0, 0))

        for r_offset in range(30, 0, -6):
            shade = tuple(min(255, max(0, c - r_offset)) for c in self.ring_color)
            pygame.draw.circle(surface, shade, (cx, cy), ARENA_RADIUS + r_offset)
        pygame.draw.circle(surface, self.ring_color, (cx, cy), ARENA_RADIUS, 4)

        arena_surf = pygame.Surface((ARENA_RADIUS * 2 + 10, ARENA_RADIUS * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(arena_surf, self.floor_color + (255,), (ARENA_RADIUS + 5, ARENA_RADIUS + 5), ARENA_RADIUS)
        for i in range(0, ARENA_RADIUS * 2, 40):
            alpha_line = 20
            pygame.draw.line(arena_surf, (0, 0, 0, alpha_line), (i, 0), (i, ARENA_RADIUS * 2 + 10), 1)
            pygame.draw.line(arena_surf, (0, 0, 0, alpha_line), (0, i), (ARENA_RADIUS * 2 + 10, i), 1)
        surface.blit(arena_surf, (cx - ARENA_RADIUS - 5, cy - ARENA_RADIUS - 5))

        for ring_r in [50, 100, 150, 200, 250]:
            pygame.draw.circle(surface, tuple(min(255, max(0, c - 40)) for c in self.floor_color), (cx, cy), ring_r, 1)

        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + math.cos(rad) * (ARENA_RADIUS - 30)
            y1 = cy + math.sin(rad) * (ARENA_RADIUS - 30)
            x2 = cx + math.cos(rad) * (ARENA_RADIUS - 5)
            y2 = cy + math.sin(rad) * (ARENA_RADIUS - 5)
            pygame.draw.line(surface, self.ring_color, (x1, y1), (x2, y2), 2)

        for obs in self.obstacles:
            ox = obs["x"] + sx
            oy = obs["y"] + sy
            pygame.draw.circle(surface, (100, 80, 60), (ox, oy), obs["r"] + 3)
            pygame.draw.circle(surface, (150, 130, 100), (ox, oy), obs["r"])
            pygame.draw.circle(surface, (80, 60, 40), (ox, oy), obs["r"], 2)

        for pad in self.boost_pads:
            px = pad["x"] + sx
            py = pad["y"] + sy
            active = pad["cooldown"] <= 0
            color = (80, 255, 200) if active else (80, 100, 100)
            if active:
                pulse = math.sin(pygame.time.get_ticks() * 0.008) * 4
                pygame.draw.circle(surface, color, (px, py), pad["r"] + pulse, 2)
            pygame.draw.circle(surface, color, (px, py), pad["r"], 1)
            inner_c = tuple(min(255, c + 80) for c in color)
            pygame.draw.circle(surface, inner_c, (px, py), int(pad["r"] * 0.5))

        pygame.draw.circle(surface, (255, 215, 0), (cx, cy), 4)


def resolve_top_collision(t1, t2, particles):
    dx = t2.x - t1.x
    dy = t2.y - t1.y
    dist = math.sqrt(dx * dx + dy * dy)
    min_dist = t1.radius + t2.radius

    if dist >= min_dist or dist == 0:
        return False

    nx = dx / dist
    ny = dy / dist

    total_mass = t1.mass + t2.mass
    overlap = min_dist - dist
    w1 = t2.mass / total_mass
    w2 = t1.mass / total_mass

    t1.x -= nx * overlap * w1
    t1.y -= ny * overlap * w1
    t2.x += nx * overlap * w2
    t2.y += ny * overlap * w2

    tx = -ny
    ty = nx

    t1_dn = t1.vx * nx + t1.vy * ny
    t1_dt = t1.vx * tx + t1.vy * ty
    t2_dn = t2.vx * nx + t2.vy * ny
    t2_dt = t2.vx * tx + t2.vy * ty

    m1 = t1.mass
    m2 = t2.mass
    e = 0.75

    if t1.invincible:
        m1 *= 5
    if t2.invincible:
        m2 *= 5

    new_t1_dn = (t1_dn * (m1 - m2) + t2_dn * 2 * m2) / (m1 + m2) * e
    new_t2_dn = (t2_dn * (m2 - m1) + t1_dn * 2 * m1) / (m1 + m2) * e

    t1.vx = tx * t1_dt + nx * new_t1_dn
    t1.vy = ty * t1_dt + ny * new_t1_dn
    t2.vx = tx * t2_dt + nx * new_t2_dn
    t2.vy = ty * t2_dt + ny * new_t2_dn

    t1_spin_ratio = t1.spin / t1.max_spin if t1.max_spin > 0 else 0
    t2_spin_ratio = t2.spin / t2.max_spin if t2.max_spin > 0 else 0

    t1_speed = math.sqrt(t1.vx ** 2 + t1.vy ** 2)
    t2_speed = math.sqrt(t2.vx ** 2 + t2.vy ** 2)

    mom1 = m1 * t1_speed * t1_spin_ratio
    mom2 = m2 * t2_speed * t2_spin_ratio

    collide_x = (t1.x + t2.x) / 2
    collide_y = (t1.y + t2.y) / 2

    impact = abs(mom1 - mom2) + (t1_speed + t2_speed) * 50

    if mom1 > mom2:
        spin_loss = (mom1 - mom2) * 0.003
        if not t2.invincible:
            t2.spin = max(0, t2.spin - spin_loss)
        if not t1.invincible:
            t1.spin = max(0, t1.spin - spin_loss * 0.3)
        knockback = (mom1 - mom2) * 0.002
        if t1.special_active and t1.type == TopType.ATTACK:
            knockback *= 2.5
        t2.vx += nx * knockback
        t2.vy += ny * knockback
    else:
        spin_loss = (mom2 - mom1) * 0.003
        if not t1.invincible:
            t1.spin = max(0, t1.spin - spin_loss)
        if not t2.invincible:
            t2.spin = max(0, t2.spin - spin_loss * 0.3)
        knockback = (mom2 - mom1) * 0.002
        if t2.special_active and t2.type == TopType.ATTACK:
            knockback *= 2.5
        t1.vx -= nx * knockback
        t1.vy -= ny * knockback

    t1.special_meter = min(100, t1.special_meter + impact * 0.002)
    t2.special_meter = min(100, t2.special_meter + impact * 0.002)

    spark_count = int(min(25, 8 + impact / 200))
    mix_color = (
        (t1.color[0] + t2.color[0]) // 2,
        (t1.color[1] + t2.color[1]) // 2,
        (t1.color[2] + t2.color[2]) // 2,
    )
    particles.emit_sparks(collide_x, collide_y, -nx, -ny, spark_count, (255, 220, 100))

    shake_amount = min(15, impact / 80)
    return shake_amount


def check_obstacle_collision(top, obstacles):
    total_shake = 0
    for obs in obstacles:
        dx = top.x - obs["x"]
        dy = top.y - obs["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        min_dist = top.radius + obs["r"]
        if dist < min_dist and dist > 0:
            nx = dx / dist
            ny = dy / dist
            overlap = min_dist - dist
            top.x += nx * overlap
            top.y += ny * overlap
            dot = top.vx * nx + top.vy * ny
            if dot < 0:
                top.vx -= 2 * dot * nx
                top.vy -= 2 * dot * ny
                top.vx *= 0.6
                top.vy *= 0.6
                top.spin -= top.max_spin * 0.04
                total_shake += 5
    return total_shake


def check_boost_pad(top, pads, particles):
    for pad in pads:
        if pad["cooldown"] > 0:
            continue
        dx = top.x - pad["x"]
        dy = top.y - pad["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < pad["r"] + top.radius * 0.5:
            top.spin = min(top.max_spin, top.spin + top.max_spin * 0.25)
            particles.emit_special(pad["x"], pad["y"], (80, 255, 200), 20)
            pad["cooldown"] = 5.0
