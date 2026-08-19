import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TOP_PRESETS, ARENA_CENTER, ARENA_RADIUS, RINGOUT_RADIUS
from top import Top
from arena import resolve_top_collision
from particles import ParticleSystem

preset1 = list(TOP_PRESETS.values())[0]

print("=" * 60)
print("DEBUG: BOUNCE LOGIC")
print(f"ARENA_RADIUS = {ARENA_RADIUS}")
print(f"RINGOUT_RADIUS = {RINGOUT_RADIUS}")
print(f"ARENA_CENTER = {ARENA_CENTER}")
print("=" * 60)

t2 = Top('BoundaryTest', preset1, 2)
t2.launch(0, 0, 0, 1.0)

t2.x = ARENA_CENTER[0] + ARENA_RADIUS + 15  # r = ARENA_RADIUS + 15
t2.y = ARENA_CENTER[1]
t2.vx = 300
t2.vy = 0

dx = t2.x - ARENA_CENTER[0]
dy = t2.y - ARENA_CENTER[1]
dist = math.sqrt(dx * dx + dy * dy) if 'math' in dir() else (dx*dx + dy*dy) ** 0.5
import math
dist = math.sqrt(dx * dx + dy * dy)
print(f"Test case: Top at (x={t2.x:.0f}, y={t2.y:.0f})")
print(f"  dx={dx:.0f}, dy={dy:.0f}, dist={dist:.1f}")
print(f"  ARENA_RADIUS = {ARENA_RADIUS}")
print(f"  RINGOUT_RADIUS = {RINGOUT_RADIUS}")
print(f"  dist >= ARENA_RADIUS? {dist >= ARENA_RADIUS}")
print(f"  dist >= RINGOUT_RADIUS? {dist >= RINGOUT_RADIUS}")

nx = dx / dist
ny = dy / dist
dot = t2.vx * nx + t2.vy * ny
print(f"  nx={nx:.3f}, ny={ny:.3f}")
print(f"  vx={t2.vx:.0f}, vy={t2.vy:.0f}")
print(f"  dot (v . n) = {dot:.0f}")
print(f"  dot < 0? {dot < 0}  <- PROBLEM: Only bounces if moving outward (dot<0 means moving inward)")

result = t2.check_boundary()
print(f"  check_boundary result: {result}")
print(f"  After call - vx={t2.vx:.0f}, ko={t2.is_knocked_out}")
print()

print("Bug Analysis: dot < 0 means velocity points INWARD (toward center).")
print("But the top at r=ARENA_RADIUS+15, vx=+300 means velocity is OUTWARD (positive nx, positive vx).")
print("So dot should be POSITIVE, NOT negative. The condition dot < 0 is WRONG for outward.")
print("We want to bounce when the top is moving OUTWARD beyond the wall. So we need dot > 0!")
print()

print("=" * 60)
print("DEBUG: COLLISION RESOLUTION")
print("=" * 60)
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

dx = pb.x - pa.x
dy = pb.y - pa.y
dist = math.sqrt(dx*dx + dy*dy)
min_dist = pa.radius + pb.radius

print(f"Attacker (P1): pos=({pa.x:.0f},{pa.y:.0f}) radius={pa.radius:.0f}")
print(f"Victim   (P2): pos=({pb.x:.0f},{pb.y:.0f}) radius={pb.radius:.0f}")
print(f"  dx={dx:.0f}, dy={dy:.0f}, dist={dist:.1f}")
print(f"  min_dist (r1+r2) = {min_dist:.1f}")
print(f"  dist >= min_dist? {dist >= min_dist} <- Should be FALSE for collision!")
print(f"  Distance between centers: {dist:.1f}")
print(f"  Combined radius:          {min_dist:.1f}")
print(f"  Overlap exists?           {dist < min_dist} <- FALSE, so no collision detected")
print(f"  PROBLEM: They are {dist - min_dist:.0f} pixels APART!")
print(f"  Place them closer together.")
print()

print("Trying with closer positions...")
pa.x = ARENA_CENTER[0]
pb.x = ARENA_CENTER[0] + 40  # much closer
dx = pb.x - pa.x
dist = math.sqrt(dx*dx + dy*dy)
print(f"  P1=({pa.x:.0f},{pa.y:.0f}), P2=({pb.x:.0f},{pb.y:.0f}), dist={dist:.1f}, min={min_dist:.1f}")
print(f"  dist < min_dist? {dist < min_dist}")
result = resolve_top_collision(pa, pb, ps)
print(f"  resolve returned: {result}")
print(f"  pb.vx after: {pb.vx:.0f}")
print(f"  particles: {len(ps.particles)}")
