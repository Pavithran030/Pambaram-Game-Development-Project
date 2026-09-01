// ═══════════════════════════════════════
//  PAMBARAM - top.js
//  Top physics class (mirrors Python Top)
// ═══════════════════════════════════════

class Top {
  constructor(name, preset, playerId, isAi = false, difficulty = Difficulty.MEDIUM) {
    this.name      = name;
    this.preset    = preset;
    this.playerId  = playerId;
    this.isAi      = isAi;
    this.difficulty = difficulty;

    this.type      = preset.type;
    this.baseMass  = preset.mass;
    this.mass      = preset.mass;
    this.maxSpin   = preset.spin_speed;
    this.baseMaxSpin = preset.spin_speed;
    this.spinDecay = preset.spin_decay;
    this.baseSpinDecay = preset.spin_decay;
    this.baseGrip  = preset.grip;
    this.grip      = preset.grip;
    this.color     = preset.color;
    this.accent    = preset.accent;
    this.specialName = preset.special;

    this.radius = 22 + (this.mass - 1.8) * 3;

    this.reset();
  }

  reset() {
    this.x = ARENA_CX + (this.playerId === 1 ? -200 : 200);
    this.y = ARENA_CY;
    this.vx = 0; this.vy = 0;
    this.spin = 0;
    this.rotation = Math.random() * Math.PI * 2;
    this.isSpinning    = false;
    this.isLaunched    = false;
    this.isKnockedOut  = false;
    this.knockoutTimer = 0;

    this.specialMeter  = 0;
    this.specialActive = false;
    this.specialTimer  = 0;

    this.dashCooldown = 0;
    this.isDashing    = false;
    this.dashTimer    = 0;

    this.wobble        = 0;
    this.invincible    = false;
    this.invincibleTimer = 0;

    this.steerX = 0;
    this.steerY = 0;
    this.trail  = [];     // [{x,y,r}]

    // restore base stats in case special changed them
    this.mass      = this.baseMass;
    this.grip      = this.baseGrip;
    this.spinDecay = this.baseSpinDecay;
  }

  launch(dirX, dirY, force, spinFactor = 1.0) {
    this.isLaunched  = true;
    this.isSpinning  = true;
    this.spin        = this.maxSpin * Math.min(1, spinFactor);
    this.vx          = dirX * force;
    this.vy          = dirY * force;
  }

  steer(dx, dy) { this.steerX = dx; this.steerY = dy; }

  dash(dx, dy) {
    if (this.dashCooldown > 0 || !this.isSpinning) return false;
    const mag = Math.hypot(dx, dy);
    if (mag === 0) return false;
    this.vx += (dx / mag) * 600;
    this.vy += (dy / mag) * 600;
    this.isDashing    = true;
    this.dashTimer    = 0.25;
    this.dashCooldown = 1.5;
    this.spin         = Math.max(0, this.spin - this.maxSpin * 0.08);
    this.specialMeter = Math.min(100, this.specialMeter + 5);
    return true;
  }

  activateSpecial(allTops) {
    if (this.specialMeter < 100 || !this.isSpinning) return false;
    this.specialMeter  = 0;
    this.specialActive = true;

    if (this.type === TopType.ATTACK) {
      this.specialTimer    = 0.8;
      this.invincible      = true;
      this.invincibleTimer = 0.8;
      const spd = Math.hypot(this.vx, this.vy);
      if (spd > 0) { this.vx *= 2.5; this.vy *= 2.5; }
      else {
        this.vx = Math.cos(this.rotation) * 800;
        this.vy = Math.sin(this.rotation) * 800;
      }
    } else if (this.type === TopType.DEFENSE) {
      this.specialTimer    = 3.0;
      this.invincible      = true;
      this.invincibleTimer = 3.0;
      this.mass = this.baseMass * 2.0;
      this.grip = this.baseGrip * 1.5;
    } else if (this.type === TopType.BALANCE) {
      this.specialTimer = 0.5;
      this.spin = Math.min(this.maxSpin, this.spin + this.maxSpin * 0.4);
    } else if (this.type === TopType.SPEED) {
      this.specialTimer = 2.5;
      this.grip      = this.baseGrip * 0.5;
      this.spinDecay = this.baseSpinDecay * 0.5;
      if (allTops) {
        allTops.forEach(other => {
          if (other !== this && other.isLaunched && !other.isKnockedOut) {
            const dx = this.x - other.x, dy = this.y - other.y;
            const d  = Math.hypot(dx, dy);
            if (d < 250 && d > 0) {
              const pull = (250 - d) * 4;
              other.vx += (dx / d) * pull;
              other.vy += (dy / d) * pull;
            }
          }
        });
      }
    }
    return true;
  }

