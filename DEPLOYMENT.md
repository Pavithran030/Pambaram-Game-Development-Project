# Pambaram — Free Online Deployment Guide (No Docker Required)

This guide explains how **Pambaram: Spinning Top Battle Arena** is prepared for online deployment and walks through every **100% free, Docker-free** option to publish and play it in a web browser.

---

## Why Pygbag (WebAssembly) Is Recommended

Pambaram is a client-side 60 FPS Pygame application (`1200×800` virtual canvas, procedural top artwork, procedural 16-bit PCM SFX, and keyboard/mouse physics). Standard Python web hosts (Render, Vercel Python, PythonAnywhere) only serve HTTP backends and cannot open an OS Pygame window in a visitor's browser.

By packaging the game with **Pygbag** (Python + `pygame-ce` compiled to WebAssembly), the entire game runs natively inside the player's browser at 60 FPS with:
- **$0 hosting cost** (pure static HTML/JS/WASM files)
- **Zero Docker, zero VMs, and zero server cold-starts**
- **No external asset files needed** (zero images/audio to host separately)

---

## Deployment Updates Included in This Branch (`new-ui`)

1. **Async Game Loop ([`main.py`](main.py), [`src/pambaram/main.py`](src/pambaram/main.py)):**
   - Converted `Game.run()` and `main()` to `async def` yielding `await asyncio.sleep(0)` every frame so the browser tab stays responsive.
   - Added `sys.platform == "emscripten"` guards for display initialization (`1200×800`), fullscreen hint toast, non-exiting quit behavior, and avoiding `sys.exit()` in WASM.
2. **Browser Persistence ([`src/pambaram/settings.py`](src/pambaram/settings.py)):**
   - When running under `emscripten`, settings and lifetime stats save/load automatically via `window.localStorage` (`pambaram_settings_v1`) instead of an ephemeral in-memory filesystem.
3. **Cross-Platform Arrow Glyphs & Fonts ([`src/pambaram/config.py`](src/pambaram/config.py), [`src/pambaram/ui.py`](src/pambaram/ui.py)):**
   - Added Linux fonts (`dejavusans`, `liberationsans`) to `FONT_FAMILIES`.
   - Added automatic vector arrow rendering in `draw_key_row` when the fallback font (`freesansbold`) lacks `←` / `→` glyphs, preventing missing-glyph tofu boxes (`□`).
4. **Procedural Audio Web Fallback ([`src/pambaram/sound.py`](src/pambaram/sound.py)):**
   - Added `pygame.mixer.pre_init(44100, -16, 2, 512)` and a pure-Python RIFF WAV header (`struct` + `io.BytesIO`) fallback inside `SoundManager` in case raw PCM buffer loading is rejected by the WebAssembly mixer.
5. **Clean Web Packager & Custom Browser Template ([`scripts/stage_web.py`](scripts/stage_web.py), [`web/pambaram.tmpl`](web/pambaram.tmpl)):**
   - Stages a minimal `build_src/pambaram/` bundle (`main.py`, `pambaram/`, generated `favicon.png`) so `tests/`, `docs/`, `.venv/`, and batch scripts are never packed into the browser archive.
   - Disables right-click browser context menus globally so P2 top selection and right-drag aiming work cleanly.
6. **Automated CI/CD Workflows (No Docker):**
   - [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) — Free automated tests + GitHub Pages web deployment.
   - [`.github/workflows/release-binaries.yml`](.github/workflows/release-binaries.yml) — Free Windows `.exe` and Linux builds on GitHub Releases.

---

## Step 1: Test the Browser Build Locally

1. **Install Pygbag** (in your active Python virtual environment):
   ```bash
   pip install -r requirements.txt -r requirements-web.txt
   ```
2. **Stage, build, and run the local web dev server:**
   ```bash
   python scripts/stage_web.py --serve
   ```
3. Open **`http://localhost:8000`** in Chrome, Edge, or Firefox.
4. Click/tap the **"Click or tap to start Pambaram!"** prompt (browsers require one user interaction to unlock Web Audio).
5. Verify:
   - Menu text and arrow keycaps (`← / →`) render crisply.
   - Right-click on a card in **Choose Your Top** assigns Player 2 / AI without opening the browser context menu.
   - Sound effects play on clicks, launches, and collisions.
   - Lifetime stats/mute state persist across browser refreshes.

---

## Step 2: Deploy for Free on GitHub Pages (Recommended)

This repository already includes [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml). For public GitHub repositories, **GitHub Actions minutes** and **GitHub Pages** (`1 GB` site size, `100 GB/month` soft bandwidth) are **100% free** (non-commercial use).

### Steps:
1. **Push this branch** to GitHub (or merge `new-ui` into `main`):
   ```bash
   git add .
   git commit -m "Add Pygbag web deployment support, CI workflows, and DEPLOYMENT.md"
   git push origin new-ui
   ```
