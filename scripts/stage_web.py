"""Stage a minimal, clean Pambaram package for Pygbag web builds and optionally
run `pygbag` to build/archive/serve it.

Why a staging directory?
Pygbag packages every non-hidden file under its target directory into the
browser archive (there is no `.pygbagignore`). Staging into `build_src/`
keeps `tests/`, `docs/`, batch scripts, and `.env` out of the web bundle.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE_ROOT = ROOT / "build_src"
STAGE_DIR = STAGE_ROOT / "pambaram"
TEMPLATE_PATH = ROOT / "web" / "pambaram.tmpl"


def _generate_favicon(dest: Path) -> bool:
    """Render Pambaram's procedural icon as a 64x64 PNG without needing a display."""
    try:
        import pygame
    except ImportError:
        return False

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    src_dir = str(ROOT / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from pambaram.top_art import make_icon

    pygame.init()
    try:
        icon = make_icon(64)
        pygame.image.save(icon, str(dest))
        return True
    finally:
        pygame.quit()


def stage(stage_dir: Path = STAGE_DIR) -> Path:
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)

    shutil.copy2(ROOT / "main.py", stage_dir / "main.py")
    shutil.copytree(
        ROOT / "src" / "pambaram",
        stage_dir / "pambaram",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )

    _generate_favicon(stage_dir / "favicon.png")
    return stage_dir


def run_pygbag(mode: str, port: int = 8000, stage_dir: Path = STAGE_DIR):
    cmd = [
        sys.executable,
        "-m",
        "pygbag",
        "--app_name",
        "pambaram",
        "--title",
        "Pambaram: Spinning Top Battle Arena",
        "--width",
        "1200",
        "--height",
        "800",
        "--template",
        str(TEMPLATE_PATH),
    ]
    favicon = stage_dir / "favicon.png"
    if favicon.is_file():
        cmd.extend(["--icon", str(favicon)])
    if mode == "build":
        cmd.append("--build")
    elif mode == "archive":
        cmd.append("--archive")
    elif mode == "serve":
        cmd.extend(["--port", str(port)])

    cmd.append(str(stage_dir))
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))


def main():
    parser = argparse.ArgumentParser(description="Stage and build Pambaram for WebAssembly via Pygbag.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--build", action="store_true", help="Stage and compile static web bundle into build_src/build/web/")
    group.add_argument("--archive", action="store_true", help="Stage and compile itch.io-ready build_src/build/web.zip")
    group.add_argument("--serve", action="store_true", help="Stage, compile, and serve locally via Pygbag dev server")
    parser.add_argument("--port", type=int, default=8000, help="Local dev server port for --serve (default: 8000)")
    args = parser.parse_args()

    stage_path = stage()
    print(f"Staged clean web package at: {stage_path}")

    if args.build:
        run_pygbag("build", args.port)
    elif args.archive:
        run_pygbag("archive", args.port)
    elif args.serve:
        run_pygbag("serve", args.port)


if __name__ == "__main__":
    main()
