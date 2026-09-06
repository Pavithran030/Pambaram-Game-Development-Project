import pygame
import math
from .config import *


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
    """Shared panel styling: optional fill, optional stroke. One call site
    instead of every screen hand-rolling two draw_rounded_rect calls."""
    rect = pygame.Rect(rect)
    if fill is not None:
        draw_rounded_rect(surface, rect, fill, radius)
    if border is not None:
        draw_rounded_rect(surface, rect, border, radius, border_w)


def draw_glow(surface, rect, color, pad=18, alpha=50, layers=5, radius=None):
    """Soft radial-ish glow behind rect. Each layer is a pill (fully rounded
    on its own height) rather than a fixed corner radius, so wide short
    rects (like title text) get a smooth bloom instead of a visible box."""
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


class Button:
    def __init__(self, x, y, w, h, text, callback=None, font_size=28,
                 idle_color=None, hover_color=None, active_color=None, text_color=None, radius=12):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font_size = font_size
        self.idle_color = idle_color or COLORS["button_idle"]
        self.hover_color = hover_color or COLORS["button_hover"]
        self.active_color = active_color or COLORS["button_active"]
        self.text_color = text_color or COLORS["text_white"]
        self.radius = radius
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
            draw_glow(surface, draw_rect, COLORS["accent_gold"], pad=14, radius=self.radius + 6, alpha=55, layers=3)
        else:
            col = self.idle_color

        border_c = COLORS["accent_gold"] if self.hovered else tuple(min(255, c + 28) for c in col)
        draw_panel(surface, draw_rect, fill=col, border=border_c, radius=self.radius, border_w=2 if self.hovered else 1)

        font = get_font(self.font_size, bold=True)
        ts = font.render(self.text, True, self.text_color)
        tr = ts.get_rect(center=draw_rect.center)
        surface.blit(ts, tr)


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


def get_top_card_rects(names):
    """Single source of truth for the top-select card grid geometry, shared
    by the click handler (main.py) and the renderer below. Sized so two full
    rows of 8 cards clear the button bar at the bottom of the screen."""
    card_w, card_h = 240, 228
    gap_x, gap_y = 20, 14
    cols = 4
    start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
    start_y = 124
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
    card_w, card_h = 260, 340
    gap_x = 30
    cols = 4
    start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
    start_y = 120
    rects = {}
    for idx, key in enumerate(keys):
        col = idx % cols
        row = idx // cols
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_x)
        rects[key] = pygame.Rect(cx, cy, card_w, card_h)
    return rects


