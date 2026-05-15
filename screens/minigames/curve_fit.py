"""
screens/minigames/curve_fit.py

Mini-juego de ajuste de curvas (Mínimos Cuadrados – Línea 2).

Muestra puntos dispersos de "consumo de energía" en un gráfico.
Conforme el usuario completa cada paso, la línea de tendencia se va
dibujando automáticamente sobre los puntos.
"""

import pygame
import math
import random
import re
import time

WHITE      = (255, 255, 255)
DARK_GREY  = (18,  20,  28)
PANEL      = (30,  33,  45)
GRID_COL   = (42,  46,  62)
AXIS_COL   = (90,  95, 115)
LIGHT_GREY = (110, 115, 130)
GREEN      = ( 50, 225,  90)
RED        = (220,  55,  55)
YELLOW     = (255, 220,   0)
CYAN       = ( 70, 195, 255)
ORANGE     = (255, 145,  30)
DOT_COL    = (255, 100,  80)

FEEDBACK_MS = 850

# Puntos de datos fijos (consumo de energía por tramo)
_DATA_POINTS = [
    (0.5, 1.8), (1.0, 2.9), (1.5, 3.5), (2.0, 4.8),
    (2.5, 5.2), (3.0, 6.7), (3.5, 7.1), (4.0, 8.4),
    (4.5, 9.0), (5.0, 9.8),
]
# Línea de tendencia (y = 1.9x + 0.95)
_SLOPE, _INTERCEPT = 1.9, 0.95
_X_MIN, _X_MAX = 0.0, 5.5
_Y_MIN, _Y_MAX = 0.0, 12.0

# Etiquetas de los ejes
_X_TICKS = [1, 2, 3, 4, 5]
_Y_TICKS = [2, 4, 6, 8, 10]


# ── Estado del módulo ──────────────────────────────────────────────────────
_nivel_id      = None
_paso_actual   = 0
_input_text    = ""
_feedback      = None
_feedback_tick = 0
_enunciado     = ""
_preguntas     = []


def reset_curve_fit() -> None:
    global _nivel_id, _paso_actual, _input_text, _feedback, _feedback_tick
    global _enunciado, _preguntas
    _nivel_id      = None
    _paso_actual   = 0
    _input_text    = ""
    _feedback      = None
    _feedback_tick = 0
    _enunciado     = ""
    _preguntas     = []


def _comparar(user_input: str, correcta: str) -> bool:
    u = user_input.strip().lower().replace(',', '.')
    c = correcta.strip().lower().replace(',', '.')
    try:
        patron = r'-?\d+\.?\d*'
        u_num  = float(re.findall(patron, u)[0])
        c_num  = float(re.findall(patron, c)[0])
        tol    = max(0.01, abs(c_num) * 0.03)   # ±3 %
        return abs(u_num - c_num) <= tol
    except Exception:
        return u == c


