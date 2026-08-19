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

#### Player 1 (Blue)
| Action               | Input                          |
|----------------------|--------------------------------|
| Launch Top           | **Left Click + Drag** on your top, then release |
| Steer / Move       | **W A S D**                    |
| Dash (speed burst)  | **Left SHIFT + Direction**     |
| Special Ability    | **SPACE** (when meter full)     |

#### Player 2 (Red) — only in VS PLAYER mode
| Action               | Input                          |
|----------------------|--------------------------------|
| Launch Top           | **Right Click + Drag** on P2 top |
| Steer / Move       | **Arrow Keys ← ↑ ↓ →**     |
| Dash (speed burst)  | **Right SHIFT + Direction**    |
| Special Ability    | **ENTER** (when meter full)     |

#### Global
| Action               | Input                          |
|----------------------|--------------------------------|
| Pause / Resume        | **ESC**                        |
| Force AI Launch (debug)| **Middle Mouse Button**         |

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
├── main.py              # Game entry point & Game Manager (state machine, loop)
├── config.py            # All constants, top/arena presets, colors, enums
├── top.py               # Top class: physics, spin, movement, specials
├── arena.py             # Arena rendering, collision detection, hazards
├── ai.py                  # AI Controller: state machine & difficulty levels
├── particles.py     # Particle effects: dust, sparks, trails, ring-out
├── ui.py                  # UI Components: buttons, bars, menus, HUD, screens
├── .env              # Game configuration variables
├── requirements.txt       # Python dependencies
├── install.bat         # Windows installer (double-click)
├── run_game.bat      # Windows game launcher (double-click)
└── Pambaram_Game_Development_Plan.md   # Original design document
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
- Drag & flick launch system with power meter
- WASD/Arrow steering with spin-dependent resistance
- Dash moves consuming spin energy
- 4 unique special abilities per top type
- 3 AI difficulty levels (Easy / Medium / Hard)
- AI state machine: Idle → Approach → Attack → Retreat → Defend → Special

✅ Visual / FX
- Spin trails with alpha fade
- Screen shake on heavy impacts
- Sparks & dust particles
- Wobble animation as spin dies
- Special move glow effects
- 3-2-1 countdown

✅ UI / UX
- Main Menu, Top Selection, Arena Selection
- Live HUD: spin bars, special meters, timer
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

## Development Roadmap Reference

The game implements features from **Phase 1 & 1 (Core Prototype) and **Phase 2 (Gameplay Polish) of the design document:
- ✅ Phase 1 - Core Prototype (Weeks 1-2)
- ✅ Phase 2 - Gameplay Polish (Weeks 3-4)
- ⬜ Phase 3 - Content & Progression (Weeks 5-6)
- ⬜ Phase 4 - UI, Audio & Polish (Weeks 7-8)
- ⬜ Phase 5 - Testing & Submission (Week 9)

---

## License

Created as a Game Development Subject Project.
Educational use only.
