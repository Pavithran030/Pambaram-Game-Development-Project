# 🎯 Pambaram: The Spinning Top Battle Arena
## 2D Game Development Plan & Design Document

---

## 1. Game Overview

| Field | Details |
|-------|---------|
| **Game Title** | Pambaram: Spinning Top Battle Arena |
| **Genre** | Arcade / Physics-Based Action |
| **Platform** | PC (Web/Standalone) |
| **Engine** | Unity 2D / Godot / Pygame (student-friendly) |
| **Perspective** | Top-Down 2D |
| **Target Audience** | Casual gamers, students, nostalgia seekers |
| **Play Time** | 2-5 minutes per match |
| **Inspiration** | Traditional Indian Pambaram (பம்பரம்), Beyblade, SpinTops |

### Core Concept
Players control spinning tops in an enclosed arena. Using physics-based momentum, spin force, and strategic strikes, players must knock opponents' tops out of the ring or deplete their spin energy to win.

---

## 2. Game Mechanics

### 2.1 Core Loop
```
[Launch Top] → [Spin & Maneuver] → [Collide & Attack] → [Win/Lose] → [Next Round]
```

### 2.2 Player Actions
| Action | Input | Description |
|--------|-------|-------------|
| **Launch** | Hold & Release / Drag & Flick | Set initial spin speed and direction |
| **Steer** | WASD / Arrow Keys | Apply slight directional force while spinning |
| **Special Move** | Spacebar (when meter full) | Activate unique top ability |
| **Dash** | Shift + Direction | Brief speed burst, consumes spin energy |

### 2.3 Physics System

#### Spin Physics
- **Angular Velocity**: Determines top's rotation speed (RPM)
- **Friction**: Gradually reduces angular velocity over time
- **Precession**: Slight wobble as spin decreases (visual feedback)
- **Momentum Transfer**: Collision physics based on mass × velocity

#### Movement Physics
- **Centrifugal Force**: Faster spin = harder to change direction
- **Gyroscopic Stability**: High spin = stable, low spin = wobbly/uncontrollable
- **Arena Boundary**: Bounce off walls with energy loss
- **Knockout Zone**: Ring-out area outside the main arena circle

### 2.4 Win Conditions
1. **Ring Out** — Push opponent outside the arena boundary
2. **Spin Out** — Reduce opponent's spin to zero (they "die" from wobbling)
3. **Time Out** — Player with highest remaining spin energy wins

---

## 3. Game Modes

### 3.1 Single Player
| Mode | Description |
|------|-------------|
| **Campaign** | Progress through villages, unlock new tops and arenas |
| **Survival** | Endless waves of AI opponents |
| **Tutorial** | Learn mechanics step-by-step |
| **Time Trial** | Maximize spin time in a solo arena |

### 3.2 Multiplayer
| Mode | Players | Description |
|------|---------|-------------|
| **1v1 Duel** | 2 | Classic knockout battle |
| **Battle Royale** | 4-8 | Last top standing wins |
| **Team Battle** | 2v2 / 3v3 | Cooperative team matches |
| **Tournament** | 8 | Bracket-style elimination |

---

## 4. Top (Character) System

### 4.1 Top Attributes
```
Top Profile:
├── Name: "Velu Vettaikaran"
├── Type: Attack / Defense / Balance / Speed
├── Mass: 1.0 - 5.0 (affects collision momentum)
├── Spin Speed: 1.0 - 5.0 (base RPM)
├── Spin Decay: 1.0 - 5.0 (how fast spin reduces)
├── Grip: 1.0 - 5.0 (traction on arena surface)
├── Special Ability: Unique power move
└── Rarity: Common / Rare / Epic / Legendary
```

### 4.2 Top Types

#### ⚔️ Attack Type
- High mass, fast spin decay
- Strong collision damage
- Special: "Ram Strike" — Dash with 2x damage

#### 🛡️ Defense Type
- Heavy mass, slow spin, low decay
- Resistant to knockback
- Special: "Iron Wall" — Temporary invincibility + reflect

#### ⚖️ Balance Type
- Average stats across all attributes
- Special: "Spin Boost" — Instantly restore 30% spin energy

