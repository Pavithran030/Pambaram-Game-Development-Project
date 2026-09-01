// ═══════════════════════════════════════
//  PAMBARAM - particles.js
// ═══════════════════════════════════════

class Particle {
  constructor(x, y, vx, vy, color, life, size) {
    this.x = x; this.y = y;
    this.vx = vx; this.vy = vy;
    this.color = color;
    this.life = life; this.maxLife = life;
    this.size = size;
    this.z = 0;
    this.vz = 0;
  }

  update(dt) {
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.z += this.vz * dt;
    this.vy += 200 * dt;
    this.vx *= 0.98;
    this.vz *= 0.98;
    this.life -= dt;
    return this.life > 0;
  }



  draw(ctx, angle = 0) {
    const a = Math.max(0, this.life / this.maxLife);
    const p = projectPoint(this.x, this.y, this.z, angle);
    const sx = p.x;
    const sy = p.y;
    ctx.globalAlpha = a;
    ctx.fillStyle = this.color;
    ctx.beginPath();
    ctx.ellipse(sx, sy, this.size * a * 0.5, this.size * a * 0.2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

class ParticleSystem {
  constructor() {
    this.particles = [];
  }

  _rnd(min, max) {
    return min + Math.random() * (max - min);
  }

  emitSparks(x, y, nx, ny, count = 8, color = "#f5b947") {
    for (let i = 0; i < count; i++) {
      const angle = Math.atan2(ny, nx) + this._rnd(-0.6, 0.6);
      const speed = this._rnd(80, 300);
      const p = new Particle(
        x, y,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed - 60,
        color,
        this._rnd(0.3, 0.7),
        this._rnd(2, 5)
      );
      p.z = this._rnd(5, 30);
      p.vz = this._rnd(20, 80);
      this.particles.push(p);
    }
  }

  emitRingout(x, y, count = 40) {
    for (let i = 0; i < count; i++) {
      const angle = this._rnd(0, Math.PI * 2);
      const speed = this._rnd(100, 500);
      const p = new Particle(
        x, y,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed,
        `hsl(${this._rnd(0, 60)},90%,65%)`,
        this._rnd(0.4, 1.0),
        this._rnd(3, 8)
      );
      p.z = this._rnd(10, 50);
      p.vz = this._rnd(20, 100);
      this.particles.push(p);
    }
  }

  emitSpin(x, y, count = 2, color = "rgba(255,255,255,0.6)") {
    for (let i = 0; i < count; i++) {
      const angle = this._rnd(0, Math.PI * 2);
      const speed = this._rnd(20, 80);
      const p = new Particle(
        x, y,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed - 30,
        color,
        this._rnd(0.2, 0.5),
        this._rnd(1.5, 3)
      );
      p.z = this._rnd(0, 10);
      p.vz = this._rnd(5, 20);
      this.particles.push(p);
    }
  }

  emitSpecial(x, y, color, count = 30) {
    for (let i = 0; i < count; i++) {
      const angle = this._rnd(0, Math.PI * 2);
      const speed = this._rnd(150, 600);
      const p = new Particle(
        x, y,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed,
        color,
        this._rnd(0.5, 1.2),
        this._rnd(4, 10)
      );
      p.z = this._rnd(20, 60);
      p.vz = this._rnd(30, 120);
      this.particles.push(p);
    }
  }

  emitBoost(x, y) {
    for (let i = 0; i < 12; i++) {
      const angle = this._rnd(0, Math.PI * 2);
      const p = new Particle(
        x, y,
        Math.cos(angle) * this._rnd(60, 200),
        Math.sin(angle) * this._rnd(60, 200),
        "#42e0d6",
        this._rnd(0.3, 0.6),
        this._rnd(2, 5)
      );
      p.z = this._rnd(5, 25);
      p.vz = this._rnd(10, 40);
      this.particles.push(p);
    }
  }

  emitDust(x, y, count = 10) {
    for (let i = 0; i < count; i++) {
      const angle = this._rnd(0, Math.PI * 2);
      const speed = this._rnd(50, 200);
      const color = `hsl(${this._rnd(30, 50)}, ${this._rnd(30, 70)}%, ${this._rnd(40, 70)}%)`;
      const p = new Particle(
        x, y,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed,
        color,
        this._rnd(0.3, 0.8),
        this._rnd(3, 7)
      );
      p.z = this._rnd(0, 20);
      p.vz = this._rnd(10, 50);
      this.particles.push(p);
    }
  }

  update(dt) {
    this.particles = this.particles.filter((p) => p.update(dt));
  }

  draw(ctx, angle = 0) {
    this.particles.forEach(p => p.draw(ctx, angle));
  }
}
