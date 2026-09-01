// ═══════════════════════════════════════
//  PAMBARAM - arena.js
// ═══════════════════════════════════════

class Arena {
  constructor(presetKey = "Gramam Thidal") {
    this.presetKey = presetKey;
    const p = ARENA_PRESETS[presetKey];
    this.floorColor = p.floor;
    this.ringColor  = p.ring;
    this.voidColor  = p.void;
    this.gripMod    = p.grip;
    this.hazards    = p.hazards;

    this.obstacles  = [];
    this.boostPads  = [];
    this._setupHazards();
  }

  _setupHazards() {
    if (this.hazards.includes("pillars")) {
      [0, Math.PI/2, Math.PI, 3*Math.PI/2].forEach(angle => {
        const r = 80;
        this.obstacles.push({
          x: ARENA_CX + Math.cos(angle) * r,
          y: ARENA_CY + Math.sin(angle) * r,
          r: 25, cooldown: 0,
        });
      });
    }
    if (this.hazards.includes("boost_pads")) {
      [Math.PI/4, 3*Math.PI/4, 5*Math.PI/4, 7*Math.PI/4].forEach(angle => {
        const r = 160;
        this.boostPads.push({
          x: ARENA_CX + Math.cos(angle) * r,
          y: ARENA_CY + Math.sin(angle) * r,
          r: 35, cooldown: 0,
        });
      });
    }
  }

  update(dt) {
    this.boostPads.forEach(p => { if (p.cooldown > 0) p.cooldown -= dt; });
  }



  // Draw a 3D cylinder (for obstacles)
  _drawCylinder(ctx, x, y, radius, height, color, topColor, shakeX, shakeY, angle) {
    const p = projectPoint(x + shakeX, y + shakeY, 0, angle);
    const cx = p.x;
    const cy = p.y;
    const topP = projectPoint(x + shakeX, y + shakeY, height, angle);
    const topCx = topP.x;
    const topCy = topP.y;

    // Shadow on ground
    ctx.save();
    ctx.shadowColor = "rgba(0,0,0,0.3)";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.ellipse(cx, cy, radius, radius * 0.4, 0, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0,0,0,0.2)";
    ctx.fill();
    ctx.restore();

    // Body (side)
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(cx - radius, cy);
    ctx.lineTo(topCx - radius, topCy);
    ctx.ellipse(topCx, topCy, radius, radius * 0.4, 0, 0, Math.PI * 2);
    ctx.lineTo(cx + radius, cy);
    ctx.ellipse(cx, cy, radius, radius * 0.4, 0, Math.PI * 2, 0);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "rgba(0,0,0,0.3)";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();

    // Top
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(topCx, topCy, radius, radius * 0.4, 0, 0, Math.PI * 2);
    ctx.fillStyle = topColor || color;
    ctx.fill();
    ctx.strokeStyle = "rgba(0,0,0,0.2)";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();

    return { cx, cy, topCx, topCy };
  }

