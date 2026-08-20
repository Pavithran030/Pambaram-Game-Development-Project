import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

print("=" * 60)
print("INTEGRATION TEST: Game Manager Simulation")
print("=" * 60)

from config import TOP_PRESETS, ARENA_CENTER, ARENA_RADIUS, GameState, Difficulty
from main import Game

game = Game()
print(f"Initial state: {game.state.name}")
assert game.state == GameState.MENU, "Initial state should be MENU"
print("  [PASS] State = MENU")

print()
print("Simulating state transitions:")
game._quick_match()
assert game.state == GameState.TOP_SELECT, "Quick match should go to top select"
print(f"  After Quick Match -> {game.state.name}: PASS")

game.p1_top_name = "Thiruvalluvar"
game.p2_top_name = "Velu Vettaikaran"
game.selected_arena = "Gramam Thidal"
game._start_match()
assert game.state == GameState.PLAYING, "Start match -> PLAYING"
print(f"  After Start Match -> {game.state.name}: PASS")
print(f"  P1 Top: {game.p1.name}, P2 Top: {game.p2.name}")
print(f"  Arena: {game.arena.preset_key}")
assert game.p1.name == "Thiruvalluvar"
assert game.p2.name == "Velu Vettaikaran"
print("  [PASS] Tops & Arena initialized correctly")

print()
print("Simulating countdown...")
for i in range(60 * 5):
    game._update_countdown(1.0 / 60)
    if game.match_started:
        print(f"  Countdown finished after {(i+1)/60:.1f}s: match_started = True: PASS")
        break
assert game.match_started
assert not game.p2.is_launched or game.p2_is_ai  # AI may auto-launch
if game.p2_is_ai and not game.p2.is_launched:
    game._ai_auto_launch()
    print(f"  AI auto-launch executed: P2 launched = {game.p2.is_launched}")

print()
print("Simulating 10 seconds of gameplay...")
game.p1.launch(0.5, 0, 400, 1.0)
if not game.p2.is_launched:
    game.p2.launch(-0.5, 0, 400, 1.0)

dt = 1.0 / 60
spin1_0 = game.p1.spin
spin2_0 = game.p2.spin
hit_countdown = 30
collision_happened = 0
bounce_happened = 0

for i in range(int(60 * 10)):
    game.match_time -= dt
    keys = {pygame.K_w: False, pygame.K_a: False, pygame.K_s: False, pygame.K_d: False}
    if i < 60 * 3:
        game.p1.steer(1, 0)
    else:
        game.p1.steer(-0.3, 0.2)

    if game.ai_controller:
        res = game.ai_controller.update(game.p1, dt)
        if res and res[0] is not None:
            steer, do_dash, do_special = res
            if not game.p2.is_knocked_out:
                game.p2.steer(steer[0], steer[1])
                if do_dash:
                    game.p2.dash(steer[0], steer[1])

    game.p1.update(dt, game.arena.grip_mod)
    game.p2.update(dt, game.arena.grip_mod)

    r1 = game.p1.check_boundary()
    r2 = game.p2.check_boundary()
    if r1 == "bounce" or r2 == "bounce":
        bounce_happened += 1

    col = __import__("arena").resolve_top_collision(game.p1, game.p2, game.particles)
    if col > 0:
        collision_happened += 1

    __import__("arena").check_obstacle_collision(game.p1, game.arena.obstacles)
    __import__("arena").check_obstacle_collision(game.p2, game.arena.obstacles)
    __import__("arena").check_boost_pad(game.p1, game.arena.boost_pads, game.particles)
    __import__("arena").check_boost_pad(game.p2, game.arena.boost_pads, game.particles)

    game.arena.update(dt)
    game.particles.update(dt)

    if game.p1.is_knocked_out or game.p2.is_knocked_out:
        break

print(f"  P1 Spin: {spin1_0:.0f} -> {game.p1.spin:.0f}")
print(f"  P2 Spin: {spin2_0:.0f} -> {game.p2.spin:.0f}")
print(f"  Collisions detected: {collision_happened}")
print(f"  Bounces detected: {bounce_happened}")
print(f"  Particle count: {len(game.particles.particles)}")
print(f"  P1 position: ({game.p1.x:.0f}, {game.p1.y:.0f})")
print(f"  P2 position: ({game.p2.x:.0f}, {game.p2.y:.0f})")
assert game.p1.spin < spin1_0, "P1 spin should decay over time"
assert game.p2.spin < spin2_0, "P2 spin should decay over time"
print("  [PASS] 10s gameplay simulation completed")

