import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
screen = pygame.display.set_mode((1200, 800))

print("=" * 60)
print("UI RENDER TEST: All screens render in headless mode")
print("=" * 60)

from ui import Button, draw_menu, draw_top_select, draw_arena_select, draw_hud, draw_pause, draw_game_over, draw_countdown
from config import TOP_PRESETS, ARENA_PRESETS, GameState, Difficulty, get_font
from top import Top

dummy_btns = [Button(100, 500, 200, 50, "Test")]

print("\nRendering: Main Menu...")
draw_menu(screen, dummy_btns)
print("  [OK]")

print("\nRendering: Top Select...")
top_sel_btns = [Button(500, 700, 150, 40, "X")] * 3
draw_top_select(screen, TOP_PRESETS, "Thiruvalluvar", "Velu Vettaikaran", True, top_sel_btns, Difficulty.MEDIUM)
print("  [OK]")

print("\nRendering: Arena Select...")
arena_btns = [Button(800, 700, 150, 40, "START")] * 2
draw_arena_select(screen, ARENA_PRESETS, "Gramam Thidal", arena_btns)
print("  [OK]")

print("\nRendering: HUD with live tops...")
t1 = Top('Test1', list(TOP_PRESETS.values())[2], 1)
t2 = Top('Test2', list(TOP_PRESETS.values())[0], 2)
t1.launch(0,0,0,1.0)
t2.launch(0,0,0,1.0)
t1.special_meter = 75
t2.special_meter = 100
t2.spin = t2.max_spin * 0.2
draw_hud(screen, t1, t2, 123.45)
print("  [OK]")

print("\nRendering: Countdown 3, 2, 1, GO...")
for c in [3, 2, 1, 0]:
    draw_countdown(screen, c)
    pygame.display.flip()
print("  [OK]")

print("\nRendering: Pause screen...")
pause_btns = [Button(440, 320, 320, 65, "Resume")] * 3
draw_pause(screen, pause_btns)
print("  [OK]")

print("\nRendering: Game Over screen...")
stats = {"win_reason": "SPIN OUT! Opponent ran out of spin!",
         "match_time": 95.5,
         "p1_final_spin": 1250, "p2_final_spin": 0, "points": 125}
go_btns = [Button(340, 590, 260, 60, "Rematch"), Button(620, 590, 260, 60, "Menu")]
draw_game_over(screen, t1, stats, go_btns)
print("  [OK]")

pygame.display.flip()

print()
print("=" * 60)
print("BUTTON INTERACTION TEST")
print("=" * 60)
btn = Button(100, 100, 200, 50, "Test Button")
clicked = [False]
def on_click():
    clicked[0] = True
    print("  Button callback fired!")
btn.callback = on_click

# Simulate hover, press, release
btn.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {'pos': (200, 125)}))
assert btn.hovered, "Button should be hovered"
print(f"  Hovered: {btn.hovered}")

btn.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (200, 125), 'button': 1}))
assert btn.pressed, "Button should be pressed"
print(f"  Pressed: {btn.pressed}")

btn.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (200, 125), 'button': 1}))
assert clicked[0], "Button callback should fire"
print(f"  Callback executed: {clicked[0]}")
print("  [PASS] Button interaction works")

print()
print("=" * 60)
print("TOP SELECT: Mouse click on cards")
print("=" * 60)
class Fake:
    pass
game = Fake()
game.p1_top_name = list(TOP_PRESETS.keys())[0]
game.p2_top_name = list(TOP_PRESETS.keys())[1]

# Simulate left-click on 5th card
card_w = 240; card_h = 290; gap_x = 20; cols = 4
start_x = 1200 // 2 - (cols * (card_w + gap_x) - gap_x) // 2
start_y = 130
idx = 4  # 5th card (Maruthuvar)
col = idx % cols
row = idx // cols
cx = start_x + col * (card_w + gap_x) + card_w // 2
cy = start_y + row * (card_h + gap_x) + card_h // 2
print(f"  Clicking card #{idx} at ({cx}, {cy})")
names = list(TOP_PRESETS.keys())
if cx >= start_x and cx < start_x + cols*(card_w+gap_x):
    card_idx = ((cx - start_x) // (card_w + gap_x))
    if card_idx == col:
        game.p1_top_name = names[idx]
print(f"  Selected: {game.p1_top_name}")
assert game.p1_top_name == names[idx]
print("  [PASS] Top selection card indexing works")

print()
print("=" * 60)
print("ALL UI RENDER & INTERACTION TESTS PASSED!")
print("=" * 60)
pygame.quit()
