import pygame
import math
import random

class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, gravity=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.max_life = life
        self.life = life
        self.gravity = gravity

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= dt

    def draw(self, surface, shake=(0, 0)):
        alpha = max(0, self.life / self.max_life)
        size = max(1, int(self.size * alpha))
        c = (
            min(255, max(0, int(self.color[0] * alpha + 0))),
            min(255, max(0, int(self.color[1] * alpha + 0))),
            min(255, max(0, int(self.color[2] * alpha + 0))),
        )
        pygame.draw.circle(surface, c, (int(self.x + shake[0]), int(self.y + shake[1])), size)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def update(self, dt):
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update(dt)

    def draw(self, surface, shake=(0, 0)):
        for p in self.particles:
            p.draw(surface, shake)

    def emit_dust(self, x, y, count=10):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = (
                random.randint(150, 200),
                random.randint(120, 170),
                random.randint(80, 120),
            )
            self.particles.append(Particle(x, y, vx, vy, color, random.randint(3, 7), random.uniform(0.3, 0.8)))

    def emit_sparks(self, x, y, nx, ny, count=15, color=None):
        base_color = color if color else (255, 220, 100)
        for _ in range(count):
            spread = random.uniform(-0.6, 0.6)
            angle = math.atan2(ny, nx) + spread
            speed = random.uniform(150, 450)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            c = (
                min(255, base_color[0] + random.randint(-30, 30)),
                min(255, base_color[1] + random.randint(-30, 30)),
                min(255, base_color[2] + random.randint(-30, 30)),
            )
            self.particles.append(Particle(x, y, vx, vy, c, random.randint(2, 5), random.uniform(0.2, 0.6)))

    def emit_ringout(self, x, y, count=30):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = (255, random.randint(100, 200), 50)
            self.particles.append(Particle(x, y, vx, vy, color, random.randint(4, 9), random.uniform(0.5, 1.2)))

    def emit_special(self, x, y, color, count=40):
        for i in range(count):
            angle = (i / count) * math.pi * 2 + random.uniform(-0.2, 0.2)
            speed = random.uniform(200, 500)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            c = (
                min(255, color[0] + random.randint(-40, 40)),
                min(255, color[1] + random.randint(-40, 40)),
                min(255, color[2] + random.randint(-40, 40)),
            )
            self.particles.append(Particle(x, y, vx, vy, c, random.randint(3, 8), random.uniform(0.4, 1.0)))

    def emit_spin(self, x, y, count=3):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(20, 80)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = (200, 200, 200)
            self.particles.append(Particle(x, y, vx, vy, color, random.randint(1, 3), random.uniform(0.1, 0.3)))
