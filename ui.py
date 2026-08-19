import pygame
import math
from config import *

def draw_rounded_rect(surface, rect, color, radius=15, border=0, border_color=None):
    rect = pygame.Rect(rect)
    if rect.width < radius * 2:
        radius = rect.width // 2
    if rect.height < radius * 2:
        radius = rect.height // 2
    r = rect
    inner = pygame.Rect(r.left, r.top + radius, r.width, r.height - 2 * radius)
    pygame.draw.rect(surface, color, inner, border)
    inner = pygame.Rect(r.left + radius, r.top, r.width - 2 * radius, r.height)
    pygame.draw.rect(surface, color, inner, border)
    for corner in [(r.left + radius, r.top + radius),
                   (r.right - radius - 1, r.top + radius),
                   (r.left + radius, r.bottom - radius - 1),
                   (r.right - radius - 1, r.bottom - radius - 1)]:
        pygame.draw.circle(surface, color, corner, radius, border)
    if border > 0 and border_color:
        for corner in [(r.left + radius, r.top + radius),
                       (r.right - radius - 1, r.top + radius),
                       (r.left + radius, r.bottom - radius - 1),
                       (r.right - radius - 1, r.bottom - radius - 1)]:
            pygame.draw.circle(surface, border_color, corner, radius, border)

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
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.rect.collidepoint(event.pos) and self.pressed:
                self.pressed = False
                if self.callback:
                    self.callback()
            else:
                self.pressed = False
        return False

    def draw(self, surface):
        if self.pressed:
            col = self.active_color
        elif self.hovered:
            col = self.hover_color
        else:
            col = self.idle_color
        draw_rounded_rect(surface, self.rect, col, self.radius)
        border_c = tuple(min(255, c + 50) for c in col)
        draw_rounded_rect(surface, self.rect, border_c, self.radius, 2)
        font = get_font(self.font_size, bold=True)
        ts = font.render(self.text, True, self.text_color)
        tr = ts.get_rect(center=self.rect.center)
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

