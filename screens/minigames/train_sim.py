"""
screens/minigames/train_sim.py

Mini-juego simulador de velocidad del tren (Ecuaciones Diferenciales - Linea 3).

El usuario ingresa los valores de pendiente (Runge-Kutta).
Cada valor correcto hace avanzar suavemente el tren por la via.
Si hay error (por ahora desactivado), el tren frena bruscamente.
"""

import pygame
import math
import random
import re
import time
from core.math_fmt import fmt_math

WHITE      = (255, 255, 255)
DARK_GREY  = (14,  16,  22)
PANEL      = (26,  30,  42)
GRID_COL   = (36,  42,  58)
AXIS_COL   = (75,  85, 105)
LIGHT_GREY = (105, 115, 135)
GREEN      = ( 50, 225,  90)
YELLOW     = (255, 210,   0)
CYAN       = ( 70, 195, 255)
ORANGE     = (255, 148,  28)
RED        = (220,  55,  55)
RAIL_COL   = (130, 140, 160)
TIE_COL    = (100,  80,  55)

FEEDBACK_MS  = 900
TRAIN_EASE   = 0.06   # velocidad de interpolacion del tren (suavizado)

# Curva RK (derivada)  dy/dx = f(x,y) = cos(x) - simplificado para visual
def _rk_slope(x):
    return math.cos(x * 0.8) * 60 + 70   # velocidad ficticia en km/h

_RK_X  = [0.0, 1.0, 2.0, 3.0, 4.0]   # pasos de x
_X_MIN, _X_MAX = -0.3, 4.8
_Y_MIN, _Y_MAX = 0.0, 160.0


# -- Estado del modulo -------------------------------------------------------
_nivel_id        = None
_paso_actual     = 0
_input_text      = ""
_feedback        = None
_feedback_tick   = 0
_train_x         = 0.0   # posicion logica del tren [0, 1]
_train_x_target  = 0.0   # posicion destino
_enunciado       = ""
_preguntas       = []


def reset_train_sim() -> None:
    global _nivel_id, _paso_actual, _input_text
    global _feedback, _feedback_tick, _train_x, _train_x_target, _enunciado, _preguntas
    _nivel_id       = None
    _paso_actual    = 0
    _input_text     = ""
    _feedback       = None
    _feedback_tick  = 0
    _train_x        = 0.0
    _train_x_target = 0.0
    _enunciado      = ""
    _preguntas      = []


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


# -- Helpers de coordenadas para el grafico ----------------------------------

def _to_screen(gx, gy, rect):
    px = rect.left + (gx - _X_MIN) / (_X_MAX - _X_MIN) * rect.width
    py = rect.bottom - (gy - _Y_MIN) / (_Y_MAX - _Y_MIN) * rect.height
    return int(px), int(py)


# -- Dibujo del grafico de velocidad -----------------------------------------

def _draw_velocity_graph(screen, rect, n_puntos, font_small):
    """Dibuja la curva de velocidad y los puntos RK calculados."""
    pygame.draw.rect(screen, PANEL, rect, border_radius=8)
    pygame.draw.rect(screen, AXIS_COL, rect, 1, border_radius=8)

    # Cuadricula
    for gx in _RK_X[1:]:
        sx, _ = _to_screen(gx, 0, rect)
        pygame.draw.line(screen, GRID_COL, (sx, rect.top), (sx, rect.bottom), 1)
    for gy in [40, 80, 120]:
        _, sy = _to_screen(0, gy, rect)
        pygame.draw.line(screen, GRID_COL, (rect.left, sy), (rect.right, sy), 1)

    # Ejes
    _, oy = _to_screen(0, 0, rect)
    pygame.draw.line(screen, AXIS_COL, (rect.left, oy), (rect.right, oy), 2)

    # Curva de velocidad (siempre visible, atenuada)
    pts = []
    for k in range(121):
        gx = _X_MIN + (_X_MAX - _X_MIN) * k / 120
        gy = _rk_slope(gx)
        sx, sy = _to_screen(gx, gy, rect)
        if rect.left <= sx <= rect.right:
            pts.append((sx, max(rect.top, min(rect.bottom, sy))))
    if len(pts) >= 2:
        pygame.draw.lines(screen, (60, 90, 130), False, pts, 2)

    # Puntos RK calculados (van apareciendo con cada paso)
    rk_pts = []
    for i in range(min(n_puntos, len(_RK_X))):
        gx = _RK_X[i]
        gy = _rk_slope(gx)
        sx, sy = _to_screen(gx, gy, rect)
        rk_pts.append((sx, sy))
        pygame.draw.circle(screen, ORANGE, (sx, sy), 8)
        pygame.draw.circle(screen, WHITE,  (sx, sy), 8, 2)
        lbl = font_small.render(f"k{i+1}", True, ORANGE)
        screen.blit(lbl, (sx + 10, sy - 16))

    # Linea que une los puntos RK
    if len(rk_pts) >= 2:
        pygame.draw.lines(screen, ORANGE, False, rk_pts, 2)

    # Etiquetas
    screen.blit(font_small.render("t", True, LIGHT_GREY), (rect.right + 4, oy - 10))
    screen.blit(font_small.render("v (km/h)", True, LIGHT_GREY),
                (rect.left, rect.top - 22))


