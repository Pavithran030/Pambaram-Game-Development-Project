import pygame
import pygame.gfxdraw
import math
from .config import *
from .top_art import render_top


# ======================================================================
# Primitives
# ======================================================================
def _lighten(color, amount):
    return tuple(min(255, int(c + (255 - c) * amount)) for c in color[:3])


def _darken(color, amount):
    return tuple(max(0, int(c * (1 - amount))) for c in color[:3])


def draw_rounded_rect(surface, rect, color, radius=12, border=0, border_color=None):
    """Draw a filled rounded rect, or a rounded-rect outline when no border_color
    is given (treating `color` as the stroke color and `border` as its width)."""
    rect = pygame.Rect(rect)
    if border > 0:
        if border_color:
            pygame.draw.rect(surface, color, rect, border_radius=radius)
            pygame.draw.rect(surface, border_color, rect, width=border, border_radius=radius)
        else:
            pygame.draw.rect(surface, color, rect, width=border, border_radius=radius)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_panel(surface, rect, fill=None, border=None, radius=14, border_w=2):
    """Shared panel styling: optional fill (RGB or RGBA), optional stroke."""
    rect = pygame.Rect(rect)
    if fill is not None:
        if len(fill) == 4 and fill[3] < 255:
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
            surface.blit(panel, rect.topleft)
        else:
            draw_rounded_rect(surface, rect, fill[:3], radius)
    if border is not None:
        draw_rounded_rect(surface, rect, border, radius, border_w)


def draw_glow(surface, rect, color, pad=18, alpha=50, layers=5, radius=None):
    """Soft glow behind rect, built from stacked translucent rounded rects."""
    rect = pygame.Rect(rect)
    glow_surf = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        frac = i / layers
        g = int(pad * frac)
        a = max(3, int(alpha * (1 - frac) + alpha * 0.15))
        r = pygame.Rect(pad - g, pad - g, rect.width + g * 2, rect.height + g * 2)
        rr = radius if radius is not None else r.height // 2
        pygame.draw.rect(glow_surf, (*color[:3], a), r, border_radius=rr)
    surface.blit(glow_surf, (rect.x - pad, rect.y - pad))


# ======================================================================
# Text
# ======================================================================
def draw_text(surface, text, font, color, pos, anchor="center", shadow=False, alpha=255):
    """Render text anchored at pos ("center", "midleft", "topleft", ...).
    An optional soft drop shadow keeps text readable over busy backgrounds."""
    ts = font.render(text, True, color)
    rect = ts.get_rect(**{anchor: pos})
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        if alpha < 255:
            sh.set_alpha(int(alpha * 0.6))
        else:
            sh.set_alpha(150)
        surface.blit(sh, rect.move(0, 2))
    if alpha < 255:
        ts.set_alpha(alpha)
    surface.blit(ts, rect)
    return rect


