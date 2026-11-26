"""Procedural artwork for the spinning tops.

Every top is built from the same layers a real battle top has, drawn from the
outside in:

    attack ring  - the metal outer ring. Its silhouette depends on the type:
                   ATTACK  = three hooked blades
                   DEFENSE = a thick, round, studded rim
                   BALANCE = six even lobes
                   SPEED   = four thin swept fins
    energy layer - the coloured disc, with panel lines and accent inlays
    accent ring  - a notched ring in the accent colour
    bit chip     - the dark centre cap with a type emblem
    highlight    - a fixed specular sheen (it does not rotate, which is what
                   sells the "spinning under a light" look)

Shapes are drawn on a 2x surface and smooth-scaled down, which gives clean
anti-aliased edges with plain pygame drawing calls.
"""
import math
import pygame
import pygame.gfxdraw

from .config import TopType

SUPERSAMPLE = 2
_OUTLINE_POINTS = 120


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _lighten(c, t):
    return _mix(c, (255, 255, 255), t)


def _darken(c, t):
    return _mix(c, (0, 0, 0), t)


# ----------------------------------------------------------------------
# Attack-ring silhouettes: radius (0..1) as a function of angle.
# ----------------------------------------------------------------------
def _attack_profile(theta):
    # Three blades: radius ramps up across each sector, then drops sharply
    # -> a hooked, saw-like edge that "leads" in the spin direction.
    sector = 2 * math.pi / 3
    t = (theta % sector) / sector
    return 0.80 + 0.20 * (t ** 1.6)


def _defense_profile(theta):
    # Heavy round rim with eight shallow studs.
    return 0.93 + 0.07 * max(0.0, math.cos(8 * theta)) ** 3


def _balance_profile(theta):
    # Six even, rounded lobes.
    return 0.86 + 0.14 * abs(math.cos(3 * theta)) ** 1.5


def _speed_profile(theta):
    # Four thin fins swept back like turbine blades.
    sector = math.pi / 2
    t = (theta % sector) / sector
    fin = max(0.0, 1.0 - abs(t - 0.18) / 0.18) if t < 0.36 else 0.0
    return 0.76 + 0.24 * fin ** 0.7


_PROFILES = {
    TopType.ATTACK: _attack_profile,
    TopType.DEFENSE: _defense_profile,
    TopType.BALANCE: _balance_profile,
    TopType.SPEED: _speed_profile,
}

_OUTLINE_CACHE = {}


def _unit_outline(top_type):
    pts = _OUTLINE_CACHE.get(top_type)
    if pts is None:
        prof = _PROFILES.get(top_type, _balance_profile)
        pts = []
        for i in range(_OUTLINE_POINTS):
            th = 2 * math.pi * i / _OUTLINE_POINTS
            pts.append((th, prof(th)))
        _OUTLINE_CACHE[top_type] = pts
    return pts


def _poly(cx, cy, radius, top_type, rotation, scale=1.0):
    return [(cx + math.cos(th + rotation) * radius * r * scale,
             cy + math.sin(th + rotation) * radius * r * scale)
            for th, r in _unit_outline(top_type)]


# Note: no gfxdraw anti-aliasing here. On an alpha surface those calls
# *replace* edge pixels with partial alpha instead of blending, which leaves
# see-through seams between layers. The 2x supersample + smoothscale already
# anti-aliases every edge.
def _fill_poly(surf, pts, color):
    pygame.draw.polygon(surf, color, [(int(round(x)), int(round(y))) for x, y in pts])


def _disc(surf, cx, cy, r, color):
    pygame.draw.circle(surf, color, (int(cx), int(cy)), max(1, int(r)))


def _emblem(surf, cx, cy, r, top_type, rotation, color):
    """Small type glyph on the bit chip."""
    if top_type == TopType.ATTACK:
        n, k = 3, 1.0        # triangle
    elif top_type == TopType.DEFENSE:
        n, k = 4, 1.0        # square
    elif top_type == TopType.SPEED:
        n, k = 4, 0.45       # 4-point star
    else:
        n, k = 6, 1.0        # hexagon
    pts = []
    steps = n * (2 if k < 1 else 1)
    for i in range(steps):
        a = rotation + 2 * math.pi * i / steps
        rr = r if (k >= 1 or i % 2 == 0) else r * k
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    _fill_poly(surf, pts, color)


def metal_color(base):
    """Steel tinted slightly toward the top's colour."""
    return _mix((150, 156, 168), base, 0.25)


