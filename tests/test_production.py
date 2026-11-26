"""Production-readiness checks: save data, crash safety, window behaviour,
menu keyboard navigation and art rendering."""
import sys
import os
import json
import tempfile
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

# Point the save folder at a throwaway temp dir (never the real one).
tmp_home = tempfile.mkdtemp(prefix="pambaram-test-")
os.environ["APPDATA"] = tmp_home
os.environ["HOME"] = tmp_home
os.environ.pop("PAMBARAM_NO_SAVE", None)

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from pambaram import settings as store
from pambaram.config import *
from pambaram.main import Game
from pambaram.top import Top
from pambaram.top_art import render_top, make_icon

passed = 0


def check(cond, msg):
    global passed
    assert cond, msg
    passed += 1
    print(f"  [PASS] {msg}")


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, {"key": k, "mod": 0, "unicode": ""})


print("=" * 60)
print("SAVE DATA")
print("=" * 60)
check(store.data_dir().startswith(tmp_home), "save folder is redirected for tests")
check(store.load() == store.DEFAULTS, "no save file -> defaults")

os.makedirs(store.data_dir(), exist_ok=True)
path = os.path.join(store.data_dir(), "settings.json")
with open(path, "w") as f:
    f.write("{ this is not json")
check(store.load() == store.DEFAULTS, "corrupt save file -> defaults, no crash")

with open(path, "w") as f:
    json.dump({"p1_top": "Nope", "arena": 5, "difficulty": "ULTRA", "muted": "yes",
               "p2_top": "Sooravali", "stats": {"matches": -3, "best_score": 900}}, f)
s = store.load()
check(s["p1_top"] == store.DEFAULTS["p1_top"] and s["arena"] == store.DEFAULTS["arena"]
      and s["difficulty"] == "MEDIUM" and s["muted"] is False, "invalid values are replaced by defaults")
check(s["p2_top"] == "Sooravali" and s["stats"]["best_score"] == 900 and s["stats"]["matches"] == 0,
      "valid values survive, invalid stats are dropped")

# Choices made in-game are remembered by the next session.
g = Game()
g.p1_top_name, g.p2_top_name, g.selected_arena = "Kallazhagar", "Puyal Kaalai", "Neon Arangam"
g._cycle_difficulty()   # MEDIUM -> HARD
g._toggle_mute()
g2 = Game()
check((g2.p1_top_name, g2.p2_top_name, g2.selected_arena, g2.ai_difficulty, g2.muted)
      == ("Kallazhagar", "Puyal Kaalai", "Neon Arangam", Difficulty.HARD, True),
      "selections, difficulty and mute persist across launches")
check(not g2.sound.enabled, "muted setting really silences sound")
g2._toggle_mute()
check(not g2.muted, "M toggles sound back on")

# Stats + best score are recorded once per match (start from a fresh save).
os.remove(path)
g = Game()
g.p2_is_ai = True
g._start_match()
while not g.match_started:
    g._update_gameplay(1 / 60)
g.p2.spin = 0
g._check_win_conditions()
st = store.load()["stats"]
check(st["matches"] == 1 and st["p1_wins"] == 1 and st["wins_vs_ai_by_difficulty"][g.ai_difficulty.name] == 1,
      "a finished match updates lifetime stats")
check(g.stats["new_best"] and st["best_score"] == g.stats["points"] > 0, "a first win sets a new best score")

check(store.save({"x": 1}) and not any(n.endswith(".tmp") for n in os.listdir(store.data_dir())),
      "saving is atomic (no temp files left behind)")

os.environ["PAMBARAM_NO_SAVE"] = "1"
before = open(path).read()
store.save({"should": "not be written"})
check(open(path).read() == before, "PAMBARAM_NO_SAVE=1 disables writing")
os.environ.pop("PAMBARAM_NO_SAVE")

try:
    raise RuntimeError("boom")
except RuntimeError as e:
    log = store.write_crash_log(e)
check(log and "RuntimeError: boom" in open(log, encoding="utf-8").read(), "crashes are written to crash.log")

print()
print("=" * 60)
print("WINDOW & NAVIGATION")
print("=" * 60)
g = Game()
g._start_match()
g.state = GameState.PLAYING
for ev in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
    g.state = GameState.PLAYING
    g.handle_event(pygame.event.Event(ev, {}))
    check(g.state == GameState.PAUSED, f"{pygame.event.event_name(ev)} auto-pauses a match")
g.state = GameState.MENU
g.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST, {}))
check(g.state == GameState.MENU, "losing focus outside a match changes nothing")

g = Game()
g._start_top_select()
g._handle_top_select_events(key(pygame.K_RETURN))
check(g.state == GameState.ARENA_SELECT, "ENTER on top select -> arena select")
first = g.selected_arena
g._handle_arena_select_events(key(pygame.K_RIGHT))
check(g.selected_arena != first, "arrow keys change the arena")
g._handle_arena_select_events(key(pygame.K_ESCAPE))
check(g.state == GameState.TOP_SELECT, "ESC on arena select -> back to top select")
g._handle_top_select_events(key(pygame.K_ESCAPE))
check(g.state == GameState.MENU, "ESC on top select -> back to menu")
g._start_match()
g.state = GameState.GAME_OVER
g._handle_gameover_events(key(pygame.K_RETURN))
check(g.state == GameState.PLAYING and not g.match_started, "ENTER on game over -> rematch")
g.state = GameState.GAME_OVER
g._handle_gameover_events(key(pygame.K_ESCAPE))
check(g.state == GameState.MENU, "ESC on game over -> main menu")

# The view can be resized to any shape and the mouse still maps correctly.
for size in ((1200, 800), (1920, 1080), (900, 900), (640, 360)):
    g.window = pygame.display.set_mode(size)
    scale, w, h, ox, oy = g._view_transform()
    cx, cy = g._map_mouse_pos((ox + int(600 * scale), oy + int(400 * scale)))
    check(abs(cx - 600) <= 2 and abs(cy - 400) <= 2, f"mouse mapping is correct at {size[0]}x{size[1]}")
    g._draw()

print()
print("=" * 60)
print("TOP ARTWORK")
print("=" * 60)
for name, p in TOP_PRESETS.items():
    t = Top(name, p, 1)
    art = render_top(int(t.radius), p["color"], p["accent"], p["type"], 1.0, 1.0)
    w, h = art.get_size()
    centre = art.get_at((w // 2, h // 2))
    corner = art.get_at((0, 0))
    assert centre.a == 255 and corner.a == 0, name
check(True, "all 8 tops render opaque bodies with transparent surroundings")
icon = make_icon(64)
check(icon.get_size() == (64, 64), "window icon renders")

# Spot the old corner 'badge dot' bug: nothing should be drawn outside the
# top's own radius except its team ring.
g = Game()
g._start_match()
g.screen.fill((0, 0, 0))
g.p1.draw(g.screen)
r = int(g.p1.radius)
bx, by = int(g.p1.x + r * 0.74), int(g.p1.y + r * 0.74)
col = g.screen.get_at((bx, by))
check(col[:3] != COLORS["p1_color"], "no player badge dot on the top body")

print()
print("=" * 60)
print(f"ALL {passed} PRODUCTION TESTS PASSED!")
print("=" * 60)
pygame.quit()