  draw(ctx, shakeX = 0, shakeY = 0, angle = 0) {
    // Project the arena center with rotation
    const center = projectPoint(ARENA_CX, ARENA_CY, 0, angle);
    const cx = center.x + shakeX;
    const cy = center.y + shakeY;

    // Void backdrop (dark 3D space) – keep fixed relative to center after rotation
    ctx.save();
    ctx.fillStyle = this.voidColor;
    ctx.beginPath();
    // Draw a larger ellipse for depth, centered at projected center
    ctx.ellipse(cx, cy, RINGOUT_R + 80, (RINGOUT_R + 80) * 0.35, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Arena floor – 3D ellipse with gradient
    ctx.save();
    const grad = ctx.createRadialGradient(cx, cy - 20, 0, cx, cy, ARENA_R);
    grad.addColorStop(0, this.floorColor);
    grad.addColorStop(0.7, this.floorColor);
    grad.addColorStop(1, this.ringColor);
    ctx.beginPath();
    ctx.ellipse(cx, cy, ARENA_R, ARENA_R * 0.45, 0, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.shadowColor = "rgba(0,0,0,0.4)";
    ctx.shadowBlur = 30;
    ctx.strokeStyle = this.ringColor;
    ctx.lineWidth = 6;
    ctx.stroke();
    ctx.restore();

    // Concentric ellipses for depth
    ctx.save();
    ctx.strokeStyle = "rgba(0,0,0,0.08)";
    ctx.lineWidth = 1;
    [50, 100, 150, 200, 250].forEach(r => {
      ctx.beginPath();
      ctx.ellipse(cx, cy, r, r * 0.45, 0, 0, Math.PI * 2);
      ctx.stroke();
    });
    ctx.restore();

    // Tick marks (3D perspective) – project points on the circle with rotation
    ctx.save();
    ctx.strokeStyle = this.ringColor;
    ctx.lineWidth = 2;
    for (let deg = 0; deg < 360; deg += 45) {
      const rad = deg * Math.PI / 180;
      const r1 = ARENA_R - 28;
      const r2 = ARENA_R - 4;
      // Compute world positions on the circle and project them
      const wx1 = ARENA_CX + Math.cos(rad) * r1;
      const wy1 = ARENA_CY + Math.sin(rad) * r1;
      const wx2 = ARENA_CX + Math.cos(rad) * r2;
      const wy2 = ARENA_CY + Math.sin(rad) * r2;
      const p1 = projectPoint(wx1, wy1, 0, angle);
      const p2 = projectPoint(wx2, wy2, 0, angle);
      ctx.beginPath();
      ctx.moveTo(p1.x + shakeX, p1.y + shakeY);
      ctx.lineTo(p2.x + shakeX, p2.y + shakeY);
      ctx.stroke();
    }
    ctx.restore();

    // Danger ring (bounce zone) – dashed ellipse
    ctx.save();
    ctx.strokeStyle = "rgba(245,185,71,0.3)";
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 6]);
    // Draw as an ellipse in screen space (approximation)
    ctx.beginPath();
    ctx.ellipse(cx, cy, ARENA_R, ARENA_R * 0.45, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // Draw obstacles as 3D cylinders
    this.obstacles.forEach(obs => {
      this._drawCylinder(ctx, obs.x, obs.y, obs.r, 40, "#645040", "#967850", shakeX, shakeY, angle);
    });

    // Boost pads as glowing 3D disks
    this.boostPads.forEach(pad => {
      const alpha = pad.cooldown > 0 ? 0.25 : 0.7;
      const p = projectPoint(pad.x + shakeX, pad.y + shakeY, 0, angle);
      const px = p.x;
      const py = p.y;
      ctx.save();
      ctx.globalAlpha = alpha;
      if (pad.cooldown <= 0) {
        ctx.shadowColor = "#42e0d6";
        ctx.shadowBlur = 30;
      }
      ctx.beginPath();
      ctx.ellipse(px, py, pad.r, pad.r * 0.4, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#42e0d6";
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = "#a0f8f2";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.restore();
    });
  }
}

// ── Collision resolution (mass-weighted overlap, v2 Fix #6) ──
function resolveTopCollision(t1, t2, particles) {
  const dx   = t2.x - t1.x, dy = t2.y - t1.y;
  const dist = Math.hypot(dx, dy);
  const minD = t1.radius + t2.radius;
  if (dist >= minD || dist === 0) return 0;

  const nx = dx / dist, ny = dy / dist;
  const overlap = minD - dist;

  // Mass-weighted separation
  const m1   = t1.invincible ? t1.mass * 5 : t1.mass;
  const m2   = t2.invincible ? t2.mass * 5 : t2.mass;
  const totM = m1 + m2;
  t1.x -= nx * overlap * (m2 / totM);
  t1.y -= ny * overlap * (m2 / totM);
  t2.x += nx * overlap * (m1 / totM);
  t2.y += ny * overlap * (m1 / totM);

  // Elastic impulse
  const tx = -ny, ty = nx;
  const t1dn = t1.vx*nx + t1.vy*ny, t1dt = t1.vx*tx + t1.vy*ty;
  const t2dn = t2.vx*nx + t2.vy*ny, t2dt = t2.vx*tx + t2.vy*ty;
  const e    = 0.75;
  const new1dn = ((t1dn*(m1-m2)) + t2dn*2*m2) / totM * e;
  const new2dn = ((t2dn*(m2-m1)) + t1dn*2*m1) / totM * e;
  t1.vx = tx*t1dt + nx*new1dn;
  t1.vy = ty*t1dt + ny*new1dn;
  t2.vx = tx*t2dt + nx*new2dn;
  t2.vy = ty*t2dt + ny*new2dn;

  // Spin damage
  const r1 = t1.maxSpin > 0 ? t1.spin/t1.maxSpin : 0;
  const r2 = t2.maxSpin > 0 ? t2.spin/t2.maxSpin : 0;
  const dmg = Math.abs(new1dn - t1dn) * 0.015;
  if (!t2.invincible) t2.spin = Math.max(0, t2.spin - t2.maxSpin * dmg * r1);
  if (!t1.invincible) t1.spin = Math.max(0, t1.spin - t1.maxSpin * dmg * r2);

  // Particles
  const midX = (t1.x + t2.x) / 2, midY = (t1.y + t2.y) / 2;
  const relSpd = Math.abs(new1dn - t1dn);
  if (particles) particles.emitSparks(midX, midY, nx, ny, Math.min(20, 5 + relSpd*0.02));

  return Math.min(12, 3 + relSpd * 0.02);
}

function checkObstacleCollision(top, obstacles) {
  let shake = 0;
  obstacles.forEach(obs => {
    const dx = top.x - obs.x, dy = top.y - obs.y;
    const dist = Math.hypot(dx, dy);
    const minD = top.radius + obs.r;
    if (dist < minD && dist > 0) {
      const nx = dx/dist, ny = dy/dist;
      const overlap = minD - dist;
      top.x += nx * overlap;
      top.y += ny * overlap;
      const dot = top.vx*nx + top.vy*ny;
      if (dot < 0) {
        top.vx -= 2*dot*nx; top.vy -= 2*dot*ny;
        top.vx *= 0.6;      top.vy *= 0.6;
        top.spin = Math.max(0, top.spin - top.maxSpin*0.05);
        shake = 5;
      }
    }
  });
  return shake;
}

function checkBoostPad(top, pads, particles) {
  pads.forEach(pad => {
    if (pad.cooldown > 0) return;
    const dist = Math.hypot(top.x - pad.x, top.y - pad.y);
    if (dist < pad.r + top.radius) {
      const spd = Math.hypot(top.vx, top.vy);
      if (spd > 0) { top.vx *= 1.5; top.vy *= 1.5; }
      top.spin = Math.min(top.maxSpin, top.spin + top.maxSpin*0.1);
      pad.cooldown = 3.0;
      if (particles) particles.emitBoost(pad.x, pad.y);
    }
  });
}
