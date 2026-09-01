// ═══════════════════════════════════════
//  PAMBARAM - main.js
//  Game loop, input, state machine (FULLY CORRECTED)
// ═══════════════════════════════════════

class Game {
  constructor() {
    this.canvas   = document.getElementById("gameCanvas");
    this.ctx      = this.canvas.getContext("2d");
    this._resize();
    window.addEventListener("resize", () => this._resize());

    this.state       = GameState.MENU;
    this.p1TopName   = "Thiruvalluvar";
    this.p2TopName   = "Velu Vettaikaran";
    this.arenaKey    = "Gramam Thidal";
    this.p2IsAi      = true;
    this.difficulty  = Difficulty.MEDIUM;

    this.p1          = null;
    this.p2          = null;
    this.arena       = null;
    this.aiCtrl      = null;
    this.particles   = new ParticleSystem();

    this.matchTime   = MATCH_TIME;
    this.matchStarted= false;
    this.countdown   = 3;
    this.cdTimer     = 0;
    this.shakeX      = 0;
    this.shakeY      = 0;
    this.shakeDecay  = 0;

    this.keys        = {};
    this.dragP1      = null;  // {sx,sy,cx,cy}
    this.dragP2      = null;

    // Sound manager
    this.sound = new SoundManager(true);
    // Resume audio on user interaction
    document.addEventListener("click", () => this.sound.resume(), { once: true });
    document.addEventListener("keydown", () => this.sound.resume(), { once: true });

    // Camera system – adjusted for 3D view
    this.cameraX     = -100;
    this.cameraY     = -50;
    this.zoom        = 0.9;
    this.targetZoom  = 0.9;
    this.cameraDrag  = null;
    this.cameraAngle = 0;          // rotation around vertical axis (radians)
    this.cameraRotating = false;
    this.rotStartX = 0;
    this.rotStartAngle = 0;

    // Duel mode fields (manual 2-player)
    this.duelTurn    = 1;
    this.duelTimer   = 0.0;
    this.duelResults = {};
    this.winner      = null;

    this._bindUI();
    this._bindInput();
    this._loop       = this._loop.bind(this);
    this._lastTime   = null;
    requestAnimationFrame(this._loop);
  }

  // ── Canvas scaling ────────────────────────────────
  _resize() {
    const cw = window.innerWidth, ch = window.innerHeight;
    const scale = Math.min(cw / SCREEN_W, ch / SCREEN_H);
    this.canvas.width  = SCREEN_W;
    this.canvas.height = SCREEN_H;
    this.canvas.style.width  = `${SCREEN_W * scale}px`;
    this.canvas.style.height = `${SCREEN_H * scale}px`;
    this.canvas.style.position = "absolute";
    this.canvas.style.left = `${(cw - SCREEN_W*scale)/2}px`;
    this.canvas.style.top  = `${(ch - SCREEN_H*scale)/2}px`;
    this._scale = scale;
  }

