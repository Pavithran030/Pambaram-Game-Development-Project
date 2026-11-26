import pygame
import math
import random
from .config import *
from enum import Enum

class AIState(Enum):
    IDLE = 1
    APPROACH = 2
    ATTACK = 3
    RETREAT = 4
    DEFEND = 5
    SPECIAL = 6

class AIController:
    def __init__(self, top, difficulty=Difficulty.MEDIUM):
        self.top = top
        self.difficulty = difficulty
        self.state = AIState.IDLE
        self.state_timer = 0
        self.target_angle = random.uniform(0, math.pi * 2)
        self.wander_timer = 0
        self.last_decision = 0
        self.special_trigger = random.uniform(60, 100)
        self.orbit_dir = 1

    def choose_launch_angle(self, opponent):
        """Aim picked during the countdown. Better AI aims more precisely at
        the opponent's starting spot."""
        spread = {
            Difficulty.EASY: 0.55,
            Difficulty.MEDIUM: 0.30,
            Difficulty.HARD: 0.12,
        }.get(self.difficulty, 0.3)
        base = math.atan2(opponent.y - self.top.y, opponent.x - self.top.x)
        return base + random.uniform(-spread, spread)

    @staticmethod
    def _clash_power(top):
        """Same weighting the collision code uses to decide who wins a hit."""
        r = top.spin / top.max_spin if top.max_spin > 0 else 0
        return top.mass * (0.4 + 0.6 * r) * (1.25 if top.type == TopType.ATTACK else 1.0)

    def choose_launch_quality(self):
        """How well the AI times its launch meter (1.0 = perfect)."""
        lo, hi = {
            Difficulty.EASY: (0.45, 0.80),
            Difficulty.MEDIUM: (0.65, 0.93),
            Difficulty.HARD: (0.85, 1.0),
        }.get(self.difficulty, (0.65, 0.93))
        return random.uniform(lo, hi)

    def _dash_chance(self, base):
        """Per-frame dash probability, scaled by difficulty."""
        return base * {Difficulty.EASY: 0.5, Difficulty.MEDIUM: 1.0, Difficulty.HARD: 1.6}.get(self.difficulty, 1.0)

    def _dist_from_center(self):
        dx = self.top.x - ARENA_CENTER[0]
        dy = self.top.y - ARENA_CENTER[1]
        return math.sqrt(dx * dx + dy * dy)

    def _dist_to(self, other):
        dx = other.x - self.top.x
        dy = other.y - self.top.y
        return math.sqrt(dx * dx + dy * dy)

    def _near_edge(self):
        return self._dist_from_center() > ARENA_RADIUS * 0.75

    def _decide(self, opponent, dt):
        self.last_decision -= dt
        self.last_decision = max(0, self.last_decision)
        if self.last_decision > 0:
            return

        decision_interval = {
            Difficulty.EASY: 0.8,
            Difficulty.MEDIUM: 0.4,
            Difficulty.HARD: 0.2,
        }
        self.last_decision = decision_interval.get(self.difficulty, 0.5)

        dist = self._dist_to(opponent)
        my_spin = self.top.spin / self.top.max_spin if self.top.max_spin > 0 else 0
        opp_spin = opponent.spin / opponent.max_spin if opponent.max_spin > 0 else 0
        near_edge = self._near_edge()


        if near_edge and my_spin < 0.4:
            self.state = AIState.RETREAT
            return

        # Smarter AI avoids clashes it would lose (much heavier / stronger
        # opponent) and plays for stamina instead, circling at a distance.
        if self.difficulty != Difficulty.EASY:
            if self._clash_power(self.top) < 0.75 * self._clash_power(opponent) and my_spin < opp_spin + 0.25:
                if self.state != AIState.DEFEND:
                    self.orbit_dir = random.choice((-1, 1))
                self.state = AIState.DEFEND
                return

        if self.top.type == TopType.DEFENSE:
            if dist < 120 and opp_spin > my_spin:
                if self.state != AIState.DEFEND:
                    self.orbit_dir = random.choice((-1, 1))
                self.state = AIState.DEFEND
            elif dist > 200:
                self.state = AIState.APPROACH
            else:
                self.state = AIState.ATTACK

        elif self.top.type == TopType.ATTACK or self.top.type == TopType.SPEED:
            if my_spin < 0.25:
                self.state = AIState.RETREAT
            elif dist > 100:
                self.state = AIState.APPROACH
            else:
                self.state = AIState.ATTACK

        else:
            if opp_spin > my_spin + 0.2 and dist < 100:
                self.state = AIState.RETREAT
            elif dist > 150:
                self.state = AIState.APPROACH
            else:
                self.state = AIState.ATTACK

        if self.difficulty == Difficulty.EASY:
            # Softer dithering than before: EASY should read as beatable, not
            # randomly inert - mostly follow the real decision above.
            if random.random() < 0.15:
                self.state = AIState.IDLE
            elif random.random() < 0.15:
                self.state = AIState.APPROACH

    def update(self, opponent, dt, obstacles=None):
        if not self.top.is_launched or self.top.is_knocked_out:
            return None, None, None

        if not opponent.is_launched:
            # Opponent hasn't launched yet, so it isn't a real target (no
            # collision applies to it either — see main.py). Drift gently
            # toward center instead of "attacking"/dashing at a stationary
            # point and burning spin for nothing.
            self.state = AIState.IDLE
            cdx = ARENA_CENTER[0] - self.top.x
            cdy = ARENA_CENTER[1] - self.top.y
            cdist = math.sqrt(cdx * cdx + cdy * cdy)
            if cdist > 40:
                return (cdx / cdist, cdy / cdist), False, False
            return (0, 0), False, False

        self._decide(opponent, dt)
        self.state_timer += dt

        steer_x = 0
        steer_y = 0
        dash = False
        special = False

        dist = self._dist_to(opponent)
        my_spin = self.top.spin / self.top.max_spin if self.top.max_spin > 0 else 0
        dx = opponent.x - self.top.x
        dy = opponent.y - self.top.y
        opp_angle = math.atan2(dy, dx)

        center_dx = ARENA_CENTER[0] - self.top.x
        center_dy = ARENA_CENTER[1] - self.top.y
        center_dist = math.sqrt(center_dx ** 2 + center_dy ** 2)
        center_angle = math.atan2(center_dy, center_dx)

        noise_level = {
            Difficulty.EASY: 0.6,
            Difficulty.MEDIUM: 0.25,
            Difficulty.HARD: 0.08,
        }[self.difficulty]

        if self.state == AIState.IDLE:
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.target_angle = random.uniform(0, math.pi * 2)
                self.wander_timer = random.uniform(0.5, 1.5)
            steer_x = math.cos(self.target_angle)
            steer_y = math.sin(self.target_angle)

        elif self.state == AIState.APPROACH:
            noise = random.uniform(-noise_level, noise_level)
            angle = opp_angle + noise
            if self.difficulty in (Difficulty.MEDIUM, Difficulty.HARD) and dist > 100:
                opp_speed = math.sqrt(opponent.vx ** 2 + opponent.vy ** 2)
                if opp_speed > 50:
                    # MEDIUM leads the target too, just with a shorter, weaker
                    # lookahead than HARD's full prediction.
                    lead_scale = 1.0 if self.difficulty == Difficulty.HARD else 0.45
                    predict_time = min(0.5, dist / max(1, opp_speed + 100)) * lead_scale
                    pred_x = opponent.x + opponent.vx * predict_time
                    pred_y = opponent.y + opponent.vy * predict_time
                    angle = math.atan2(pred_y - self.top.y, pred_x - self.top.x)

            steer_x = math.cos(angle)
            steer_y = math.sin(angle)

            if (self.difficulty in (Difficulty.MEDIUM, Difficulty.HARD) and dist > 180
                    and self.top.dash_cooldown <= 0 and my_spin > 0.5):
                if random.random() < self._dash_chance(0.01):
                    dash = True

        elif self.state == AIState.ATTACK:
            noise = random.uniform(-noise_level * 0.5, noise_level * 0.5)
            angle = opp_angle + noise
            steer_x = math.cos(angle)
            steer_y = math.sin(angle)

            if (self.top.type in (TopType.ATTACK, TopType.SPEED) and self.top.dash_cooldown <= 0
                    and dist < 150 and my_spin > 0.45):
                if random.random() < self._dash_chance(0.012):
                    dash = True

        elif self.state == AIState.RETREAT:
            retreat_angle = opp_angle + math.pi
            if self._near_edge():
                retreat_angle = center_angle
            noise = random.uniform(-noise_level, noise_level)
            angle = retreat_angle + noise
            steer_x = math.cos(angle)
            steer_y = math.sin(angle)

            # Escape-dash only when cornered near the rim; a dash costs 8%
            # spin, so dashing away every cooldown just drains the AI.
            if (self.top.dash_cooldown <= 0 and self._near_edge() and my_spin > 0.2
                    and random.random() < self._dash_chance(0.02)):
                dash = True

        elif self.state == AIState.DEFEND:
            # Circle the opponent at a safe distance (fixed direction - it
            # used to re-roll every frame and just jittered in place).
            tangent = opp_angle + math.pi / 2 * self.orbit_dir
            steer_x = math.cos(tangent)
            steer_y = math.sin(tangent)
            if dist < 150:   # too close: open the gap
                steer_x -= math.cos(opp_angle) * 0.8
                steer_y -= math.sin(opp_angle) * 0.8
            if center_dist > ARENA_RADIUS * 0.55:   # don't drift to the rim
                steer_x += math.cos(center_angle) * 0.7
                steer_y += math.sin(center_angle) * 0.7

        elif self.state == AIState.SPECIAL:
            if self.top.special_meter >= 100:
                special = True
                self.special_trigger = random.uniform(50, 100)
            steer_x = math.cos(opp_angle)
            steer_y = math.sin(opp_angle)
            if self.state_timer > 0.5:
                self.state = AIState.ATTACK

        steer_x, steer_y = self._to_velocity_steer(steer_x, steer_y, obstacles)
        if dash and (steer_x == 0 and steer_y == 0):
            dash = False
        return (steer_x, steer_y), dash, special

    # Cruise speed the AI tries to hold in each state.
    TARGET_SPEED = {
        AIState.IDLE: 160, AIState.APPROACH: 480, AIState.ATTACK: 620,
        AIState.RETREAT: 380, AIState.DEFEND: 260, AIState.SPECIAL: 600,
    }

    def _to_velocity_steer(self, dir_x, dir_y, obstacles):
        """Turn a desired heading into a steering input that matches a target
        velocity (desired - current), so the AI brakes and corrects instead
        of flooring it past its target into walls and pillars."""
        mag = math.hypot(dir_x, dir_y)
        if mag == 0:
            return 0, 0
        dir_x, dir_y = dir_x / mag, dir_y / mag

        # Steer around pillars that sit in the way.
        for obs in obstacles or ():
            ox, oy = obs["x"] - self.top.x, obs["y"] - self.top.y
            d = math.hypot(ox, oy)
            clear = obs["r"] + self.top.radius + 30
            ahead = ox * dir_x + oy * dir_y
            if d > 0 and 0 < ahead < 140 and d < clear + 60:
                side = dir_x * oy - dir_y * ox   # which side the pillar is on
                px, py = (dir_y, -dir_x) if side > 0 else (-dir_y, dir_x)
                w = (clear + 60 - d) / (clear + 60) * 1.6
                dir_x, dir_y = dir_x + px * w, dir_y + py * w
                m = math.hypot(dir_x, dir_y)
                dir_x, dir_y = dir_x / m, dir_y / m

        speed = self.TARGET_SPEED.get(self.state, 400)
        if self._near_edge():
            # Moving outward near the rim? Slow right down.
            cx, cy = ARENA_CENTER[0] - self.top.x, ARENA_CENTER[1] - self.top.y
            cd = max(1.0, math.hypot(cx, cy))
            if dir_x * cx / cd + dir_y * cy / cd < 0:
                speed *= 0.5
        sx = dir_x * speed - self.top.vx
        sy = dir_y * speed - self.top.vy
        m = math.hypot(sx, sy)
        if m < 30:
            return 0, 0
        return sx / m, sy / m
