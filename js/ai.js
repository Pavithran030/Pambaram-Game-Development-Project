// ═══════════════════════════════════════
//  PAMBARAM - ai.js
//  AIController (mirrors Python ai.py)
// ═══════════════════════════════════════

class AIController {
  constructor(top, difficulty = Difficulty.MEDIUM) {
    this.top        = top;
    this.difficulty = difficulty;
    this.state      = AIState.IDLE;
    this.stateTimer = 0;
    this.targetAngle    = Math.random() * Math.PI * 2;
    this.wanderTimer    = 0;
    this.lastDecision   = 0;
    this.specialTrigger = 60 + Math.random() * 40;
    this.aimNoise       = 0;
    this.disengageTimer = 0;
  }

  _distFromCenter() {
    return Math.hypot(this.top.x - ARENA_CX, this.top.y - ARENA_CY);
  }
  _distTo(other) {
    return Math.hypot(other.x - this.top.x, other.y - this.top.y);
  }
  _nearEdge() { return this._distFromCenter() > ARENA_R * 0.75; }

  _decide(opp, dt) {
    if (this.disengageTimer > 0) {
      this.disengageTimer -= dt;
      this.state = AIState.IDLE;
      return;
    }
    this.lastDecision -= dt;
    if (this.lastDecision > 0) return;

    const intervals = { [Difficulty.EASY]:0.8, [Difficulty.MEDIUM]:0.4, [Difficulty.HARD]:0.2 };
    this.lastDecision = intervals[this.difficulty] || 0.5;

    const noises = { [Difficulty.EASY]:0.9, [Difficulty.MEDIUM]:0.5, [Difficulty.HARD]:0.22 };
    const nl = noises[this.difficulty] || 0.45;
    this.aimNoise = (Math.random() * 2 - 1) * nl;

    const dist    = this._distTo(opp);
    const mySpin  = this.top.maxSpin > 0 ? this.top.spin / this.top.maxSpin : 0;
    const oppSpin = opp.maxSpin > 0 ? opp.spin / opp.maxSpin : 0;
    const nearEdge = this._nearEdge();

    if (this.top.specialMeter >= this.specialTrigger && mySpin > 0.3) {
      this.state = AIState.SPECIAL; return;
    }
    if (nearEdge && mySpin < 0.4) { this.state = AIState.RETREAT; return; }

    if (this.top.type === TopType.DEFENSE) {
      if (dist < 120 && oppSpin > mySpin) this.state = AIState.DEFEND;
      else if (dist > 200) this.state = AIState.APPROACH;
      else this.state = AIState.ATTACK;
    } else if (this.top.type === TopType.ATTACK || this.top.type === TopType.SPEED) {
      if (mySpin < 0.25) this.state = AIState.RETREAT;
      else if (dist > 100) this.state = AIState.APPROACH;
      else this.state = AIState.ATTACK;
    } else {
      if (oppSpin > mySpin + 0.2 && dist < 100) this.state = AIState.RETREAT;
      else if (dist > 150) this.state = AIState.APPROACH;
      else this.state = AIState.ATTACK;
    }

    if (this.state === AIState.APPROACH || this.state === AIState.ATTACK) {
      const dchance = { [Difficulty.EASY]:0.28, [Difficulty.MEDIUM]:0.18, [Difficulty.HARD]:0.12 };
      if (Math.random() < (dchance[this.difficulty] || 0.2)) {
        this.disengageTimer = 0.9 + Math.random() * 1.3;
        this.state = AIState.IDLE;
      }
    }
  }