def _wrap_text(text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ── Helpers de coordenadas ─────────────────────────────────────────────────

def _to_screen(gx, gy, rect):
    """Convierte coordenadas del gráfico a píxeles dentro de rect."""
    px = rect.left + (gx - _X_MIN) / (_X_MAX - _X_MIN) * rect.width
    py = rect.bottom - (gy - _Y_MIN) / (_Y_MAX - _Y_MIN) * rect.height
    return int(px), int(py)


# ── Dibujo del gráfico ─────────────────────────────────────────────────────

def _draw_graph(screen, rect, progress_ratio, font_small):
    """
    progress_ratio ∈ [0, 1]: fracción de la línea de tendencia visible.
    Versión mejorada con ejes numerados, leyenda y puntos más grandes.
    """
    # ── Márgenes internos para dejar espacio a etiquetas ──────────────────
    MARGIN_L = 52   # espacio para números del eje Y
    MARGIN_B = 32   # espacio para números del eje X
    inner = pygame.Rect(
        rect.left + MARGIN_L,
        rect.top + 12,
        rect.width  - MARGIN_L - 12,
        rect.height - MARGIN_B - 12,
    )

    def to_px(gx, gy):
        px = inner.left + (gx - _X_MIN) / (_X_MAX - _X_MIN) * inner.width
        py = inner.bottom - (gy - _Y_MIN) / (_Y_MAX - _Y_MIN) * inner.height
        return int(px), int(py)

    # Fondo del panel con degradado simulado (dos rectángulos)
    pygame.draw.rect(screen, (22, 26, 38), rect, border_radius=12)
    pygame.draw.rect(screen, (32, 36, 52), inner, border_radius=4)
    pygame.draw.rect(screen, (55, 62, 88), rect, 2, border_radius=12)

    # ── Cuadrícula con líneas punteadas ───────────────────────────────────
    for gx in _X_TICKS:
        sx, _ = to_px(gx, 0)
        for dy in range(inner.top, inner.bottom, 8):
            pygame.draw.line(screen, GRID_COL, (sx, dy), (sx, min(dy + 4, inner.bottom)), 1)

    for gy in _Y_TICKS:
        _, sy = to_px(0, gy)
        for dx in range(inner.left, inner.right, 8):
            pygame.draw.line(screen, GRID_COL, (dx, sy), (min(dx + 4, inner.right), sy), 1)

    # ── Ejes principales ──────────────────────────────────────────────────
    ox, oy = to_px(0, 0)
    pygame.draw.line(screen, AXIS_COL, (inner.left,  inner.bottom), (inner.right, inner.bottom), 2)  # X
    pygame.draw.line(screen, AXIS_COL, (inner.left,  inner.top),    (inner.left,  inner.bottom), 2)  # Y

    # Flechas de ejes
    pygame.draw.polygon(screen, AXIS_COL, [
        (inner.right + 8, inner.bottom),
        (inner.right,     inner.bottom - 5),
        (inner.right,     inner.bottom + 5),
    ])
    pygame.draw.polygon(screen, AXIS_COL, [
        (inner.left,      inner.top - 8),
        (inner.left - 5,  inner.top),
        (inner.left + 5,  inner.top),
    ])

    # ── Etiquetas numéricas del eje X ─────────────────────────────────────
    for gx in _X_TICKS:
        sx, _ = to_px(gx, 0)
        tick_surf = font_small.render(str(gx), True, LIGHT_GREY)
        screen.blit(tick_surf, tick_surf.get_rect(center=(sx, inner.bottom + 14)))
        pygame.draw.line(screen, AXIS_COL, (sx, inner.bottom), (sx, inner.bottom + 5), 1)

    # ── Etiquetas numéricas del eje Y ─────────────────────────────────────
    for gy in _Y_TICKS:
        _, sy = to_px(0, gy)
        tick_surf = font_small.render(str(gy), True, LIGHT_GREY)
        screen.blit(tick_surf, tick_surf.get_rect(midright=(inner.left - 6, sy)))
        pygame.draw.line(screen, AXIS_COL, (inner.left - 4, sy), (inner.left, sy), 1)

    # ── Nombre de ejes ────────────────────────────────────────────────────
    font_axis = pygame.font.SysFont("Arial", 17, bold=True)
    x_lbl = font_axis.render("Tiempo (s)", True, CYAN)
    screen.blit(x_lbl, x_lbl.get_rect(center=(inner.centerx, rect.bottom - 10)))

    y_lbl_raw = font_axis.render("Consumo (kWh)", True, CYAN)
    y_lbl = pygame.transform.rotate(y_lbl_raw, 90)
    screen.blit(y_lbl, y_lbl.get_rect(center=(rect.left + 14, inner.centery)))

    # ── Área de dispersión con sombra bajo cada punto ─────────────────────
    for gx, gy in _DATA_POINTS:
        sx, sy = to_px(gx, gy)
        # Sombra
        pygame.draw.circle(screen, (10, 10, 20), (sx + 3, sy + 3), 9)
        # Cuerpo del punto
        pygame.draw.circle(screen, DOT_COL, (sx, sy), 9)
        pygame.draw.circle(screen, WHITE,   (sx, sy), 9, 2)
        # Brillo interior
        pygame.draw.circle(screen, (255, 180, 160), (sx - 3, sy - 3), 3)

    # ── Línea de tendencia (se dibuja encima de los puntos) ───────────────
    if progress_ratio > 0.0:
        x_end    = _X_MIN + (_X_MAX - _X_MIN) * progress_ratio
        steps    = max(2, int(progress_ratio * 80))
        pts_line = []
        for k in range(steps + 1):
            gx = _X_MIN + (x_end - _X_MIN) * k / steps
            gy = _SLOPE * gx + _INTERCEPT
            sx, sy = to_px(gx, gy)
            if inner.left - 4 <= sx <= inner.right + 4:
                pts_line.append((sx, max(inner.top, min(inner.bottom, sy))))

        if len(pts_line) >= 2:
            # Sombra de la línea
            shadow_pts = [(p[0] + 2, p[1] + 2) for p in pts_line]
            pygame.draw.lines(screen, (0, 60, 20), False, shadow_pts, 4)
            # Línea principal
            pygame.draw.lines(screen, GREEN, False, pts_line, 3)
            # Línea brillante encima (más fina, más clara)
            pygame.draw.lines(screen, (180, 255, 200), False, pts_line, 1)

        # Punta parpadeante
        if pts_line:
            now = pygame.time.get_ticks()
            pulse = abs(math.sin(now / 300)) * 4
            px, py = pts_line[-1]
            pygame.draw.circle(screen, YELLOW, (px, py), int(8 + pulse))
            pygame.draw.circle(screen, WHITE,  (px, py), 5)

    # ── Leyenda ───────────────────────────────────────────────────────────
    leg_x = inner.right - 190
    leg_y = inner.top + 14
    pygame.draw.rect(screen, (20, 24, 36), (leg_x - 8, leg_y - 6, 186, 58), border_radius=6)
    pygame.draw.rect(screen, AXIS_COL,     (leg_x - 8, leg_y - 6, 186, 58), 1, border_radius=6)

    pygame.draw.circle(screen, DOT_COL,  (leg_x + 8, leg_y + 8),  7)
    pygame.draw.circle(screen, WHITE,    (leg_x + 8, leg_y + 8),  7, 1)
    screen.blit(font_small.render("Datos medidos", True, LIGHT_GREY), (leg_x + 20, leg_y))

    pygame.draw.line(screen, GREEN, (leg_x, leg_y + 34), (leg_x + 20, leg_y + 34), 3)
    screen.blit(font_small.render("Línea de ajuste", True, GREEN), (leg_x + 26, leg_y + 26))


# ── Pantalla principal ─────────────────────────────────────────────────────

def mostrar_curve_fit(
    screen,
    WIDTH,
    HEIGHT,
    font_title,
    font_button,
    game_state,
    nivel,
    all_events,
    mouse_pos,
    start_time=None,
):
    global _nivel_id, _paso_actual, _input_text, _feedback, _feedback_tick
    global _enunciado, _preguntas

    now      = pygame.time.get_ticks()
    center_x = WIDTH // 2

    # ── Inicializar ────────────────────────────────────────────────────────
    if _nivel_id != nivel.get("id"):
        _nivel_id      = nivel.get("id")
        _paso_actual   = 0
        _input_text    = ""
        _feedback      = None
        _feedback_tick = 0
        problemas = nivel.get("problemas", [])
        if problemas:
            problema   = random.choice(problemas)
            _enunciado = problema.get("enunciado", "")
            _preguntas = problema.get("opciones", [])
        else:
            _enunciado = ""
            _preguntas = nivel.get("preguntas", [])

    total_pasos = len(_preguntas)
    if total_pasos == 0:
        return "nivel_completo"

    # ── Timer ──────────────────────────────────────────────────────────────
    remaining = max(0, 1800 - int(time.time() - start_time)) if start_time else 1800
    if remaining <= 0:
        return "tiempo_agotado"

    # ── Transición tras feedback ───────────────────────────────────────────
    if _feedback is not None:
        if now - _feedback_tick >= FEEDBACK_MS:
            if _feedback == "incorrecto":
                reset_curve_fit()
                return "incorrecto"
            _feedback   = None
            _input_text = ""
            _paso_actual += 1
            if _paso_actual >= total_pasos:
                reset_curve_fit()
                return "nivel_completo"

    else:
        for ev in all_events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if _input_text.strip():
                        correcta = _preguntas[_paso_actual]["respuesta"]
                        if _comparar(_input_text, correcta):
                            _feedback = "correcto"
                        else:
                            _feedback = "incorrecto"
                        _feedback_tick = now
                        break
                elif ev.key == pygame.K_BACKSPACE:
                    _input_text = _input_text[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(_input_text) < 22:
                    _input_text += ev.unicode

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                btn = pygame.Rect(0, 0, 240, 52)
                btn.center = (center_x, HEIGHT - 90)
                if btn.collidepoint(mouse_pos) and _input_text.strip():
                    correcta = _preguntas[_paso_actual]["respuesta"]
                    if _comparar(_input_text, correcta):
                        _feedback = "correcto"
                    else:
                        _feedback = "incorrecto"
                    _feedback_tick = now
                    break

    # ══════════════════════════════════════════════════════════════════════
    # DIBUJO
    # ══════════════════════════════════════════════════════════════════════
    screen.fill(DARK_GREY)

    # ── HUD ───────────────────────────────────────────────────────────────
    linea = nivel.get("linea", "2")
    screen.blit(font_button.render(f"Linea: {linea}", True, WHITE), (30, 20))
    screen.blit(font_button.render(f"Estacion: {nivel['estacion']}", True, WHITE), (30, 55))
    try:
        heart = pygame.image.load("assets/heart.png")
        heart = pygame.transform.scale(heart, (30, 30))
        for i in range(game_state.vidas):
            screen.blit(heart, (WIDTH - 45 - i * 38, 22))
    except Exception:
        screen.blit(font_button.render(f"Vidas: {game_state.vidas}", True, WHITE),
                    (WIDTH - 200, 20))

    # Timer HUD
    timer_col = RED if remaining <= 10 else (YELLOW if remaining <= 30 else WHITE)
    screen.blit(font_button.render(f"{remaining // 60:02}:{remaining % 60:02}", True, timer_col),
                (WIDTH - 305, 55))

    # ── Título ─────────────────────────────────────────────────────────────
    title = font_title.render("Ajuste de Curvas", True, ORANGE)
    screen.blit(title, title.get_rect(center=(center_x, 110)))

    # ── Enunciado del problema ─────────────────────────────────────────────
    if _enunciado:
        font_enun = pygame.font.SysFont("Arial", 23)
        lines = _wrap_text(_enunciado, font_enun, WIDTH - 160)
        panel_h = len(lines) * 30 + 18
        panel_rect = pygame.Rect(60, 147, WIDTH - 120, panel_h)
        pygame.draw.rect(screen, (18, 20, 28), panel_rect, border_radius=8)
        pygame.draw.rect(screen, ORANGE, panel_rect, 1, border_radius=8)
        for i, line in enumerate(lines):
            lsurf = font_enun.render(line, True, (255, 220, 180))
            screen.blit(lsurf, lsurf.get_rect(center=(center_x, 156 + i * 30 + 6)))

    # ── Gráfico ────────────────────────────────────────────────────────────
    font_small = pygame.font.SysFont("Courier New", 18)
    graph_rect = pygame.Rect(100, 230, WIDTH - 200, 365)

    # Progreso: cuánta línea mostrar
    # Durante el feedback "correcto" del paso i, mostramos (i+1)/total
    if _feedback == "correcto":
        ratio = (_paso_actual + 1) / total_pasos
    else:
        ratio = _paso_actual / total_pasos

    _draw_graph(screen, graph_rect, ratio, font_small)

    # ── Barra de progreso de ajuste ────────────────────────────────────────
    bar_rect  = pygame.Rect(100, graph_rect.bottom + 18, WIDTH - 200, 14)
    pygame.draw.rect(screen, PANEL, bar_rect, border_radius=7)
    fill_w    = int(bar_rect.width * ratio)
    if fill_w > 0:
        pygame.draw.rect(screen, GREEN,
                         pygame.Rect(bar_rect.left, bar_rect.top, fill_w, bar_rect.height),
                         border_radius=7)
    pct_surf = font_small.render(f"Ajuste: {int(ratio * 100)}%", True, GREEN)
    screen.blit(pct_surf, (bar_rect.left, bar_rect.bottom + 6))

    # ── Paso actual ────────────────────────────────────────────────────────
    if _paso_actual < total_pasos:
        paso_txt = _preguntas[_paso_actual]["pregunta"]
        paso_surf = font_title.render(f"Calcula:  {paso_txt}", True, WHITE)
        screen.blit(paso_surf, paso_surf.get_rect(center=(center_x, 680)))

    # ── Bolitas de progreso ────────────────────────────────────────────────
    dot_gap     = 44
    dot_start_x = center_x - (total_pasos * dot_gap) // 2 + dot_gap // 2
    for i in range(total_pasos):
        dx = dot_start_x + i * dot_gap
        dy = 720
        if i < _paso_actual:
            pygame.draw.circle(screen, GREEN, (dx, dy), 10)
            pygame.draw.circle(screen, WHITE, (dx, dy), 10, 2)
        elif i == _paso_actual:
            pygame.draw.circle(screen, WHITE, (dx, dy), 10)
        else:
            pygame.draw.circle(screen, LIGHT_GREY, (dx, dy), 8)

    # ── Campo de texto ─────────────────────────────────────────────────────
    field_rect = pygame.Rect(0, 0, 480, 66)
    field_rect.center = (center_x, 780)

    bg_col     = (18, 120, 50) if _feedback == "correcto" else PANEL
    border_col = GREEN if _feedback == "correcto" else ORANGE

    pygame.draw.rect(screen, bg_col,     field_rect, border_radius=12)
    pygame.draw.rect(screen, border_col, field_rect, 2, border_radius=12)

    cursor     = "|" if (now // 500) % 2 == 0 else " "
    input_surf = font_title.render(_input_text + cursor, True, WHITE)
    screen.set_clip(field_rect.inflate(-16, -8))
    screen.blit(input_surf, input_surf.get_rect(center=field_rect.center))
    screen.set_clip(None)

    # ── Botón Confirmar ────────────────────────────────────────────────────
    if _feedback is None:
        btn = pygame.Rect(0, 0, 240, 52)
        btn.center = (center_x, HEIGHT - 90)
        bc = (55, 60, 45) if btn.collidepoint(mouse_pos) else PANEL
        pygame.draw.rect(screen, bc,     btn, border_radius=10)
        pygame.draw.rect(screen, ORANGE, btn, 1, border_radius=10)
        screen.blit(font_button.render("Confirmar  [Enter]", True, WHITE),
                    font_button.render("Confirmar  [Enter]", True, WHITE).get_rect(center=btn.center))

    # ── Flash feedback ─────────────────────────────────────────────────────
    if _feedback == "correcto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((0, 200, 80, 30))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Curva Ajustada!", True, GREEN)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 38)))
    elif _feedback == "incorrecto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((200, 0, 0, 40))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Valor Incorrecto...", True, RED)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 38)))

    return None
