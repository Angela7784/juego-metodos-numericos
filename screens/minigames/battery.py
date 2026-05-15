"""
screens/minigames/battery.py

Mini-juego de barra de carga de batería (Integración – Línea 3).

Muestra la curva de potencia/velocidad del tren.
Conforme el usuario completa cada regla de integración, el área bajo
la curva se "llena" de color y la batería en pantalla sube su nivel.
"""

import pygame
import math
import random
import re
import time

WHITE      = (255, 255, 255)
DARK_GREY  = (15,  18,  24)
PANEL      = (28,  32,  44)
GRID_COL   = (38,  44,  60)
AXIS_COL   = (80,  90, 110)
LIGHT_GREY = (110, 120, 140)
GREEN      = ( 50, 225,  90)
GREEN_DIM  = ( 20,  90,  40)
YELLOW     = (255, 215,   0)
CYAN       = ( 70, 195, 255)
ORANGE     = (255, 150,  30)
RED        = (220,  55,  55)

FEEDBACK_MS = 900

# Curva de potencia: f(x) = -0.3x³ + 2x² + x + 1, x ∈ [0, 5]
def _f(x):
    return -0.3 * x**3 + 2 * x**2 + x + 1

_X_MIN, _X_MAX = 0.0, 5.0
_Y_MIN, _Y_MAX = 0.0, 20.0


# ── Estado del módulo ──────────────────────────────────────────────────────
_nivel_id      = None
_paso_actual   = 0
_input_text    = ""
_feedback      = None
_feedback_tick = 0
_enunciado     = ""
_preguntas     = []


def reset_battery() -> None:
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


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_screen(gx, gy, rect):
    px = rect.left + (gx - _X_MIN) / (_X_MAX - _X_MIN) * rect.width
    py = rect.bottom - (gy - _Y_MIN) / (_Y_MAX - _Y_MIN) * rect.height
    return int(px), int(py)


def _draw_curve_graph(screen, rect, fill_ratio, font_small):
    """Dibuja la curva de potencia con el área bajo ella llenándose."""
    pygame.draw.rect(screen, PANEL, rect, border_radius=8)
    pygame.draw.rect(screen, AXIS_COL, rect, 1, border_radius=8)

    # Cuadrícula
    for gx in [1, 2, 3, 4]:
        sx, _ = _to_screen(gx, 0, rect)
        pygame.draw.line(screen, GRID_COL, (sx, rect.top), (sx, rect.bottom), 1)
    for gy in [5, 10, 15]:
        _, sy = _to_screen(0, gy, rect)
        pygame.draw.line(screen, GRID_COL, (rect.left, sy), (rect.right, sy), 1)

    # Eje X
    _, oy = _to_screen(0, 0, rect)
    pygame.draw.line(screen, AXIS_COL, (rect.left, oy), (rect.right, oy), 2)

    # Relleno del área (verde progresivo)
    if fill_ratio > 0.0:
        x_end   = _X_MIN + (_X_MAX - _X_MIN) * fill_ratio
        n_steps = max(4, int(fill_ratio * 120))
        poly    = [(rect.left, oy)]
        for k in range(n_steps + 1):
            gx = _X_MIN + (x_end - _X_MIN) * k / n_steps
            gy = _f(gx)
            sx, sy = _to_screen(gx, gy, rect)
            sx = max(rect.left, min(rect.right, sx))
            sy = max(rect.top,  min(rect.bottom, sy))
            poly.append((sx, sy))
        poly.append((_to_screen(x_end, 0, rect)[0], oy))
        if len(poly) >= 3:
            fill_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            local_poly = [(p[0] - rect.left, p[1] - rect.top) for p in poly]
            pygame.draw.polygon(fill_surf, (*GREEN, 70), local_poly)
            screen.blit(fill_surf, (rect.left, rect.top))

    # Curva completa (siempre visible)
    pts = []
    for k in range(121):
        gx = _X_MIN + (_X_MAX - _X_MIN) * k / 120
        gy = _f(gx)
        sx, sy = _to_screen(gx, gy, rect)
        if rect.left <= sx <= rect.right:
            pts.append((sx, max(rect.top, min(rect.bottom, sy))))
    if len(pts) >= 2:
        pygame.draw.lines(screen, CYAN, False, pts, 2)

    # Línea vertical del frente del relleno
    if fill_ratio > 0.0:
        x_end = _X_MIN + (_X_MAX - _X_MIN) * fill_ratio
        lx, _ = _to_screen(x_end, 0, rect)
        pygame.draw.line(screen, YELLOW, (lx, rect.top), (lx, oy), 2)

    # Etiquetas
    screen.blit(font_small.render("t (s)", True, LIGHT_GREY),
                (rect.right - 40, oy + 6))
    screen.blit(font_small.render("P(kW)", True, LIGHT_GREY),
                (rect.left, rect.top - 22))