  update(opp, dt) {
    if (!this.top.isLaunched || this.top.isKnockedOut) return null;
    if (!opp.isLaunched) {
      this.state = AIState.IDLE;
      const cdx = ARENA_CX - this.top.x, cdy = ARENA_CY - this.top.y;
      const cd  = Math.hypot(cdx, cdy);
      if (cd > 40) return { steer:[cdx/cd, cdy/cd], dash:false, special:false };
      return { steer:[0,0], dash:false, special:false };
    }

    this._decide(opp, dt);
    this.stateTimer += dt;

    let sx = 0, sy = 0, dash = false, special = false;
    const dist = this._distTo(opp);
    const dx = opp.x - this.top.x, dy = opp.y - this.top.y;
    const oppAngle = Math.atan2(dy, dx);
    const cDx = ARENA_CX - this.top.x, cDy = ARENA_CY - this.top.y;
    const cDist = Math.hypot(cDx, cDy);
    const centerAngle = Math.atan2(cDy, cDx);

    switch (this.state) {
      case AIState.IDLE:
        this.wanderTimer -= dt;
        if (this.wanderTimer <= 0) {
          this.targetAngle = Math.random() * Math.PI * 2;
          this.wanderTimer = 0.5 + Math.random();
        }
        sx = Math.cos(this.targetAngle); sy = Math.sin(this.targetAngle);
        break;

      case AIState.APPROACH: {
        let angle = oppAngle + this.aimNoise;
        if ((this.difficulty === Difficulty.MEDIUM || this.difficulty === Difficulty.HARD) && dist > 100) {
          const oppSpd = Math.hypot(opp.vx, opp.vy);
          if (oppSpd > 50) {
            const lead = (this.difficulty === Difficulty.HARD) ? 1.0 : 0.45;
            const pt   = Math.min(0.5, dist / Math.max(1, oppSpd + 100)) * lead;
            const px   = opp.x + opp.vx*pt, py = opp.y + opp.vy*pt;
            angle = Math.atan2(py - this.top.y, px - this.top.x) + this.aimNoise*0.5;
          }
        }
        sx = Math.cos(angle); sy = Math.sin(angle);
        if ((this.difficulty === Difficulty.MEDIUM || this.difficulty === Difficulty.HARD)
            && dist > 180 && this.top.dashCooldown <= 0
            && this.top.spin > this.top.maxSpin * 0.4
            && Math.random() < (this.difficulty === Difficulty.HARD ? 0.04 : 0.02)) {
          dash = true;
        }
        break;
      }

      case AIState.ATTACK:
        sx = Math.cos(oppAngle + this.aimNoise*0.5);
        sy = Math.sin(oppAngle + this.aimNoise*0.5);
        if ((this.top.type === TopType.ATTACK || this.top.type === TopType.SPEED)
            && this.top.dashCooldown <= 0 && dist < 150 && Math.random() < 0.03) {
          dash = true;
        }
        break;

      case AIState.RETREAT: {
        let ra = oppAngle + Math.PI;
        if (this._nearEdge()) ra = centerAngle;
        sx = Math.cos(ra + this.aimNoise); sy = Math.sin(ra + this.aimNoise);
        if (this.top.dashCooldown <= 0 && Math.random() < 0.02) dash = true;
        break;
      }

      case AIState.DEFEND: {
        let tang = oppAngle + Math.PI/2;
        if (this.aimNoise < 0) tang += Math.PI;
        sx = Math.cos(tang + this.aimNoise) * 0.7;
        sy = Math.sin(tang + this.aimNoise) * 0.7;
        if (cDist > ARENA_R * 0.5) {
          sx += Math.cos(centerAngle) * 0.3;
          sy += Math.sin(centerAngle) * 0.3;
        }
        break;
      }

      case AIState.SPECIAL:
        if (this.top.specialMeter >= 100) { special = true; this.specialTrigger = 50 + Math.random()*50; }
        sx = Math.cos(oppAngle); sy = Math.sin(oppAngle);
        if (this.stateTimer > 0.5) this.state = AIState.ATTACK;
        break;
    }

    const mag = Math.hypot(sx, sy);
    if (mag > 0) { sx /= mag; sy /= mag; }
    return { steer:[sx, sy], dash, special };
  }
}
