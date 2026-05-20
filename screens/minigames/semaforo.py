"""
screens/minigames/semaforo.py

Mini-juego de conmutador de red / semáforos (Sistemas Lineales – Línea 2).

Una cuadrícula de semáforos de estación, uno por variable del sistema.
Cada variable que el usuario resuelve (x1, x2, …) cambia su luz de rojo a verde.
"""

import pygame
import math
import random
import re
import time
from core.math_fmt import fmt_math

WHITE      = (255, 255, 255)
DARK_GREY  = (22,  25,  30)
PANEL      = (35,  40,  50)
LIGHT_GREY = (90,  95, 105)
GREEN      = (50,  230, 100)
RED        = (220,  50,  50)
YELLOW_LED = (255, 230,   0)
YELLOW     = (255, 220,   0)
CYAN       = ( 70, 190, 255)
AMBER      = (255, 160,   0)

FEEDBACK_MS = 800

# Fuente con soporte completo de superíndices Unicode (²  ³  ⁴  …)
_label_font_cache: dict = {}

def _get_label_font(size: int):
    if size not in _label_font_cache:
        for name in ("Menlo", "DejaVu Sans", "Courier New", "Arial Unicode MS"):
            f = pygame.font.SysFont(name, size)
            if f.size("⁴")[0] > 8:   # glifo real, no caja vacía
                _label_font_cache[size] = f
                break
        else:
            _label_font_cache[size] = pygame.font.SysFont(None, size)
    return _label_font_cache[size]