def _draw_battery(screen, bx, by, bw, bh, charge_ratio):
    """Dibuja un icono de batería con nivel de carga."""
    # Cuerpo
    body = pygame.Rect(bx, by, bw, bh)
    pygame.draw.rect(screen, PANEL, body, border_radius=6)
    pygame.draw.rect(screen, LIGHT_GREY, body, 3, border_radius=6)
    # Terminal positivo
    term_w, term_h = 14, 24
    pygame.draw.rect(screen, LIGHT_GREY,
                     pygame.Rect(bx + bw, by + (bh - term_h) // 2, term_w, term_h),
                     border_radius=3)

    # Relleno
    padding = 8
    fill_h  = int((bh - padding * 2) * charge_ratio)
    if fill_h > 0:
        if charge_ratio > 0.6:
            fill_col = GREEN
        elif charge_ratio > 0.3:
            fill_col = YELLOW
        else:
            fill_col = RED
        fill_rect = pygame.Rect(
            bx + padding,
            by + bh - padding - fill_h,
            bw - padding * 2,
            fill_h,
        )
        pygame.draw.rect(screen, fill_col, fill_rect, border_radius=4)

    # Porcentaje
    font_big = pygame.font.SysFont("Arial", 36, bold=True)
    pct      = int(charge_ratio * 100)
    col      = GREEN if pct > 60 else (YELLOW if pct > 30 else RED)
    pct_surf = font_big.render(f"{pct}%", True, col)
    screen.blit(pct_surf, pct_surf.get_rect(center=(bx + bw // 2, by + bh + 30)))


# ── Pantalla principal ─────────────────────────────────────────────────────

def mostrar_battery(
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
                reset_battery()
                return "incorrecto"
            _feedback   = None
            _input_text = ""
            _paso_actual += 1
            if _paso_actual >= total_pasos:
                reset_battery()
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
    linea = nivel.get("linea", "3")
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
    title = font_title.render("Carga de Energía", True, GREEN)
    screen.blit(title, title.get_rect(center=(center_x, 110)))

    # ── Enunciado del problema ─────────────────────────────────────────────
    if _enunciado:
        font_enun = pygame.font.SysFont("Arial", 23)
        lines = _wrap_text(_enunciado, font_enun, WIDTH - 160)
        panel_h = len(lines) * 30 + 18
        panel_rect = pygame.Rect(60, 147, WIDTH - 120, panel_h)
        pygame.draw.rect(screen, (15, 22, 35), panel_rect, border_radius=8)
        pygame.draw.rect(screen, GREEN, panel_rect, 1, border_radius=8)
        for i, line in enumerate(lines):
            lsurf = font_enun.render(line, True, (200, 240, 210))
            screen.blit(lsurf, lsurf.get_rect(center=(center_x, 156 + i * 30 + 6)))

    # ── Ratio de llenado ───────────────────────────────────────────────────
    if _feedback == "correcto":
        ratio = (_paso_actual + 1) / total_pasos
    else:
        ratio = _paso_actual / total_pasos

    # ── Gráfico de la curva (izquierda) ────────────────────────────────────
    font_small  = pygame.font.SysFont("Courier New", 18)
    graph_rect  = pygame.Rect(60, 230, WIDTH - 260, 370)
    _draw_curve_graph(screen, graph_rect, ratio, font_small)

    # ── Batería (derecha) ───────────────────────────────────────────────────
    bat_x  = WIDTH - 155
    bat_y  = 235
    bat_w  = 80
    bat_h  = 320
    _draw_battery(screen, bat_x, bat_y, bat_w, bat_h, ratio)

    # ── Paso actual ────────────────────────────────────────────────────────
    if _paso_actual < total_pasos:
        paso_txt  = _preguntas[_paso_actual]["pregunta"]
        paso_surf = font_title.render(f"Calcula:  {paso_txt}", True, WHITE)
        screen.blit(paso_surf, paso_surf.get_rect(center=(center_x - 60, 675)))

    # ── Bolitas ────────────────────────────────────────────────────────────
    dot_gap     = 44
    dot_start_x = (center_x - 60) - (total_pasos * dot_gap) // 2 + dot_gap // 2
    for i in range(total_pasos):
        dx = dot_start_x + i * dot_gap
        dy = 715
        if i < _paso_actual:
            pygame.draw.circle(screen, GREEN, (dx, dy), 10)
            pygame.draw.circle(screen, WHITE, (dx, dy), 10, 2)
        elif i == _paso_actual:
            pygame.draw.circle(screen, WHITE, (dx, dy), 10)
        else:
            pygame.draw.circle(screen, LIGHT_GREY, (dx, dy), 8)

    # ── Campo de texto ─────────────────────────────────────────────────────
    field_rect = pygame.Rect(0, 0, 480, 66)
    field_rect.center = (center_x - 60, 785)

    bg_col     = (18, 120, 50) if _feedback == "correcto" else PANEL
    border_col = GREEN if _feedback == "correcto" else CYAN

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
        btn.center = (center_x - 60, HEIGHT - 90)
        bc = (30, 55, 40) if btn.collidepoint(mouse_pos) else PANEL
        pygame.draw.rect(screen, bc,    btn, border_radius=10)
        pygame.draw.rect(screen, GREEN, btn, 1, border_radius=10)
        screen.blit(font_button.render("Confirmar  [Enter]", True, WHITE),
                    font_button.render("Confirmar  [Enter]", True, WHITE).get_rect(center=btn.center))

    # ── Flash feedback ─────────────────────────────────────────────────────
    if _feedback == "correcto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((0, 200, 80, 32))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Energia Acumulada!", True, GREEN)
        screen.blit(msg, msg.get_rect(center=(center_x - 60, HEIGHT - 38)))
    elif _feedback == "incorrecto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((200, 0, 0, 40))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Valor Incorrecto...", True, RED)
        screen.blit(msg, msg.get_rect(center=(center_x - 60, HEIGHT - 38)))

    return None