# -- Dibujo del tren ----------------------------------------------------------

def _draw_track_and_train(screen, rect, train_pos_ratio):
    """
    rect: pygame.Rect de la zona de via.
    train_pos_ratio in [0, 1]  posicion del tren en la via.
    """
    cx    = rect.left + int(train_pos_ratio * rect.width)
    track_y = rect.centery

    # Fondo de la zona (tunel)
    pygame.draw.rect(screen, (18, 18, 26),
                     pygame.Rect(rect.left, rect.top, rect.width, rect.height - 20),
                     border_radius=4)

    # Rieles
    pygame.draw.line(screen, RAIL_COL, (rect.left, track_y - 10), (rect.right, track_y - 10), 4)
    pygame.draw.line(screen, RAIL_COL, (rect.left, track_y + 10), (rect.right, track_y + 10), 4)

    # Traviesas
    spacing = 30
    for tx in range(rect.left, rect.right, spacing):
        pygame.draw.rect(screen, TIE_COL, (tx, track_y - 14, 18, 28), border_radius=2)

    # -- Tren ------------------------------------------------------------------
    tw, th = 130, 50
    ty     = track_y - th - 8
    tx_left = cx - tw // 2

    # Carroceria principal
    pygame.draw.rect(screen, (50, 80, 160),
                     pygame.Rect(tx_left, ty, tw, th), border_radius=10)
    pygame.draw.rect(screen, CYAN,
                     pygame.Rect(tx_left, ty, tw, th), 2, border_radius=10)

    # Franja frontal
    pygame.draw.rect(screen, YELLOW,
                     pygame.Rect(tx_left + tw - 16, ty + 5, 12, th - 10), border_radius=4)

    # Ventanas
    for wi in range(3):
        wx = tx_left + 12 + wi * 32
        pygame.draw.rect(screen, (180, 220, 255),
                         pygame.Rect(wx, ty + 8, 22, 18), border_radius=3)

    # Ruedas
    for wx in [tx_left + 18, tx_left + tw - 22]:
        pygame.draw.circle(screen, (60, 60, 70), (wx, ty + th + 2), 9)
        pygame.draw.circle(screen, RAIL_COL,     (wx, ty + th + 2), 9, 2)
        pygame.draw.circle(screen, WHITE,         (wx, ty + th + 2), 3)

    # Destello de movimiento (cuando avanza)
    if train_pos_ratio > 0.02:
        for k in range(3):
            sx = tx_left - 10 - k * 18
            pygame.draw.line(screen, (70, 195, 255),
                             (sx, ty + 15), (sx - 14, ty + 15), 2)
            pygame.draw.line(screen, (70, 195, 255),
                             (sx, ty + 35), (sx - 12, ty + 35), 2)


# -- Pantalla principal -------------------------------------------------------