def draw_spin_bar(surface, x, y, w, h, ratio, label="SPIN", player_col=None):
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

    fill_w = max(4, int((w - 4) * ratio))
    fill_rect = pygame.Rect(x + 2, y + 2, fill_w, h - 4)
    draw_rounded_rect(surface, fill_rect, col, (h - 4) // 2)

    for t in (0.25, 0.5, 0.75):
        tx = x + int(w * t)
        pygame.draw.line(surface, (10, 9, 15), (tx, y + 2), (tx, y + h - 2), 1)

    border = player_col or COLORS["panel_border"]
    draw_rounded_rect(surface, bg_rect, border, h // 2, 2)

    font = get_font(14, bold=True)
    pct = int(ratio * 100)
    label_ts = font.render(f"{label} {pct}%", True, COLORS["text_white"])
    surface.blit(label_ts, (x + 8, y + h + 3))


def draw_special_bar(surface, x, y, w, h, ratio, name="SPECIAL"):
    ratio = max(0.0, min(1.0, ratio))
    ready = ratio >= 1.0
    bg_rect = pygame.Rect(x, y, w, h)

    if ready:
        draw_glow(surface, bg_rect, COLORS["special_ready"], pad=8, radius=h, alpha=45, layers=2)

    draw_rounded_rect(surface, bg_rect, (14, 14, 22), h // 2)

    fill_w = max(4, int((w - 4) * ratio))
    fill_rect = pygame.Rect(x + 2, y + 2, fill_w, h - 4)
    col = COLORS["special_ready"] if ready else (190, 145, 60)
    if ready:
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
        col = (min(255, int(col[0] + pulse * 35)), min(255, int(col[1] + pulse * 35)), col[2])
    draw_rounded_rect(surface, fill_rect, col, (h - 4) // 2)

    border = COLORS["special_ready"] if ready else COLORS["panel_border"]
    draw_rounded_rect(surface, bg_rect, border, h // 2, 2)

    font = get_font(12, bold=True)
    label = f"{name}: READY" if ready else f"{name}: {int(ratio * 100)}%"
    label_ts = font.render(label, True, COLORS["text_white"] if ready else COLORS["text_gray"])
    surface.blit(label_ts, (x + 8, y + h + 2))


def _draw_hud_panel(surface, panel, top, hud_font, is_left):
    player_col = COLORS["p1_color"] if is_left else COLORS["p2_color"]
    ko_flash = top.is_knocked_out and int(pygame.time.get_ticks() / 120) % 2 == 0
    border_col = COLORS["danger"] if ko_flash else player_col
    draw_panel(surface, panel, fill=COLORS["ui_panel"], border=border_col, radius=14, border_w=2)

    tag_w = 6
    tag_rect = pygame.Rect(panel.x if is_left else panel.right - tag_w, panel.y + 6, tag_w, panel.height - 12)
    draw_rounded_rect(surface, tag_rect, player_col, 3)

    label = f"P1: {top.name}" if is_left else f"P2: {top.name}"
    name_ts = hud_font.render(label, True, player_col)
    type_ts = hud_font.render(top.type.value, True, COLORS["text_dim"])
    surface.blit(name_ts, (panel.x + 16, panel.y + 9))
    surface.blit(type_ts, (panel.x + panel.width - type_ts.get_width() - 14, panel.y + 9))

    spin_ratio = top.spin / top.max_spin if top.max_spin > 0 else 0
    draw_spin_bar(surface, panel.x + 15, panel.y + 32, panel.width - 30, 18, spin_ratio, "SPIN", player_col)
    draw_special_bar(surface, panel.x + 15, panel.y + 76, panel.width - 30, 14, top.special_meter / 100, top.special_name)


def draw_hud(surface, p1, p2, match_time):
    hud_font_big = get_font(30, bold=True)
    hud_font = get_font(16, bold=True)

    panel_w, panel_h = 320, 114
    left_panel = pygame.Rect(20, 15, panel_w, panel_h)
    right_panel = pygame.Rect(SCREEN_WIDTH - 20 - panel_w, 15, panel_w, panel_h)

    _draw_hud_panel(surface, left_panel, p1, hud_font, is_left=True)
    _draw_hud_panel(surface, right_panel, p2, hud_font, is_left=False)

    center_w, center_h = 170, 58
    center_rect = pygame.Rect(SCREEN_WIDTH // 2 - center_w // 2, 15, center_w, center_h)
    draw_panel(surface, center_rect, fill=COLORS["ui_panel"], border=COLORS["accent_gold"], radius=14, border_w=2)

    mins = int(match_time // 60)
    secs = int(match_time % 60)
    time_str = f"{mins:02d}:{secs:02d}"
    low_time = match_time <= 20
    blink = int(pygame.time.get_ticks() / 300) % 2 == 0
    time_color = COLORS["danger"] if low_time and blink else COLORS["text_white"]
    time_ts = hud_font_big.render(time_str, True, time_color)
    surface.blit(time_ts, time_ts.get_rect(center=(SCREEN_WIDTH // 2, 36)))
    lbl = get_font(11, bold=True).render("MATCH TIME", True, COLORS["text_dim"])
    surface.blit(lbl, lbl.get_rect(center=(SCREEN_WIDTH // 2, 58)))


def draw_menu(surface, buttons):
    surface.fill(COLORS["bg_dark"])
    title_font = get_font(76, bold=True)
    sub_font = get_font(22)
    small_font = get_font(15)

    title_surf = title_font.render("PAMBARAM", True, COLORS["accent_gold"])
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 145))
    draw_glow(surface, title_rect, COLORS["accent_gold"], pad=30, radius=20, alpha=45, layers=3)

    shadow = title_font.render("PAMBARAM", True, (0, 0, 0))
    surface.blit(shadow, title_rect.move(3, 4))
    surface.blit(title_surf, title_rect)

    sub = sub_font.render("SPINNING TOP BATTLE ARENA", True, COLORS["text_gray"])
    surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 210)))

    for b in buttons:
        b.draw(surface)

    tip = small_font.render("Controls:  WASD = Steer  |  SHIFT = Dash  |  SPACE = Special  |  ESC = Pause", True, COLORS["text_dim"])
    surface.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25)))


def _draw_corner_badge(surface, x, y, text, color):
    rect = pygame.Rect(x, y, 26, 18)
    draw_rounded_rect(surface, rect, color, 6)
    ts = get_font(11, bold=True).render(text, True, (10, 10, 14))
    surface.blit(ts, ts.get_rect(center=rect.center))


def draw_top_select(surface, tops_data, p1_selection, p2_selection, p2_ai, buttons, difficulty):
    surface.fill(COLORS["bg_dark"])

    title = get_font(44, bold=True).render("CHOOSE YOUR TOP", True, COLORS["accent_gold"])
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 50)))

    info_font = get_font(20)
    p1_label = info_font.render("Player 1 - Left Click to pick", True, COLORS["p1_color"])
    p2_txt = "Player 2 - Right Click to pick" if not p2_ai else f"AI Opponent  [{difficulty.name}]"
    p2_label = info_font.render(p2_txt, True, COLORS["text_white"] if not p2_ai else COLORS["p2_color"])
    surface.blit(p1_label, (40, 96))
    surface.blit(p2_label, (SCREEN_WIDTH - 40 - p2_label.get_width(), 96))

    card_rects = get_top_card_rects(tops_data.keys())

    for name, preset in tops_data.items():
        card_rect = card_rects[name]
        p1_sel = p1_selection == name
        p2_sel = p2_selection == name
        selected = p1_sel or p2_sel

        if selected:
            draw_glow(surface, card_rect, COLORS["accent_gold"], pad=10, radius=14, alpha=35, layers=2)
        border = COLORS["accent_gold"] if selected else COLORS["panel_border"]
        draw_panel(surface, card_rect, fill=COLORS["bg_mid"], border=border, radius=12, border_w=2 if selected else 1)

        top_r = 32
        top_cx = card_rect.centerx
        top_cy = card_rect.y + 48
        pygame.draw.circle(surface, preset["color"], (top_cx, top_cy), top_r)
        pygame.draw.circle(surface, preset["accent"], (top_cx, top_cy), top_r - 13)
        pygame.draw.circle(surface, COLORS["bg_dark"], (top_cx, top_cy), max(2, top_r - 24))

        name_font = get_font(16, bold=True)
        ts = name_font.render(name, True, COLORS["text_white"])
        surface.blit(ts, ts.get_rect(center=(card_rect.centerx, card_rect.y + 96)))

        type_ts = get_font(14).render(preset["type"].value + " Type", True, COLORS["text_gray"])
        surface.blit(type_ts, type_ts.get_rect(center=(card_rect.centerx, card_rect.y + 116)))

        stat_y = card_rect.y + 140
        stat_font = get_font(12)
        stats = [
            ("Mass", preset["mass"] / 5.0),
            ("Spin", preset["spin_speed"] / 2400.0),
            ("Decay", 1 - (preset["spin_decay"] - 45) / 80.0),
            ("Grip", preset["grip"] / 1.6),
        ]
        for s_i, (sname, sratio) in enumerate(stats):
            sy = stat_y + s_i * 17
            label = stat_font.render(sname, True, COLORS["text_gray"])
            surface.blit(label, (card_rect.x + 12, sy))
            bar_rect = pygame.Rect(card_rect.x + 70, sy + 4, 140, 6)
            draw_rounded_rect(surface, bar_rect, (14, 12, 20), 3)
            fill_rect = pygame.Rect(card_rect.x + 70, sy + 4, max(2, int(140 * max(0, min(1, sratio)))), 6)
            draw_rounded_rect(surface, fill_rect, COLORS["accent_gold"], 3)

        spec_font = get_font(11, bold=True)
        st = spec_font.render(preset["special"], True, COLORS["special_ready"])
        surface.blit(st, st.get_rect(center=(card_rect.centerx, card_rect.y + 218)))

        badge_y = card_rect.y + 8
        if p1_sel:
            _draw_corner_badge(surface, card_rect.x + 8, badge_y, "P1", COLORS["p1_color"])
        if p2_sel:
            _draw_corner_badge(surface, card_rect.right - 34, badge_y, "P2", COLORS["p2_color"])

    for b in buttons:
        b.draw(surface)

    hint = info_font.render("Click a card to select  |  P1 = Left Click   P2/AI = Right Click", True, COLORS["text_gray"])
    surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 145)))