print()
print("=" * 60)
print("INTEGRATION TEST: Win Conditions")
print("=" * 60)

print()
print("Case 1: Time Up (equal remaining spins)")
game2 = Game()
# Case 1: Time Up (equal remaining spins)
game.match_time = 0
game.p1.is_launched = True
game.p2.is_launched = True
game.p1.spin = 1000
game.p1.max_spin = 2000
game.p2.spin = 1000
game.p2.max_spin = 2000
game._check_win_conditions()
assert game.state == GameState.GAME_OVER, "Time Up should trigger GAME_OVER"
assert game.winner is None, "Equal remaining spin should result in Draw"
print(f"  After Time Up: state={game.state.name}, winner={game.winner}")
print("  [PASS] Time Up handled")

# Case 2: P2 Spin Out (spin depleted)
game.state = GameState.PLAYING
game.match_time = 100
game.p1.is_launched = True
game.p1.is_spinning = True
game.p1.spin = 1000
game.p2.is_launched = True
game.p2.is_spinning = False
game.p2.spin = 0
game._check_win_conditions()
assert game.winner == game.p1, f"P1 should win when P2 spins out, got {game.winner}"
print(f"  Winner: {game.winner.name}, reason: {game.stats.get('win_reason')}")
print("  [PASS] Spin Out handled")

# Case 3: P1 Ring Out
game.state = GameState.PLAYING
game.p1.is_launched = True
game.p1.is_knocked_out = True
game.p1.knockout_timer = 2.0
game.p2.is_launched = True
game.p2.is_knocked_out = False
game.p2.is_spinning = True
game.p2.spin = 800
game._check_win_conditions()
assert game.winner == game.p2, f"P2 should win when P1 is knocked out, got {game.winner}"
print(f"  Winner: {game.winner.name}, reason: {game.stats.get('win_reason')}")
print("  [PASS] Ring Out handled")

print()
print("Case 4: Pause -> Resume cycle")
game5 = Game()
game5._quick_match()
game5._start_match()
game5.state = GameState.PAUSED
assert game5.state == GameState.PAUSED
game5._resume()
assert game5.state == GameState.PLAYING
print("  [PASS] Pause/Resume works")

print()
print("=" * 60)
print("INTEGRATION TEST: Special Abilities End-to-End")
print("=" * 60)
for name in ["Thiruvalluvar", "Kottai Veeran", "Velu Vettaikaran", "Puyal Kaalai"]:
    preset = TOP_PRESETS[name]
    t = __import__("top").Top(name, preset, 1)
    t.launch(0,0,0,1.0)
    t.special_meter = 100
    spin_before = t.spin
    mass_before = t.mass
    active = t.activate_special([t])
    print(f"  {name:18s} [{preset['type'].value:7s}]: active={t.special_active}, meter={t.special_meter}, spin={spin_before:.0f}->{t.spin:.0f}, mass={mass_before}->{t.mass}")
    assert active and t.special_active and t.special_meter == 0
print("  [PASS] All 4 specials activate correctly")

print()
print("=" * 60)
print("INTEGRATION TEST: Top Selection UI Data Validity")
print("=" * 60)
game6 = Game()
for key in game6.menu_buttons[3].text:
    pass
assert len(TOP_PRESETS) == 8, "Should have 8 tops"
print(f"  Tops available: {len(TOP_PRESETS)}")
assert len(__import__("config").ARENA_PRESETS) == 4, "Should have 4 arenas"
print(f"  Arenas available: {len(__import__('config').ARENA_PRESETS)}")
for n, p in TOP_PRESETS.items():
    for k in ["type", "mass", "spin_speed", "spin_decay", "grip", "color", "special"]:
        assert k in p, f"Top {n} missing key {k}"
print("  [PASS] All tops & arenas have valid data structures")

print()
print("=" * 60)
print("ALL INTEGRATION TESTS PASSED!")
print("=" * 60)
pygame.quit()
