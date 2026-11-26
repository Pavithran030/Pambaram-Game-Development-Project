# Pambaram: Spinning Top Battle Arena

A 2D physics-based spinning top battle game built with Python and Pygame,
inspired by the traditional Tamil Pambaram (பம்பரம்) toy and games like Beyblade.

---

## Quick Start

### Method 1: One-click Install & Run
1. **Double-click `install.bat`** to install dependencies (runs once).
2. **Double-click `run_game.bat`** to start playing!

### Method 2: Command Line
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the game
python main.py
```

### Method 3: Play or Deploy Online (Free)
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete step-by-step instructions to run and deploy the game online for free via **GitHub Pages** (Pygbag WebAssembly), **itch.io**, **Cloudflare Pages**, or **Hugging Face Spaces**.

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| Python      | 3.8+    |
| Pygame    | 2.5.0+  |
| OS        | Windows 10/11, Linux, macOS |
| RAM       | 512 MB  |
| Display   | 1200×800 minimum |

---

## How to Play

### Objective
Knock your opponent's spinning top **out of the arena (Ring Out)**
or **deplete their spin energy (Spin Out)**.
If the 3-minute timer runs out, whoever has the most spin wins.

### Game Modes
- **QUICK MATCH (vs AI)** - Fight the computer opponent
- **VS PLAYER** - 2 players on the same keyboard
- **TOURNAMENT SETUP** - Pick your tops and arena

### Controls

#### Match start
Every match opens with a **3-2-1 countdown**. During it each player:
1. **Aims** — an arrow shows where the top will fly.
2. **Times the launch** — a power meter swings up and down beside your top. Lock it
   as close to the top (the gold **PERFECT** zone) as you can.

On **FIGHT!** both tops launch at the same moment. Launch perfection decides your
**stamina**: a PERFECT launch starts at 100% spin and drains slowly; a WEAK one starts
around 60% and drains faster. Never locking the meter gives a weak launch.

After launch the stadium behaves like a real bowl: tops keep rolling, curve as they
spin, and drift back toward the centre until their stamina runs out.

#### Player 1 (Blue)
| Action               | Input                          |
|----------------------|--------------------------------|
| Aim launch (countdown) | **A / D**, or **Left Click + Drag** (pull back like a slingshot) |
| Lock launch power    | **SPACE**, or release the left-drag |
| Steer / Move       | **W A S D**                    |
| Dash (speed burst)  | **Left SHIFT + Direction** (costs 8% spin) |

**Playing vs AI:** Player 1 can also use the **arrow keys** to move/aim,
**Right SHIFT** to dash and **ENTER** to lock power.

#### Player 2 (Red) — only in VS PLAYER mode
| Action               | Input                          |
|----------------------|--------------------------------|
| Aim launch (countdown) | **← / →**, or **Right Click + Drag** |
| Lock launch power    | **ENTER** (or Right CTRL), or release the right-drag |
| Steer / Move       | **Arrow Keys ← ↑ ↓ →**     |
| Dash (speed burst)  | **Right SHIFT + Direction** (costs 8% spin) |

#### Global
| Action               | Input                          |
|----------------------|--------------------------------|
| Pause / Resume        | **ESC** (the game also pauses itself if you alt-tab or minimise) |
| Fullscreen            | **F11**                        |
| Mute / unmute sound   | **M**                          |

#### Menus (keyboard)
| Screen        | Keys |
|---------------|------|
| Choose Top    | **ENTER** next · **ESC** back |
| Choose Arena  | **← / →** pick arena · **ENTER** start · **ESC** back |
| Game Over     | **ENTER** / **R** rematch · **ESC** main menu |

#### Telling the tops apart
Each top sits on a coloured floor ring — **blue = Player 1**, **red = Player 2 / AI** —
and every top type has its own silhouette: Attack tops have hooked blades,
Defense tops a heavy studded rim, Balance tops six even lobes, Speed tops thin
swept fins.

#### Saved data
Your last tops, arena, mode, AI difficulty, sound and fullscreen choices are
remembered between sessions, along with lifetime stats (matches, wins, best
score — shown on the main menu). Files live in `%APPDATA%\Pambaram\`
(`~/.pambaram/` on macOS/Linux):
- `settings.json` — settings and stats. Delete it to reset everything; a damaged
  file is ignored automatically.
- `crash.log` — if the game ever hits an unexpected error, it shows a message
  and writes the details here.

#### How to win
- **Ring out** — smash the opponent hard enough that they fly over the rim. A top
  that drives *itself* into the wall just bounces; only a strong hit carries it out.
- **Spin out** — drain the opponent's spin to 0. Hits drain the weaker top more
  (the top ramming into the other, heavier tops and faster-spinning tops win clashes; Attack types hit harder, Defense
  types take less). Wall/pillar bounces and dashes also cost spin.
- **Time up** — after 3:00, the top with the higher spin % wins.

---

## Tops (8 Playable Characters )

### ⚔️ Attack Type
- **Velu Vettaikaran** - High mass, strong collision damage
  - Special: **Ram Strike** - Damage-boosted dash with invincibility
- **Veerapandiya** - Aggressive, devastating strikes

### 🛡️ Defense Type
- **Kottai Veeran** - Heavy, resistant to knockback
  - Special: **Iron Wall** - Temporary invincibility + mass boost
- **Kallazhagar** - Immovable object, extremely slow decay

### ⚖️ Balance Type
- **Thiruvalluvar** - Balanced stats for all situations
  - Special: **Spin Boost** - Instantly restore 40% spin energy
- **Maruthuvar** - Stable and reliable all-rounder

### 💨 Speed Type
- **Puyal Kaalai** - Fast and agile, quick direction changes
  - Special: **Whirlwind** - Pulls enemies toward you
- **Sooravali** - Blazing fast, hardest to control

---

## Arenas (4 Stages)

| Arena (Tamil Name)   | English Name        | Special Feature                         |
|-----------------------|---------------------|---------------------------------------|
| Gramam Thidal       | Village Ground      | Flat, no hazards — pure skill        |
| Kovil Prangaram     | Temple Courtyard  | Stone pillars as obstacles            |
| Aaru Paarai         | River Bed           | Sandy terrain — low grip, more sliding |
| Neon Arangam        | Neon Arena         | Cyberpunk with spin boost pads         |

---

## Project Structure

```
sample1/
├── main.py                    # Entry point shim - puts src/ on the path and runs the game
├── requirements.txt           # Python dependencies
├── install.bat                # Windows installer (double-click)
├── run_game.bat                # Windows game launcher (double-click)
├── .env                        # Game configuration variables
│
├── src/pambaram/                # The game package
│   ├── main.py                # Game Manager: state machine, main loop
│   ├── config.py              # All constants, top/arena presets, colors, enums
│   ├── top.py                 # Top class: physics, spin, movement, specials
│   ├── arena.py                # Arena rendering, collision detection, hazards
│   ├── ai.py                    # AI Controller: state machine & difficulty levels
│   ├── particles.py         # Particle effects: dust, sparks, trails, ring-out
│   ├── ui.py                    # UI Components: buttons, bars, menus, HUD, screens
│   ├── top_art.py              # Procedural top artwork (per-type silhouettes, window icon)
│   ├── settings.py             # Saved settings/stats and crash logging
│   └── sound.py                # Procedurally synthesized SFX (no audio assets needed)
│
├── tests/                        # Automated tests (see "Running Tests")
│   ├── test_logic.py
│   ├── test_ui.py
│   ├── test_integration.py
│   ├── test_match_flow.py      # launch, collisions, ring-out, win rules, controls
│   ├── test_production.py      # save data, crash log, window/menu behaviour, artwork
│   └── test_fuzz.py            # 25,000 frames of random input across every screen
│
└── docs/                         # Design docs & reference screenshots
    ├── Pambaram_Game_Development_Plan.md
    ├── Pambaram_Implementation_Flow_and_Logic.md
    ├── Pambaram_Implementation_Flow_and_Logic_v2.md
    └── screenshots/
