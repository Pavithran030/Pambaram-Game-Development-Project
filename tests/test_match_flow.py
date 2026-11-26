"""Match-start, collision and win-condition rules (regression tests)."""
import sys
import os
os.environ["PAMBARAM_NO_SAVE"] = "1"  # never touch the player's real save data
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from pambaram.config import *
from pambaram.main import Game
from pambaram.top import Top
from pambaram.arena import resolve_top_collision
from pambaram.particles import ParticleSystem

dt = 1.0 / 60
passed = 0


def check(cond, msg):
    global passed
    assert cond, msg
    passed += 1
    print(f"  [PASS] {msg}")


def new_match(ai=True):
    g = Game()
    g.p2_is_ai = ai
    g._start_match()
    return g


print("=" * 60)
print("MATCH START: both tops launch together")
print("=" * 60)
for ai in (True, False):
    g = new_match(ai)
    mode = "vs AI" if ai else "2 players"
    check(not g.p1.is_launched and not g.p2.is_launched, f"[{mode}] nobody launched during countdown")
    frames = 0
    while not g.match_started:
        g._update_gameplay(dt)
        frames += 1
        if not g.match_started:
            assert not g.p1.is_launched and not g.p2.is_launched
    check(abs(frames * dt - 3 * COUNTDOWN_STEP) < 0.05, f"[{mode}] countdown lasts {3 * COUNTDOWN_STEP:.0f}s")
    check(g.p1.is_launched and g.p2.is_launched, f"[{mode}] both tops launched on the same frame")

# Launch follows the chosen aim.
g = new_match(ai=False)
g.aim[1] = 0.0           # straight right
g.aim[2] = math.pi / 2   # straight down
g.launch_lock = {1: 1.0, 2: 1.0}
while not g.match_started:
    g._update_gameplay(dt)
check(g.p1.vx > 600 and abs(g.p1.vy) < 1, "P1 launches in its aim direction")
check(g.p2.vy > 600 and abs(g.p2.vx) < 1, "P2 launches in its aim direction")

print()
print("=" * 60)
print("LAUNCH PERFECTION -> STAMINA")
print("=" * 60)
g = new_match(ai=False)
g.launch_lock = {1: 1.0, 2: 0.2}
while not g.match_started:
    g._update_gameplay(dt)
check(g.p1.spin == g.p1.max_spin, "perfect launch starts at 100% stamina")
check(g.p2.spin < 0.65 * g.p2.max_spin, "weak launch starts with much less stamina")
check(g.p2.decay_mult > g.p1.decay_mult, "weak launch also drains stamina faster")
check(math.hypot(g.p1.vx, g.p1.vy) > math.hypot(g.p2.vx, g.p2.vy), "perfect launch is also faster")
check(g.launch_grade(1.0) == "PERFECT!" and g.launch_grade(0.2) == "WEAK", "launch grades")
check(len(g.launch_popups) == 2, "both players see their launch grade")

# SPACE locks P1 at the meter's current value; ENTER locks P2 (2P mode).
g = new_match(ai=False)
for _ in range(20):
    g._update_gameplay(dt)
expected = g.meter_value(1)
g._handle_playing_events(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE, "mod": 0, "unicode": " "}))
check(abs(g.launch_lock[1] - expected) < 1e-9, "SPACE locks P1's power at the meter value")
check(g.launch_lock[2] is None, "P1's key doesn't lock P2")
g._handle_playing_events(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN, "mod": 0, "unicode": "\r"}))
check(g.launch_lock[2] is not None, "ENTER locks P2's power")
locked = g.launch_lock[1]
for _ in range(20):
    g._update_gameplay(dt)
g._handle_playing_events(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE, "mod": 0, "unicode": " "}))
check(g.launch_lock[1] == locked, "a locked launch can't be re-rolled")

# Never locking = weak launch.
g = new_match(ai=False)
while not g.match_started:
    g._update_gameplay(dt)
check(g.launch_lock[1] == LAUNCH_UNLOCKED_QUALITY, "not locking the meter gives a weak launch")

# Drag-and-release locks too.
g = new_match(ai=False)
g._handle_playing_events(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (400, 450), "button": 1}))
g._handle_playing_events(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (330, 450), "rel": (0, 0), "buttons": (1, 0, 0)}))
g._handle_playing_events(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (330, 450), "button": 1}))
check(g.launch_lock[1] is not None, "releasing a left-drag locks P1's power")

# The AI locks its own launch during the countdown.
g = new_match(ai=True)
while not g.match_started:
    g._update_gameplay(dt)
