import pygame
import pygame.gfxdraw
import math
from .config import *

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

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _build_static_layer(self):
        """Everything that never moves, rendered once. Rebuilding the void,
        floor and grid every frame used to cost ~15 ms - most of the frame."""
        layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        layer.fill(self.void_color)
        cx, cy = ARENA_CENTER

        # Outer rim: stepped shading for depth.
        for r_offset in range(30, 0, -6):
            shade = tuple(min(255, max(0, c - r_offset)) for c in self.ring_color)
            pygame.draw.circle(layer, shade, (cx, cy), ARENA_RADIUS + r_offset)

        # Floor: shaded like a shallow bowl (darker toward the rim).
        R = ARENA_RADIUS
        floor = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
        rim_col = tuple(max(0, int(c * 0.80)) for c in self.floor_color)
        mid_col = tuple(min(255, int(c + (255 - c) * 0.06)) for c in self.floor_color)
        steps = 14
        for i in range(steps, 0, -1):
            t = i / steps
            col = tuple(int(mid_col[k] + (rim_col[k] - mid_col[k]) * t ** 2) for k in range(3))
            pygame.draw.circle(floor, col, (R, R), int(R * t))

        # Grid: exact chords clipped to the circle, blended on top.
        grid = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
        for off in range(-R + 40, R, 40):
            half = int(math.sqrt(max(0, R * R - off * off)))
            pygame.draw.line(grid, (0, 0, 0, 26), (R + off, R - half), (R + off, R + half), 1)
            pygame.draw.line(grid, (0, 0, 0, 26), (R - half, R + off), (R + half, R + off), 1)
        floor.blit(grid, (0, 0))
        layer.blit(floor, (cx - R, cy - R))

        line_col = tuple(min(255, max(0, c - 40)) for c in self.floor_color)
        for ring_r in (50, 100, 150, 200, 250):
            pygame.gfxdraw.aacircle(layer, cx, cy, ring_r, line_col)
        pygame.draw.circle(layer, self.ring_color, (cx, cy), ARENA_RADIUS, 4)
        for rr in (ARENA_RADIUS, ARENA_RADIUS - 4):
            pygame.gfxdraw.aacircle(layer, cx, cy, rr, self.ring_color)

        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + math.cos(rad) * (ARENA_RADIUS - 30)
            y1 = cy + math.sin(rad) * (ARENA_RADIUS - 30)
            x2 = cx + math.cos(rad) * (ARENA_RADIUS - 5)
            y2 = cy + math.sin(rad) * (ARENA_RADIUS - 5)
            pygame.draw.line(layer, self.ring_color, (x1, y1), (x2, y2), 2)

        # Stone pillars: shadow, body, lit top face, crack detail.
        for obs in self.obstacles:
            ox, oy, r = int(obs["x"]), int(obs["y"]), obs["r"]
            sh = pygame.Surface((r * 2 + 12, r * 2 + 12), pygame.SRCALPHA)
            pygame.draw.circle(sh, (0, 0, 0, 90), (r + 6, r + 6), r + 2)
            layer.blit(sh, (ox - r - 6 + 5, oy - r - 6 + 6))
            pygame.gfxdraw.filled_circle(layer, ox, oy, r + 3, (92, 74, 56))
            pygame.gfxdraw.aacircle(layer, ox, oy, r + 3, (70, 54, 40))
            pygame.gfxdraw.filled_circle(layer, ox, oy, r, (156, 136, 106))
            pygame.gfxdraw.filled_circle(layer, ox - 4, oy - 4, int(r * 0.62), (176, 158, 126))
            pygame.gfxdraw.aacircle(layer, ox, oy, r, (110, 90, 66))
            pygame.draw.line(layer, (118, 98, 74), (ox - r // 3, oy + r // 4), (ox + r // 5, oy - r // 6), 2)

        # Centre mark.
        pygame.gfxdraw.aacircle(layer, cx, cy, 6, line_col)
        pygame.gfxdraw.filled_circle(layer, cx, cy, 2, line_col)
        return layer

    def draw(self, surface, shake=(0, 0)):
        if getattr(self, "_static", None) is None:
            self._static = self._build_static_layer()
        sx, sy = int(round(shake[0])), int(round(shake[1]))
        if sx or sy:
            surface.fill(self.void_color)
        surface.blit(self._static, (sx, sy))

        for pad in self.boost_pads:
            px = int(pad["x"] + sx)
            py = int(pad["y"] + sy)
            active = pad["cooldown"] <= 0
            color = (80, 255, 200) if active else (80, 100, 100)
            if active:
                pulse = math.sin(pygame.time.get_ticks() * 0.008) * 4
                pygame.gfxdraw.aacircle(surface, px, py, int(pad["r"] + pulse), color)
                pygame.gfxdraw.aacircle(surface, px, py, int(pad["r"] + pulse) - 1, color)
            pygame.gfxdraw.aacircle(surface, px, py, pad["r"], color)
            inner_c = tuple(min(255, c + 80) for c in color)
            pygame.gfxdraw.filled_circle(surface, px, py, int(pad["r"] * 0.5), inner_c)
            pygame.gfxdraw.aacircle(surface, px, py, int(pad["r"] * 0.5), inner_c)


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

    # Closing speed along the contact normal. If the tops are already moving
    # apart, the overlap fix above is all that's needed - applying the
    # impulse again would yank them back together, and every frame of
    # contact would replay the sound, sparks and spin damage.
    closing = (t1.vx - t2.vx) * nx + (t1.vy - t2.vy) * ny
    if closing <= 0:
        return 0

    # How much each top is driving INTO the contact (before the bounce).
    # The aggressor - the one actually ramming - wins more of the clash.
    drive1 = max(0.0, t1.vx * nx + t1.vy * ny)
    drive2 = max(0.0, -(t2.vx * nx + t2.vy * ny))

    m1 = t1.mass * (5 if t1.invincible else 1)
    m2 = t2.mass * (5 if t2.invincible else 1)
    e = COLLISION_RESTITUTION

    # Standard impulse along the normal (tangential velocity is kept).
    j = (1 + e) * closing / (1 / m1 + 1 / m2)
    t1.vx -= (j / m1) * nx
    t1.vy -= (j / m1) * ny
    t2.vx += (j / m2) * nx
    t2.vy += (j / m2) * ny

    # Gentle pushing contact (tops grinding while steering into each other)
    # just bounces - no spin damage, sparks, shake or sound every frame.
    if closing < MIN_IMPACT_SPEED:
        return 0

    # Who wins the clash: heavier and faster-spinning tops hit harder.
    # Attack types deal more, Defense types take less.
    r1 = t1.spin / t1.max_spin if t1.max_spin > 0 else 0
    r2 = t2.spin / t2.max_spin if t2.max_spin > 0 else 0
    power1 = m1 * (0.4 + 0.6 * r1) * (1.25 if t1.type == TopType.ATTACK else 1.0)
    power2 = m2 * (0.4 + 0.6 * r2) * (1.25 if t2.type == TopType.ATTACK else 1.0)
    power1 *= 1.0 + ATTACKER_BONUS * drive1 / closing
    power2 *= 1.0 + ATTACKER_BONUS * drive2 / closing
    total_power = max(0.001, power1 + power2)
    share1 = power1 / total_power   # fraction of the clash won by t1
    share2 = power2 / total_power

    base_damage = closing * COLLISION_SPIN_DAMAGE
    dmg_to_2 = base_damage * share1 * 2 * (0.75 if t2.type == TopType.DEFENSE else 1.0)
    dmg_to_1 = base_damage * share2 * 2 * (0.75 if t1.type == TopType.DEFENSE else 1.0)
    if not t1.invincible:
        t1.spin = max(0, t1.spin - dmg_to_1)
    if not t2.invincible:
        t2.spin = max(0, t2.spin - dmg_to_2)

    # Extra knockback for the top that lost the clash.
    knockback = closing * COLLISION_KNOCKBACK * abs(share1 - share2)
    if share1 >= share2:
        if t1.special_active and t1.type == TopType.ATTACK:
            knockback *= 2.5
        t2.vx += nx * knockback
        t2.vy += ny * knockback
    else:
        if t2.special_active and t2.type == TopType.ATTACK:
            knockback *= 2.5
        t1.vx -= nx * knockback
        t1.vy -= ny * knockback

    # Mark both tops as "just hit" so a hard hit can carry them over the rim.
    if closing > 200:
        t1.hit_timer = HIT_WINDOW
        t2.hit_timer = HIT_WINDOW

    impact = closing * (m1 + m2)
    t1.special_meter = min(100, t1.special_meter + impact * 0.002)
    t2.special_meter = min(100, t2.special_meter + impact * 0.002)

    collide_x = (t1.x + t2.x) / 2
    collide_y = (t1.y + t2.y) / 2
    spark_count = int(min(28, 8 + closing / 50))
    particles.emit_sparks(collide_x, collide_y, -nx, -ny, spark_count // 2, (255, 220, 100))
    particles.emit_sparks(collide_x, collide_y, nx, ny, spark_count - spark_count // 2, (255, 220, 100))

    return min(14.0, 2.0 + closing / 90.0)


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
                top.spin = max(0, top.spin - top.max_spin * WALL_SPIN_COST)
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
            # Velocity boost only - no spin increase
            speed = math.hypot(top.vx, top.vy)
            if speed > 0:
                top.vx += (top.vx / speed) * 200
                top.vy += (top.vy / speed) * 200
            elif dist > 0:
                top.vx += (dx / dist) * 200
                top.vy += (dy / dist) * 200
            particles.emit_special(pad["x"], pad["y"], (80, 255, 200), 20)
            pad["cooldown"] = 5.0