#### 💨 Speed Type
- Light mass, high spin speed, fast decay
- Agile movement, quick direction changes
- Special: "Whirlwind" — Spin rapidly creating a vacuum that pulls enemies

### 4.3 Top Customization
- **Tip Material**: Wood (grip↑), Metal (mass↑), Ceramic (speed↑)
- **Body Shape**: Classic round, pointed, flat, spiked
- **Paint/Skin**: Unlockable visual themes (village art, neon, metallic)
- **Weight Distribution**: Customizable stat sliders (within type limits)

---

## 5. Arena (Level) Design

### 5.1 Arena Structure
```
Arena Layout:
┌─────────────────────────────┐
│    [Knockout Zone - Void]   │
│   ┌─────────────────────┐   │
│   │   [Main Arena]      │   │
│   │  ○ ○ ○ ○ ○ ○ ○     │   │
│   │  ○ ○ ○ ○ ○ ○ ○     │   │
│   │  ○ ○ ○ ○ ○ ○ ○     │   │
│   │  ○ ○ ○ ○ ○ ○ ○     │   │
│   └─────────────────────┘   │
│    [Knockout Zone - Void]   │
└─────────────────────────────┘
```

### 5.2 Arena Types

| Arena Name | Theme | Special Feature |
|------------|-------|-----------------|
| **Village Ground** | Rural Tamil Nadu | Flat, no hazards — pure skill |
| **Temple Courtyard** | Ancient temple | Pillars in center as obstacles |
| **River Bed** | Sandy terrain | Low grip, tops slide more |
| **Market Square** | Crowded bazaar | Moving NPCs as obstacles |
| **Neon Arena** | Cyberpunk | Speed boost zones |
| **Volcanic Ring** | Lava theme | Outer ring deals damage over time |
| **Ice Rink** | Frozen lake | Ultra-low grip, slippery physics |
| **Storm Platform** | Rainy rooftop | Wind gusts push tops randomly |

### 5.3 Hazards & Power-ups
| Element | Effect |
|---------|--------|
| 🌀 Spin Boost Pad | +20% spin energy on contact |
| ⚡ Speed Zone | 2x movement speed for 3 seconds |
| 🧲 Magnet Zone | Pulls tops toward center |
| 🌪️ Whirlwind | Random directional force |
| 🪨 Rock Obstacle | Bounce off with energy loss |

---

## 6. AI System (Single Player)

### 6.1 AI Difficulty Levels
| Level | Behavior |
|-------|----------|
| **Easy** | Random movement, poor collision timing, no special moves |
| **Medium** | Basic targeting, uses special occasionally, decent defense |
| **Hard** | Predictive movement, combo attacks, optimal special timing |
| **Expert** | Perfect physics calculation, feints, corner trapping |

### 6.2 AI States (State Machine)
```
[Idle] → [Approach] → [Attack] → [Retreat] → [Defend] → [Special]
   ↑                                              |
   └──────────────────[Recover]←───────────────────┘
```

### 6.3 AI Behaviors
- **Aggressor**: Charges directly at player
- **Defender**: Circles arena edge, waits for player to make mistakes
- **Opportunist**: Targets weakened tops in multiplayer
- **Trapper**: Tries to corner opponent near edges

---

## 7. UI/UX Design

### 7.1 HUD Elements
```
┌──────────────────────────────────────────────────┐
│  [P1 Health/Spin]          [P2 Health/Spin]     │
│  ████████░░ 85%            ██████░░░░ 60%       │
│  [Special: READY]          [Special: CHARGING]  │
│                                                  │
│           ┌──────────────┐                      │
│           │   ARENA      │                      │
│           │   (Game)     │                      │
│           └──────────────┘                      │
│                                                  │
│  [Timer: 02:45]    [Combo: x3]   [Score: 1200] │
└──────────────────────────────────────────────────┘
```

### 7.2 Screens
1. **Main Menu** — Logo, Play, Options, Credits
2. **Top Selection** — Grid of unlocked tops with stats preview
3. **Arena Selection** — Map of available arenas
4. **Gameplay HUD** — Real-time stats, minimap
5. **Pause Menu** — Resume, Restart, Settings, Quit
6. **Victory/Defeat** — Stats summary, rewards, next match
7. **Upgrade Screen** — Spend coins to improve top stats