```

---

## Win Conditions

1. **Ring Out** - Knock opponent's top completely outside the arena boundary ring
2. **Spin Out** - Reduce opponent's spin energy to 0% (they stop spinning)
3. **Time Out** - When the 3-minute timer ends, higher remaining spin % wins

---

## Physics Features Implemented (from Design Document)

✅ Core Physics
- Spin decay & angular velocity simulation
- Momentum transfer on collisions (mass × velocity)
- Gyroscopic stability (more spin = more maneuverable and stable)
- Arena wall bounce with energy loss
- Ring-out zone detection

✅ Gameplay
- Simultaneous launch: both players aim during the countdown, launch together on FIGHT!
- WASD/Arrow steering with spin-dependent resistance
- Dash moves consuming spin energy
- Collision clashes decided by mass, spin and top type; hard hits can ring out
- 3 AI difficulty levels (Easy / Medium / Hard)
- AI state machine: Idle → Approach → Attack → Retreat → Defend → Special

✅ Visual / FX
- Spin trails with alpha fade
- Screen shake on heavy impacts
- Sparks & dust particles
- Wobble animation as spin dies
- Special move glow effects
- 3-2-1 countdown with aim arrows

✅ UI / UX
- Main Menu, Top Selection, Arena Selection
- Live HUD: spin bars, dash cooldown, timer
- Pause menu, Victory/Defeat screen with stats

---

## Troubleshooting

### Pygame Install Fails?
```bash
# Option 1: Upgrade pip first
python -m pip install --upgrade pip
python -m pip install pygame

# Option 2: User mode install
python -m pip install --user pygame

# Option 3: Using Python launcher
py -m pip install pygame
```

### Permission Denied / Access Error?
- Right-click `install.bat` → **Run as Administrator**

### Game Window Opens Then Closes Immediately?
- Open Command Prompt in the folder and run:
```
python main.py
```
Then read the error message.

---

## Running Tests

```bash
python tests/test_logic.py         # physics / logic
python tests/test_ui.py            # every screen renders
python tests/test_integration.py   # full game-manager flow
python tests/test_match_flow.py    # launch, collisions, ring-out, win rules, controls
python tests/test_production.py    # save data, crash log, window & menu behaviour
python tests/test_fuzz.py          # random-input stress test (takes a few minutes)
```
Each script exits with an error if anything fails. Tests never touch your real
save data.

---

## Development Roadmap Reference

The game implements features from **Phase 1 & 1 (Core Prototype) and **Phase 2 (Gameplay Polish) of the [design document](docs/Pambaram_Game_Development_Plan.md):
- ✅ Phase 1 - Core Prototype (Weeks 1-2)
- ✅ Phase 2 - Gameplay Polish (Weeks 3-4)
- ⬜ Phase 3 - Content & Progression (Weeks 5-6)
- ⬜ Phase 4 - UI, Audio & Polish (Weeks 7-8)
- ⬜ Phase 5 - Testing & Submission (Week 9)

---

## License

Created as a Game Development Subject Project.
Educational use only.