check(g.launch_lock[2] is not None and g.p2.launch_quality > 0.4, "AI picks its launch power itself")

print()
print("=" * 60)
print("CONTROLS & MOVEMENT")
print("=" * 60)
g = new_match(ai=True)
for k in (pygame.K_w, pygame.K_UP):
    check(k in g._keys(1, "up"), f"vs AI, P1 moves up with {pygame.key.name(k)}")
check(pygame.K_RSHIFT in g._keys(1, "dash") and pygame.K_RETURN in g._keys(1, "launch"),
      "vs AI, P1 can also dash with R-SHIFT and launch with ENTER")
g = new_match(ai=False)
check(pygame.K_UP not in g._keys(1, "up") and pygame.K_UP in g._keys(2, "up"),
      "in 2-player mode the arrows belong to P2")


class FakeKeys:
    def __init__(self, *down):
        self.down = set(down)

    def __getitem__(self, k):
        return k in self.down


g = new_match(ai=True)
g.launch_lock[1] = 1.0
while not g.match_started:
    g._update_gameplay(dt)
g.p1.vx = g.p1.vy = 0
g.p1.x, g.p1.y = ARENA_CENTER
for _ in range(30):
    g._steer_player(g.p1, FakeKeys(pygame.K_RIGHT))
    g.p1.update(dt, 1.0)
check(g.p1.vx > 250, f"holding an arrow key steers P1 vs AI (vx={g.p1.vx:.0f} after 0.5s)")

# A launched top keeps moving: it must not coast to a dead stop with most
# of its spin left (it used to freeze ~6s after launch at 94% spin).
t = Top("x", TOP_PRESETS["Thiruvalluvar"], 1)
t.launch(math.cos(-0.35), math.sin(-0.35), LAUNCH_FORCE, quality=1.0)
moving_frames = 0
for f in range(60 * 15):
    t.update(dt, 1.0)
    t.check_boundary()
    if f > 60 * 5 and math.hypot(t.vx, t.vy) > 15:
        moving_frames += 1
check(moving_frames > 0.8 * 60 * 10, "a spinning top keeps rolling instead of freezing in place")
check(math.hypot(t.x - ARENA_CENTER[0], t.y - ARENA_CENTER[1]) < ARENA_RADIUS,
      "the bowl keeps a free-rolling top inside the arena")

# The AI hunts the player down instead of sitting still.
g = new_match(ai=True)
while not g.match_started:
    g._update_gameplay(dt)
start_d = math.hypot(g.p1.x - g.p2.x, g.p1.y - g.p2.y)
hits = [0]
g.sound.play = lambda name, *a, **k: hits.__setitem__(0, hits[0] + (name == "collision"))
for _ in range(60 * 8):
    if g.state != GameState.PLAYING:
        break
    g._update_gameplay(dt)
check(hits[0] > 0, f"the AI attacks a passive player ({hits[0]} hits in 8s)")

# Slingshot drag sets the aim (pull left -> fly right).
g = new_match(ai=False)
g._handle_playing_events(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (400, 450), "button": 1}))
g._handle_playing_events(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (300, 450), "rel": (0, 0), "buttons": (1, 0, 0)}))
check(abs(g.aim[1] - 0.0) < 1e-6, "left-drag backwards aims P1 forward")
g._handle_playing_events(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (800, 450), "button": 3}))
g._handle_playing_events(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (800, 350), "rel": (0, 0), "buttons": (0, 0, 1)}))
check(abs(g.aim[2] - math.pi / 2) < 1e-6, "right-drag aims P2 independently")

# Pausing mid-drag must not leave a stale drag behind.
g._pause()
check(g.drag_p1 is None and g.drag_p2 is None, "pausing clears in-progress aim drags")

print()
print("=" * 60)
print("COLLISIONS")
print("=" * 60)
ps = ParticleSystem()
a = Top("A", TOP_PRESETS["Velu Vettaikaran"], 1)
b = Top("B", TOP_PRESETS["Puyal Kaalai"], 2)
a.launch(0, 0, 0)
b.launch(0, 0, 0)
a.x, a.y = 560, 450
b.x, b.y = 560 + a.radius + b.radius - 4, 450
a.vx, b.vx = 600, 0
spin_b = b.spin
shake = resolve_top_collision(a, b, ps)
check(shake > 0, "a real hit reports an impact")
check(b.vx > 0 and a.vx < 600, "momentum moves from attacker to target")
check(b.spin < spin_b, "the hit top loses spin")
check(a.hit_timer > 0 and b.hit_timer > 0, "both tops are flagged as just-hit")

