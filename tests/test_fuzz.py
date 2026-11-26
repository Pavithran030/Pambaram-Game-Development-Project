"""Monkey test: drive the real event/update/draw path with thousands of random
inputs across every screen and check nothing crashes and the game state
stays valid."""
import sys
import os
import random
os.environ["PAMBARAM_NO_SAVE"] = "1"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import math
import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from pambaram.config import *
from pambaram.main import Game

KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT,
        pygame.K_RIGHT, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_LSHIFT, pygame.K_RSHIFT,
        pygame.K_m, pygame.K_r, pygame.K_KP_ENTER, pygame.K_x]


def random_event(rng):
    kind = rng.random()
    pos = (rng.randint(-50, 1300), rng.randint(-50, 900))
    if kind < 0.35:
        return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos, "rel": (0, 0), "buttons": (0, 0, 0)})
    if kind < 0.55:
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": rng.choice((1, 1, 2, 3))})
    if kind < 0.75:
        return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": rng.choice((1, 1, 2, 3))})
    if kind < 0.97:
        return pygame.event.Event(pygame.KEYDOWN, {"key": rng.choice(KEYS), "mod": 0, "unicode": ""})
    return pygame.event.Event(rng.choice((pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED)), {})


def click_targets(g):
    """Real buttons/cards on the current screen, in game coordinates."""
    from pambaram.ui import get_top_card_rects, get_arena_card_rects
    btns = {
        GameState.MENU: g.menu_buttons, GameState.TOP_SELECT: g.top_select_buttons,
        GameState.ARENA_SELECT: g.arena_select_buttons, GameState.PAUSED: g.pause_buttons,
        GameState.GAME_OVER: g.gameover_buttons,
    }.get(g.state, [])
    rects = [b.rect for b in btns]
    if g.state == GameState.TOP_SELECT:
        rects += list(get_top_card_rects(TOP_PRESETS).values())
    if g.state == GameState.ARENA_SELECT:
        rects += list(get_arena_card_rects(ARENA_PRESETS).values())
    return rects


def to_window(g, pos):
    scale, _, _, ox, oy = g._view_transform()
    return (int(pos[0] * scale + ox), int(pos[1] * scale + oy))


rng = random.Random(1234)
g = Game()
g._quit = lambda: None          # the fuzzer may click QUIT; keep going
states_seen = set()
matches_finished = 0
frames = 25000
for frame in range(frames):
    # Alternate 'chaos' phases (any input, including ESC / focus loss, which
    # pause the game) with 'calm play' phases (only gameplay keys + mouse),
    # so whole matches also get played through.
    calm = (frame // 900) % 2 == 1
    for _ in range(rng.randint(0, 3)):
        ev = random_event(rng)
        if calm and (ev.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED)
                     or (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_m))):
            continue
        g.handle_event(ev)
    if calm and g.state == GameState.PAUSED:
        g._resume()
    # A proper click (press + release) on a real button or card.
    targets = click_targets(g)
    if targets and rng.random() < (0.01 if calm else 0.04):
        pos = to_window(g, rng.choice(targets).center)
        btn = rng.choice((1, 1, 3))
        for etype in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            data = {"pos": pos, "rel": (0, 0), "buttons": (0, 0, 0)} if etype == pygame.MOUSEMOTION \
                else {"pos": pos, "button": btn}
            g.handle_event(pygame.event.Event(etype, data))
    if frame % 3000 == 0:
        g.window = pygame.display.set_mode(rng.choice(((1200, 800), (800, 600), (1600, 900))))
    # Keep matches moving: sometimes jump straight into one.
    if g.state == GameState.MENU and rng.random() < 0.01:
        g._start_match()
    prev = g.state
    if g.state == GameState.PLAYING and g.p1 and g.p2:
        g._update_gameplay(1 / 60)
        # Speed things up so matches actually end during the fuzz.
        g.p1.spin = max(0, g.p1.spin - g.p1.max_spin * 0.012)
    if prev == GameState.PLAYING and g.state == GameState.GAME_OVER:
        matches_finished += 1
    if frame % 4 == 0:
        g._draw()
    states_seen.add(g.state)

    # Invariants.
    assert g.state in GameState
    if g.p1 and g.state in (GameState.PLAYING, GameState.PAUSED):
        for t in (g.p1, g.p2):
            assert math.isfinite(t.x) and math.isfinite(t.y) and math.isfinite(t.vx) and math.isfinite(t.vy)
            assert 0 <= t.spin <= t.max_spin + 1e-6
            assert -200 < t.x < SCREEN_WIDTH + 200 and -200 < t.y < SCREEN_HEIGHT + 200
        assert g.match_time <= MATCH_TIME

print(f"  {frames} frames of random input, screens visited: {sorted(s.name for s in states_seen)}")
print(f"  matches finished during fuzz: {matches_finished}")
assert len(states_seen) == len(GameState), "fuzz should reach every screen"
assert matches_finished > 0
print("ALL FUZZ TESTS PASSED!")
pygame.quit()
