"""
screens/minigames/oscilloscope.py

Mini-juego del osciloscopio interactivo (Ecuaciones No Lineales – Línea 1).

Una onda senoidal vibra caóticamente en pantalla.
Conforme el usuario ingresa los valores correctos de cada paso,
la onda se va estabilizando hasta quedar perfectamente suave.
"""

import pygame
import math
import re
import random
import time
from core.math_fmt import fmt_math

# ── Colores ────────────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
DARK_GREY  = (20,  20,  20)
PANEL_GREY = (35,  38,  45)
LIGHT_GREY = (70,  70,  80)
GREEN      = (40,  230, 110)
RED        = (220,  55,  55)
YELLOW     = (255, 220,   0)
CYAN       = ( 80, 200, 255)
GRID_COL   = ( 45,  55,  45)

FEEDBACK_MS = 900   # duración del flash de respuesta


# ── Estado del módulo ──────────────────────────────────────────────────────
_nivel_id       = None
_paso_actual    = 0
_input_text     = ""
_feedback       = None        # None | "correcto" | "incorrecto"
_feedback_tick  = 0
_chaos_level    = 1.0         # 1.0 = máximo caos, 0.0 = onda estable
_enunciado      = ""
_preguntas      = []


def reset_oscilloscope() -> None:
    global _nivel_id, _paso_actual, _input_text
    global _feedback, _feedback_tick, _chaos_level, _enunciado, _preguntas
    _nivel_id      = None
    _paso_actual   = 0
    _input_text    = ""
    _feedback      = None
    _feedback_tick = 0
    _chaos_level   = 1.0
    _enunciado     = ""
    _preguntas     = []


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


# ── Comparación numérica ───────────────────────────────────────────────────

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


# ── Dibujo del osciloscopio ────────────────────────────────────────────────

def _draw_oscilloscope(screen, WIDTH, HEIGHT, chaos_level, now):
    """
    Dibuja la pantalla del osciloscopio con la onda senoidal.
    - chaos_level = 1.0 → onda muy irregular y ruidosa
    - chaos_level = 0.0 → onda limpia y estable
    """
    # Marco del osciloscopio (desplazado hacia abajo para dar espacio al enunciado)
    osc_rect = pygame.Rect(80, 255, WIDTH - 160, 265)
    pygame.draw.rect(screen, PANEL_GREY, osc_rect, border_radius=8)
    pygame.draw.rect(screen, CYAN,       osc_rect, 2, border_radius=8)

    # Cuadrícula interna
    cols, rows = 8, 4
    cw = osc_rect.width  // cols
    ch = osc_rect.height // rows
    for ci in range(1, cols):
        x = osc_rect.left + ci * cw
        pygame.draw.line(screen, GRID_COL, (x, osc_rect.top), (x, osc_rect.bottom), 1)
    for ri in range(1, rows):
        y = osc_rect.top + ri * ch
        pygame.draw.line(screen, GRID_COL, (osc_rect.left, y), (osc_rect.right, y), 1)

    # Eje central
    cy = osc_rect.centery
    pygame.draw.line(screen, (60, 80, 60), (osc_rect.left, cy), (osc_rect.right, cy), 1)

    # ── Generar puntos de la onda ──────────────────────────────────────────
    amp_base  = 90                   # amplitud de la onda base
    amp_noise = chaos_level * 65     # amplitud del ruido (desaparece al estabilizar)
    freq_base = 2.5                  # frecuencias de la onda senoidal base

    # Velocidades de las perturbaciones (varían con el tiempo → "vibra")
    t_sec = now / 1000.0

    points = []
    for px in range(osc_rect.left + 1, osc_rect.right - 1, 2):
        # Posición normalizada [0, 1] dentro del panel
        ratio = (px - osc_rect.left) / osc_rect.width
        phase = ratio * freq_base * 2 * math.pi - t_sec * 2.5

        y_base = amp_base * math.sin(phase)

        # Capas de ruido/caos que se reducen con el avance del jugador
        noise = 0.0
        if chaos_level > 0.0:
            # Componentes de alta frecuencia caóticas
            noise += amp_noise * 0.6  * math.sin(ratio * 18  * math.pi + t_sec * 7.3)
            noise += amp_noise * 0.35 * math.sin(ratio * 31  * math.pi - t_sec * 11.1)
            noise += amp_noise * 0.20 * math.cos(ratio * 47  * math.pi + t_sec * 4.7)
            noise += amp_noise * 0.15 * math.sin(ratio * 5.5 * math.pi - t_sec * 3.2)
            # Modulación de amplitud aleatoria suavizada
            noise += amp_noise * 0.25 * math.sin(t_sec * 2.9 + ratio * 8)

        py_val = cy + y_base + noise
        # Clamp dentro del panel
        py_val = max(osc_rect.top + 4, min(osc_rect.bottom - 4, py_val))
        points.append((px, int(py_val)))

    if len(points) >= 2:
        # Color de la onda: rojo cuando caótica, verde cuando estable
        r = int(220 * chaos_level + 40 * (1 - chaos_level))
        g = int(230 * (1 - chaos_level) + 55 * chaos_level)
        b = int(50  * (1 - chaos_level) + 80 * chaos_level)
        pygame.draw.lines(screen, (r, g, b), False, points, 2)

    # Etiquetas de ejes
    font_small = pygame.font.SysFont("Courier New", 18, bold=True)
    screen.blit(font_small.render("V", True, CYAN), (osc_rect.left - 25, cy - 10))
    screen.blit(font_small.render("t", True, CYAN), (osc_rect.right + 5, cy - 10))

    # Indicador de estabilidad
    stable_pct = int((1 - chaos_level) * 100)
    col_bar    = GREEN if stable_pct > 70 else (YELLOW if stable_pct > 35 else RED)
    bar_label  = font_small.render(f"Estabilidad: {stable_pct}%", True, col_bar)
    screen.blit(bar_label, (osc_rect.left, osc_rect.bottom + 10))

    # Barra de progreso de estabilidad
    bar_w   = osc_rect.width
    bar_h   = 8
    bar_rect = pygame.Rect(osc_rect.left, osc_rect.bottom + 35, bar_w, bar_h)
    pygame.draw.rect(screen, LIGHT_GREY, bar_rect, border_radius=4)
    fill_rect = pygame.Rect(osc_rect.left, osc_rect.bottom + 35,
                            int(bar_w * (1 - chaos_level)), bar_h)
    if fill_rect.width > 0:
        pygame.draw.rect(screen, col_bar, fill_rect, border_radius=4)