def draw_arena_select(surface, arenas_data, selection, buttons):
    surface.fill(COLORS["bg_dark"])
    title = get_font(44, bold=True).render("CHOOSE ARENA", True, COLORS["accent_gold"])
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 60)))

    card_rects = get_arena_card_rects(arenas_data.keys())

    for key, preset in arenas_data.items():
        card_rect = card_rects[key]
        selected = selection == key

        if selected:
            draw_glow(surface, card_rect, COLORS["accent_gold"], pad=12, radius=18, alpha=40, layers=2)
        border = COLORS["accent_gold"] if selected else COLORS["panel_border"]
        draw_panel(surface, card_rect, fill=COLORS["bg_mid"], border=border, radius=16, border_w=3 if selected else 1)

        acx = card_rect.centerx
        acy = card_rect.y + 115
        ar = 80
        pygame.draw.circle(surface, preset["void_color"], (acx, acy), ar + 25)
        pygame.draw.circle(surface, preset["ring_color"], (acx, acy), ar + 4, 3)
        pygame.draw.circle(surface, preset["floor_color"], (acx, acy), ar)

        name_font = get_font(20, bold=True)
        ts = name_font.render(preset["name"], True, COLORS["text_white"])
        surface.blit(ts, ts.get_rect(center=(card_rect.centerx, card_rect.y + 235)))

        tamil_font = get_font(14, bold=True)
        tt = tamil_font.render(key, True, COLORS["text_gray"])
        surface.blit(tt, tt.get_rect(center=(card_rect.centerx, card_rect.y + 258)))

        desc = get_font(14).render(preset["desc"], True, COLORS["text_gray"])
        surface.blit(desc, desc.get_rect(center=(card_rect.centerx, card_rect.y + 285)))

        grip_label = get_font(12).render(
            f"Grip: {'Low' if preset['grip_mod'] < 0.9 else 'High' if preset['grip_mod'] > 1.05 else 'Normal'}",
            True, COLORS["accent_green"])
        surface.blit(grip_label, grip_label.get_rect(center=(card_rect.centerx, card_rect.y + 310)))

        if selected:
            sel_font = get_font(14, bold=True)
            st = sel_font.render("SELECTED", True, COLORS["accent_gold"])
            surface.blit(st, st.get_rect(center=(card_rect.centerx, card_rect.y + 328)))

    for b in buttons:
        b.draw(surface)