  _endSpecial() {
    this.mass      = this.baseMass;
    this.grip      = this.baseGrip;
    this.spinDecay = this.baseSpinDecay;
  }

  update(dt, arenaGripMod = 1.0) {
    if (this.isKnockedOut) {
      this.knockoutTimer += dt;
      this.vx *= 0.95;  this.vy *= 0.95;
      this.x  += this.vx * dt;  this.y  += this.vy * dt;
      if (this.spin > 0) this.spin -= this.spinDecay * 3 * dt;
      return;
    }
    if (!this.isLaunched) return;

    const spinRatio = this.maxSpin > 0 ? this.spin / this.maxSpin : 0;

    // Timers
    if (this.specialActive) {
      this.specialTimer -= dt;
      if (this.specialTimer <= 0) { this.specialActive = false; this._endSpecial(); }
    }
    if (this.invincible) {
      this.invincibleTimer -= dt;
      if (this.invincibleTimer <= 0) this.invincible = false;
    }
    if (this.dashCooldown > 0) this.dashCooldown -= dt;
    if (this.isDashing) {
      this.dashTimer -= dt;
      if (this.dashTimer <= 0) this.isDashing = false;
    }

    // Spin decay
    const decayMod = this.isDashing ? 2.5 : 1.0;
    this.spin -= this.spinDecay * decayMod * dt;
    if (this.spin <= 0) { this.spin = 0; this.isSpinning = false; }

    // Wobble
    this.wobble = Math.max(0, (1.0 - spinRatio) * 15);
    if (spinRatio < 0.2)
      this.wobble += Math.sin(performance.now() * 0.02) * (5 - spinRatio * 25);

    // Steering (pure force — no embedded damping, v2 Fix #3)
    const effGrip    = this.grip * arenaGripMod;
    let   steerPower = 250 * effGrip * (0.3 + spinRatio * 0.7);
    if (this.isDashing) steerPower *= 2.5;

    if (this.isSpinning && (this.steerX !== 0 || this.steerY !== 0)) {
      const mag = Math.hypot(this.steerX, this.steerY);
      if (mag > 0) {
        const nx = this.steerX / mag, ny = this.steerY / mag;
        const res = 1.0 + (1.0 - spinRatio) * 0.5;
        this.vx += (nx * steerPower) * dt / res;
        this.vy += (ny * steerPower) * dt / res;
      }
    }

    // Single drag pass (v2 Fix #3)
    const friction = 0.4 * effGrip;
    const spd = Math.hypot(this.vx, this.vy);
    if (spd > 0) {
      const drag     = friction * dt * (1 + (1 - spinRatio) * 0.5);
      const newSpd   = Math.max(0, spd - drag * spd);
      this.vx *= newSpd / spd;
      this.vy *= newSpd / spd;
    }

    // Speed cap
    let maxSpd = 800 * (0.7 + spinRatio * 0.5);
    if (this.type === TopType.SPEED)  maxSpd *= 1.25;
    if (this.isDashing)               maxSpd *= 2.0;
    const curSpd = Math.hypot(this.vx, this.vy);
    if (curSpd > maxSpd) {
      this.vx *= maxSpd / curSpd;
      this.vy *= maxSpd / curSpd;
    }

    this.x += this.vx * dt;
    this.y += this.vy * dt;

    if (this.isSpinning) {
      this.rotation     += spinRatio * 18 * dt;
      this.specialMeter  = Math.min(100, this.specialMeter + spinRatio * 8 * dt);
    }

    // Trail
    this.trail.push({ x: this.x, y: this.y, r: spinRatio });
    if (this.trail.length > 20) this.trail.shift();

    this.steerX = 0; this.steerY = 0;
  }

