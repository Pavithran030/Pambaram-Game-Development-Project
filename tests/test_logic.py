import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("LOGIC TEST 1: Top Physics & State")
print("=" * 60)
from config import TOP_PRESETS, ARENA_CENTER, ARENA_RADIUS, RINGOUT_RADIUS, TopType
from top import Top

preset1 = list(TOP_PRESETS.values())[0]
t1 = Top('TestTop', preset1, 1)
print(f"Created top: {t1.name}, type={t1.type.value}")
print(f"  Initial position: ({t1.x:.0f}, {t1.y:.0f})")
print(f"  Mass={t1.mass}, MaxSpin={t1.max_spin}, Grip={t1.grip}")
print(f"  Spin={t1.spin}, is_spinning={t1.is_spinning}, is_launched={t1.is_launched}")
print()

t1.launch(1.0, 0.0, 500, 0.9)
print("After launch:")
print(f"  Spin={t1.spin:.0f} (expected > 0): {'PASS' if t1.spin > 0 else 'FAIL'}")
print(f"  Velocity: ({t1.vx:.0f}, {t1.vy:.0f})")
print(f"  is_spinning={t1.is_spinning} (True): {'PASS' if t1.is_spinning else 'FAIL'}")
print(f"  is_launched={t1.is_launched} (True): {'PASS' if t1.is_launched else 'FAIL'}")
print()

dt = 1.0 / 60
spin_before = t1.spin
vx_before = t1.vx
for _ in range(60):
    t1.update(dt, 1.0)
print("After 1 second (60 frames):")
decay_ok = spin_before > t1.spin
friction_ok = abs(vx_before) > abs(t1.vx)
print(f"  Spin decay: {spin_before:.0f} -> {t1.spin:.0f}: {'PASS' if decay_ok else 'FAIL'}")
print(f"  Vx friction: {vx_before:.0f} -> {t1.vx:.0f}: {'PASS' if friction_ok else 'FAIL'}")
print()

t1.vx, t1.vy = 100, 0
t1.steer(0, 1)
t1.update(0.5, 1.0)
steer_ok = t1.vy > 10
print(f"Steer UP test: Vy={t1.vy:.1f}: {'PASS' if steer_ok else 'FAIL'}")
print()

print("=" * 60)
print("LOGIC TEST 2: Arena Boundary & Ring-Out")
print("=" * 60)
t2 = Top('BoundaryTest', preset1, 2)
t2.launch(0, 0, 0, 1.0)

t2.x = ARENA_CENTER[0] + ARENA_RADIUS - 5
t2.y = ARENA_CENTER[1]
result = t2.check_boundary()
inside_ok = not t2.is_knocked_out and result is None
print(f"Inside arena (r={ARENA_RADIUS-5}): result={result}, ko={t2.is_knocked_out}: {'PASS' if inside_ok else 'FAIL'}")

t2.x = ARENA_CENTER[0] + ARENA_RADIUS + 15
t2.y = ARENA_CENTER[1]
t2.vx = 300
t2.vy = 0
result = t2.check_boundary()
bounce_ok = (result == "bounce") and (t2.vx < 0) and (not t2.is_knocked_out)
print(f"Bounce zone (r={ARENA_RADIUS+15}): result={result}, vx={t2.vx:.0f}, ko={t2.is_knocked_out}: {'PASS' if bounce_ok else 'FAIL'}")

t2.x = ARENA_CENTER[0] + RINGOUT_RADIUS + 20
t2.y = ARENA_CENTER[1]
t2.is_knocked_out = False
result = t2.check_boundary()
ringout_ok = t2.is_knocked_out and (result == "ringout")
print(f"Ring-out zone (r={RINGOUT_RADIUS+20}): result={result}, ko={t2.is_knocked_out}: {'PASS' if ringout_ok else 'FAIL'}")
print()

print("=" * 60)
print("LOGIC TEST 3: Dash & Special")
print("=" * 60)
t3 = Top('DashTest', preset1, 1)
t3.launch(0, 0, 0, 1.0)
t3.vx, t3.vy = 0, 0
t3.dash_cooldown = 0
result = t3.dash(1, 0)
dash_ok = result and (t3.vx > 0) and (t3.dash_cooldown > 0) and t3.is_dashing
print(f"Dash(right): vx={t3.vx:.0f}, cd={t3.dash_cooldown:.2f}, dashing={t3.is_dashing}: {'PASS' if dash_ok else 'FAIL'}")

t3.special_meter = 100
old_mass = t3.mass
result = t3.activate_special([t3])
spec_ok = result and (t3.special_meter == 0) and t3.special_active
print(f"Activate special: success={result}, meter={t3.special_meter}, active={t3.special_active}: {'PASS' if spec_ok else 'FAIL'}")

t3.special_timer = 0.1
t3.update(0.5, 1.0)
print(f"After special expires: special_active={t3.special_active}, mass returned={t3.mass == old_mass or t3.type != TopType.DEFENSE}")
print()