  _mapMouse(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (SCREEN_W / rect.width),
      y: (e.clientY - rect.top)  * (SCREEN_H / rect.height),
    };
  }

  // ── UI event bindings ─────────────────────────────
  _bindUI() {
    // Main Menu
    document.getElementById("mBtn-vsai").onclick     = () => { this.p2IsAi = true;  this._goTopSelect(); };
    document.getElementById("mBtn-vsplayer").onclick = () => { this.p2IsAi = false; this._goTopSelect(); };
    document.getElementById("mBtn-difficulty").onclick = () => {
      const cycle = { [Difficulty.EASY]: Difficulty.MEDIUM, [Difficulty.MEDIUM]: Difficulty.HARD, [Difficulty.HARD]: Difficulty.EASY };
      this.difficulty = cycle[this.difficulty];
      document.getElementById("diffLabel").textContent = this.difficulty;
    };

    // Top Select
    document.getElementById("tsBack").onclick = () => { this.state = GameState.MENU; showScreen("screen-menu"); };
    document.getElementById("tsNext").onclick = () => { this.state = GameState.ARENA_SELECT; this._goArenaSelect(); };
    document.getElementById("topGrid").addEventListener("click", e => {
      const card = e.target.closest(".top-card");
      if (card) { this.p1TopName = card.dataset.name; this._refreshTopGrid(); }
    });
    document.getElementById("topGrid").addEventListener("contextmenu", e => {
      e.preventDefault();
      const card = e.target.closest(".top-card");
      if (card) { this.p2TopName = card.dataset.name; this._refreshTopGrid(); }
    });

    // Arena Select
    document.getElementById("asBack").onclick  = () => { this.state = GameState.TOP_SELECT; showScreen("screen-topselect"); };
    document.getElementById("asStart").onclick = () => this._startMatch();
    document.getElementById("arenaGrid").addEventListener("click", e => {
      const card = e.target.closest(".arena-card");
      if (card) { this.arenaKey = card.dataset.key; this._refreshArenaGrid(); }
    });

    // Pause
    document.getElementById("pResume").onclick  = () => { this.state = GameState.PLAYING; showScreen("screen-hud"); };
    document.getElementById("pRestart").onclick = () => this._startMatch();
    document.getElementById("pMenu").onclick    = () => { this.state = GameState.MENU; showScreen("screen-menu"); };

    // Game Over
    document.getElementById("goRematch").onclick = () => this._startMatch();
    document.getElementById("goMenu").onclick    = () => { this.state = GameState.MENU; showScreen("screen-menu"); };
  }

  _bindInput() {
    window.addEventListener("keydown", e => {
      this.keys[e.code] = true;
      if (e.code === "Escape" && this.state === GameState.PLAYING) {
        this.state = GameState.PAUSED;
        showScreen("screen-pause");
      }
      // Special keys (prevent page scroll)
      if (["Space","ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(e.code)) e.preventDefault();
    });
    window.addEventListener("keyup",  e => { this.keys[e.code] = false; });

    // Mouse drag for launching
    this.canvas.addEventListener("mousedown", e => {
      if (this.state !== GameState.PLAYING || !this.matchStarted) return;
      const pos = this._mapMouse(e);
      if (e.button === 0 && this.p1 && !this.p1.isLaunched) {
        this.dragP1 = { sx: pos.x, sy: pos.y, cx: pos.x, cy: pos.y };
      }
      if (e.button === 2 && !this.p2IsAi && this.p2 && !this.p2.isLaunched) {
        this.dragP2 = { sx: pos.x, sy: pos.y, cx: pos.x, cy: pos.y };
      }
    });
    this.canvas.addEventListener("mousemove", e => {
      const pos = this._mapMouse(e);
      if (this.dragP1) { this.dragP1.cx = pos.x; this.dragP1.cy = pos.y; }
      if (this.dragP2) { this.dragP2.cx = pos.x; this.dragP2.cy = pos.y; }
    });
    this.canvas.addEventListener("mouseup", e => {
      if (e.button === 0 && this.dragP1) { this._releaseLaunch(this.p1, this.dragP1); this.dragP1 = null; }
      if (e.button === 2 && this.dragP2) { this._releaseLaunch(this.p2, this.dragP2); this.dragP2 = null; }
    });
    this.canvas.addEventListener("contextmenu", e => e.preventDefault());

    // Camera drag (on empty space – not on a top) – left button for pan
    this.canvas.addEventListener("mousedown", e => {
      if (this.state !== GameState.PLAYING) return;
      const pos = this._mapMouse(e);
      // Check if click is on a top (P1 or P2)
      const onTop = (this.p1 && Math.hypot(pos.x - this.p1.x, pos.y - this.p1.y) < this.p1.radius + 15) ||
                    (this.p2 && Math.hypot(pos.x - this.p2.x, pos.y - this.p2.y) < this.p2.radius + 15);
      // Left button: pan
      if (e.button === 0 && !onTop) {
        this.cameraDrag = {
          startX: pos.x,
          startY: pos.y,
          camStartX: this.cameraX,
          camStartY: this.cameraY
        };
      }
      // Middle button: rotate
      if (e.button === 1 && !onTop) {
        this.cameraRotating = true;
        this.rotStartX = pos.x;
        this.rotStartAngle = this.cameraAngle;
        e.preventDefault(); // prevent default middle-button scroll
      }
    });
    this.canvas.addEventListener("mousemove", e => {
      const pos = this._mapMouse(e);
      if (this.dragP1) { this.dragP1.cx = pos.x; this.dragP1.cy = pos.y; }
      if (this.dragP2) { this.dragP2.cx = pos.x; this.dragP2.cy = pos.y; }
      if (this.cameraDrag) {
        const dx = pos.x - this.cameraDrag.startX;
        const dy = pos.y - this.cameraDrag.startY;
        this.cameraX = this.cameraDrag.camStartX + dx;
        this.cameraY = this.cameraDrag.camStartY + dy;
      }
      if (this.cameraRotating) {
        const dx = pos.x - this.rotStartX;
        // map horizontal movement to angle change (sensitivity)
        const sensitivity = 0.005;
        this.cameraAngle = this.rotStartAngle + dx * sensitivity;
      }
    });
    this.canvas.addEventListener("mouseup", e => {
      if (e.button === 0 && this.dragP1) { this._releaseLaunch(this.p1, this.dragP1); this.dragP1 = null; }
      if (e.button === 2 && this.dragP2) { this._releaseLaunch(this.p2, this.dragP2); this.dragP2 = null; }
      if (e.button === 0 && this.cameraDrag) { this.cameraDrag = null; }
      if (e.button === 1 && this.cameraRotating) { this.cameraRotating = false; }
    });
    // Zoom with mouse wheel
    this.canvas.addEventListener("wheel", e => {
      e.preventDefault();
      if (this.state !== GameState.PLAYING) return;
      const delta = e.deltaY > 0 ? -0.1 : 0.1;
      this.targetZoom = Math.max(0.3, Math.min(2.5, this.targetZoom + delta));
    }, { passive: false });
    // Prevent context menu on middle-click
    this.canvas.addEventListener("contextmenu", e => e.preventDefault());

    // Touch: P1 single-touch launch
    this.canvas.addEventListener("touchstart", e => {
      e.preventDefault();
      if (this.state !== GameState.PLAYING || !this.matchStarted) return;
      const t = e.changedTouches[0];
      const pos = this._mapMouse(t);
      if (this.p1 && !this.p1.isLaunched)
        this.dragP1 = { sx: pos.x, sy: pos.y, cx: pos.x, cy: pos.y };
    }, { passive: false });
    this.canvas.addEventListener("touchmove", e => {
      e.preventDefault();
      if (!this.dragP1) return;
      const pos = this._mapMouse(e.changedTouches[0]);
      this.dragP1.cx = pos.x; this.dragP1.cy = pos.y;
    }, { passive: false });
    this.canvas.addEventListener("touchend", e => {
      if (this.dragP1) { this._releaseLaunch(this.p1, this.dragP1); this.dragP1 = null; }
    });
  }

  _releaseLaunch(top, drag) {
    const dx   = drag.sx - drag.cx;
    const dy   = drag.sy - drag.cy;
    const dist = Math.hypot(dx, dy);
    if (dist > 8) {
      const force  = Math.min(900, dist * 4.5 + 200);
      const factor = Math.min(1.0, 0.5 + dist / 400);
      top.launch(dx / dist, dy / dist, force, factor);
      this.sound.play("launch");
    }
  }

  // ── Navigation helpers ────────────────────────────
  _goTopSelect() {
    this.state = GameState.TOP_SELECT;
    const p2LabelEl = document.getElementById("p2Label");
    if (p2LabelEl) p2LabelEl.textContent = this.p2IsAi ? "AI: " : "P2: ";
    this._refreshTopGrid();
    showScreen("screen-topselect");
  }

  _refreshTopGrid() {
    buildTopGrid(document.getElementById("topGrid"), this.p1TopName, this.p2TopName);
    const p1El = document.getElementById("p1PickName");
    const p2El = document.getElementById("p2PickName");
    if (p1El) p1El.textContent = this.p1TopName;
    if (p2El) p2El.textContent = this.p2TopName;
  }

  _goArenaSelect() {
    this._refreshArenaGrid();
    showScreen("screen-arenaselect");
  }

  _refreshArenaGrid() {
    buildArenaGrid(document.getElementById("arenaGrid"), this.arenaKey);
  }

  // ── Match lifecycle ───────────────────────────────
  _startMatch() {
    this.p1 = new Top(this.p1TopName, TOP_PRESETS[this.p1TopName], 1, false, this.difficulty);
    this.p2 = new Top(this.p2TopName, TOP_PRESETS[this.p2TopName], 2, this.p2IsAi, this.difficulty);
    this.arena    = new Arena(this.arenaKey);
    this.aiCtrl   = this.p2IsAi ? new AIController(this.p2, this.difficulty) : null;
    this.particles= new ParticleSystem();

    this.matchTime    = MATCH_TIME;
    this.matchStarted = false;
    this.countdown    = 3;
    this.cdTimer      = 0;
    this.shakeX = this.shakeY = this.shakeDecay = 0;

    // Reset duel fields
    this.duelTurn    = 1;
    this.duelTimer   = 0.0;
    this.duelResults = {};
    this.winner      = null;

    // Update HUD labels
    document.getElementById("hudP1Name").textContent = `P1: ${this.p1.name}`;
    document.getElementById("hudP2Name").textContent = `${this.p2IsAi?"AI":"P2"}: ${this.p2.name}`;
    document.getElementById("hudP1Type").textContent = this.p1.type;
    document.getElementById("hudP2Type").textContent = this.p2.type;

    this.state = GameState.PLAYING;
    showScreen("screen-hud");
    showCountdown(this.countdown);
    setLaunchHint("Drag your top to LAUNCH!");
  }

  _applyShake(strength) {
    this.shakeDecay = Math.max(this.shakeDecay, strength * 0.3);
    const angle = Math.random() * Math.PI * 2;
    this.shakeX = Math.cos(angle) * strength;
    this.shakeY = Math.sin(angle) * strength;
  }

  _updateShake(dt) {
    if (this.shakeDecay > 0) {
      this.shakeDecay -= dt * 20;
      if (this.shakeDecay <= 0) { this.shakeX = this.shakeY = 0; this.shakeDecay = 0; }
      else {
        const angle = Math.random() * Math.PI * 2;
        this.shakeX = Math.cos(angle) * this.shakeDecay;
        this.shakeY = Math.sin(angle) * this.shakeDecay;
      }
    }
  }

  // ── Main Loop ─────────────────────────────────────
  _loop(ts) {
    const dt = this._lastTime !== null ? Math.min((ts - this._lastTime) / 1000, 0.05) : 1/60;
    this._lastTime = ts;
    this._update(dt);
    this._draw();
    requestAnimationFrame(this._loop);
  }

  _update(dt) {
    if (this.state !== GameState.PLAYING) return;

    // Smooth zoom
    this.zoom += (this.targetZoom - this.zoom) * 0.1;

    // Countdown
    if (!this.matchStarted) {
      this.cdTimer += dt;
      if (this.cdTimer >= 0.9) {
        this.cdTimer = 0;
        this.countdown--;
        if (this.countdown < 0) {
          this.matchStarted = true;
          showCountdown(null);
          if (this.p2IsAi && this.p2 && !this.p2.isLaunched)
            this.p2.launch(-1, 0, 700, 0.9);
        } else {
          showCountdown(this.countdown === 0 ? 0 : this.countdown);
        }
      }
      return;
    }

    this.matchTime -= dt;

    // ── P1 keyboard controls ──
    if (this.p1 && this.p1.isLaunched && !this.p1.isKnockedOut) {
      const sx = (this.keys["KeyD"]?1:0) - (this.keys["KeyA"]?1:0);
      const sy = (this.keys["KeyS"]?1:0) - (this.keys["KeyW"]?1:0);
      if (sx || sy) this.p1.steer(sx, sy);
      if (this.keys["ShiftLeft"] && (sx || sy)) {
        if (this.p1.dash(sx, sy)) this.sound.play("dash");
      }
      if (this.keys["Space"]) {
        if (this.p1.activateSpecial([this.p1, this.p2])) {
          this.particles.emitSpecial(this.p1.x, this.p1.y, this.p1.color, 30);
          this._applyShake(5);
          this.sound.play("special");
        }
      }
    }

    // ── P2 keyboard controls (manual) ──
    if (!this.p2IsAi && this.p2 && this.p2.isLaunched && !this.p2.isKnockedOut) {
      const sx = (this.keys["ArrowRight"]?1:0) - (this.keys["ArrowLeft"]?1:0);
      const sy = (this.keys["ArrowDown"]?1:0) - (this.keys["ArrowUp"]?1:0);
      if (sx || sy) this.p2.steer(sx, sy);
      if (this.keys["ControlRight"] && (sx || sy)) {
        if (this.p2.dash(sx, sy)) this.sound.play("dash");
      }
      if (this.keys["Enter"]) {
        if (this.p2.activateSpecial([this.p1, this.p2])) {
          this.particles.emitSpecial(this.p2.x, this.p2.y, this.p2.color, 30);
          this._applyShake(5);
          this.sound.play("special");
        }
      }
    }

    // ── AI update ──
    if (this.aiCtrl && this.p2 && this.p1) {
      const res = this.aiCtrl.update(this.p1, dt);
      if (res && this.p2.isLaunched && !this.p2.isKnockedOut) {
        this.p2.steer(res.steer[0], res.steer[1]);
        if (res.dash) {
          if (this.p2.dash(res.steer[0], res.steer[1])) this.sound.play("dash");
        }
        if (res.special) {
          if (this.p2.activateSpecial([this.p1, this.p2])) {
            this.particles.emitSpecial(this.p2.x, this.p2.y, this.p2.color, 30);
            this._applyShake(5);
            this.sound.play("special");
          }
        }
      }
    }

    // ── Duel mode (manual 2-player) ──
    if (!this.p2IsAi) {
      this._updateDuel(dt);
    }

    // ── Physics ──
    const grip = this.arena ? this.arena.gripMod : 1.0;
    this.p1.update(dt, grip);
    this.p2.update(dt, grip);

    // Boundaries
    if (this.p1.isLaunched) {
      const b1 = this.p1.checkBoundary();
      if (b1 === "bounce") { this._applyShake(4); this.sound.play("collision"); }
      if (b1 === "ringout") { this.particles.emitRingout(this.p1.x, this.p1.y, 40); this._applyShake(10); this.sound.play("ringout"); }
    }
    if (this.p2.isLaunched) {
      const b2 = this.p2.checkBoundary();
      if (b2 === "bounce") { this._applyShake(4); this.sound.play("collision"); }
      if (b2 === "ringout") { this.particles.emitRingout(this.p2.x, this.p2.y, 40); this._applyShake(10); this.sound.play("ringout"); }
    }

    // Top-on-top collision
    if (this.p1.isLaunched && this.p2.isLaunched) {
      const sh = resolveTopCollision(this.p1, this.p2, this.particles);
      if (sh) { this._applyShake(sh); this.sound.play("collision"); }
    }

    // Obstacles & boost pads
    if (this.arena) {
      if (this.p1.isLaunched) {
        const s = checkObstacleCollision(this.p1, this.arena.obstacles);
        if (s) { this._applyShake(s); this.sound.play("collision"); }
        checkBoostPad(this.p1, this.arena.boostPads, this.particles);
      }
      if (this.p2.isLaunched) {
        const s = checkObstacleCollision(this.p2, this.arena.obstacles);
        if (s) { this._applyShake(s); this.sound.play("collision"); }
        checkBoostPad(this.p2, this.arena.boostPads, this.particles);
      }
      this.arena.update(dt);
    }

    // Idle spin particles
    if (this.p1.isSpinning && Math.random() < 0.08)
      this.particles.emitSpin(this.p1.x, this.p1.y, 1, this.p1.color+"99");
    if (this.p2.isSpinning && Math.random() < 0.08)
      this.particles.emitSpin(this.p2.x, this.p2.y, 1, this.p2.color+"99");

    this.particles.update(dt);
    this._updateShake(dt);

    // HUD update
    if (this.p1 && this.p2) updateHUD(this.p1, this.p2, this.matchTime);

    // Launch hint
    const p1Hint = !this.p1.isLaunched ? "P1: Drag to launch" : "";
    const p2Hint = (!this.p2.isLaunched && !this.p2IsAi) ? "P2: Right-drag to launch" : "";
    setLaunchHint([p1Hint, p2Hint].filter(Boolean).join("  |  "));

    this._checkWin();
  }

  // ── Duel mode (manual 2-player) ──
  _updateDuel(dt) {
    if (this.duelTurn === 0) return;
    let activeTop = this.duelTurn === 1 ? this.p1 : this.p2;
    if (!activeTop.isLaunched) return;
    if (activeTop.isSpinning && !activeTop.isKnockedOut) {
      this.duelTimer += dt;
    }
    if ((activeTop.spin <= 0 && !activeTop.isSpinning) || activeTop.isKnockedOut) {
      this.duelResults[this.duelTurn] = this.duelTimer;
      if (this.duelTurn === 1) {
        this.duelTurn = 2;
        this.duelTimer = 0;
        if (!this.p2.isLaunched) {
          const angle = Math.random() * 2 * Math.PI;
          const force = 600 + Math.random() * 300;
          this.p2.launch(Math.cos(angle), Math.sin(angle), force, 0.8 + Math.random() * 0.2);
          this.particles.emitDust(this.p2.x, this.p2.y, 20);
          this.sound.play("launch");
        }
        setLaunchHint("P2's turn!");
      } else {
        this.duelTurn = 0;
        const t1 = this.duelResults[1] || 0;
        const t2 = this.duelResults[2] || 0;
        if (t1 > t2) this.winner = this.p1;
        else if (t2 > t1) this.winner = this.p2;
        else this.winner = null;
        this.matchTime = 0; // force game over
      }
    }
  }

  _checkWin() {
    if (!this.matchStarted) return;
    const bothLaunched = this.p1.isLaunched && this.p2.isLaunched;

    const p1Out  = bothLaunched && this.p1.isKnockedOut && this.p1.knockoutTimer > 1.5;
    const p2Out  = bothLaunched && this.p2.isKnockedOut && this.p2.knockoutTimer > 1.5;
    const p1Dead = bothLaunched && !this.p1.isSpinning && this.p1.spin <= 0 && !this.p1.isKnockedOut;
    const p2Dead = bothLaunched && !this.p2.isSpinning && this.p2.spin <= 0 && !this.p2.isKnockedOut;

    let winner = null, reason = "";

    // If duel mode ended, use stored winner
    if (!this.p2IsAi && this.duelTurn === 0 && this.winner) {
      winner = this.winner;
      reason = `DUEL COMPLETE! ${winner.name} spun longer!`;
    } else if (!this.p2IsAi && this.duelTurn === 0 && !this.winner) {
      reason = "DUEL DRAW — equal spin time!";
    } else {
      // AI mode or simultaneous
      if      (p1Out && !p2Out)  { winner = this.p2; reason = `RING OUT! ${this.p1.name} was knocked out!`; }
      else if (p2Out && !p1Out)  { winner = this.p1; reason = `RING OUT! ${this.p2.name} was knocked out!`; }
      else if (p1Out && p2Out)   {
        winner = this.p1.knockoutTimer < this.p2.knockoutTimer ? this.p1 : this.p2.knockoutTimer < this.p1.knockoutTimer ? this.p2 : null;
        reason = "DOUBLE RING OUT!";
      }
      else if (p1Dead && !p2Dead) { winner = this.p2; reason = `SPIN OUT! ${this.p1.name} ran out of spin!`; }
      else if (p2Dead && !p1Dead) { winner = this.p1; reason = `SPIN OUT! ${this.p2.name} ran out of spin!`; }
      else if (p1Dead && p2Dead)  { winner = null; reason = "DOUBLE SPIN OUT — DRAW!"; }
      else if (this.matchTime <= 0) {
        if (!bothLaunched) {
          if      (this.p1.isLaunched) { winner = this.p1; reason = `TIME UP! ${this.p2.name} never launched!`; }
          else if (this.p2.isLaunched) { winner = this.p2; reason = `TIME UP! ${this.p1.name} never launched!`; }
          else { reason = "TIME UP — DRAW (neither launched)!"; }
        } else {
          const s1 = this.p1.maxSpin > 0 ? this.p1.spin/this.p1.maxSpin : 0;
          const s2 = this.p2.maxSpin > 0 ? this.p2.spin/this.p2.maxSpin : 0;
          if (Math.abs(s1-s2) > 0.02) {
            winner = s1 > s2 ? this.p1 : this.p2;
            reason = `TIME UP! ${winner.name} has more spin!`;
          } else { reason = "TIME UP — EQUAL SPIN, DRAW!"; }
        }
      } else return; // no condition yet
    }

    // If no winner and reason not set, draw
    if (!winner && !reason) {
      reason = "DRAW!";
    }

    // Calculate points
    const elapsed = MATCH_TIME - Math.max(0, this.matchTime);
    let points = 0;
    if (winner) {
      const spinPct = winner.maxSpin > 0 ? (winner.spin / winner.maxSpin) * 100 : 0;
      const timeBonus = Math.max(0, 50 - elapsed * 0.5);
      points = Math.round(spinPct * 0.7 + timeBonus);
    }

    this.state = GameState.GAME_OVER;
    showGameOver(winner, this.p1, this.p2, reason, elapsed, points);
  }

  _draw() {
    const ctx = this.ctx;
    ctx.fillStyle = "#0b0e17";
    ctx.fillRect(0, 0, SCREEN_W, SCREEN_H);

    if (this.state === GameState.PLAYING || this.state === GameState.PAUSED || this.state === GameState.GAME_OVER) {
      ctx.save();
      // Apply camera transform
      ctx.translate(this.cameraX, this.cameraY);
      ctx.scale(this.zoom, this.zoom);

      const sx = this.shakeX, sy = this.shakeY;
      if (this.arena) this.arena.draw(ctx, sx, sy);
      this.particles.draw(ctx);
      if (this.p1) this.p1.draw(ctx, sx, sy);
      if (this.p2) this.p2.draw(ctx, sx, sy);

      // Draw launch drag vector (in camera space)
      if (this.dragP1 && this.p1) this._drawDrag(ctx, this.p1, this.dragP1, "#4294f5");
      if (this.dragP2 && this.p2) this._drawDrag(ctx, this.p2, this.dragP2, "#e64652");

      ctx.restore();
    }
  }

  _drawDrag(ctx, top, drag, color) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(top.x, top.y);
    ctx.lineTo(drag.cx, drag.cy);
    ctx.strokeStyle = color;
    ctx.lineWidth   = 3;
    ctx.setLineDash([8, 6]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Arrowhead in opposite direction (launch direction)
    const dx = top.x - drag.cx, dy = top.y - drag.cy;
    const d  = Math.hypot(dx, dy);
    if (d > 10) {
      const ax = top.x + dx/d*20, ay = top.y + dy/d*20;
      ctx.beginPath();
      ctx.arc(ax, ay, 5, 0, Math.PI*2);
      ctx.fillStyle = color;
      ctx.fill();
    }
    ctx.restore();
  }
}

// ── Bootstrap ─────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => { window._game = new Game(); });