def draw_spin_bar(surface, x, y, w, h, ratio, label="SPIN", player_col=None):
    if ratio > 0.6:
        col = COLORS["spin_full"]
    elif ratio > 0.3:
        col = COLORS["spin_mid"]
    else:
        col = COLORS["spin_low"]
    bg_rect = pygame.Rect(x, y, w, h)
    draw_rounded_rect(surface, bg_rect, (20, 15, 30), h // 2)
    border = player_col or (60, 55, 80)
    draw_rounded_rect(surface, bg_rect, border, h // 2, 2)
    fill_w = max(4, int((w - 4) * max(0, min(1, ratio))))
    fill_rect = pygame.Rect(x + 2, y + 2, fill_w, h - 4)
    draw_rounded_rect(surface, fill_rect, col, (h - 4) // 2)
    font = get_font(14, bold=True)
    pct = int(max(0, min(100, ratio * 100)))
    label_ts = font.render(f"{label} {pct}%", True, COLORS["text_white"])
    surface.blit(label_ts, (x + 8, y + h + 3))

def draw_special_bar(surface, x, y, w, h, ratio, name="SPECIAL"):
    ready = ratio >= 1.0
    bg_rect = pygame.Rect(x, y, w, h)
    draw_rounded_rect(surface, bg_rect, (20, 15, 30), h // 2)
    border = COLORS["special_ready"] if ready else (80, 75, 100)
    draw_rounded_rect(surface, bg_rect, border, h // 2, 2)
    fill_w = max(4, int((w - 4) * max(0, min(1, ratio))))
    fill_rect = pygame.Rect(x + 2, y + 2, fill_w, h - 4)
    col = COLORS["special_ready"] if ready else (200, 150, 40)
    if ready:
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
        col = (
            min(255, int(col[0] + pulse * 40)),
            min(255, int(col[1] + pulse * 40)),
            min(255, int(col[2])),
        )
    draw_rounded_rect(surface, fill_rect, col, (h - 4) // 2)
    font = get_font(12, bold=True)
    label = f"{name}: READY" if ready else f"{name}: {int(ratio * 100)}%"
    label_ts = font.render(label, True, COLORS["text_white"] if ready else COLORS["text_gray"])
    surface.blit(label_ts, (x + 8, y + h + 2))

def draw_hud(surface, p1, p2, match_time, combo_p1=0, combo_p2=0):
    hud_font_big = get_font(32, bold=True)
    hud_font = get_font(18, bold=True)

    left_panel = pygame.Rect(20, 15, 340, 120)
    right_panel = pygame.Rect(SCREEN_WIDTH - 360, 15, 340, 120)
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    draw_rounded_rect(overlay, left_panel, (25, 20, 40, 220), 15)
    draw_rounded_rect(overlay, right_panel, (25, 20, 40, 220), 15)
    surface.blit(overlay, (0, 0))
    draw_rounded_rect(surface, left_panel, COLORS["p1_color"], 15, 2)
    draw_rounded_rect(surface, right_panel, COLORS["p2_color"], 15, 2)

    p1_name = hud_font.render(f"P1  {p1.name}", True, COLORS["p1_color"])
    surface.blit(p1_name, (left_panel.x + 15, left_panel.y + 10))
    p2_name = hud_font.render(f"P2  {p2.name}", True, COLORS["p2_color"])
    surface.blit(p2_name, (right_panel.x + 15, right_panel.y + 10))

    p1_type = hud_font.render(p1.type.value, True, COLORS["text_gray"])
    surface.blit(p1_type, (left_panel.x + left_panel.width - p1_type.get_width() - 15, left_panel.y + 10))
    p2_type = hud_font.render(p2.type.value, True, COLORS["text_gray"])
    surface.blit(p2_type, (right_panel.x + right_panel.width - p2_type.get_width() - 15, right_panel.y + 10))

    p1_spin = p1.spin / p1.max_spin if p1.max_spin > 0 else 0
    draw_spin_bar(surface, left_panel.x + 15, left_panel.y + 40, 310, 22, p1_spin, "SPIN", COLORS["p1_color"])

    p2_spin = p2.spin / p2.max_spin if p2.max_spin > 0 else 0
    draw_spin_bar(surface, right_panel.x + 15, right_panel.y + 40, 310, 22, p2_spin, "SPIN", COLORS["p2_color"])

    draw_special_bar(surface, left_panel.x + 15, left_panel.y + 88, 310, 16, p1.special_meter / 100, p1.special_name)
    draw_special_bar(surface, right_panel.x + 15, right_panel.y + 88, 310, 16, p2.special_meter / 100, p2.special_name)

    center_w = 200
    center_h = 80
    center_rect = pygame.Rect(SCREEN_WIDTH // 2 - center_w // 2, 20, center_w, center_h)
    overlay2 = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    draw_rounded_rect(overlay2, center_rect, (25, 20, 40, 220), 15)
    surface.blit(overlay2, (0, 0))
    draw_rounded_rect(surface, center_rect, COLORS["accent_gold"], 15, 2)

    mins = int(match_time // 60)
    secs = int(match_time % 60)
    time_str = f"{mins:02d}:{secs:02d}"
    time_ts = hud_font_big.render(time_str, True, COLORS["accent_gold"])
    time_rect = time_ts.get_rect(center=(SCREEN_WIDTH // 2, 48))
    surface.blit(time_ts, time_rect)

    sub_label = hud_font.render("MATCH TIME", True, COLORS["text_gray"])
    sub_rect = sub_label.get_rect(center=(SCREEN_WIDTH // 2, 78))
    surface.blit(sub_label, sub_rect)

def draw_menu(surface, buttons):
    title_font = get_font(84, bold=True)
    sub_font = get_font(28)
    small_font = get_font(18)

    bg_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for r in range(400, 100, -30):
        a = 5
        pygame.draw.circle(bg_overlay, (100, 50, 180, a), ARENA_CENTER, r)
    surface.blit(bg_overlay, (0, 0))

    title_surf = title_font.render("PAMBARAM", True, COLORS["accent_gold"])
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 140))
    glow = pygame.Surface((title_surf.get_width() + 40, title_surf.get_height() + 40), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 200, 50, 40), glow.get_rect().center, glow.get_width() // 2)
    surface.blit(glow, (title_rect.x - 20, title_rect.y - 20))
    surface.blit(title_surf, title_rect)

    sub = sub_font.render("SPINNING TOP BATTLE ARENA", True, COLORS["text_gray"])
    sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 205))
    surface.blit(sub, sub_rect)

    for angle in range(0, 360, 30):
        rad = math.radians(angle + pygame.time.get_ticks() * 0.02)
        cx = SCREEN_WIDTH // 2 + math.cos(rad) * 200
        cy = 220 + math.sin(rad) * 18
        pygame.draw.circle(surface, COLORS["accent_gold"], (int(cx), int(cy)), 3)

    for b in buttons:
        b.draw(surface)

    hint = small_font.render("A Python Pygame Game Development Project", True, COLORS["text_gray"])
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
    surface.blit(hint, hint_rect)

    tip = small_font.render("Controls:  WASD = Steer  |  SHIFT = Dash  |  SPACE = Special  |  ESC = Pause", True, COLORS["text_gray"])
    tip_rect = tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 18))
    surface.blit(tip, tip_rect)

def draw_top_select(surface, tops_data, p1_selection, p2_selection, p2_ai, buttons, difficulty):
    surface.fill(COLORS["bg_dark"])

    title = get_font(44, bold=True).render("CHOOSE YOUR TOP", True, COLORS["accent_gold"])
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 50)))

    info_font = get_font(20)
    p1_label = info_font.render("Player 1 (WASD + LSHIFT + LCTRL)", True, COLORS["p1_color"])
    p2_txt = "Player 2 (Arrows + RSHIFT + RCTRL)" if not p2_ai else f"AI Opponent [{difficulty.name}]"
    p2_label = info_font.render(p2_txt, True, COLORS["text_white"] if not p2_ai else COLORS["p2_color"])
    surface.blit(p1_label, (40, 100))
    surface.blit(p2_label, (SCREEN_WIDTH - 40 - p2_label.get_width(), 100))

    card_w = 240
    card_h = 290
    gap_x = 20
    gap_y = 20
    cols = 4
    start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
    start_y = 130

    for idx, (name, preset) in enumerate(tops_data.items()):
        col = idx % cols
        row = idx // cols
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_y)
        card_rect = pygame.Rect(cx, cy, card_w, card_h)

        selected = p1_selection == name or p2_selection == name
        p1_sel = p1_selection == name
        p2_sel = p2_selection == name

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        draw_rounded_rect(overlay, card_rect, (35, 30, 55, 230), 16)
        surface.blit(overlay, (0, 0))
        border = COLORS["accent_gold"] if selected else (70, 65, 95)
        if p1_sel:
            border = COLORS["p1_color"]
        if p2_sel:
            border = COLORS["p2_color"]
        draw_rounded_rect(surface, card_rect, border, 16, 3)

        top_r = 45
        top_cx = card_rect.centerx
        top_cy = card_rect.y + 70
        pygame.draw.circle(surface, preset["color"], (top_cx, top_cy), top_r)
        pygame.draw.circle(surface, preset["accent"], (top_cx, top_cy), top_r - 18)
        pygame.draw.circle(surface, (255, 255, 255), (top_cx, top_cy), max(2, top_r - 32))

        name_font = get_font(18, bold=True)
        ts = name_font.render(name, True, COLORS["text_white"])
        surface.blit(ts, ts.get_rect(center=(card_rect.centerx, card_rect.y + 140)))

        type_ts = info_font.render(preset["type"].value + " Type", True,
                                   COLORS["accent_green"] if preset["type"] == TopType.BALANCE
                                   else COLORS["accent_red"] if preset["type"] == TopType.ATTACK
                                   else COLORS["accent_blue"] if preset["type"] == TopType.DEFENSE
                                   else COLORS["accent_purple"])
        surface.blit(type_ts, type_ts.get_rect(center=(card_rect.centerx, card_rect.y + 165)))

        stat_y = card_rect.y + 190
        stat_font = get_font(13)
        stats = [
            ("Mass", preset["mass"] / 5.0, "⚔"),
            ("Spin", preset["spin_speed"] / 2400.0, "⚡"),
            ("Decay", 1 - (preset["spin_decay"] - 45) / 80.0, "⏱"),
            ("Grip", preset["grip"] / 1.6, "🧲"),
        ]
        for s_i, (sname, sratio, sym) in enumerate(stats):
            sy = stat_y + s_i * 22
            label = stat_font.render(f"{sym} {sname}", True, COLORS["text_gray"])
            surface.blit(label, (card_rect.x + 12, sy))
            bar_rect = pygame.Rect(card_rect.x + 80, sy + 5, 130, 7)
            draw_rounded_rect(surface, bar_rect, (20, 15, 30), 3)
            fill_rect = pygame.Rect(card_rect.x + 80, sy + 5, max(2, int(130 * max(0, min(1, sratio)))), 7)
            draw_rounded_rect(surface, fill_rect, COLORS["accent_gold"], 3)

        spec_font = get_font(12, bold=True)
        st = spec_font.render(f"★ {preset['special']}", True, COLORS["special_ready"])
        surface.blit(st, st.get_rect(center=(card_rect.centerx, card_rect.y + 275)))

    for b in buttons:
        b.draw(surface)

    hint = info_font.render("Click a card to select.  P1 = Left Click   |   P2/AI = Right Click", True, COLORS["text_gray"])
    surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)))