---

## 8. Audio Design

### 8.1 Sound Effects
| Event | SFX Description |
|-------|-----------------|
| Launch | "Whirrrrr!" — spinning start sound |
| Collision | "Clack!" — wood/metal impact |
| Spin Decay | Gradual pitch drop — "wheee→wheee→whee" |
| Ring Out | "Whoosh + thud" — falling out |
| Special Move | Unique sound per ability |
| Victory | Traditional Tamil drum beat (Thavil) |
| Defeat | Spin dying out + crowd "aww" |

### 8.2 Music
- **Menu**: Traditional South Indian folk melody (Nadaswaram inspired)
- **Gameplay**: Upbeat percussion-driven track
- **Boss Battle**: Intense, fast-paced traditional drums
- **Victory**: Triumphant fanfare

---

## 9. Art Style

### 9.1 Visual Direction
- **Style**: Hand-drawn 2D with slight cel-shading
- **Color Palette**: Warm earthy tones (browns, reds, golds) + vibrant top colors
- **Animation**: Frame-by-frame spin rotation, squash & stretch on collisions
- **Particle Effects**: Dust clouds on launch, spark on collision, spin trail

### 9.2 Sprite Requirements
| Asset | Count | Notes |
|-------|-------|-------|
| Tops (base) | 20+ | 8 directions × 4 rarity tiers |
| Tops (spinning) | 20+ | Rotating animation frames |
| Arenas | 8 | Background + foreground layers |
| UI Elements | 50+ | Buttons, bars, icons, frames |
| Effects | 30+ | Dust, sparks, trails, explosions |
| Characters (spectators) | 16 | 4 per arena, idle animations |

---

## 10. Technical Architecture

### 10.1 Game Engine Choice

#### Option A: Unity 2D (Recommended)
- **Pros**: Excellent physics (Box2D), huge community, C# scripting, asset store
- **Cons**: Steeper learning curve, heavier build size
- **Best For**: Polished final submission with rich features

#### Option B: Godot
- **Pros**: Lightweight, free, GDScript is easy, built-in 2D is excellent
- **Cons**: Smaller community, fewer tutorials
- **Best For**: Quick development, open-source preference

#### Option C: Pygame (Python)
- **Pros**: Extremely simple, great for learning, Python familiarity
- **Cons**: No built-in physics, manual collision, performance limits
- **Best For**: Prototype or if Python is required by subject

### 10.2 Core Systems Architecture
```
GameManager (Singleton)
├── StateMachine (Menu, Playing, Paused, GameOver)
├── PhysicsManager
│   ├── SpinPhysics (angular velocity, friction, precession)
│   ├── CollisionHandler (momentum transfer, knockback)
│   └── BoundaryManager (arena limits, ring-out detection)
├── InputManager
│   ├── LaunchSystem (drag/hold mechanics)
│   ├── MovementController (WASD steering)
│   └── SpecialAbilityTrigger
├── AIManager (for single player)
│   ├── StateMachine (Idle, Approach, Attack, Retreat)
│   └── Pathfinding (simple vector-based)
├── UIManager
│   ├── HUDController
│   ├── MenuNavigation
│   └── AnimationController
├── AudioManager
├── SaveLoadManager (progress, unlocks, settings)
└── SceneManager (arena loading, transitions)
```

### 10.3 Key Classes/Scripts