# Overlapping but separating: no second impulse.
a.x, b.x = 560, 560 + a.radius + b.radius - 4
a.vx, b.vx = -100, 100
spin_a, spin_b = a.spin, b.spin
check(resolve_top_collision(a, b, ps) == 0, "separating tops are not hit again")
check(a.vx == -100 and b.vx == 100 and a.spin == spin_a and b.spin == spin_b,
      "separating tops keep their velocity and spin")

# Soft push: no damage.
a.x, b.x = 560, 560 + a.radius + b.radius - 4
a.vx, b.vx = 40, 0
spin_b = b.spin
check(resolve_top_collision(a, b, ps) == 0 and b.spin == spin_b, "gentle push contact does no spin damage")

print()
print("=" * 60)
print("RING OUT")
print("=" * 60)


def run_to_wall(top, speed, hit):
    top.launch(0, 0, 0)
    top.x, top.y = ARENA_CENTER[0] + ARENA_RADIUS - 10, ARENA_CENTER[1]
    top.vx, top.vy = speed, 0
    top.hit_timer = HIT_WINDOW if hit else 0
    for _ in range(60):
        top.update(dt, 1.0)
        top.check_boundary()
        if top.is_knocked_out:
            break
    return top.is_knocked_out


check(run_to_wall(Top("x", TOP_PRESETS["Sooravali"], 1), 900, hit=True),
      "a top smashed into the rim flies out (ring-out is possible)")
check(not run_to_wall(Top("x", TOP_PRESETS["Sooravali"], 1), 900, hit=False),
      "a top that drives itself into the wall bounces back")
check(not run_to_wall(Top("x", TOP_PRESETS["Sooravali"], 1), 300, hit=True),
      "a weak hit near the rim only bounces")

print()
print("=" * 60)
print("WIN CONDITIONS")
print("=" * 60)


def started_match():
    g = new_match(ai=False)
    while not g.match_started:
        g._update_gameplay(dt)
    return g


g = started_match()
g.p1.is_knocked_out = True
g.p1.knockout_timer = KO_CONFIRM_TIME
g._check_win_conditions()
check(g.state == GameState.GAME_OVER and g.winner is g.p2, "P1 ring-out -> P2 wins")

g = started_match()
g.p2.is_knocked_out = True
g.p2.knockout_timer = KO_CONFIRM_TIME
g._check_win_conditions()
check(g.winner is g.p1, "P2 ring-out -> P1 wins")

# Both rang out: the one that went out first must not win just because the
# other's knockout timer hasn't finished counting yet.
g = started_match()
g.p1.is_knocked_out, g.p1.knockout_timer = True, KO_CONFIRM_TIME
g.p2.is_knocked_out, g.p2.knockout_timer = True, KO_CONFIRM_TIME - 0.5
g._check_win_conditions()
check(g.winner is g.p2, "double ring-out: the top that stayed in longer wins")

g = started_match()
g.p1.is_knocked_out, g.p1.knockout_timer = True, KO_CONFIRM_TIME
g.p2.is_knocked_out, g.p2.knockout_timer = True, KO_CONFIRM_TIME - 0.1
g._check_win_conditions()
check(g.state == GameState.GAME_OVER and g.winner is None, "near-simultaneous double ring-out is a draw")

# A spin-out must not be awarded while the other top is mid ring-out.
g = started_match()
g.p2.is_knocked_out, g.p2.knockout_timer = True, 0.1
g.p1.spin = 0
g._check_win_conditions()
check(g.state == GameState.PLAYING, "spin-out waits for a pending ring-out to resolve")

g = started_match()
g.p2.spin = 0
g._check_win_conditions()
check(g.winner is g.p1 and "SPIN OUT" in g.stats["win_reason"], "P2 spin-out -> P1 wins")

g = started_match()
g.match_time = 0
g.p1.spin, g.p2.spin = g.p1.max_spin * 0.6, g.p2.max_spin * 0.3
g._check_win_conditions()
check(g.winner is g.p1 and "TIME UP" in g.stats["win_reason"], "time up -> more spin % wins")

g = started_match()
g.match_time = 0
g.p2.is_knocked_out, g.p2.knockout_timer = True, 0.1
g._check_win_conditions()
check(g.state == GameState.GAME_OVER and g.winner is g.p1, "time up during a ring-out still ends the match")

g = started_match()
g.p2_is_ai = True
g.p2.spin = 0
g._check_win_conditions()
check(g.stats["p2_label"] == "AI", "game-over labels P2 as AI in AI mode")

print()
print("=" * 60)
print(f"ALL {passed} MATCH FLOW TESTS PASSED!")
print("=" * 60)
pygame.quit()