def draw_text_glow(surface, text_surf, rect, color, strength=0.55, spread=6):
    """Soft bloom behind a rendered text surface: tint a copy, blur it by
    down/up-scaling, and blit it additively. Unlike a rectangle glow, this
    follows the letter shapes."""
    pad = spread * 4
    w, h = text_surf.get_width() + pad * 2, text_surf.get_height() + pad * 2
    # Composite onto opaque black: this premultiplies the text by its alpha,
    # which matters because additive blending ignores alpha and SDL's text
    # surfaces carry the text colour even in fully transparent pixels.
    base = pygame.Surface((w, h))
    base.fill((0, 0, 0))
    base.blit(text_surf, (pad, pad))
    base.fill((*color[:3],), special_flags=pygame.BLEND_RGB_MIN)
    small = pygame.transform.smoothscale(base, (max(1, w // spread), max(1, h // spread)))
    blurred = pygame.transform.smoothscale(small, (w, h))
    s = max(0, min(255, int(255 * strength)))
    blurred.fill((s, s, s), special_flags=pygame.BLEND_RGB_MULT)
    surface.blit(blurred, (rect.x - pad, rect.y - pad), special_flags=pygame.BLEND_RGB_ADD)


def wrap_text(text, font, max_width):
    """Greedy word wrap; returns a list of lines that each fit max_width."""
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if font.size(trial)[0] <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_text_block(surface, text, font, color, center_x, top_y, max_width, line_gap=2, max_lines=None):
    lines = wrap_text(text, font, max_width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
    y = top_y
    lh = font.get_linesize() + line_gap - 4
    for line in lines:
        draw_text(surface, line, font, color, (center_x, y), anchor="midtop")
        y += lh
    return y


def draw_chip(surface, text, center, color, size=12, filled=False, pad_x=9, height=None):
    """Small rounded label. Outline style by default; filled for badges."""
    font = get_font(size, family="semibold")
    tw, th = font.size(text)
    h = height or th + 6
    rect = pygame.Rect(0, 0, tw + pad_x * 2, h)
    rect.center = center
    if filled:
        draw_rounded_rect(surface, rect, color, h // 2)
        txt_col = (255, 255, 255)
    else:
        draw_rounded_rect(surface, rect, _darken(color, 0.78), h // 2)
        draw_rounded_rect(surface, rect, _darken(color, 0.25), h // 2, 1)
        txt_col = _lighten(color, 0.25)
    draw_text(surface, text, font, txt_col, rect.center)
    return rect


def _measure_key_row(items, size):
    key_font = get_font(size - 1, family="semibold")
    txt_font = get_font(size, family="body")
    widths = []
    for kind, text in items:
        if kind == "key":
            widths.append(key_font.size(text)[0] + 14)
        else:
            widths.append(txt_font.size(text)[0])
    total = sum(widths) + 7 * (len(items) - 1)
    return widths, total


def draw_key_row(surface, items, pos, anchor="center", size=14, text_color=None):
    """A row of keycaps and words, e.g. [("key","W A S D"), ("text","move")]."""
    key_font = get_font(size - 1, family="semibold")
    txt_font = get_font(size, family="body")
    text_color = text_color or COLORS["text_gray"]
    widths, total = _measure_key_row(items, size)
    key_h = size + 10
    x, y = pos
    if anchor == "center":
        x -= total // 2
    elif anchor == "right":
        x -= total
    for (kind, text), w in zip(items, widths):
        if kind == "key":
            r = pygame.Rect(x, y - key_h // 2, w, key_h)
            draw_rounded_rect(surface, r.move(0, 2), (6, 7, 10), 6)
            draw_rounded_rect(surface, r, (38, 42, 56), 6)
            draw_rounded_rect(surface, r, (78, 85, 108), 6, 1)
            draw_text(surface, text, key_font, COLORS["text_white"], r.center)
        elif kind == "accent":
            draw_text(surface, text, get_font(size, family="semibold"), COLORS["accent_gold"], (x, y),
                      anchor="midleft")
        else:
            draw_text(surface, text, txt_font, text_color, (x, y), anchor="midleft")
        x += w + 7
    return total


# ======================================================================
# Widgets
# ======================================================================
class Button:
    def __init__(self, x, y, w, h, text, callback=None, font_size=28,
                 idle_color=None, hover_color=None, active_color=None, text_color=None, radius=12,
                 primary=False, accent=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font_size = font_size
        self.idle_color = idle_color or COLORS["button_idle"]
        self.hover_color = hover_color or COLORS["button_hover"]
        self.active_color = active_color or COLORS["button_active"]
        self.text_color = text_color or COLORS["text_white"]
        self.radius = radius
        self.primary = primary
        self.accent = accent or COLORS["accent_gold"]
        self.hovered = False
        self.pressed = False

    def handle_event(self, event):
        clicked = False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.rect.collidepoint(event.pos) and self.pressed:
                self.pressed = False
                clicked = True
                if self.callback:
                    self.callback()
            else:
                self.pressed = False
        return clicked

    def draw(self, surface):
        draw_rect = self.rect.copy()
        if self.pressed:
            col = self.active_color
            draw_rect.y += 2
        elif self.hovered:
            col = self.hover_color
            draw_rect.y -= 2
            draw_glow(surface, draw_rect, self.accent, pad=14, radius=self.radius + 6, alpha=55, layers=3)
        else:
            col = self.idle_color

        # Drop shadow for depth.
        draw_rounded_rect(surface, draw_rect.move(0, 4), (4, 5, 8), self.radius)

        if self.primary:
            border_c = _lighten(self.accent, 0.2) if self.hovered else self.accent
            border_w = 2
            text_col = _lighten(self.accent, 0.35)
        else:
            border_c = self.accent if self.hovered else tuple(min(255, c + 28) for c in col)
            border_w = 2 if self.hovered else 1
            text_col = self.text_color
        draw_panel(surface, draw_rect, fill=col, border=border_c, radius=self.radius, border_w=border_w)

        font = get_font(self.font_size, bold=True)
        # Shrink the label rather than let it spill past the button edge.
        size = self.font_size
        while font.size(self.text)[0] > draw_rect.width - 24 and size > 12:
            size -= 1
            font = get_font(size, bold=True)
        draw_text(surface, self.text, font, text_col, draw_rect.center, shadow=True)


class Slider:
    def __init__(self, x, y, w, h, min_val=0, max_val=100, initial=50):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.dragging = False
        self.handle_r = h + 4

    @property
    def ratio(self):
        return (self.value - self.min_val) / (self.max_val - self.min_val)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.inflate(10, 10).collidepoint(event.pos):
                self.dragging = True
                self._update_from_mouse(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_from_mouse(event.pos)

    def _update_from_mouse(self, pos):
        x = pos[0]
        left = self.rect.left
        right = self.rect.right
        r = (x - left) / (right - left)
        r = max(0, min(1, r))
        self.value = self.min_val + r * (self.max_val - self.min_val)

    def draw(self, surface):
        track_rect = pygame.Rect(self.rect.x, self.rect.centery - 4, self.rect.width, 8)
        draw_rounded_rect(surface, track_rect, (20, 20, 30), 4)
        fill_rect = pygame.Rect(self.rect.x, self.rect.centery - 4, int(self.rect.width * self.ratio), 8)
        draw_rounded_rect(surface, fill_rect, COLORS["accent_gold"], 4)
        hx = self.rect.x + self.rect.width * self.ratio
        hy = self.rect.centery
        pygame.draw.circle(surface, COLORS["button_active"], (int(hx), int(hy)), self.handle_r)
        pygame.draw.circle(surface, COLORS["accent_gold"], (int(hx), int(hy)), self.handle_r - 2)


# ======================================================================
# Layout helpers (shared with click handling in main.py)
# ======================================================================
def get_top_card_rects(names):
    """Single source of truth for the top-select card grid geometry, shared
    by the click handler (main.py) and the renderer below."""
    card_w, card_h = 240, 236
    gap_x, gap_y = 20, 14
    cols = 4
    start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
    start_y = 132
    rects = {}
    for idx, name in enumerate(names):
        col = idx % cols
        row = idx // cols
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_y)
        rects[name] = pygame.Rect(cx, cy, card_w, card_h)
    return rects


def get_arena_card_rects(keys):
    """Single source of truth for the arena-select card grid geometry, shared
    by the click handler (main.py) and the renderer below."""
    card_w, card_h = 260, 350
    gap_x = 30
    cols = 4
    start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
    start_y = 128
    rects = {}
    for idx, key in enumerate(keys):
        col = idx % cols
        row = idx // cols
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_x)
        rects[key] = pygame.Rect(cx, cy, card_w, card_h)
    return rects


# Stat bar ranges, taken from the presets so every bar uses the full width.
def _preset_range(key):
    vals = [p[key] for p in TOP_PRESETS.values()]
    return min(vals), max(vals)


_RANGES = {k: _preset_range(k) for k in ("mass", "spin_speed", "spin_decay", "grip")}


def _norm(value, key, invert=False):
    lo, hi = _RANGES[key]
    t = 0.5 if hi == lo else (value - lo) / (hi - lo)
    if invert:
        t = 1 - t
    return 0.18 + 0.82 * max(0.0, min(1.0, t))


def top_stat_rows(preset):
    """(label, bar ratio, value text) for a top's card. "Stamina" replaces the
    raw decay number: a longer bar now always means better."""
    return [
        ("Mass", _norm(preset["mass"], "mass"), f"{preset['mass']:.1f}"),
        ("Spin", _norm(preset["spin_speed"], "spin_speed"), f"{preset['spin_speed']}"),
        ("Stamina", _norm(preset["spin_decay"], "spin_decay", invert=True),
         f"{int(preset['spin_speed'] / preset['spin_decay'])}s"),
        ("Grip", _norm(preset["grip"], "grip"), f"{preset['grip']:.1f}"),
    ]


def _draw_top_icon(surface, cx, cy, r, preset, spinning=False):
    rot = pygame.time.get_ticks() * 0.004 if spinning else 0.35
    shadow = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(shadow, (0, 0, 0, 110), (r + 2, r + 2), r)
    surface.blit(shadow, (cx - r - 2 + 3, cy - r - 2 + 5))
    art = render_top(r, preset["color"], preset["accent"], preset["type"], rot, 0.0)
    surface.blit(art, art.get_rect(center=(cx, cy)))


# ======================================================================
# HUD
# ======================================================================
def draw_spin_bar(surface, x, y, w, h, ratio, label="SPIN", player_col=None):
    """Spin meter. If label is not None the "LABEL NN%" caption is drawn
    under the bar."""
    ratio = max(0.0, min(1.0, ratio))
    if ratio > 0.55:
        col = COLORS["spin_full"]
    elif ratio > 0.25:
        col = COLORS["spin_mid"]
    else:
        col = COLORS["spin_low"]
        if ratio < 0.15:
            pulse = (math.sin(pygame.time.get_ticks() * 0.012) + 1) * 0.5
            col = tuple(min(255, int(c + pulse * 40)) for c in col)

    bg_rect = pygame.Rect(x, y, w, h)
    draw_rounded_rect(surface, bg_rect, (14, 14, 22), h // 2)

    if ratio > 0:
        fill_w = max(h - 4, int((w - 4) * ratio))
        fill_rect = pygame.Rect(x + 2, y + 2, fill_w, h - 4)
        draw_rounded_rect(surface, fill_rect, col, (h - 4) // 2)
        hl = pygame.Rect(x + 4, y + 3, max(0, fill_w - 4), max(1, (h - 4) // 3))
        draw_rounded_rect(surface, hl, _lighten(col, 0.35), hl.height // 2)

    for t in (0.25, 0.5, 0.75):
        tx = x + int(w * t)
        pygame.draw.line(surface, (10, 9, 15), (tx, y + 2), (tx, y + h - 3), 1)

    border = player_col or COLORS["panel_border"]
    draw_rounded_rect(surface, bg_rect, border, h // 2, 2)

    if label is not None:
        font = get_font(14, family="semibold")
        draw_text(surface, f"{label}  {int(round(ratio * 100))}%", font, COLORS["text_white"],
                  (x + 4, y + h + 4), anchor="topleft")


def draw_special_bar(surface, x, y, w, h, ratio, name="SPECIAL"):
    # Special ability system removed; keep function as no-op for backward compatibility
    pass


def _draw_hud_panel(surface, panel, top, player_label, is_left):
    player_col = COLORS["p1_color"] if is_left else COLORS["p2_color"]
    ko = top.is_knocked_out
    ko_flash = ko and int(pygame.time.get_ticks() / 120) % 2 == 0
    border_col = COLORS["danger"] if ko_flash else player_col
    draw_panel(surface, panel, fill=COLORS["ui_panel"], border=border_col, radius=14, border_w=2)

    # Row 1: player badge, top name, type chip.
    badge_txt = "P1" if is_left else ("AI" if player_label == "AI" else "P2")
    badge_w = get_font(12, family="semibold").size(badge_txt)[0] + 18
    badge = draw_chip(surface, badge_txt, (panel.x + 14 + badge_w // 2, panel.y + 21), player_col,
                      size=12, filled=True, height=20)

    name_font = get_font(18, bold=True)
    type_rect_w = get_font(11, family="semibold").size(top.type.value.upper())[0] + 18
    max_name_w = panel.right - 14 - type_rect_w - 10 - (badge.right + 8)
    name = top.name
    if name_font.size(name)[0] > max_name_w:
        while len(name) > 3 and name_font.size(name + "...")[0] > max_name_w:
            name = name[:-1]
        name = name.rstrip() + "..."
    draw_text(surface, name, name_font, COLORS["text_white"], (badge.right + 8, badge.centery), anchor="midleft")
    draw_chip(surface, top.type.value.upper(), (panel.right - 14 - type_rect_w // 2, badge.centery),
              TYPE_COLORS.get(top.type, COLORS["text_gray"]), size=11)

    # Row 2: spin bar + percentage.
    spin_ratio = max(0.0, min(1.0, top.spin / top.max_spin if top.max_spin > 0 else 0))
    pct_font = get_font(18, bold=True)
    bar_w = panel.width - 28 - 56
    draw_spin_bar(surface, panel.x + 14, panel.y + 40, bar_w, 16, spin_ratio, None, player_col)
    draw_text(surface, f"{int(round(spin_ratio * 100))}%", pct_font, COLORS["text_white"],
              (panel.right - 14, panel.y + 48), anchor="midright")

    # Row 3: status line.
    small = get_font(12, family="semibold")
    status_y = panel.y + 72
    if ko:
        draw_text(surface, "RING OUT!", small, COLORS["danger"], (panel.x + 14, status_y), anchor="midleft")
    elif not top.is_launched:
        draw_text(surface, "AIMING…", small, COLORS["text_gray"], (panel.x + 14, status_y), anchor="midleft")
    elif top.dash_cooldown > 0:
        draw_text(surface, f"DASH  {top.dash_cooldown:.1f}s", small, COLORS["text_dim"],
                  (panel.x + 14, status_y), anchor="midleft")
    else:
        draw_text(surface, "DASH READY", small, COLORS["accent_green"], (panel.x + 14, status_y), anchor="midleft")

    if not ko and top.is_launched and spin_ratio < 0.2:
        blink = int(pygame.time.get_ticks() / 250) % 2 == 0
        if blink:
            draw_text(surface, "LOW SPIN!", small, COLORS["danger"], (panel.right - 14, status_y), anchor="midright")
    else:
        draw_text(surface, player_label, small, player_col, (panel.right - 14, status_y), anchor="midright")


def draw_hud(surface, p1, p2, match_time, p1_label="PLAYER 1", p2_label="PLAYER 2"):
    panel_w, panel_h = 330, 88
    left_panel = pygame.Rect(18, 14, panel_w, panel_h)
    right_panel = pygame.Rect(SCREEN_WIDTH - 18 - panel_w, 14, panel_w, panel_h)

    _draw_hud_panel(surface, left_panel, p1, p1_label, is_left=True)
    _draw_hud_panel(surface, right_panel, p2, p2_label, is_left=False)

    center_w, center_h = 160, 66
    center_rect = pygame.Rect(SCREEN_WIDTH // 2 - center_w // 2, 14, center_w, center_h)
    low_time = match_time <= 20
    draw_panel(surface, center_rect, fill=COLORS["ui_panel"],
               border=COLORS["danger"] if low_time else COLORS["accent_gold"], radius=14, border_w=2)

    mins = int(match_time // 60)
    secs = int(match_time % 60)
    blink = int(pygame.time.get_ticks() / 300) % 2 == 0
    time_color = COLORS["danger"] if low_time and blink else COLORS["text_white"]
    draw_text(surface, f"{mins:02d}:{secs:02d}", get_font(34, bold=True), time_color,
              (SCREEN_WIDTH // 2, 40))
    draw_text(surface, "MATCH TIME", get_font(11, family="semibold"), COLORS["text_gray"],
              (SCREEN_WIDTH // 2, 67))


# ======================================================================
# Screens
# ======================================================================
def draw_menu(surface, buttons, version=None, stats=None):
    surface.fill(COLORS["bg_dark"])

    title_font = get_font(88, bold=True)
    title_pos = (SCREEN_WIDTH // 2, 140)
    title_surf = title_font.render("PAMBARAM", True, COLORS["accent_gold"])
    title_rect = title_surf.get_rect(center=title_pos)
    draw_text_glow(surface, title_surf, title_rect, COLORS["accent_gold"], strength=0.6, spread=8)
    draw_text(surface, "PAMBARAM", title_font, (0, 0, 0), (title_pos[0] + 3, title_pos[1] + 5))
    surface.blit(title_surf, title_rect)

    sub_font = get_font(20, family="semibold")
    draw_text(surface, "S P I N N I N G   T O P   B A T T L E   A R E N A", sub_font,
              COLORS["text_gray"], (SCREEN_WIDTH // 2, 210))

    line_w = 120
    for side in (-1, 1):
        x0 = SCREEN_WIDTH // 2 + side * 300
        pygame.draw.line(surface, COLORS["panel_border"], (x0 - line_w // 2, 210), (x0 + line_w // 2, 210), 1)

    for b in buttons:
        b.draw(surface)

    # Controls footer.
    footer = pygame.Rect(SCREEN_WIDTH // 2 - 470, SCREEN_HEIGHT - 112, 940, 86)
    draw_panel(surface, footer, fill=COLORS["ui_panel"], border=COLORS["panel_border"], radius=14, border_w=1)
    draw_chip(surface, "P1", (footer.x + 36, footer.y + 27), COLORS["p1_color"], filled=True, height=22)
    draw_key_row(surface, [("key", "W A S D"), ("text", "move"), ("key", "L-SHIFT"), ("text", "dash"),
                           ("key", "A / D"), ("text", "aim"), ("key", "SPACE"), ("text", "launch power")],
                 (footer.x + 62, footer.y + 27), anchor="left")
    draw_chip(surface, "P2", (footer.x + 36, footer.y + 60), COLORS["p2_color"], filled=True, height=22)
    draw_key_row(surface, [("key", "ARROWS"), ("text", "move"), ("key", "R-SHIFT"), ("text", "dash"),
                           ("key", "← / →"), ("text", "aim"), ("key", "ENTER"), ("text", "launch power")],
                 (footer.x + 62, footer.y + 60), anchor="left")
    draw_text(surface, "Playing vs AI? Player 1 can use WASD or the arrow keys.", get_font(13, family="body"),
              COLORS["text_dim"], (SCREEN_WIDTH // 2, footer.y - 16))
    draw_key_row(surface, [("key", "ESC"), ("text", "pause"), ("key", "M"), ("text", "mute")],
                 (footer.right - 22, footer.y + 27), anchor="right")
    draw_key_row(surface, [("key", "F11"), ("text", "fullscreen")], (footer.right - 22, footer.y + 60),
                 anchor="right")

    small = get_font(12, family="semibold")
    if version:
        draw_text(surface, f"v{version}", small, COLORS["text_dim"], (SCREEN_WIDTH - 14, 14), anchor="topright")
    if stats and stats.get("matches", 0) > 0:
        line = (f"Matches {stats['matches']}   ·   P1 wins {stats['p1_wins']}   ·   "
                f"Best score {stats['best_score']}")
        draw_text(surface, line, small, COLORS["text_dim"], (14, 14), anchor="topleft")


def _draw_player_pill(surface, rect, tag, name, hint, color):
    draw_panel(surface, rect, fill=_darken(color, 0.8), border=color, radius=rect.height // 2, border_w=2)
    chip = draw_chip(surface, tag, (rect.x + 30, rect.centery), color, size=12, filled=True, height=22)
    draw_text(surface, name, get_font(18, bold=True), COLORS["text_white"], (chip.right + 10, rect.centery),
              anchor="midleft")
    draw_text(surface, hint, get_font(12, family="semibold"), _lighten(color, 0.3),
              (rect.right - 18, rect.centery), anchor="midright")


def draw_top_select(surface, tops_data, p1_selection, p2_selection, p2_ai, buttons, difficulty, hover=None):
    surface.fill(COLORS["bg_dark"])

    draw_text(surface, "CHOOSE YOUR TOP", get_font(46, bold=True), COLORS["accent_gold"],
              (SCREEN_WIDTH // 2, 44), shadow=True)

    # Who-picked-what bar.
    pill_w, pill_h = 440, 38
    left = pygame.Rect(40, 80, pill_w, pill_h)
    right = pygame.Rect(SCREEN_WIDTH - 40 - pill_w, 80, pill_w, pill_h)
    _draw_player_pill(surface, left, "P1", p1_selection, "LEFT CLICK", COLORS["p1_color"])
    p2_tag = f"AI · {difficulty.name}" if p2_ai else "P2"
    _draw_player_pill(surface, right, p2_tag, p2_selection, "RIGHT CLICK", COLORS["p2_color"])
    draw_text(surface, "VS", get_font(22, bold=True), COLORS["text_gray"], (SCREEN_WIDTH // 2, left.centery))

    card_rects = get_top_card_rects(tops_data.keys())
    name_font = get_font(19, bold=True)
    label_font = get_font(13, family="semibold")
    value_font = get_font(12, family="semibold")
    desc_font = get_font(13, family="body")

    for name, preset in tops_data.items():
        card = card_rects[name]
        p1_sel = p1_selection == name
        p2_sel = p2_selection == name
        hovered = hover == name

        if p1_sel and p2_sel:
            glow_col = COLORS["accent_purple"]
        elif p1_sel:
            glow_col = COLORS["p1_color"]
        elif p2_sel:
            glow_col = COLORS["p2_color"]
        else:
            glow_col = None

        if glow_col:
            draw_glow(surface, card, glow_col, pad=12, radius=16, alpha=40, layers=3)
        fill = (26, 29, 41) if hovered else COLORS["bg_mid"]
        if p1_sel and p2_sel:
            draw_panel(surface, card, fill=fill, border=COLORS["p1_color"], radius=12, border_w=3)
            draw_rounded_rect(surface, card.inflate(-8, -8), COLORS["p2_color"], 9, 2)
        elif glow_col:
            draw_panel(surface, card, fill=fill, border=glow_col, radius=12, border_w=3)
        else:
            border = (96, 104, 132) if hovered else COLORS["panel_border"]
            draw_panel(surface, card, fill=fill, border=border, radius=12, border_w=1)

        _draw_top_icon(surface, card.centerx, card.y + 44, 30, preset, spinning=(p1_sel or p2_sel or hovered))

        draw_text(surface, name, name_font, COLORS["text_white"], (card.centerx, card.y + 90))
        draw_chip(surface, preset["type"].value.upper() + " TYPE", (card.centerx, card.y + 114),
                  TYPE_COLORS.get(preset["type"], COLORS["text_gray"]), size=11, height=19)

        stat_y = card.y + 136
        bar_x = card.x + 82
        bar_w = card.width - 82 - 52
        for s_i, (sname, sratio, sval) in enumerate(top_stat_rows(preset)):
            cy = stat_y + s_i * 17
            draw_text(surface, sname, label_font, COLORS["text_gray"], (card.x + 16, cy), anchor="midleft")
            bar_rect = pygame.Rect(bar_x, cy - 3, bar_w, 6)
            draw_rounded_rect(surface, bar_rect, (10, 11, 17), 3)
            fill_rect = pygame.Rect(bar_x, cy - 3, max(6, int(bar_w * sratio)), 6)
            draw_rounded_rect(surface, fill_rect, COLORS["accent_gold"], 3)
            draw_text(surface, sval, value_font, COLORS["text_white"], (card.right - 16, cy), anchor="midright")

        draw_text_block(surface, preset.get("desc", ""), desc_font, (176, 182, 198),
                        card.centerx, card.y + 200, card.width - 28, max_lines=2)

        if p1_sel:
            draw_chip(surface, "P1", (card.x + 26, card.y + 18), COLORS["p1_color"], size=12, filled=True, height=22)
        if p2_sel:
            draw_chip(surface, "AI" if p2_ai else "P2", (card.right - 26, card.y + 18), COLORS["p2_color"],
                      size=12, filled=True, height=22)

    for b in buttons:
        b.draw(surface)

    draw_key_row(surface, [("key", "LEFT CLICK"), ("text", "pick for Player 1"), ("text", "   "),
                           ("key", "RIGHT CLICK"), ("text", "pick for " + ("the AI" if p2_ai else "Player 2")),
                           ("text", "   "), ("key", "ENTER"), ("text", "next")],
                 (SCREEN_WIDTH // 2, 670), size=15)


def draw_arena_select(surface, arenas_data, selection, buttons, hover=None):
    surface.fill(COLORS["bg_dark"])
    draw_text(surface, "CHOOSE ARENA", get_font(46, bold=True), COLORS["accent_gold"],
              (SCREEN_WIDTH // 2, 50), shadow=True)
    draw_text(surface, "Each arena changes floor grip and hazards", get_font(17, family="body"),
              COLORS["text_gray"], (SCREEN_WIDTH // 2, 92))

    card_rects = get_arena_card_rects(arenas_data.keys())
    name_font = get_font(22, bold=True)
    key_font = get_font(14, family="semibold")
    desc_font = get_font(14, family="body")

    for key, preset in arenas_data.items():
        card = card_rects[key]
        selected = selection == key
        hovered = hover == key

        if selected:
            draw_glow(surface, card, COLORS["accent_gold"], pad=12, radius=18, alpha=40, layers=3)
        if selected:
            border, bw = COLORS["accent_gold"], 3
        else:
            border, bw = ((96, 104, 132) if hovered else COLORS["panel_border"]), 1
        draw_panel(surface, card, fill=(26, 29, 41) if hovered else COLORS["bg_mid"],
                   border=border, radius=16, border_w=bw)

        acx, acy, ar = card.centerx, card.y + 112, 72
        pygame.gfxdraw.filled_circle(surface, acx, acy, ar + 22, preset["void_color"])
        pygame.gfxdraw.aacircle(surface, acx, acy, ar + 22, preset["void_color"])
        pygame.draw.circle(surface, preset["ring_color"], (acx, acy), ar + 6)
        pygame.gfxdraw.filled_circle(surface, acx, acy, ar, preset["floor_color"])
        pygame.gfxdraw.aacircle(surface, acx, acy, ar, preset["floor_color"])
        for rr in (24, 48):
            pygame.gfxdraw.aacircle(surface, acx, acy, rr, _darken(preset["floor_color"], 0.18))
        for haz in preset["hazards"]:
            if haz == "pillars":
                for a in range(4):
                    ang = a * math.pi / 2
                    px, py = int(acx + math.cos(ang) * 20), int(acy + math.sin(ang) * 20)
                    pygame.gfxdraw.filled_circle(surface, px, py, 6, (150, 130, 100))
                    pygame.gfxdraw.aacircle(surface, px, py, 6, (80, 60, 40))
            elif haz == "boost_pads":
                for a in range(4):
                    ang = math.pi / 4 + a * math.pi / 2
                    px, py = int(acx + math.cos(ang) * 40), int(acy + math.sin(ang) * 40)
                    pygame.gfxdraw.aacircle(surface, px, py, 9, (80, 255, 200))
                    pygame.gfxdraw.filled_circle(surface, px, py, 4, (160, 255, 230))

        draw_text(surface, preset["name"], name_font, COLORS["text_white"], (card.centerx, card.y + 222))
        draw_text(surface, key, key_font, COLORS["text_gray"], (card.centerx, card.y + 246))
        draw_text_block(surface, preset["desc"], desc_font, (176, 182, 198), card.centerx, card.y + 262,
                        card.width - 32, max_lines=2)

        g = preset["grip_mod"]
        grip_txt, grip_col = ("LOW GRIP", COLORS["accent_cyan"]) if g < 0.9 else \
            (("HIGH GRIP", COLORS["accent_green"]) if g > 1.05 else ("NORMAL GRIP", COLORS["text_gray"]))
        haz = preset["hazards"]
        haz_txt = "PILLARS" if "pillars" in haz else ("BOOST PADS" if "boost_pads" in haz else "NO HAZARDS")
        haz_col = COLORS["accent_purple"] if haz else COLORS["text_gray"]
        f = get_font(11, family="semibold")
        w1 = f.size(grip_txt)[0] + 18
        w2 = f.size(haz_txt)[0] + 18
        total = w1 + w2 + 8
        x0 = card.centerx - total // 2
        draw_chip(surface, grip_txt, (x0 + w1 // 2, card.y + 322), grip_col, size=11, height=20)
        draw_chip(surface, haz_txt, (x0 + w1 + 8 + w2 // 2, card.y + 322), haz_col, size=11, height=20)

        if selected:
            draw_chip(surface, "SELECTED", (card.right - 50, card.y + 18), COLORS["accent_gold"], size=11,
                      filled=True, height=20)

    draw_key_row(surface, [("key", "CLICK"), ("text", "or"), ("key", "← →"), ("text", "to choose an arena,"),
                           ("key", "ENTER"), ("text", "or"), ("accent", "START!"), ("text", "to fight")],
                 (SCREEN_WIDTH // 2, 530), size=15)

    for b in buttons:
        b.draw(surface)


def draw_pause(surface, buttons, p2_is_ai=True):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surface.blit(overlay, (0, 0))

    panel = pygame.Rect(SCREEN_WIDTH // 2 - 250, 130, 500, 500)
    draw_panel(surface, panel, fill=COLORS["ui_panel"], border=COLORS["panel_border"], radius=18, border_w=2)

    draw_text(surface, "PAUSED", get_font(56, bold=True), COLORS["accent_gold"], (SCREEN_WIDTH // 2, 200),
              shadow=True)
    for b in buttons:
        b.draw(surface)

    pygame.draw.line(surface, COLORS["panel_border"], (panel.x + 30, 540), (panel.right - 30, 540), 1)
    draw_key_row(surface, [("key", "W A S D"), ("text", "move"), ("key", "L-SHIFT"), ("text", "dash")],
                 (SCREEN_WIDTH // 2, 568), size=13)
    if not p2_is_ai:
        draw_key_row(surface, [("key", "ARROWS"), ("text", "move"), ("key", "R-SHIFT"), ("text", "dash")],
                     (SCREEN_WIDTH // 2, 600), size=13)
    else:
        draw_key_row(surface, [("text", "or"), ("key", "ARROWS"), ("text", "move"), ("key", "R-SHIFT"),
                               ("text", "dash")], (SCREEN_WIDTH // 2, 600), size=13)


def draw_game_over(surface, winner, stats, buttons):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    surface.blit(overlay, (0, 0))

    is_p1 = winner and winner.player_id == 1
    win_color = COLORS["p1_color"] if is_p1 else (COLORS["p2_color"] if winner else COLORS["accent_gold"])

    if winner:
        label = stats.get(f"p{winner.player_id}_label", f"PLAYER {winner.player_id}")
        result = f"{label} WINS!"
    else:
        result = "DRAW!"
    big_font = get_font(72, bold=True)
    title_surf = big_font.render(result, True, win_color)
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
    draw_text_glow(surface, title_surf, title_rect, win_color, strength=0.6, spread=8)
    draw_text(surface, result, big_font, win_color, title_rect.center, shadow=True)

    y = 212
    if winner:
        draw_text(surface, winner.name, get_font(30, bold=True), _lighten(winner.color, 0.35),
                  (SCREEN_WIDTH // 2, y))
        y += 36
    draw_text_block(surface, stats.get("win_reason", ""), get_font(19, family="semibold"), (205, 210, 222),
                    SCREEN_WIDTH // 2, y, 820, max_lines=2)

    panel = pygame.Rect(SCREEN_WIDTH // 2 - 300, 318, 600, 260)
    draw_panel(surface, panel, fill=COLORS["ui_panel"], border=COLORS["accent_gold"], radius=16, border_w=2)

    p1_pct = max(0.0, min(1.0, stats.get("p1_spin_pct", 0.0)))
    p2_pct = max(0.0, min(1.0, stats.get("p2_spin_pct", 0.0)))

    col_w = 230
    label_font = get_font(13, family="semibold")
    name_font = get_font(18, bold=True)
    pct_font = get_font(30, bold=True)
    for side, (pid, pct, col) in enumerate(((1, p1_pct, COLORS["p1_color"]), (2, p2_pct, COLORS["p2_color"]))):
        cx = panel.x + 30 + col_w // 2 if side == 0 else panel.right - 30 - col_w // 2
        draw_text(surface, stats.get(f"p{pid}_label", f"PLAYER {pid}"), label_font, col, (cx, panel.y + 26))
        draw_text(surface, stats.get(f"p{pid}_name", ""), name_font, COLORS["text_white"], (cx, panel.y + 50))
        draw_spin_bar(surface, cx - col_w // 2, panel.y + 74, col_w, 18, pct, None, col)
        draw_text(surface, f"{int(round(pct * 100))}%", pct_font, COLORS["text_white"], (cx, panel.y + 116))
        draw_text(surface, "SPIN LEFT", get_font(11, family="semibold"), COLORS["text_gray"], (cx, panel.y + 140))

    draw_text(surface, "VS", get_font(24, bold=True), COLORS["text_gray"], (panel.centerx, panel.y + 84))

    pygame.draw.line(surface, COLORS["panel_border"], (panel.x + 30, panel.y + 164),
                     (panel.right - 30, panel.y + 164), 1)

    match_time = stats.get("match_time", 0)
    mins = int(match_time // 60)
    secs = int(match_time % 60)
    points = stats.get("points", 0)
    val_font = get_font(28, bold=True)
    cap_font = get_font(12, family="semibold")
    blocks = [("MATCH TIME", f"{mins:02d}:{secs:02d}", COLORS["text_white"])]
    blocks.append(("SCORE", f"+{points}" if points > 0 else "—", COLORS["accent_gold"]))
    if "best_score" in stats:
        blocks.append(("BEST", str(stats["best_score"]), COLORS["text_white"]))
    for i, (cap, val, col) in enumerate(blocks):
        cx = panel.x + panel.width * (i + 1) // (len(blocks) + 1)
        draw_text(surface, val, val_font, col, (cx, panel.y + 200))
        draw_text(surface, cap, cap_font, COLORS["text_gray"], (cx, panel.y + 232))

    if stats.get("new_best"):
        draw_chip(surface, "NEW BEST!", (panel.right - 58, panel.y + 176), COLORS["accent_gold"], size=12,
                  filled=True, height=22)

    draw_key_row(surface, [("key", "ENTER"), ("text", "rematch"), ("key", "ESC"), ("text", "main menu")],
                 (SCREEN_WIDTH // 2, 700), size=13)

    for b in buttons:
        b.draw(surface)


def draw_toast(surface, text, alpha_t=1.0):
    """Short status message (e.g. SOUND OFF) near the bottom of the screen."""
    font = get_font(16, bold=True)
    w = font.size(text)[0] + 40
    rect = pygame.Rect(SCREEN_WIDTH // 2 - w // 2, 112, w, 40)
    a = int(235 * max(0.0, min(1.0, alpha_t)))
    draw_panel(surface, rect, fill=(10, 11, 18, a), border=COLORS["accent_gold"], radius=20, border_w=2)
    draw_text(surface, text, font, COLORS["text_white"], rect.center, alpha=int(255 * alpha_t))


# ======================================================================
# Match start: aiming, countdown, FIGHT banner
# ======================================================================
def draw_aim_arrow(surface, top, angle, color, label, active=False):
    """Arrow showing where a top will fly when the countdown ends."""
    pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
    r = top.radius
    dx, dy = math.cos(angle), math.sin(angle)
    length = 120 + (10 if active else int(pulse * 8))
    x0, y0 = top.x + dx * (r + 8), top.y + dy * (r + 8)
    x1, y1 = top.x + dx * (r + length), top.y + dy * (r + length)

    col = _lighten(color, 0.3) if active else color
    # Dashed shaft.
    seg, gap = 12, 7
    dist = math.hypot(x1 - x0, y1 - y0) - 16
    d = 0.0
    while d < dist:
        e = min(dist, d + seg)
        pygame.draw.line(surface, col, (x0 + dx * d, y0 + dy * d), (x0 + dx * e, y0 + dy * e), 5)
        d += seg + gap
    # Head.
    px, py = -dy, dx
    tip = (x1 + dx * 6, y1 + dy * 6)
    left = (x1 - dx * 16 + px * 12, y1 - dy * 16 + py * 12)
    right = (x1 - dx * 16 - px * 12, y1 - dy * 16 - py * 12)
    pts = [tuple(map(int, p)) for p in (tip, left, right)]
    pygame.gfxdraw.filled_polygon(surface, pts, col)
    pygame.gfxdraw.aapolygon(surface, pts, col)

    draw_chip(surface, label, (int(top.x), int(top.y - r - 24)), color, size=12, filled=True, height=22)


def draw_aim_hints(surface, p2_is_ai):
    """Bottom-corner panels telling each player how to aim and launch."""
    w, h = 268, 104

    def panel(rect, tag, color, title, row1, row2):
        draw_panel(surface, rect, fill=COLORS["ui_panel"], border=color, radius=12, border_w=2)
        chip = draw_chip(surface, tag, (rect.x + 26, rect.y + 20), color, size=12, filled=True, height=22)
        draw_text(surface, title, get_font(15, bold=True), COLORS["text_white"], (chip.right + 8, chip.centery),
                  anchor="midleft")
        draw_key_row(surface, row1, (rect.x + 14, rect.y + 50), anchor="left", size=13)
        draw_key_row(surface, row2, (rect.x + 14, rect.y + 80), anchor="left", size=13)

    left = pygame.Rect(16, SCREEN_HEIGHT - h - 14, w, h)
    if p2_is_ai:
        panel(left, "P1", COLORS["p1_color"], "AIM & LAUNCH",
              [("key", "A D"), ("text", "/"), ("key", "← →"), ("text", "aim")],
              [("key", "SPACE"), ("text", "/"), ("key", "ENTER"), ("text", "lock power")])
    else:
        panel(left, "P1", COLORS["p1_color"], "AIM & LAUNCH",
              [("key", "A"), ("key", "D"), ("text", "aim"), ("key", "SPACE"), ("text", "power")],
              [("text", "or"), ("key", "LEFT-DRAG"), ("text", "and release")])

    right = pygame.Rect(SCREEN_WIDTH - 16 - w, SCREEN_HEIGHT - h - 14, w, h)
    if p2_is_ai:
        draw_panel(surface, right, fill=COLORS["ui_panel"], border=COLORS["p2_color"], radius=12, border_w=2)
        chip = draw_chip(surface, "AI", (right.x + 26, right.y + 20), COLORS["p2_color"], size=12, filled=True,
                         height=22)
        draw_text(surface, "AI IS AIMING…", get_font(15, bold=True), COLORS["text_white"],
                  (chip.right + 8, chip.centery), anchor="midleft")
        draw_text(surface, "Lock power at the top of", get_font(13, family="body"), COLORS["text_gray"],
                  (right.x + 14, right.y + 50), anchor="midleft")
        draw_text(surface, "the swing for max stamina", get_font(13, family="body"), COLORS["text_gray"],
                  (right.x + 14, right.y + 72), anchor="midleft")
    else:
        panel(right, "P2", COLORS["p2_color"], "AIM & LAUNCH",
              [("key", "←"), ("key", "→"), ("text", "aim"), ("key", "ENTER"), ("text", "power")],
              [("text", "or"), ("key", "RIGHT-DRAG"), ("text", "and release")])


def draw_launch_meter(surface, top, value, locked, color, grade=None):
    """Vertical power meter beside a top during the countdown. The gold band
    at the top is the PERFECT zone; locked shows where the player stopped it."""
    bar_w, bar_h = 16, 120
    r = int(top.radius)
    x = int(top.x - r - 40 - bar_w) if top.player_id == 1 else int(top.x + r + 40)
    y = int(top.y - bar_h // 2)
    frame = pygame.Rect(x, y, bar_w, bar_h)
    draw_rounded_rect(surface, frame.inflate(8, 8), (10, 11, 18), 8)

    # Zones, from the top down: PERFECT (gold), GREAT (green), GOOD, WEAK.
    zones = [(1.0, 0.92, COLORS["accent_gold"]), (0.92, 0.75, COLORS["accent_green"]),
             (0.75, 0.50, (70, 110, 90)), (0.50, 0.0, (60, 40, 48))]
    v = locked if locked is not None else value
    for hi, lo, col in zones:
        zy = y + int((1 - hi) * bar_h)
        zh = max(1, int((hi - lo) * bar_h))
        pygame.draw.rect(surface, _darken(col, 0.62), (x, zy, bar_w, zh))
        # Bright fill for the part of each zone below the current power.
        fill_top = max(lo, min(hi, v))
        if fill_top > lo:
            fy = y + int((1 - fill_top) * bar_h)
            pygame.draw.rect(surface, col, (x + 3, fy, bar_w - 6, y + int((1 - lo) * bar_h) - fy))
    draw_rounded_rect(surface, frame, color, 4, 2)
    my = y + int((1 - v) * bar_h)
    marker_col = (255, 255, 255) if locked is None else _lighten(color, 0.4)
    pygame.draw.rect(surface, marker_col, (x - 5, my - 2, bar_w + 10, 4), border_radius=2)

    cap_font = get_font(11, family="semibold")
    if locked is None:
        draw_text(surface, "POWER", cap_font, COLORS["text_gray"], (frame.centerx, y - 14), shadow=True)
    else:
        q_col = COLORS["accent_gold"] if locked >= 0.92 else (
            COLORS["accent_green"] if locked >= 0.5 else COLORS["danger"])
        draw_text(surface, grade or "", get_font(14, bold=True), q_col, (frame.centerx, y - 15), shadow=True)
    draw_text(surface, f"{int(round(v * 100))}%", cap_font, COLORS["text_white"],
              (frame.centerx, frame.bottom + 14), shadow=True)


def draw_launch_popup(surface, top, text, sub, color, t):
    """Launch-grade text that floats up from a top after launch (t: 1 -> 0)."""
    t = max(0.0, min(1.0, t))
    alpha = int(255 * min(1.0, t * 3))
    rise = int((1 - t) * 30)
    cx, cy = int(top.x), int(top.y - top.radius - 40 - rise)
    big = get_font(24, bold=True)
    bw = max(big.size(text)[0], get_font(13, family="semibold").size(sub)[0]) + 28
    bg = pygame.Surface((bw, 56), pygame.SRCALPHA)
    pygame.draw.rect(bg, (8, 9, 14, int(alpha * 0.82)), bg.get_rect(), border_radius=12)
    pygame.draw.rect(bg, (*color[:3], alpha), bg.get_rect(), width=2, border_radius=12)
    surface.blit(bg, (cx - bw // 2, cy - 18))
    draw_text(surface, text, big, color, (cx, cy), shadow=True, alpha=alpha)
    draw_text(surface, sub, get_font(13, family="semibold"), COLORS["text_white"], (cx, cy + 22),
              shadow=True, alpha=alpha)


def draw_countdown(surface, count, progress=0.0):
    """count is 3, 2 or 1; progress (0..1) is how far through that number."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 80))
    surface.blit(overlay, (0, 0))

    header = pygame.Rect(SCREEN_WIDTH // 2 - 230, 112, 460, 58)
    draw_panel(surface, header, fill=(10, 11, 18, 225), border=COLORS["panel_border"], radius=14, border_w=1)
    draw_text(surface, "GET READY — AIM YOUR LAUNCH", get_font(21, bold=True), COLORS["text_white"],
              (SCREEN_WIDTH // 2, header.y + 20))
    draw_text(surface, "Both tops launch at the same time on FIGHT!", get_font(14, family="semibold"),
              COLORS["text_gray"], (SCREEN_WIDTH // 2, header.y + 42))

    if count <= 0:
        draw_fight_banner(surface, 1.0)
        return

    font = get_font(150, bold=True)
    txt = font.render(str(count), True, COLORS["accent_gold"])
    p = max(0.0, min(1.0, progress))
    scale = 1.25 - 0.25 * min(1.0, p * 4)
    alpha = 255 if p < 0.75 else int(255 * (1 - (p - 0.75) / 0.25))
    w, h = txt.get_width(), txt.get_height()
    scaled = pygame.transform.smoothscale(txt, (max(1, int(w * scale)), max(1, int(h * scale))))
    scaled.set_alpha(alpha)
    rect = scaled.get_rect(center=(SCREEN_WIDTH // 2, 290))
    draw_text_glow(surface, scaled, rect, COLORS["accent_gold"], strength=0.5 * alpha / 255, spread=8)
    shadow = pygame.transform.smoothscale(font.render(str(count), True, (0, 0, 0)), scaled.get_size())
    shadow.set_alpha(int(alpha * 0.6))
    surface.blit(shadow, rect.move(0, 5))
    surface.blit(scaled, rect)


def draw_fight_banner(surface, t):
    """t goes 1 -> 0 while the banner is on screen."""
    t = max(0.0, min(1.0, t))
    font = get_font(120, bold=True)
    txt = font.render("FIGHT!", True, COLORS["accent_red"])
    grow = 1.0 + (1.0 - t) * 0.35
    w, h = txt.get_width(), txt.get_height()
    scaled = pygame.transform.smoothscale(txt, (int(w * grow), int(h * grow)))
    alpha = int(255 * min(1.0, t * 2))
    scaled.set_alpha(alpha)
    rect = scaled.get_rect(center=(SCREEN_WIDTH // 2, 290))
    draw_text_glow(surface, scaled, rect, COLORS["accent_red"], strength=0.6 * alpha / 255, spread=8)
    surface.blit(scaled, rect)