def _make_label_surf(text: str, font, color, max_w: int):
    """Renderiza texto en una o varias líneas si supera max_w."""
    if font.size(text)[0] <= max_w:
        return font.render(text, True, color)
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    surfs   = [font.render(l, True, color) for l in lines]
    line_h  = surfs[0].get_height()
    total_h = line_h * len(surfs) + 3 * (len(surfs) - 1)
    max_lw  = max(s.get_width() for s in surfs)
    out     = pygame.Surface((max_lw, total_h), pygame.SRCALPHA)
    for idx, s in enumerate(surfs):
        out.blit(s, ((max_lw - s.get_width()) // 2, idx * (line_h + 3)))
    return out


# ── Estado del módulo ──────────────────────────────────────────────────────
_nivel_id      = None
_paso_actual   = 0
_input_text    = ""
_feedback      = None
_feedback_tick = 0
_resueltas     = set()   # índices de variables ya resueltas
_enunciado     = ""
_preguntas     = []


def reset_semaforo() -> None:
    global _nivel_id, _paso_actual, _input_text, _feedback, _feedback_tick, _resueltas
    global _enunciado, _preguntas
    _nivel_id      = None
    _paso_actual   = 0
    _input_text    = ""
    _feedback      = None
    _feedback_tick = 0
    _resueltas     = set()
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
    result = []
    for raw in text.split('\n'):
        if font.size(raw)[0] <= max_width:
            result.append(raw)
        else:
            words = raw.split()
            current = ""
            for word in words:
                test = (current + " " + word).strip()
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        result.append(current)
                    current = word
            if current:
                result.append(current)
    return result


# ── Dibujo de un semáforo individual ───────────────────────────────────────

def _draw_semaforo(screen, cx, cy, estado, label_surf, font_button, parpadeo, box_h=160):
    """
    estado: 'rojo' | 'verde' | 'activo'
    parpadeo: bool – si es el activo, hace blink ámbar
    box_h: altura de la caja (se escala todo proporcionalmente)
    """
    scale  = box_h / 160
    box_w  = int(80  * scale)
    lr     = int(22  * scale)   # radio luz
    lo     = int(30  * scale)   # offset luz desde cy
    sup_h  = int(20  * scale)   # altura soporte
    sup_w  = max(4, int(10 * scale))
    glow_r = int(35  * scale)

    box = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
    pygame.draw.rect(screen, (20, 22, 28), box, border_radius=max(4, int(10 * scale)))
    pygame.draw.rect(screen, LIGHT_GREY,   box, 2, border_radius=max(4, int(10 * scale)))

    # Soporte
    pygame.draw.rect(screen, LIGHT_GREY, (cx - sup_w // 2, cy + box_h // 2, sup_w, sup_h))

    # Luz superior
    red_on  = estado in ("rojo", "activo")
    red_col = RED if red_on else (60, 15, 15)
    pygame.draw.circle(screen, red_col, (cx, cy - lo), lr)
    if red_on:
        gs = glow_r * 2
        glow = pygame.Surface((gs, gs), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*RED, 40), (glow_r, glow_r), glow_r)
        screen.blit(glow, (cx - glow_r, cy - lo - glow_r))

    # Luz inferior
    green_on  = estado == "verde"
    green_col = GREEN if green_on else (10, 50, 20)
    pygame.draw.circle(screen, green_col, (cx, cy + lo), lr)
    if green_on:
        gs = glow_r * 2
        glow = pygame.Surface((gs, gs), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*GREEN, 40), (glow_r, glow_r), glow_r)
        screen.blit(glow, (cx - glow_r, cy + lo - glow_r))

    # Luz ámbar (activo)
    if estado == "activo":
        now = pygame.time.get_ticks()
        if (now // 400) % 2 == 0:
            pygame.draw.circle(screen, AMBER, (cx, cy), max(8, int(16 * scale)))

    # Etiqueta debajo
    label_top = cy + box_h // 2 + sup_h + max(6, int(10 * scale))
    screen.blit(label_surf, label_surf.get_rect(midtop=(cx, label_top)))


# ── Pantalla principal ─────────────────────────────────────────────────────

def mostrar_semaforo(
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
    global _nivel_id, _paso_actual, _input_text, _feedback, _feedback_tick, _resueltas
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
        _resueltas     = set()
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

    # ── Transición tras feedback ───────────────────────────────────────────
    if _feedback is not None:
        if now - _feedback_tick >= FEEDBACK_MS:
            if _feedback == "incorrecto":
                reset_semaforo()
                return "incorrecto"
            _resueltas.add(_paso_actual)
            _feedback   = None
            _input_text = ""
            _paso_actual += 1
            if _paso_actual >= total_pasos:
                reset_semaforo()
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
                btn = pygame.Rect(0, 0, 288, 52)
                btn.center = (center_x, HEIGHT - 95)
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

    # Cuadrícula de fondo (efecto red)
    for gx in range(0, WIDTH, 80):
        pygame.draw.line(screen, (30, 35, 45), (gx, 0), (gx, HEIGHT), 1)
    for gy in range(0, HEIGHT, 80):
        pygame.draw.line(screen, (30, 35, 45), (0, gy), (WIDTH, gy), 1)

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

    # Timer HUD (a la izquierda de los corazones)
    timer_col  = RED if remaining <= 10 else (YELLOW if remaining <= 30 else WHITE)
    timer_surf = font_title.render(f"{remaining // 60:02}:{remaining % 60:02}", True, timer_col)
    hearts_left_x = WIDTH - 45 - (max(game_state.vidas, 1) - 1) * 38
    timer_rect = timer_surf.get_rect(right=hearts_left_x - 18, centery=37)
    screen.blit(timer_surf, timer_rect)

    # ── Título ─────────────────────────────────────────────────────────────
    title = font_title.render("Red de Señales", True, YELLOW)
    screen.blit(title, title.get_rect(center=(center_x, 115)))

    # ── Enunciado del problema ─────────────────────────────────────────────
    enun_bottom = 148
    if _enunciado:
        font_enun = pygame.font.SysFont("Courier New", 21)
        lines = _wrap_text(_enunciado, font_enun, WIDTH - 160)
        panel_h = len(lines) * 30 + 18
        panel_rect = pygame.Rect(60, 150, WIDTH - 120, panel_h)
        pygame.draw.rect(screen, (20, 25, 35), panel_rect, border_radius=8)
        pygame.draw.rect(screen, CYAN, panel_rect, 1, border_radius=8)
        for i, line in enumerate(lines):
            lsurf = font_enun.render(line, True, (200, 225, 255))
            screen.blit(lsurf, lsurf.get_rect(center=(center_x, 159 + i * 30 + 6)))
        enun_bottom = 150 + panel_h

    # ── Semáforos ──────────────────────────────────────────────────────────
    # Escalar semáforo según cantidad de pasos para que todo quepa
    sem_box_h   = 120 if total_pasos >= 5 else 160
    sem_scale   = sem_box_h / 160
    sup_h       = int(20 * sem_scale)
    lbl_off     = max(6, int(10 * sem_scale))

    spacing     = min(int(160 * sem_scale), (WIDTH - 200) // max(total_pasos, 1))
    start_sem   = center_x - (total_pasos - 1) * spacing // 2
    sem_cy      = max(int(280 * sem_scale) + 60, enun_bottom + sem_box_h // 2 + 20)

    lbl_font_sz = 20 if total_pasos >= 5 else font_button.size("A")[1]
    label_font  = _get_label_font(lbl_font_sz)
    label_surfs = []
    for i in range(total_pasos):
        label_txt  = _preguntas[i]["pregunta"]
        label_surfs.append(_make_label_surf(label_txt, label_font, CYAN, spacing - 8))

    max_label_h = max((s.get_height() for s in label_surfs), default=24)

    for i in range(total_pasos):
        sx = start_sem + i * spacing
        if i in _resueltas:
            estado = "verde"
        elif i == _paso_actual:
            estado = "activo"
        else:
            estado = "rojo"
        _draw_semaforo(screen, sx, sem_cy, estado, label_surfs[i], font_button,
                       parpadeo=(i == _paso_actual), box_h=sem_box_h)

    # ── Variable actual ────────────────────────────────────────────────────
    label_bottom = sem_cy + sem_box_h // 2 + sup_h + lbl_off + max_label_h
    resuelve_y   = max(int(HEIGHT * 0.68), label_bottom + 20)
    field_y      = max(int(HEIGHT * 0.78), resuelve_y + 62)
    if _paso_actual < total_pasos:
        var_txt  = _preguntas[_paso_actual]["pregunta"]
        var_surf = font_title.render(f"Resuelve:  {var_txt}", True, WHITE)
        screen.blit(var_surf, var_surf.get_rect(center=(center_x, resuelve_y)))

    # ── Campo de texto ─────────────────────────────────────────────────────
    field_rect = pygame.Rect(0, 0, 480, 66)
    field_rect.center = (center_x, field_y)

    if _feedback == "correcto":
        bg_col, border_col = (18, 120, 50), GREEN
    else:
        bg_col, border_col = PANEL, CYAN

    pygame.draw.rect(screen, bg_col,    field_rect, border_radius=12)
    pygame.draw.rect(screen, border_col, field_rect, 2, border_radius=12)

    cursor     = "|" if (now // 500) % 2 == 0 else " "
    input_surf = font_title.render(_input_text + cursor, True, WHITE)
    screen.set_clip(field_rect.inflate(-16, -8))
    screen.blit(input_surf, input_surf.get_rect(center=field_rect.center))
    screen.set_clip(None)

    # ── Botón Confirmar ────────────────────────────────────────────────────
    if _feedback is None:
        lbl_confirm = font_button.render("Confirmar", True, WHITE)
        btn = pygame.Rect(0, 0, lbl_confirm.get_width() + 48, 52)
        btn.center = (center_x, field_rect.bottom + 40)
        bc = (50, 65, 80) if btn.collidepoint(mouse_pos) else PANEL
        pygame.draw.rect(screen, bc,   btn, border_radius=10)
        pygame.draw.rect(screen, CYAN, btn, 1, border_radius=10)
        screen.blit(lbl_confirm, lbl_confirm.get_rect(center=btn.center))

    # ── Flash de feedback ──────────────────────────────────────────────────
    if _feedback == "correcto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((0, 200, 80, 35))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Señal Sincronizada!", True, GREEN)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 40)))
    elif _feedback == "incorrecto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((200, 0, 0, 40))
        screen.blit(fb, (0, 0))
        msg = font_title.render("Valor Incorrecto...", True, RED)
        screen.blit(msg, msg.get_rect(center=(center_x, HEIGHT - 40)))

    return None
