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
        # Rolled once per decision tick (not every frame - see _decide) so the
        # AI actually commits to a slightly-off heading for a while instead
        # of re-sampling noise 60x/sec, which averages out to a near-perfect
        # beeline and reads as "always follows the player exactly".
        self.aim_noise = 0.0
        # A genuine multi-second "back off and wander" period, rolled with
        # some probability whenever the AI would otherwise engage. Without
        # this the AI re-evaluates into APPROACH/ATTACK every single decision
        # tick (as often as every 0.2s on HARD) and stays glued to the
        # opponent, which is what was making matches collapse into constant
        # contact and end almost immediately.
        self.disengage_timer = 0.0

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
        if self.disengage_timer > 0:
            self.disengage_timer -= dt
            self.state = AIState.IDLE
            return

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

        # Roll a fresh aim offset for this whole decision window. Held
        # steady until the next tick, so movement visibly drifts/wanders
        # instead of homing in on a razor-precise intercept course.
        noise_level = {
            Difficulty.EASY: 0.9,
            Difficulty.MEDIUM: 0.5,
            Difficulty.HARD: 0.22,
        }.get(self.difficulty, 0.45)
        self.aim_noise = random.uniform(-noise_level, noise_level)

        dist = self._dist_to(opponent)
        my_spin = self.top.spin / self.top.max_spin if self.top.max_spin > 0 else 0
        opp_spin = opponent.spin / opponent.max_spin if opponent.max_spin > 0 else 0
        near_edge = self._near_edge()

        if self.top.special_meter >= self.special_trigger and my_spin > 0.3:
            self.state = AIState.SPECIAL
            return

        if near_edge and my_spin < 0.4:
            self.state = AIState.RETREAT
            return

        if self.top.type == TopType.DEFENSE:
            if dist < 120 and opp_spin > my_spin:
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

        if self.state in (AIState.APPROACH, AIState.ATTACK):
            disengage_chance = {
                Difficulty.EASY: 0.28,
                Difficulty.MEDIUM: 0.18,
                Difficulty.HARD: 0.12,
            }.get(self.difficulty, 0.2)
            if random.random() < disengage_chance:
                # Back off and wander for a real stretch of time rather than
                # just one decision tick, so contact doesn't stay constant.
                self.disengage_timer = random.uniform(0.9, 2.2)
                self.state = AIState.IDLE
        elif self.difficulty == Difficulty.EASY and random.random() < 0.15:
            # EASY still gets its own lighter, single-tick dithering on top
            # of the shared disengage above, so it reads as a bit less sharp.
            self.state = AIState.APPROACH

    def update(self, opponent, dt):
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
        dx = opponent.x - self.top.x
        dy = opponent.y - self.top.y
        opp_angle = math.atan2(dy, dx)

        center_dx = ARENA_CENTER[0] - self.top.x
        center_dy = ARENA_CENTER[1] - self.top.y
        center_dist = math.sqrt(center_dx ** 2 + center_dy ** 2)
        center_angle = math.atan2(center_dy, center_dx)

        if self.state == AIState.IDLE:
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.target_angle = random.uniform(0, math.pi * 2)
                self.wander_timer = random.uniform(0.5, 1.5)
            steer_x = math.cos(self.target_angle)
            steer_y = math.sin(self.target_angle)

        elif self.state == AIState.APPROACH:
            angle = opp_angle + self.aim_noise
            if self.difficulty in (Difficulty.MEDIUM, Difficulty.HARD) and dist > 100:
                opp_speed = math.sqrt(opponent.vx ** 2 + opponent.vy ** 2)
                if opp_speed > 50:
                    # MEDIUM leads the target too, just with a shorter, weaker
                    # lookahead than HARD's full prediction.
                    lead_scale = 1.0 if self.difficulty == Difficulty.HARD else 0.45
                    predict_time = min(0.5, dist / max(1, opp_speed + 100)) * lead_scale
                    pred_x = opponent.x + opponent.vx * predict_time
                    pred_y = opponent.y + opponent.vy * predict_time
                    angle = math.atan2(pred_y - self.top.y, pred_x - self.top.x) + self.aim_noise * 0.5

            steer_x = math.cos(angle)
            steer_y = math.sin(angle)

            if self.difficulty in (Difficulty.MEDIUM, Difficulty.HARD) and dist > 180 and self.top.dash_cooldown <= 0 and self.top.spin > self.top.max_spin * 0.4:
                if random.random() < (0.04 if self.difficulty == Difficulty.HARD else 0.02):
                    dash = True

        elif self.state == AIState.ATTACK:
            angle = opp_angle + self.aim_noise * 0.5
            steer_x = math.cos(angle)
            steer_y = math.sin(angle)

            if self.top.type in (TopType.ATTACK, TopType.SPEED) and self.top.dash_cooldown <= 0 and dist < 150:
                if random.random() < 0.03:
                    dash = True

        elif self.state == AIState.RETREAT:
            retreat_angle = opp_angle + math.pi
            if self._near_edge():
                retreat_angle = center_angle
            angle = retreat_angle + self.aim_noise
            steer_x = math.cos(angle)
            steer_y = math.sin(angle)

            if self.top.dash_cooldown <= 0 and random.random() < 0.02:
                dash = True

        elif self.state == AIState.DEFEND:
            tangent = opp_angle + math.pi / 2
            if self.aim_noise < 0:
                tangent += math.pi
            angle = tangent + self.aim_noise
            steer_x = math.cos(angle) * 0.7
            steer_y = math.sin(angle) * 0.7
            if center_dist > ARENA_RADIUS * 0.5:
                steer_x += math.cos(center_angle) * 0.3
                steer_y += math.sin(center_angle) * 0.3

        elif self.state == AIState.SPECIAL:
            if self.top.special_meter >= 100:
                special = True
                self.special_trigger = random.uniform(50, 100)
            steer_x = math.cos(opp_angle)
            steer_y = math.sin(opp_angle)
            if self.state_timer > 0.5:
                self.state = AIState.ATTACK

        mag = math.sqrt(steer_x ** 2 + steer_y ** 2)
        if mag > 0:
            steer_x /= mag
            steer_y /= mag

        return (steer_x, steer_y), dash, special