  checkBoundary() {
    const dx   = this.x - ARENA_CX;
    const dy   = this.y - ARENA_CY;
    const dist = Math.hypot(dx, dy);

    // v2 Fix #2: ring-out recovery
    if (dist <= RINGOUT_R && this.isKnockedOut) {
      this.isKnockedOut  = false;
      this.knockoutTimer = 0;
    }

    if (dist >= RINGOUT_R && !this.isKnockedOut) {
      this.isKnockedOut  = true;
      this.knockoutTimer = 0;
      return "ringout";
    }

    // Bounce zone: only reflect if moving outward (v2 Fix #1)
    if (dist >= ARENA_R && !this.isKnockedOut && dist < RINGOUT_R) {
      const nx  = dx / dist, ny = dy / dist;
      const dot = this.vx * nx + this.vy * ny;
      if (dot > 0) {
        this.vx -= 2 * dot * nx;
        this.vy -= 2 * dot * ny;
        this.vx *= 0.65; this.vy *= 0.65;
        this.spin = Math.max(0, this.spin - this.maxSpin * 0.03);
        const push = ARENA_R - dist - 2;
        if (push < 0) { this.x += nx * push; this.y += ny * push; }
        return "bounce";
      }
    }
    return null;
  }



  draw(ctx, shakeX = 0, shakeY = 0, angle = 0) {
    // Trail in 3D – project trail points using global projectPoint
    for (let i = 0; i < this.trail.length; i++) {
      const pt  = this.trail[i];
      const a   = (i / this.trail.length) * 0.35;
      const p = projectPoint(pt.x + shakeX, pt.y + shakeY, 0, angle);
      ctx.globalAlpha = a;
      ctx.beginPath();
      ctx.ellipse(p.x, p.y, this.radius * 0.6, this.radius * 0.6 * 0.35, 0, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    let z = 0;
    if (this.isKnockedOut) z = -10;
    else if (this.isSpinning) z = this.radius * 0.6 + Math.sin(this.rotation) * 2;
    else z = 2;

    const p = projectPoint(this.x + shakeX, this.y + shakeY, z, angle);
    const sx = p.x;
    const sy = p.y;

    // Wobble offset in 3D
    const wx = this.wobble > 0 ? (Math.random() - 0.5) * this.wobble * 0.5 : 0;
    const wy = this.wobble > 0 ? (Math.random() - 0.5) * this.wobble * 0.5 : 0;

    ctx.save();
    ctx.translate(sx + wx, sy + wy);

    // --- 3D-style top rendering ---

    const r = this.radius;
    const spinRatio = this.maxSpin > 0 ? this.spin / this.maxSpin : 0;

    // 1. Shadow on ground (ellipse) – adjusted for 3D perspective
    ctx.save();
    ctx.translate(0, r * 0.3);
    ctx.scale(1, 0.25);
    ctx.beginPath();
    ctx.arc(0, 0, r * 0.9, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0,0,0,0.3)";
    ctx.fill();
    ctx.restore();

    // 2. Body cone (from wide base to narrow top)
    // Draw a gradient from bottom to top
    const grad = ctx.createLinearGradient(0, -r * 0.8, 0, r * 0.8);
    const c = this.color;
    grad.addColorStop(0, this.accent);       // top highlight
    grad.addColorStop(0.4, c);               // mid tone
    grad.addColorStop(0.8, this._darken(c, 0.3)); // shadow
    grad.addColorStop(1, this._darken(c, 0.5));   // base shadow

    ctx.beginPath();
    ctx.moveTo(0, -r * 0.85);
    ctx.quadraticCurveTo(r * 0.9, -r * 0.3, r * 0.95, r * 0.2);
    ctx.quadraticCurveTo(r * 0.9, r * 0.7, 0, r * 0.85);
    ctx.quadraticCurveTo(-r * 0.9, r * 0.7, -r * 0.95, r * 0.2);
    ctx.quadraticCurveTo(-r * 0.9, -r * 0.3, 0, -r * 0.85);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.strokeStyle = this._darken(c, 0.2);
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 3. Highlight / gloss stripe
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(r * 0.1, -r * 0.6);
    ctx.quadraticCurveTo(r * 0.3, -r * 0.2, r * 0.2, r * 0.2);
    ctx.quadraticCurveTo(r * 0.1, r * 0.5, 0, r * 0.6);
    ctx.strokeStyle = "rgba(255,255,255,0.25)";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();

    // 4. Tip (bottom point)
    ctx.beginPath();
    ctx.moveTo(0, r * 0.85);
    ctx.lineTo(r * 0.2, r * 1.2);
    ctx.lineTo(-r * 0.2, r * 1.2);
    ctx.closePath();
    ctx.fillStyle = this._darken(c, 0.4);
    ctx.fill();
    ctx.strokeStyle = this._darken(c, 0.6);
    ctx.lineWidth = 1;
    ctx.stroke();

    // 5. Spinning blades (4 arms) – rotate with top spin
    ctx.save();
    ctx.translate(0, -r * 0.1);
    ctx.rotate(this.rotation);
    for (let i = 0; i < 4; i++) {
      const angle = i * Math.PI / 2;
      ctx.rotate(angle);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(r * 0.85, 0);
      ctx.strokeStyle = this._lighten(c, 0.4);
      ctx.lineWidth = spinRatio > 0.3 ? 3 : 2;
      ctx.stroke();
      // Blade tip highlight
      if (spinRatio > 0.5) {
        ctx.beginPath();
        ctx.arc(r * 0.85, 0, 2, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.fill();
      }
    }
    ctx.restore();

    // 6. Center hub (metal bearing)
    const hubGrad = ctx.createRadialGradient(0, -r*0.05, 2, 0, 0, r*0.2);
    hubGrad.addColorStop(0, "#f0f0f0");
    hubGrad.addColorStop(0.5, "#c0c0c0");
    hubGrad.addColorStop(1, "#888888");
    ctx.beginPath();
    ctx.arc(0, -r*0.05, r*0.2, 0, Math.PI*2);
    ctx.fillStyle = hubGrad;
    ctx.fill();
    ctx.strokeStyle = "#666";
    ctx.lineWidth = 1;
    ctx.stroke();

    // 7. Top knob (stem)
    ctx.beginPath();
    ctx.moveTo(-r*0.08, -r*0.85);
    ctx.lineTo(r*0.08, -r*0.85);
    ctx.lineTo(r*0.04, -r*1.0);
    ctx.lineTo(-r*0.04, -r*1.0);
    ctx.closePath();
    ctx.fillStyle = this.accent;
    ctx.fill();
    ctx.strokeStyle = this._darken(this.accent, 0.3);
    ctx.lineWidth = 1;
    ctx.stroke();

    // 8. Glow for special active
    if (this.specialActive) {
      ctx.save();
      ctx.shadowColor = this.playerId === 1 ? "#4294f5" : "#e64652";
      ctx.shadowBlur = 30;
      ctx.beginPath();
      ctx.arc(0, 0, r * 1.1, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255,255,255,0.2)";
      ctx.lineWidth = 4;
      ctx.stroke();
      ctx.restore();
    }

    // 9. Invincibility ring
    if (this.invincible) {
      ctx.save();
      ctx.shadowColor = "#ffffff";
      ctx.shadowBlur = 20;
      ctx.beginPath();
      ctx.arc(0, 0, r + 6, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255,255,255,0.6)";
      ctx.lineWidth = 3;
      ctx.setLineDash([6, 6]);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
    }

    ctx.restore();

    // Player badge (outside the transformed group)
    if (!this.isKnockedOut) {
      ctx.font      = "bold 11px Inter, sans-serif";
      ctx.fillStyle = this.playerId === 1 ? "#4294f5" : "#e64652";
      ctx.textAlign = "center";
      ctx.fillText(`P${this.playerId}`, sx, sy - this.radius - 10);
    }
  }

  // Helper: darken a color
  _darken(hex, amount) {
    let r = parseInt(hex.slice(1,3), 16);
    let g = parseInt(hex.slice(3,5), 16);
    let b = parseInt(hex.slice(5,7), 16);
    r = Math.max(0, r - amount * 255);
    g = Math.max(0, g - amount * 255);
    b = Math.max(0, b - amount * 255);
    return `rgb(${r},${g},${b})`;
  }

  // Helper: lighten a color
  _lighten(hex, amount) {
    let r = parseInt(hex.slice(1,3), 16);
    let g = parseInt(hex.slice(3,5), 16);
    let b = parseInt(hex.slice(5,7), 16);
    r = Math.min(255, r + amount * 255);
    g = Math.min(255, g + amount * 255);
    b = Math.min(255, b + amount * 255);
    return `rgb(${r},${g},${b})`;
  }
}