2. On GitHub, open your repository -> **Settings** -> **Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Open the **Actions** tab and confirm **Deploy Pambaram Web (GitHub Pages)** succeeds.
   - The workflow automatically runs the headless tests (`test_ui.py`, `test_integration.py`, `test_match_flow.py`, `test_production.py`, `test_web_deploy.py`), stages `build_src/pambaram/`, builds WASM with Pygbag, and publishes `build_src/pambaram/build/web/`.
5. Play your live game at:
   ```text
   https://<your-github-username>.github.io/<your-repo-name>/
   ```
   *(For this repo: `https://pavithran030.github.io/Pambaram-Game-Development-Project/`.)*

---

## Step 3: Deploy for Free on itch.io (Best for Sharing & Game Showcases)

itch.io hosts HTML5/WebAssembly browser games for free (up to `500 MB` ZIP, `1,000` files—Pambaram's bundle is well under `1 MB`).

### Steps:
1. Build the itch.io archive locally:
   ```bash
   python scripts/stage_web.py --archive
   ```
   This generates **`build_src/pambaram/build/web.zip`** with `index.html`, `favicon.png`, and `pambaram.apk` at the ZIP root.
2. Sign in to [itch.io](https://itch.io) -> **Dashboard** -> **Create new project**.
3. Fill in Title & Project URL, and set:
   - **Kind of project:** `HTML`
   - **Pricing:** `No payments` (`$0` / Free)
   - **Uploads:** Upload `build_src/pambaram/build/web.zip` and check **"This file will be played in the browser"**.
   - **Embed options:**
     - **Viewport dimensions:** `1200` × `800` (or `960` × `640` to preserve the 3:2 ratio)
     - Enable **Fullscreen button**
4. Click **Save & view page**, test in the embed player, then switch visibility to **Public**.

---

## Step 4: Deploy for Free on Cloudflare Pages (Unlimited Bandwidth)

Cloudflare Pages provides **unlimited static bandwidth** and allows commercial projects on its free tier (`500` builds/month, `20,000` files max).

### Option A — Git Integration (Automatic):
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/) -> **Workers & Pages** -> **Create** -> **Pages** -> **Connect to Git**.
2. Select your GitHub repository and branch (`main` or `new-ui`).
3. Configure build settings:
   - **Build command:**
     ```bash
     pip install -r requirements.txt -r requirements-web.txt && python scripts/stage_web.py --build
     ```
   - **Build output directory:** `build_src/pambaram/build/web`
4. Click **Save and Deploy**. Your live URL will be `https://<project-name>.pages.dev`.

### Option B — Direct CLI Upload:
```bash
python scripts/stage_web.py --build
npx wrangler pages deploy build_src/pambaram/build/web --project-name=pambaram-game
```

---

## Step 5: Deploy for Free on Hugging Face Static Spaces (No Docker)

You can also host the compiled Pygbag static files directly on a **Static** Hugging Face Space (no container or Dockerfile required):
1. Build the static web files locally:
   ```bash
   python scripts/stage_web.py --build
   ```
2. On [Hugging Face Spaces](https://huggingface.co/spaces), click **New Space** and select **Space SDK = Static**, **Template = Blank**, **Public**.
3. Upload every file inside **`build_src/pambaram/build/web/`** (`index.html`, `favicon.png`, `pambaram.apk`, `pambaram.tar.gz`) to the root of the Space repository.
4. Hugging Face serves `index.html` immediately at `https://huggingface.co/spaces/<username>/<space-name>`.

---

## Step 6: Free Downloadable Desktop Builds (GitHub Releases)

[`.github/workflows/release-binaries.yml`](.github/workflows/release-binaries.yml) builds standalone **Windows (`Pambaram.exe`)** and **Linux (`Pambaram`)** executables via PyInstaller directly on GitHub Actions (no Docker).
- Run manually from **Actions -> Build Desktop Release Binaries -> Run workflow**, or push a version tag:
  ```bash
  git tag v1.1.0
  git push origin v1.1.0
  ```

---

## Verification & Troubleshooting

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| Browser shows `Click or tap to start Pambaram!` | Browser Autoplay Policy (Pygbag UME gate) | Expected behavior—one click/tap unlocks Web Audio and launches the game. |
| No audio in browser | Audio hardware unavailable or raw PCM rejected | `SoundManager` automatically falls back to WAV-in-memory and never crashes; press **`M`** to verify sound isn't muted. |
| Right-click opens browser menu | Testing outside `web/pambaram.tmpl` | Build via `python scripts/stage_web.py`, which passes `--template web/pambaram.tmpl` containing the `contextmenu` guard. |
| Missing `build_src/pambaram/build/web/pambaram.tar.gz` | Deploying `web.zip` to GitHub/Cloudflare/HF Pages | Only itch.io uses `web.zip`/`.apk`. Static web hosts must serve the full `build_src/pambaram/build/web/` folder. |
| Local desktop tests | Verify before pushing | Run `python tests/test_ui.py && python tests/test_integration.py && python tests/test_match_flow.py && python tests/test_production.py && python tests/test_web_deploy.py`. |