def draw_pause(surface, buttons):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surface.blit(overlay, (0, 0))

    panel = pygame.Rect(SCREEN_WIDTH // 2 - 220, 140, 440, 420)
    draw_panel(surface, panel, fill=COLORS["ui_panel"], border=COLORS["panel_border"], radius=18, border_w=2)

    title = get_font(56, bold=True).render("PAUSED", True, COLORS["accent_gold"])
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 210)))
    for b in buttons:
        b.draw(surface)


def draw_game_over(surface, winner, stats, buttons):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    surface.blit(overlay, (0, 0))

    is_p1 = winner and winner.player_id == 1
    win_color = COLORS["p1_color"] if is_p1 else (COLORS["p2_color"] if winner else COLORS["accent_gold"])

    big_font = get_font(72, bold=True)
    result = f"PLAYER {winner.player_id} WINS!" if winner else "DRAW!"
    title_surf = big_font.render(result, True, win_color)
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 175))
    draw_glow(surface, title_rect, win_color, pad=26, radius=18, alpha=45, layers=3)
    surface.blit(title_surf, title_rect)

    if winner:
        name_font = get_font(32, bold=True)
        nt = name_font.render(f'"{winner.name}"', True, winner.color)
        surface.blit(nt, nt.get_rect(center=(SCREEN_WIDTH // 2, 245)))
        sub = get_font(22).render(stats.get("win_reason", ""), True, COLORS["text_gray"])
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 285)))
    else:
        sub = get_font(22).render(stats.get("win_reason", ""), True, COLORS["text_gray"])
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 245)))

    panel = pygame.Rect(SCREEN_WIDTH // 2 - 250, 320, 500, 220)
    draw_panel(surface, panel, fill=COLORS["ui_panel"], border=COLORS["accent_gold"], radius=16, border_w=2)

    stat_font = get_font(22, bold=True)
    label_font = get_font(18)
    p1_spin = stats.get("p1_final_spin", 0)
    p2_spin = stats.get("p2_final_spin", 0)
    score_font = get_font(28, bold=True)
    p1s = score_font.render(f"{int(p1_spin)}", True, COLORS["p1_color"])
    p2s = score_font.render(f"{int(p2_spin)}", True, COLORS["p2_color"])
    vs = stat_font.render("vs", True, COLORS["text_gray"])
    surface.blit(p1s, (panel.x + 50, panel.y + 25))
    surface.blit(vs, vs.get_rect(center=(panel.centerx, panel.y + 40)))
    surface.blit(p2s, (panel.right - 50 - p2s.get_width(), panel.y + 25))

    p1l = label_font.render("P1 Spin Remaining", True, COLORS["text_gray"])
    p2l = label_font.render("P2 Spin Remaining", True, COLORS["text_gray"])
    surface.blit(p1l, (panel.x + 50, panel.y + 65))
    surface.blit(p2l, (panel.right - 50 - p2l.get_width(), panel.y + 65))

    match_time = stats.get("match_time", 0)
    mins = int(match_time // 60)
    secs = int(match_time % 60)
    mt = stat_font.render(f"Time: {mins:02d}:{secs:02d}", True, COLORS["text_white"])
    surface.blit(mt, mt.get_rect(center=(panel.centerx, panel.y + 115)))

    points = stats.get("points", 0)
    if points > 0:
        pt = stat_font.render(f"Score: +{points}", True, COLORS["accent_gold"])
        surface.blit(pt, pt.get_rect(center=(panel.centerx, panel.y + 150)))

    for b in buttons:
        b.draw(surface)


def draw_launch_indicator(surface, top, is_player, drag_start, current_pos, shake=(0, 0)):
    if not drag_start or not current_pos:
        return
    tx, ty = top.x + shake[0], top.y + shake[1]
    sx, sy = drag_start
    cx, cy = current_pos
    dx = sx - cx
    dy = sy - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 5:
        return
    dir_x = dx / max(1, dist)
    dir_y = dy / max(1, dist)

    col = COLORS["p1_color"] if is_player == 1 else COLORS["p2_color"]
    pygame.draw.line(surface, col, (int(tx), int(ty)),
                     (int(tx + dir_x * dist * 1.2), int(ty + dir_y * dist * 1.2)), 4)

    arrow_x = tx + dir_x * dist * 1.2
    arrow_y = ty + dir_y * dist * 1.2
    angle = math.atan2(dir_y, dir_x)
    for a_off in [2.6, -2.6]:
        ax = arrow_x - math.cos(angle + a_off) * 15
        ay = arrow_y - math.sin(angle + a_off) * 15
        pygame.draw.line(surface, col, (int(arrow_x), int(arrow_y)), (int(ax), int(ay)), 4)


def draw_countdown(surface, count):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    if count > 0:
        txt_str = str(count)
        col = COLORS["accent_gold"]
        base_size = 170
    else:
        txt_str = "FIGHT!"
        col = COLORS["accent_red"]
        base_size = 110

    font = get_font(base_size, bold=True)
    txt = font.render(txt_str, True, col)

    beat = (pygame.time.get_ticks() % 500) / 500.0
    scale = 1.0 + (1.0 - beat) * 0.12
    w, h = txt.get_width(), txt.get_height()
    scaled = pygame.transform.smoothscale(txt, (max(1, int(w * scale)), max(1, int(h * scale))))
    rect = scaled.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    draw_glow(surface, rect, col, pad=40, radius=20, alpha=40, layers=3)
    surface.blit(scaled, rect)