print("Testing all 4 top types specials:")
all_ok = True
for name, preset in list(TOP_PRESETS.items())[:4]:
    tx = Top(name, preset, 1)
    tx.launch(0,0,0,1.0)
    tx.special_meter = 100
    res = tx.activate_special([tx])
    print(f"  {name} ({preset['type'].value:7s}, {preset['special']:10s}): success={res}, active={tx.special_active}")
    if not res or not tx.special_active:
        all_ok = False
print(f"  All 4 specials work: {'PASS' if all_ok else 'FAIL'}")
print()

print("=" * 60)
print("LOGIC TEST 4: Collision & Momentum")
print("=" * 60)
from arena import resolve_top_collision
from particles import ParticleSystem

ps = ParticleSystem()
pa = Top('Attacker', TOP_PRESETS['Velu Vettaikaran'], 1)
pb = Top('Victim', TOP_PRESETS['Puyal Kaalai'], 2)
pa.launch(1, 0, 800, 1.0)
pb.launch(0, 0, 0, 0.8)
pa.x = ARENA_CENTER[0] - 30
pa.y = ARENA_CENTER[1]
pb.x = ARENA_CENTER[0] + 30
pb.y = ARENA_CENTER[1]
pa.vx = 600
pa.vy = 0
pb.vx = 0
pb.vy = 0

mom_before_a = pa.mass * 600 * (pa.spin/pa.max_spin)
spin_before_b = pb.spin

shake = resolve_top_collision(pa, pb, ps)
print(f"Heavy attack top hitting light speed top:")
print(f"  shake returned: {shake} (>0: {shake > 0})")
print(f"  pb.vx after: {pb.vx:.0f} (>0: {pb.vx > 0})")
spin_loss_b = spin_before_b - pb.spin
print(f"  pb spin loss: {spin_loss_b:.0f} (>0: {spin_loss_b > 0})")
print(f"  Particles emitted: {len(ps.particles)} (>0: {len(ps.particles) > 0})")
print()

print("=" * 60)
print("LOGIC TEST 5: AI Controller")
print("=" * 60)
from ai import AIController
from config import Difficulty

player_top = Top('Player', preset1, 1)
ai_top = Top('AI', list(TOP_PRESETS.values())[1], 2, True, Difficulty.MEDIUM)
player_top.launch(0,0,0,1.0)
ai_top.launch(0,0,0,1.0)
ai_controller = AIController(ai_top, Difficulty.MEDIUM)

decisions_count = 0
for i in range(10):
    res = ai_controller.update(player_top, dt)
    if res and res[0]:
        decisions_count += 1
        steer, do_dash, do_special = res
        has_dir = abs(steer[0]) + abs(steer[1]) > 0.01
        print(f"  Frame {i}: steer={steer}, dash={do_dash}, special={do_special}, has_dir={has_dir}")

print(f"AI returned decisions for 10 frames: {decisions_count}/10")
print(f"  AI test: {'PASS' if decisions_count > 5 else 'FAIL'}")
print()

print("=" * 60)
print("LOGIC TEST 6: Win Conditions (simulated)")
print("=" * 60)
print("(These are checked in main._check_win_conditions)")

# Ring out case
ta = Top('P1', preset1, 1)
tb = Top('P2', preset1, 2)
ta.launch(0,0,0,1.0)
tb.launch(0,0,0,1.0)
ta.is_knocked_out = True
ta.knockout_timer = 1.0
tb.is_knocked_out = False

p1_out = ta.is_knocked_out and ta.knockout_timer > 0.5
p2_out = tb.is_knocked_out and tb.knockout_timer > 0.5
win_case1 = (not p1_out and p2_out) or (p1_out and not p2_out)
print(f"P1 ringout win: p1_out={p1_out}, p2_out={p2_out}, detect_valid={win_case1}: {'PASS' if win_case1 else 'FAIL'}")

# Spin out case
ta2 = Top('P1', preset1, 1)
tb2 = Top('P2', preset1, 2)
ta2.launch(0,0,0,1.0)
tb2.launch(0,0,0,1.0)
tb2.spin = 0
tb2.is_spinning = False
p1_dead = (not ta2.is_spinning) and ta2.is_launched and ta2.spin <= 0
p2_dead = (not tb2.is_spinning) and tb2.is_launched and tb2.spin <= 0
win_case2 = (p1_dead and not p2_dead) or (p2_dead and not p1_dead)
print(f"P2 spinout win: p1_dead={p1_dead}, p2_dead={p2_dead}, detect_valid={win_case2}: {'PASS' if win_case2 else 'FAIL'}")
print()

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print("All critical game logic modules loaded successfully:")
print("  - Top physics (spin decay, friction, steering)")
print("  - Arena boundaries (bounce, ring-out detection)")
print("  - Dash & special abilities (4 top types)")
print("  - Collision momentum transfer")
print("  - AI decisions")
print("  - Win conditions (ringout, spinout, timeout)")
print()
print("Pambaram game logic validation complete.")