def draw_arena_select(surface, arenas_data, selection, buttons):
    surface.fill(COLORS["bg_dark"])
    title = get_font(44, bold=True).render("CHOOSE ARENA", True, COLORS["accent_gold"])
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 60)))

    card_w = 260
    card_h = 340
    gap_x = 30
    cols = 4
    start_x = SCREEN_WIDTH // 2 - (cols * (card_w + gap_x) - gap_x) // 2
    start_y = 120

    for idx, (key, preset) in enumerate(arenas_data.items()):
        col = idx % cols
        row = idx // cols
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_x)
        card_rect = pygame.Rect(cx, cy, card_w, card_h)

        selected = selection == key
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        draw_rounded_rect(overlay, card_rect, (35, 30, 55, 230), 16)
        surface.blit(overlay, (0, 0))
        border = COLORS["accent_gold"] if selected else (70, 65, 95)
        draw_rounded_rect(surface, card_rect, border, 16, 3)

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

        grip_label = get_font(12).render(f"Grip: {'Low' if preset['grip_mod'] < 0.9 else 'High' if preset['grip_mod'] > 1.05 else 'Normal'}", True, COLORS["accent_green"])
        surface.blit(grip_label, grip_label.get_rect(center=(card_rect.centerx, card_rect.y + 310)))

        if selected:
            sel_font = get_font(14, bold=True)
            st = sel_font.render("✓ SELECTED", True, COLORS["accent_gold"])
            surface.blit(st, st.get_rect(center=(card_rect.centerx, card_rect.y + 328)))

    for b in buttons:
        b.draw(surface)

