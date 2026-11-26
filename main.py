# /// script
# dependencies = [
#   "pygame-ce",
# ]
# ///
"""Entry point. The game itself lives in src/pambaram/ - this just puts
that package on the path and hands off to it, so `python main.py` keeps
working unchanged from the project root and under Pygbag web builds."""
import asyncio
import os
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402, F401  (detected by Pygbag preloader for pygame-ce WASM)

_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_ROOT, "src")
if os.path.isdir(_SRC) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from pambaram.main import main

if __name__ == "__main__":
    asyncio.run(main())