def mostrar_train_sim(
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
    global _nivel_id, _paso_actual, _input_text
    global _feedback, _feedback_tick, _train_x, _train_x_target, _enunciado, _preguntas

    now      = pygame.time.get_ticks()
    center_x = WIDTH // 2

    # -- Inicializar ----------------------------------------------------------
    if _nivel_id != nivel.get("id"):
        _nivel_id       = nivel.get("id")
        _paso_actual    = 0
        _input_text     = ""
        _feedback       = None
        _feedback_tick  = 0
        _train_x        = 0.0
        _train_x_target = 0.0
        problemas = nivel.get("problemas", [])
        if problemas:
            problema   = nivel.get("problema_seleccionado") or random.choice(problemas)
            _enunciado = fmt_math(problema.get("enunciado", ""))
            _preguntas = problema.get("opciones", [])
        else:
            _enunciado = ""
            _preguntas = nivel.get("preguntas", [])

    total_pasos = len(_preguntas)
    if total_pasos == 0:
        return "nivel_completo"

    # -- Timer ----------------------------------------------------------------
    remaining = max(0, 1800 - int(time.time() - start_time)) if start_time else 1800
    if remaining <= 0:
        return "tiempo_agotado"

    # -- Layout dinámico anclado desde abajo ----------------------------------
    _enun_lines_n  = len(_enunciado.split('\n')) if _enunciado else 0
    _enun_bottom   = 143 + _enun_lines_n * 28 + 14 if _enun_lines_n else 143
    _confirm_cy    = HEIGHT - 35
    _field_cy      = _confirm_cy - 66     # confirm_half(25)+gap(12)+field_half(29)
    _dot_y         = _field_cy   - 51     # field_half(29)+gap(12)+dot_r(10)
    _calcula_y     = _dot_y      - 50     # dot_r(10)+gap(14)+calcula_half(26)
    _progreso_y    = _calcula_y  - 58     # calcula_half(26)+gap(14)+progreso_half(18)
    _track_h       = 60
    _track_bottom  = _progreso_y - 34     # progreso_half(18)+gap(16)
    _track_top     = _track_bottom - _track_h
    _graph_bottom  = _track_top  - 10
    _graph_h       = max(80, _graph_bottom - (_enun_bottom + 10))
    _graph_top     = _enun_bottom + 10

    _confirm_rect  = pygame.Rect(0, 0, 240, 50)
    _confirm_rect.center = (center_x, _confirm_cy)

    # -- Suavizado de movimiento del tren ------------------------------------
    _train_x += (_train_x_target - _train_x) * TRAIN_EASE

    # -- Check continuo: todos los pasos completados y tren ha llegado --------
    if _paso_actual >= total_pasos and _train_x >= 0.95:
        reset_train_sim()
        return "nivel_completo"

    # -- Transicion tras feedback ---------------------------------------------
    if _feedback is not None:
        if now - _feedback_tick >= FEEDBACK_MS:
            if _feedback == "incorrecto":
                reset_train_sim()
                return "incorrecto"
            _feedback   = None
            _input_text = ""
            _paso_actual += 1
            _train_x_target = _paso_actual / total_pasos
            if _paso_actual >= total_pasos:
                _train_x_target = 1.0

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
                if _confirm_rect.collidepoint(mouse_pos) and _input_text.strip():
                    correcta = _preguntas[_paso_actual]["respuesta"]
                    if _comparar(_input_text, correcta):
                        _feedback = "correcto"
                    else:
                        _feedback = "incorrecto"
                    _feedback_tick = now
                    break

    # =========================================================================
    # DIBUJO
    # =========================================================================
    screen.fill(DARK_GREY)

    # -- HUD ------------------------------------------------------------------
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

    # Timer HUD (a la izquierda de los corazones)
    timer_col  = RED if remaining <= 10 else (YELLOW if remaining <= 30 else WHITE)
    timer_surf = font_button.render(f"{remaining // 60:02}:{remaining % 60:02}", True, timer_col)
    hearts_left_x = WIDTH - 45 - (max(game_state.vidas, 1) - 1) * 38
    timer_rect = timer_surf.get_rect(right=hearts_left_x - 15, centery=37)
    screen.blit(timer_surf, timer_rect)

    # -- Titulo ---------------------------------------------------------------
    title = font_title.render("Simulador de Velocidad", True, ORANGE)
    screen.blit(title, title.get_rect(center=(center_x, 110)))

    # -- Enunciado del problema -----------------------------------------------
    if _enunciado:
        font_enun = pygame.font.SysFont("Courier New", 22)
        lines     = _enunciado.split('\n')
        line_h    = 28
        panel_h   = len(lines) * line_h + 14
        panel_rect = pygame.Rect(80, 143, WIDTH - 160, panel_h)
        pygame.draw.rect(screen, (18, 20, 30), panel_rect, border_radius=8)
        pygame.draw.rect(screen, ORANGE, panel_rect, 1, border_radius=8)
        for i, line in enumerate(lines):
            lsurf = font_enun.render(line, True, (255, 220, 180))
            screen.blit(lsurf, lsurf.get_rect(center=(center_x, 143 + 7 + i * line_h + line_h // 2)))

    # -- Grafico RK (parte superior) -----------------------------------------
    font_small = pygame.font.SysFont("Courier New", 18)
    graph_rect = pygame.Rect(80, _graph_top, WIDTH - 160, _graph_h)
    n_puntos_mostrar = _paso_actual + (1 if _feedback == "correcto" else 0)
    _draw_velocity_graph(screen, graph_rect, n_puntos_mostrar, font_small)

    # -- Zona del tren (parte inferior) --------------------------------------
    track_rect = pygame.Rect(40, _track_top, WIDTH - 80, _track_h)
    _draw_track_and_train(screen, track_rect, _train_x)

    # Etiqueta de progreso del tren
    km_surf = font_button.render(f"Progreso: {int(_train_x * 100)}%", True, YELLOW)
    screen.blit(km_surf, km_surf.get_rect(center=(center_x, _progreso_y)))

    # -- Paso actual ----------------------------------------------------------
    if _paso_actual < total_pasos:
        paso_txt  = _preguntas[_paso_actual]["pregunta"]
        paso_surf = font_title.render(f"Calcula:  {paso_txt}", True, WHITE)
        screen.blit(paso_surf, paso_surf.get_rect(center=(center_x, _calcula_y)))

    # -- Bolitas de progreso --------------------------------------------------
    dot_gap     = 44
    dot_start_x = center_x - (total_pasos * dot_gap) // 2 + dot_gap // 2
    for i in range(total_pasos):
        dx = dot_start_x + i * dot_gap
        if i < _paso_actual:
            pygame.draw.circle(screen, GREEN, (dx, _dot_y), 10)
            pygame.draw.circle(screen, WHITE, (dx, _dot_y), 10, 2)
        elif i == _paso_actual:
            pygame.draw.circle(screen, WHITE, (dx, _dot_y), 10)
        else:
            pygame.draw.circle(screen, LIGHT_GREY, (dx, _dot_y), 8)

    # -- Campo de texto -------------------------------------------------------
    field_rect = pygame.Rect(0, 0, 460, 58)
    field_rect.center = (center_x, _field_cy)

    bg_col     = (18, 120, 50) if _feedback == "correcto" else PANEL
    border_col = GREEN if _feedback == "correcto" else ORANGE

    pygame.draw.rect(screen, bg_col,     field_rect, border_radius=12)
    pygame.draw.rect(screen, border_col, field_rect, 2, border_radius=12)

    cursor     = "|" if (now // 500) % 2 == 0 else " "
    input_surf = font_title.render(_input_text + cursor, True, WHITE)
    screen.set_clip(field_rect.inflate(-16, -8))
    screen.blit(input_surf, input_surf.get_rect(center=field_rect.center))
    screen.set_clip(None)

    # -- Boton Confirmar ------------------------------------------------------
    if _feedback is None and _paso_actual < total_pasos:
        bc = (55, 50, 28) if _confirm_rect.collidepoint(mouse_pos) else PANEL
        pygame.draw.rect(screen, bc,          _confirm_rect, border_radius=10)
        pygame.draw.rect(screen, ORANGE,      _confirm_rect, 1, border_radius=10)
        lbl = font_button.render("Confirmar", True, WHITE)
        screen.blit(lbl, lbl.get_rect(center=_confirm_rect.center))

    # -- Flash feedback -------------------------------------------------------
    if _feedback == "correcto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((0, 200, 80, 30))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Tren en Marcha!", True, GREEN)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 38)))
    elif _feedback == "incorrecto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((200, 0, 0, 40))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Valor Incorrecto...", True, RED)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 38)))

    return None