def draw_pause(surface, buttons):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    title = get_font(64, bold=True).render("PAUSED", True, COLORS["accent_gold"])
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 200)))
    for b in buttons:
        b.draw(surface)

def draw_game_over(surface, winner, stats, buttons):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    is_p1 = winner and winner.player_id == 1
    win_color = COLORS["p1_color"] if is_p1 else COLORS["p2_color"]

    big_font = get_font(72, bold=True)
    result = "VICTORY" if winner else "DRAW"
    if winner:
        result = f"PLAYER {winner.player_id} WINS!"
    title = big_font.render(result, True, win_color if winner else COLORS["accent_gold"])
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 180)))

    if winner:
        name_font = get_font(32, bold=True)
        nt = name_font.render(f"「{winner.name}」", True, winner.color)
        surface.blit(nt, nt.get_rect(center=(SCREEN_WIDTH // 2, 245)))

        sub = get_font(22).render(stats.get("win_reason", ""), True, COLORS["text_gray"])
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 285)))

    panel = pygame.Rect(SCREEN_WIDTH // 2 - 250, 320, 500, 220)
    ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    draw_rounded_rect(ov, panel, (30, 25, 50, 230), 16)
    surface.blit(ov, (0, 0))
    draw_rounded_rect(surface, panel, COLORS["accent_gold"], 16, 2)

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

def draw_launch_indicator(surface, top, is_player, drag_start, current_pos):
    if not drag_start or not current_pos:
        return
    sx, sy = drag_start
    cx, cy = current_pos
    dx = sx - cx
    dy = sy - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 5:
        return
    max_dist = 200
    power = min(1.0, dist / max_dist)
    dir_x = dx / max(1, dist)
    dir_y = dy / max(1, dist)

    col = COLORS["p1_color"] if is_player == 1 else COLORS["p2_color"]
    pygame.draw.line(surface, col, (int(top.x), int(top.y)),
                     (int(top.x + dir_x * dist * 1.2), int(top.y + dir_y * dist * 1.2)), 4)

    arrow_x = top.x + dir_x * dist * 1.2
    arrow_y = top.y + dir_y * dist * 1.2
    angle = math.atan2(dir_y, dir_x)
    for a_off in [2.6, -2.6]:
        ax = arrow_x - math.cos(angle + a_off) * 15
        ay = arrow_y - math.sin(angle + a_off) * 15
        pygame.draw.line(surface, col, (int(arrow_x), int(arrow_y)), (int(ax), int(ay)), 4)

    bar_w = 180
    bar_h = 16
    bx = top.x - bar_w // 2
    by = top.y - top.radius - 40
    bar_rect = pygame.Rect(bx, by, bar_w, bar_h)
    draw_rounded_rect(surface, bar_rect, (20, 15, 30), 8)
    pcol = (80 + int(power * 175), 255 - int(power * 175), 80)
    fill_rect = pygame.Rect(bx + 2, by + 2, max(4, int((bar_w - 4) * power)), bar_h - 4)
    draw_rounded_rect(surface, fill_rect, pcol, 6)
    pct = get_font(12, bold=True).render(f"LAUNCH {int(power * 100)}%", True, COLORS["text_white"])
    surface.blit(pct, pct.get_rect(center=bar_rect.center))

def draw_countdown(surface, count):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    surface.blit(overlay, (0, 0))
    if count > 0:
        txt = get_font(180, bold=True).render(str(count), True, COLORS["accent_gold"])
    else:
        txt = get_font(120, bold=True).render("FIGHT!", True, COLORS["accent_red"])
    rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    glow = pygame.Surface((rect.width + 60, rect.height + 60), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 200, 50, 35), glow.get_rect().center, glow.get_width() // 2)
    surface.blit(glow, (rect.x - 30, rect.y - 30))
    surface.blit(txt, rect)