```csharp
// Unity C# Example Structure

public class TopController : MonoBehaviour {
    // Physics Properties
    public float mass = 2.0f;
    public float spinSpeed = 1000f;      // Current RPM
    public float maxSpinSpeed = 2000f;
    public float spinDecayRate = 50f;    // RPM lost per second
    public float grip = 1.0f;            // Traction coefficient

    // State
    public bool isSpinning = false;
    public bool isKnockedOut = false;
    public float specialMeter = 0f;      // 0-100

    // Components
    private Rigidbody2D rb;
    private TopType topType;
    private SpecialAbility specialAbility;

    void Update() {
        ApplySpinDecay();
        UpdateVisualWobble();
        CheckKnockoutCondition();
    }

    void ApplySpinDecay() {
        spinSpeed -= spinDecayRate * Time.deltaTime;
        if (spinSpeed <= 0) {
            spinSpeed = 0;
            isSpinning = false;
            OnSpinDepleted();
        }
    }

    void OnCollisionEnter2D(Collision2D collision) {
        TopController otherTop = collision.gameObject.GetComponent<TopController>();
        if (otherTop != null) {
            ResolveCollision(otherTop, collision);
        }
    }

    void ResolveCollision(TopController other, Collision2D collision) {
        // Momentum-based knockback calculation
        float myMomentum = mass * rb.velocity.magnitude * (spinSpeed / maxSpinSpeed);
        float otherMomentum = other.mass * other.rb.velocity.magnitude * (other.spinSpeed / other.maxSpinSpeed);

        Vector2 knockbackDir = (transform.position - other.transform.position).normalized;

        if (myMomentum > otherMomentum) {
            other.rb.AddForce(knockbackDir * (myMomentum - otherMomentum) * 2f, ForceMode2D.Impulse);
            other.spinSpeed -= myMomentum * 0.1f; // Spin damage
        }
    }

    public void Launch(Vector2 direction, float force, float initialSpin) {
        rb.AddForce(direction * force, ForceMode2D.Impulse);
        spinSpeed = initialSpin;
        isSpinning = true;
    }

    public void ActivateSpecial() {
        if (specialMeter >= 100f) {
            specialAbility.Execute(this);
            specialMeter = 0f;
        }
    }
}
```

### 10.4 Data Flow
```
Player Input → InputManager → TopController → PhysicsManager → Render
     ↓              ↓              ↓              ↓
  UI Update ← GameManager ← CollisionEvent ← AudioManager
```

---

## 11. Development Roadmap

### Phase 1: Core Prototype (Week 1-2)
- [ ] Set up project (Unity/Godot/Pygame)
- [ ] Basic top sprite + rotation animation
- [ ] Launch mechanic (click & drag / hold & release)
- [ ] Basic physics (spin decay, movement, friction)
- [ ] Simple circular arena with boundary
- [ ] 1v1 local multiplayer (2 players on same keyboard)
- [ ] Win condition (ring out or spin depletion)

### Phase 2: Gameplay Polish (Week 3-4)
- [ ] Collision system with momentum transfer
- [ ] Top types (Attack, Defense, Balance, Speed)
- [ ] Special abilities for each type
- [ ] Dash mechanic
- [ ] Basic AI opponent (3 difficulty levels)
- [ ] Single player vs AI mode
- [ ] Score system & timer

### Phase 3: Content & Progression (Week 5-6)
- [ ] Top selection screen with 8+ tops
- [ ] Top stats system & customization
- [ ] 4+ unique arenas with themes
- [ ] Arena hazards & power-ups
- [ ] Campaign mode (6-10 levels)
- [ ] Survival mode
- [ ] Unlock system (coins, achievements)

### Phase 4: UI, Audio & Polish (Week 7-8)
- [ ] Complete UI system (menus, HUD, transitions)
- [ ] All sound effects & music
- [ ] Particle effects (dust, sparks, trails)
- [ ] Screen shake on heavy collisions
- [ ] Visual polish (lighting, post-processing)
- [ ] Tutorial system
- [ ] Settings (volume, controls, graphics)

### Phase 5: Testing & Submission (Week 9)
- [ ] Bug fixing & balance tuning
- [ ] Performance optimization
- [ ] Build & packaging
- [ ] Documentation & presentation
- [ ] Playtesting with friends/classmates

---

## 12. Asset List

### 12.1 Required Assets
| Category | Item | Priority | Source |
|----------|------|----------|--------|
| **Sprites** | Top base (4 types × 4 colors) | High | Create custom |
| **Sprites** | Arena backgrounds (4) | High | Create custom |
| **Sprites** | UI elements (buttons, bars) | High | Create custom / Kenney Assets |
| **Animation** | Spin rotation (8 frames) | High | Create custom |
| **Animation** | Wobble/dying animation | Medium | Create custom |
| **Animation** | Launch dust effect | Medium | Create custom |
| **SFX** | Spin sounds (looping) | High | Freesound.org / Bfxr |
| **SFX** | Collision sounds | High | Freesound.org / Bfxr |
| **SFX** | UI sounds | Medium | Freesound.org |
| **Music** | Menu theme | Medium | Freesound.org / compose |
| **Music** | Battle theme | Medium | Freesound.org / compose |
| **Font** | Tamil/Indian style display font | Low | Google Fonts (Ponnala) |