# ── Pantalla principal ─────────────────────────────────────────────────────

def mostrar_oscilloscope(
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
    """
    Retorna:
      'nivel_completo'  → todos los pasos correctos
      None              → sin acción este frame
    """
    global _nivel_id, _paso_actual, _input_text
    global _feedback, _feedback_tick, _chaos_level, _enunciado, _preguntas

    now      = pygame.time.get_ticks()
    center_x = WIDTH  // 2

    # ── Inicializar al entrar al nivel ─────────────────────────────────────
    if _nivel_id != nivel.get("id"):
        _nivel_id     = nivel.get("id")
        _paso_actual  = 0
        _input_text   = ""
        _feedback     = None
        _chaos_level  = 1.0
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

    # ── Timer ──────────────────────────────────────────────────────────────
    remaining = max(0, 1800 - int(time.time() - start_time)) if start_time else 1800
    if remaining <= 0:
        return "tiempo_agotado"

    # ── Resolver feedback y transición al siguiente paso ───────────────────
    if _feedback is not None:
        if now - _feedback_tick >= FEEDBACK_MS:
            if _feedback == "incorrecto":
                reset_oscilloscope()
                return "incorrecto"
            _feedback   = None
            _input_text = ""
            _paso_actual += 1
            if _paso_actual >= total_pasos:
                reset_oscilloscope()
                return "nivel_completo"

    else:
        # ── Procesar entrada de teclado ────────────────────────────────────
        for ev in all_events:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if _input_text.strip():
                        correcta = _preguntas[_paso_actual]["respuesta"]
                        if _comparar(_input_text, correcta):
                            _feedback    = "correcto"
                            _chaos_level = max(0.0, 1.0 - (_paso_actual + 1) / total_pasos)
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
                btn.center = (center_x, HEIGHT - 120)
                if btn.collidepoint(mouse_pos) and _input_text.strip():
                    correcta = _preguntas[_paso_actual]["respuesta"]
                    if _comparar(_input_text, correcta):
                        _feedback    = "correcto"
                        _chaos_level = max(0.0, 1.0 - (_paso_actual + 1) / total_pasos)
                    else:
                        _feedback = "incorrecto"
                    _feedback_tick = now
                    break

    # ══════════════════════════════════════════════════════════════════════
    # DIBUJO
    # ══════════════════════════════════════════════════════════════════════
    screen.fill(DARK_GREY)

    # Líneas de escaneo sutiles (efecto CRT)
    scan_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for sy in range(0, HEIGHT, 4):
        pygame.draw.line(scan_surf, (0, 0, 0, 30), (0, sy), (WIDTH, sy), 1)
    screen.blit(scan_surf, (0, 0))

    # ── HUD ───────────────────────────────────────────────────────────────
    linea = nivel.get("linea", "1")
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
    title = font_title.render("Osciloscopio", True, CYAN)
    screen.blit(title, title.get_rect(center=(center_x, 130)))

    # ── Enunciado del problema ─────────────────────────────────────────────
    if _enunciado:
        font_enun = pygame.font.SysFont("Arial", 23)
        lines = _wrap_text(_enunciado, font_enun, WIDTH - 160)
        panel_h = len(lines) * 30 + 18
        panel_rect = pygame.Rect(60, 150, WIDTH - 120, panel_h)
        pygame.draw.rect(screen, (15, 25, 40), panel_rect, border_radius=8)
        pygame.draw.rect(screen, CYAN, panel_rect, 1, border_radius=8)
        for i, line in enumerate(lines):
            lsurf = font_enun.render(line, True, (200, 225, 255))
            screen.blit(lsurf, lsurf.get_rect(center=(center_x, 159 + i * 30 + 6)))

    # ── Osciloscopio animado ───────────────────────────────────────────────
    _draw_oscilloscope(screen, WIDTH, HEIGHT, _chaos_level, now)

    # ── Indicador de paso ──────────────────────────────────────────────────
    paso_surf = font_button.render(
        f"Paso {_paso_actual + 1} de {total_pasos}", True, YELLOW)
    screen.blit(paso_surf, paso_surf.get_rect(center=(center_x, 580)))

    # Bolitas de progreso
    dot_gap     = 44
    dot_start_x = center_x - (total_pasos * dot_gap) // 2 + dot_gap // 2
    for i in range(total_pasos):
        dot_x = dot_start_x + i * dot_gap
        dot_y = 610
        if i < _paso_actual:
            pygame.draw.circle(screen, GREEN, (dot_x, dot_y), 10)
            pygame.draw.circle(screen, WHITE, (dot_x, dot_y), 10, 2)
        elif i == _paso_actual:
            pygame.draw.circle(screen, WHITE, (dot_x, dot_y), 10)
        else:
            pygame.draw.circle(screen, LIGHT_GREY, (dot_x, dot_y), 8)

    # ── Pregunta actual ────────────────────────────────────────────────────
    if _feedback is None or True:   # siempre visible
        pregunta_txt = _preguntas[_paso_actual]["pregunta"]
        preg_surf    = font_title.render(f"Calcula:  {pregunta_txt}", True, WHITE)
        screen.blit(preg_surf, preg_surf.get_rect(center=(center_x, 665)))

    # ── Campo de texto ─────────────────────────────────────────────────────
    field_rect = pygame.Rect(0, 0, 500, 68)
    field_rect.center = (center_x, 740)

    if _feedback == "correcto":
        field_bg, border_c = (18, 130, 55), GREEN
    elif _feedback == "incorrecto":
        field_bg, border_c = (140, 25, 25), RED
    else:
        field_bg, border_c = (45, 48, 58), CYAN

    pygame.draw.rect(screen, field_bg,   field_rect, border_radius=12)
    pygame.draw.rect(screen, border_c,   field_rect, 2, border_radius=12)

    cursor     = "|" if (now // 500) % 2 == 0 else " "
    input_surf = font_title.render(_input_text + cursor, True, WHITE)
    screen.set_clip(field_rect.inflate(-18, -8))
    screen.blit(input_surf, input_surf.get_rect(center=field_rect.center))
    screen.set_clip(None)

    # ── Botón Confirmar ────────────────────────────────────────────────────
    if _feedback is None:
        btn = pygame.Rect(0, 0, 240, 52)
        btn.center = (center_x, HEIGHT - 120)
        btn_col = (50, 65, 80) if btn.collidepoint(mouse_pos) else (40, 50, 65)
        pygame.draw.rect(screen, btn_col, btn, border_radius=10)
        pygame.draw.rect(screen, CYAN,    btn, 1, border_radius=10)
        label = font_button.render("Confirmar  [Enter]", True, WHITE)
        screen.blit(label, label.get_rect(center=btn.center))

    # ── Flash de feedback ──────────────────────────────────────────────────
    if _feedback == "correcto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((0, 200, 80, 40))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Señal Estabilizada!", True, GREEN)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 60)))

    elif _feedback == "incorrecto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((200, 0, 0, 40))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Valor Incorrecto...", True, RED)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 60)))

    return None
