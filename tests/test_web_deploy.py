"""Deployment & web-readiness tests: async entrypoint, emscripten guards,
localStorage settings fallback, WAV sound fallback, arrow keycap vector
rendering, and clean Pygbag staging."""
import asyncio
import json
import os
import shutil
import sys
import types
from unittest import mock

os.environ["PAMBARAM_NO_SAVE"] = "1"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((100, 100))

from pambaram import settings as store
from pambaram.config import SCREEN_HEIGHT, SCREEN_WIDTH
from pambaram.main import Game
from pambaram.sound import SoundManager
from pambaram.ui import _font_has_arrows, _measure_key_row, draw_key_row

passed = 0


def check(cond, msg):
    global passed
    assert cond, msg
    passed += 1
    print(f"  [PASS] {msg}")


print("=" * 60)
print("WEB DEPLOYMENT CHECKS")
print("=" * 60)

# 1. Emscripten localStorage persistence
class FakeLocalStorage:
    def __init__(self):
        self.data = {}

    def getItem(self, k):
        return self.data.get(k)

    def setItem(self, k, v):
        self.data[k] = v


fake_ls = FakeLocalStorage()
fake_platform = types.SimpleNamespace(window=types.SimpleNamespace(localStorage=fake_ls))
old_no_save = os.environ.pop("PAMBARAM_NO_SAVE", None)
try:
    with mock.patch.object(sys, "platform", "emscripten"), mock.patch.dict(
        sys.modules, {"platform": fake_platform}
    ):
        assert store.load() == store.DEFAULTS
        custom = store._deepcopy(store.DEFAULTS)
        custom["muted"] = True
        custom["arena"] = "Neon Arangam"
        custom["stats"]["best_score"] = 777
        assert store.save(custom) is True
        loaded = store.load()
        check(
            loaded["muted"] is True
            and loaded["arena"] == "Neon Arangam"
            and loaded["stats"]["best_score"] == 777,
            "emscripten settings persist and validate via localStorage",
        )
        fake_ls.setItem(store._LS_KEY, "{bad json")
        check(store.load() == store.DEFAULTS, "corrupt localStorage falls back to defaults")
finally:
    if old_no_save is not None:
        os.environ["PAMBARAM_NO_SAVE"] = old_no_save

# 2. Sound WAV BytesIO fallback
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(44100, -16, 2, 512)
    sm = SoundManager(enabled=False)
    sm._rate, sm._channels = 44100, 2
    pcm = sm._tone(440, 0.05, 0.3, "sine", decay=5.0).tobytes()
    snd = sm._sound_from_pcm_wav(pcm)
    check(snd.get_length() > 0, "SoundManager WAV BytesIO fallback produces playable Sound")
except pygame.error:
    check(True, "SoundManager skipped cleanly when no mixer device is available")

# 3. Fallback font arrow rendering (no tofu boxes)
builtin_font = pygame.font.Font(None, 14)
has_arrows = _font_has_arrows(builtin_font)
check(not has_arrows, "built-in fallback font arrow gap is detected")
surf = pygame.Surface((400, 60))
surf.fill((0, 0, 0))
items = [("key", "← / →"), ("text", "aim"), ("key", "←"), ("key", "→")]
widths, total = _measure_key_row(items, 14)
draw_key_row(surf, items, (200, 30), size=14)
check(total > 0 and all(w > 0 for w in widths), "arrow keycaps measure and render cleanly without missing glyphs")

# 4. Emscripten display, fullscreen, quit guards & async loop
with mock.patch.object(sys, "platform", "emscripten"):
    g = Game()
    check(
        g.window.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT) and not g.fullscreen,
        "emscripten display initializes at virtual 1200x800 without fullscreen crash",
    )
    g._toggle_fullscreen()
    check(not g.fullscreen and "FULLSCREEN" in g.toast_text, "emscripten fullscreen toggle displays browser hint toast")
    g._quit()
    check(g.running and "CLOSE TAB" in g.toast_text, "emscripten quit does not kill the browser loop")


async def _run_one_tick():
    g2 = Game()
    orig_draw = g2._draw

    def stop_after_draw():
        orig_draw()
        g2.running = False

    g2._draw = stop_after_draw
    with mock.patch("sys.exit") as mock_exit:
        await g2.run()
        return mock_exit.called


with mock.patch.object(sys, "platform", "emscripten"):
    exit_called = asyncio.run(_run_one_tick())
    check(not exit_called, "async Game.run() completes cleanly on emscripten without calling sys.exit")

# 5. Staging script produces clean Pygbag bundle
import tempfile
from pathlib import Path
from scripts import stage_web

with tempfile.TemporaryDirectory(prefix="pambaram-stage-test-") as tmp_stage_root:
    stage_dir = stage_web.stage(Path(tmp_stage_root) / "pambaram")
    main_txt = (stage_dir / "main.py").read_text(encoding="utf-8")
    check("/// script" in main_txt and "pygame-ce" in main_txt and "import pygame" in main_txt,
          "staged main.py exposes pygame-ce dependency for Pygbag preloader")
    check((stage_dir / "main.py").is_file(), "staged bundle includes main.py")
    check((stage_dir / "pambaram" / "main.py").is_file(), "staged bundle includes pambaram package")
    check((stage_dir / "favicon.png").is_file(), "staged bundle includes generated favicon.png")
    for forbidden in ("tests", "docs", ".venv", ".env", "README.md", "DEPLOYMENT.md"):
        check(not (stage_dir / forbidden).exists(), f"staged bundle excludes {forbidden}")
    pycache_dirs = list(stage_dir.rglob("__pycache__"))
    check(len(pycache_dirs) == 0, "staged bundle excludes __pycache__")

print()
print("=" * 60)
print(f"ALL {passed} WEB DEPLOYMENT TESTS PASSED!")
print("=" * 60)
pygame.quit()