def render_top(radius, color, accent, top_type, rotation=0.0, spin_ratio=1.0, team_color=None):
    """Return an SRCALPHA surface (size 2*radius+pad square) of the top,
    centred, at the given rotation. spin_ratio (0..1) adds motion blur."""
    S = SUPERSAMPLE
    pad = 6
    size = int((radius + pad) * 2)
    R = radius * S
    big = pygame.Surface((size * S, size * S), pygame.SRCALPHA)
    c = size * S / 2

    metal = metal_color(color)
    metal_dark = _darken(metal, 0.45)

    # Motion-blur envelope: at speed the blades smear into a translucent disc.
    if spin_ratio > 0.3:
        a = int(110 * min(1.0, (spin_ratio - 0.3) / 0.5))
        _disc(big, c, c, R * 0.99, (*metal_dark, a))
        _disc(big, c, c, R * 0.90, (*metal, a))

    # Attack ring: dark outline, metal body, lighter inner bevel.
    _fill_poly(big, _poly(c, c, R, top_type, rotation, 1.0), metal_dark)
    _fill_poly(big, _poly(c, c, R, top_type, rotation, 0.93), metal)
    _fill_poly(big, _poly(c, c, R, top_type, rotation, 0.80), _lighten(metal, 0.15))

    # Energy layer: radial gradient disc in the top's colour.
    e_r = R * 0.72
    rim = _darken(color, 0.35)
    core = _lighten(color, 0.25)
    for i in range(6, -1, -1):
        t = i / 6
        _disc(big, c, c, e_r * (0.55 + 0.45 * t), _mix(core, rim, t))
    pygame.draw.circle(big, _darken(color, 0.55), (int(c), int(c)), int(e_r), max(1, int(R * 0.03)))

    # Panel lines + accent inlays, rotating with the layer.
    n_panels = {TopType.ATTACK: 3, TopType.DEFENSE: 4, TopType.SPEED: 4}.get(top_type, 6)
    line_col = _darken(color, 0.55)
    for i in range(n_panels):
        a = rotation + 2 * math.pi * i / n_panels
        x1, y1 = c + math.cos(a) * e_r * 0.52, c + math.sin(a) * e_r * 0.52
        x2, y2 = c + math.cos(a) * e_r * 0.98, c + math.sin(a) * e_r * 0.98
        pygame.draw.line(big, line_col, (x1, y1), (x2, y2), max(2, int(R * 0.05)))
        # Accent inlay in the middle of each panel.
        am = a + math.pi / n_panels
        ix, iy = c + math.cos(am) * e_r * 0.80, c + math.sin(am) * e_r * 0.80
        _disc(big, ix, iy, R * 0.085, _darken(accent, 0.4))
        _disc(big, ix, iy, R * 0.065, accent)

    # Accent ring with notches.
    a_r = R * 0.46
    _disc(big, c, c, a_r, _darken(accent, 0.25))
    _disc(big, c, c, a_r * 0.86, accent)
    for i in range(8):
        a = rotation + 2 * math.pi * i / 8 + math.pi / 8
        x, y = c + math.cos(a) * a_r * 0.93, c + math.sin(a) * a_r * 0.93
        _disc(big, x, y, R * 0.028, _darken(accent, 0.45))

    # Bit chip: dark metal cap with the type emblem.
    b_r = R * 0.27
    _disc(big, c, c, b_r, (24, 26, 34))
    _disc(big, c, c, b_r * 0.86, (44, 48, 60))
    _emblem(big, c, c, b_r * 0.58, top_type, rotation, team_color or accent)
    _disc(big, c, c, max(2, b_r * 0.16), (235, 238, 245))

    # Static specular highlight (upper-left) and a faint rim light.
    hl = pygame.Surface((size * S, size * S), pygame.SRCALPHA)
    hx, hy = c - R * 0.32, c - R * 0.36
    pygame.draw.ellipse(hl, (255, 255, 255, 46),
                        pygame.Rect(hx - R * 0.42, hy - R * 0.22, R * 0.84, R * 0.44))
    pygame.draw.ellipse(hl, (255, 255, 255, 60),
                        pygame.Rect(hx - R * 0.20, hy - R * 0.09, R * 0.40, R * 0.18))
    big.blit(hl, (0, 0))

    return pygame.transform.smoothscale(big, (size, size))


def make_icon(size=64):
    """Window icon: a balance-type top in the game's gold and blue."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    art = render_top(size // 2 - 6, (66, 148, 245), (245, 185, 71), TopType.ATTACK, rotation=0.4)
    surf.blit(art, art.get_rect(center=(size // 2, size // 2)))
    return surf
