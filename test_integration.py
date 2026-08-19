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
assert game.state == GameState.ARENA_SELECT, "Quick match should go to arena select"
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
game2._quick_match()
game2._start_match()
game2.match_started = True
game2.p1.launch(0, 0, 0, 0.5)
game2.p2.launch(0, 0, 0, 0.5)
game2.match_time = -0.01
game2.p1.spin = game2.p1.max_spin * 0.5
game2.p2.spin = game2.p2.max_spin * 0.5
game2._check_win_conditions()
assert game2.state == GameState.GAME_OVER, "Should go to game over on timeout"
print(f"  After Time Up: state={game2.state.name}, winner={game2.winner.name if game2.winner else None}")
print("  [PASS] Time Up handled")

print()
print("Case 2: P2 Spin Out (spin depleted)")
game3 = Game()
game3._quick_match()
game3._start_match()
game3.match_started = True
game3.p1.launch(0,0,0,0.5)
game3.p2.launch(0,0,0,0.5)
game3.p2.spin = 0
game3.p2.is_spinning = False
game3._check_win_conditions()
assert game3.state == GameState.GAME_OVER
assert game3.winner is game3.p1, "P1 should win on P2 spin out"
print(f"  Winner: {game3.winner.name}, reason: {game3.stats.get('win_reason', 'n/a')[:50]}")
print("  [PASS] Spin Out handled")

print()
print("Case 3: P1 Ring Out")
game4 = Game()
game4._quick_match()
game4._start_match()
game4.match_started = True
game4.p1.launch(0,0,0,0.5)
game4.p2.launch(0,0,0,0.5)
game4.p1.is_knocked_out = True
game4.p1.knockout_timer = 1.0
game4._check_win_conditions()
assert game4.state == GameState.GAME_OVER
assert game4.winner is game4.p2, "P2 should win on P1 ring out"
print(f"  Winner: {game4.winner.name}, reason: {game4.stats.get('win_reason', 'n/a')[:50]}")
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