### 12.2 Free Resources
- **Sprites**: OpenGameArt.org, Kenney.nl
- **SFX**: Freesound.org, Bfxr (generator)
- **Music**: Freesound.org, Incompetech (Kevin MacLeod)
- **Fonts**: Google Fonts, FontSquirrel

---

## 13. Scoring & Progression

### 13.1 Scoring System
| Action | Points |
|--------|--------|
| Win match | 100 |
| Perfect win (no damage) | +50 bonus |
| Fast win (<30 seconds) | +25 bonus |
| Ring out opponent | +20 bonus |
| Special move KO | +15 bonus |
| Survival wave cleared | 50 × wave number |

### 13.2 Currency & Upgrades
- **Coins**: Earned from matches, used for upgrades
- **Upgrade Types**:
  - Mass (+0.2 per level, max +1.0)
  - Spin Speed (+5% per level, max +25%)
  - Spin Decay (-5% per level, max -25%)
  - Grip (+0.1 per level, max +0.5)

---

## 14. Testing Plan

### 14.1 Test Cases
| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T01 | Launch top with max drag | Top spins at max RPM, moves in drag direction |
| T02 | Two tops collide head-on | Momentum transfer, both deflect, spin reduces |
| T03 | Heavy top vs light top | Heavy top pushes light top significantly |
| T04 | Top hits arena edge | Bounces back with energy loss |
| T05 | Top crosses boundary | "Ring Out" triggered, opponent wins |
| T06 | Spin reaches zero | Top stops, wobble animation, player loses |
| T07 | Special meter fills | Meter UI updates, special becomes usable |
| T08 | Activate special | Ability executes, meter resets to 0 |
| T09 | AI on Easy difficulty | AI moves randomly, easy to defeat |
| T10 | AI on Hard difficulty | AI uses tactics, challenging to defeat |

### 14.2 Balance Checklist
- [ ] No single top type dominates all others
- [ ] All arenas feel fair for all top types
- [ ] Special abilities feel powerful but not game-breaking
- [ ] Difficulty curve is gradual in campaign
- [ ] Controls feel responsive and intuitive

---

## 15. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Physics feels unfun | Medium | High | Prototype early, iterate on feel |
| Scope too large | High | High | Cut features if needed, focus on core loop |
| Art takes too long | Medium | Medium | Use placeholders, prioritize gameplay |
| Performance issues | Low | Medium | Optimize physics, limit particle count |
| Multiplayer networking | Low | High | Stick to local multiplayer / AI only |

---

## 16. Submission Checklist

- [ ] **Executable Build** (.exe / .apk / WebGL)
- [ ] **Source Code** (well-commented)
- [ ] **Game Design Document** (this file)
- [ ] **Gameplay Video** (2-3 minutes)
- [ ] **Screenshots** (menu, gameplay, victory)
- [ ] **README** (how to play, controls, features)
- [ ] **Presentation** (PPT / PDF explaining your game)

---

## 17. Appendix

### 17.1 Glossary
- **Pambaram**: Traditional Tamil spinning top toy
- **RPM**: Revolutions per minute (spin speed)
- **Precession**: The wobbling motion of a spinning object
- **Gyroscopic Effect**: Stability provided by spinning mass
- **Ring Out**: Knocking opponent outside the arena

### 17.2 Reference Games
- Beyblade (console/PC games)
- SpinTops (mobile)
- Lethal Racing (top-down physics)
- Rocket League (momentum-based collision)

### 17.3 Tamil Cultural Elements to Include
- Arena names in Tamil (e.g., "Gramam Thidal" — Village Ground)
- Traditional top designs (wooden, nail-tipped)
- Folk music inspired soundtrack
- Spectator NPCs in veshti/saree
- Festival atmosphere (Pongal/Jallikattu vibes)

---

*Document Version: 1.0*
*Created for: Game Development Subject Project*
*Game: Pambaram — 2D Spinning Top Battle Arena*
