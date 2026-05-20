"""
screens/minigames/cables.py

Mini-juego de arrastrar y soltar cables (Interpolación – Línea 1).

Lado izquierdo : terminales con las etiquetas de pregunta  (f(a), f(b), …)
Lado derecho   : terminales con los valores de respuesta  (barajados)

Mecánica
--------
- Clic en un terminal izquierdo y arrastra hasta el terminal derecho correcto.
- Conexión correcta → cable verde fijo, chispas desaparecen.
- Conexión incorrecta → destello rojo, desconexión.
- Al conectar los 4 pares → retorna "nivel_completo".
"""

import pygame
import random
import math
import time
from core.math_fmt import fmt_math

# ── Colores ────────────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
DARK_GREY  = (30,  30,  30)
LIGHT_GREY = (70,  70,  70)
GREEN      = (40,  210, 110)
RED        = (220, 55,  55)
YELLOW     = (255, 220,  0)
ORANGE     = (255, 140,  0)
CYAN       = ( 80, 200, 255)

PORT_R    = 20      # radio del terminal
FLASH_MS  = 480     # duración del destello de error
CABLE_W   = 5       # grosor del cable


# ── Estado del módulo ──────────────────────────────────────────────────────
_nivel_id       = None
_derecha_order  = []   # _derecha_order[visual_j] = índice de pregunta real
_conexiones     = {}   # left_idx → right_visual_j  (parejas correctas bloqueadas)
_dragging_from  = None # left_idx que se está arrastrando, o None
_wrong_flash    = {}   # left_idx → tick_fin  (ms)
_enunciado      = ""   # enunciado del problema seleccionado
_preguntas      = []   # opciones del problema seleccionado


def reset_cables() -> None:
    global _nivel_id, _derecha_order, _conexiones, _dragging_from, _wrong_flash
    global _enunciado, _preguntas
    _nivel_id      = None
    _derecha_order = []
    _conexiones    = {}
    _dragging_from = None
    _wrong_flash   = {}
    _enunciado     = ""
    _preguntas     = []


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


# ── Helpers de dibujo ──────────────────────────────────────────────────────

def _draw_cable(screen, p1, p2, color, width=CABLE_W):
    """Cable con curvatura natural (quadratic bezier aproximado)."""
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2 + 55   # sag descendente
    pts = []
    for k in range(21):
        t  = k / 20
        x  = (1 - t)**2 * p1[0] + 2 * (1 - t) * t * mx + t**2 * p2[0]
        y  = (1 - t)**2 * p1[1] + 2 * (1 - t) * t * my + t**2 * p2[1]
        pts.append((int(x), int(y)))
    if len(pts) >= 2:
        pygame.draw.lines(screen, color, False, pts, width)


def _draw_sparks(screen, cx, cy, now, intensity=1.0):
    """Chispas animadas alrededor de un terminal sin conectar."""
    rng = random.Random((now // 80) * 1000 + cx * 31 + cy)
    n_sparks = int(4 * intensity)
    for _ in range(n_sparks):
        angle = rng.uniform(0, 2 * math.pi)
        dist  = rng.uniform(22, 42)
        sx    = cx + int(math.cos(angle) * dist)
        sy    = cy + int(math.sin(angle) * dist)
        col   = YELLOW if rng.random() > 0.45 else ORANGE
        pygame.draw.line(screen, col, (cx, cy), (sx, sy), 2)
        # Pequeña chispa secundaria
        angle2 = angle + rng.uniform(-0.6, 0.6)
        dist2  = rng.uniform(5, 18)
        sx2    = sx + int(math.cos(angle2) * dist2)
        sy2    = sy + int(math.sin(angle2) * dist2)
        pygame.draw.line(screen, ORANGE, (sx, sy), (sx2, sy2), 1)


def _get_layout(n, WIDTH, HEIGHT, top_y=260):
    """Devuelve listas de coordenadas (x,y) para terminales izquierdos y derechos."""
    available = HEIGHT - top_y - 80
    spacing   = min(130, available // max(n, 1))
    mid_y     = (top_y + HEIGHT - 80) // 2
    start_y   = mid_y - (n - 1) * spacing // 2
    lx = WIDTH // 4
    rx = 3 * WIDTH // 4
    left_ports  = [(lx, start_y + i * spacing) for i in range(n)]
    right_ports = [(rx, start_y + i * spacing) for i in range(n)]
    return left_ports, right_ports


def _hit_port(mx, my, ports, exclude=None):
    """Retorna el índice del primer terminal tocado, o None."""
    for i, (px, py) in enumerate(ports):
        if exclude is not None and i in exclude:
            continue
        if math.hypot(mx - px, my - py) <= PORT_R + 14:
            return i
    return None


# ── Pantalla principal ─────────────────────────────────────────────────────

def mostrar_cables(
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
      'nivel_completo'  → todos los cables conectados correctamente
      None              → sin acción este frame
    """
    global _nivel_id, _derecha_order, _conexiones, _dragging_from, _wrong_flash
    global _enunciado, _preguntas

    now = pygame.time.get_ticks()

    # ── Inicializar al entrar al nivel ─────────────────────────────────────
    if _nivel_id != nivel.get("id"):
        _nivel_id      = nivel.get("id")
        _conexiones    = {}
        _dragging_from = None
        _wrong_flash   = {}
        problemas = nivel.get("problemas", [])
        if problemas:
            problema   = nivel.get("problema_seleccionado") or random.choice(problemas)
            _enunciado = fmt_math(problema.get("enunciado", ""))
            _preguntas = problema.get("opciones", [])
        else:
            _enunciado = ""
            _preguntas = nivel.get("preguntas", [])
        indices = list(range(len(_preguntas)))
        random.shuffle(indices)
        _derecha_order = indices

    n = len(_preguntas)
    if n == 0:
        return "nivel_completo"

    # ── Timer ──────────────────────────────────────────────────────────────
    remaining = max(0, 1800 - int(time.time() - start_time)) if start_time else 1800
    if remaining <= 0:
        return "tiempo_agotado"

    # Limpiar destellos expirados
    _wrong_flash = {k: v for k, v in _wrong_flash.items() if now < v}

    # Calcular fondo del panel del enunciado para que los terminales no se encimen
    _font_enun_tmp = pygame.font.SysFont("Arial", 23)
    _enun_lines    = len(_wrap_text(_enunciado, _font_enun_tmp, WIDTH - 160)) if _enunciado else 0
    enun_bottom    = 175 + _enun_lines * 30 + 18 + 20 if _enunciado else 195

    left_ports, right_ports = _get_layout(n, WIDTH, HEIGHT, top_y=enun_bottom)

    # ── Procesar eventos ───────────────────────────────────────────────────
    locked_left  = set(_conexiones.keys())
    locked_right = set(_conexiones.values())

    for ev in all_events:
        if ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            idx = _hit_port(mx, my, left_ports, exclude=locked_left)
            if idx is not None:
                _dragging_from = idx

        elif ev.type == pygame.MOUSEBUTTONUP:
            if _dragging_from is not None:
                mx, my = ev.pos
                j = _hit_port(mx, my, right_ports, exclude=locked_right)
                if j is not None:
                    real_idx = _derecha_order[j]
                    if real_idx == _dragging_from:
                        _conexiones[_dragging_from] = j    # ✓ correcto
                    else:
                        _wrong_flash[_dragging_from] = now + FLASH_MS  # ✗ error
                _dragging_from = None

    # ── ¿Completado? ───────────────────────────────────────────────────────
    if len(_conexiones) == n:
        reset_cables()
        return "nivel_completo"

    # ══════════════════════════════════════════════════════════════════════
    # DIBUJO
    # ══════════════════════════════════════════════════════════════════════
    screen.fill(DARK_GREY)

    # Fondo de cuadrícula técnica sutil
    for gx in range(0, WIDTH, 60):
        pygame.draw.line(screen, (40, 40, 40), (gx, 0), (gx, HEIGHT), 1)
    for gy in range(0, HEIGHT, 60):
        pygame.draw.line(screen, (40, 40, 40), (0, gy), (WIDTH, gy), 1)

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
    timer_txt = f"{remaining // 60:02}:{remaining % 60:02}"
    screen.blit(font_button.render(timer_txt, True, timer_col), (WIDTH - 305, 55))

    # ── Título ─────────────────────────────────────────────────────────────
    title_surf = font_title.render("Conecta los cables", True, YELLOW)
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 110)))

    instr = font_button.render("Arrastra cada terminal izquierdo al valor correcto", True, LIGHT_GREY)
    screen.blit(instr, instr.get_rect(center=(WIDTH // 2, 155)))

    # ── Enunciado del problema ─────────────────────────────────────────────
    if _enunciado:
        font_enun = pygame.font.SysFont("Arial", 23)
        lines = _wrap_text(_enunciado, font_enun, WIDTH - 160)
        panel_h = len(lines) * 30 + 18
        panel_rect = pygame.Rect(60, 175, WIDTH - 120, panel_h)
        pygame.draw.rect(screen, (18, 28, 45), panel_rect, border_radius=8)
        pygame.draw.rect(screen, CYAN, panel_rect, 1, border_radius=8)
        for i, line in enumerate(lines):
            lsurf = font_enun.render(line, True, (200, 225, 255))
            screen.blit(lsurf, lsurf.get_rect(center=(WIDTH // 2, 184 + i * 30 + 6)))

    # ── Cables ya conectados ───────────────────────────────────────────────
    for left_idx, right_j in _conexiones.items():
        _draw_cable(screen, left_ports[left_idx], right_ports[right_j], GREEN)

    # ── Cable en arrastre ──────────────────────────────────────────────────
    if _dragging_from is not None:
        _draw_cable(screen, left_ports[_dragging_from], mouse_pos, CYAN, 3)

    # ── Terminales izquierdos ──────────────────────────────────────────────
    for i, (px, py) in enumerate(left_ports):
        label = _preguntas[i]["pregunta"]

        if i in _conexiones:
            ring_col  = GREEN
            inner_col = (15, 80, 40)
            chispas   = False
        elif i in _wrong_flash:
            ring_col  = RED
            inner_col = (80, 20, 20)
            chispas   = True
        elif i == _dragging_from:
            ring_col  = CYAN
            inner_col = (20, 70, 90)
            chispas   = False
        else:
            ring_col  = WHITE
            inner_col = LIGHT_GREY
            chispas   = True

        # Chispas antes del terminal para que queden detrás
        if chispas:
            _draw_sparks(screen, px, py, now)

        pygame.draw.circle(screen, ring_col,  (px, py), PORT_R)
        pygame.draw.circle(screen, inner_col, (px, py), PORT_R - 6)

        lbl = font_button.render(label, True, ring_col)
        screen.blit(lbl, (px + PORT_R + 12, py - lbl.get_height() // 2))

    # ── Terminales derechos ────────────────────────────────────────────────
    locked_right = set(_conexiones.values())

    for j, (px, py) in enumerate(right_ports):
        real_idx   = _derecha_order[j]
        label      = _preguntas[real_idx]["respuesta"]
        connected  = j in locked_right

        if connected:
            ring_col  = GREEN
            inner_col = (15, 80, 40)
            chispas   = False
        else:
            ring_col  = WHITE
            inner_col = LIGHT_GREY
            chispas   = True

        if chispas:
            _draw_sparks(screen, px, py, now)

        pygame.draw.circle(screen, ring_col,  (px, py), PORT_R)
        pygame.draw.circle(screen, inner_col, (px, py), PORT_R - 6)

        lbl = font_button.render(label, True, ring_col)
        screen.blit(lbl, (px - PORT_R - 12 - lbl.get_width(),
                          py - lbl.get_height() // 2))

    # ── Progreso ───────────────────────────────────────────────────────────
    done     = len(_conexiones)
    prog_txt = font_button.render(f"Conectados: {done} / {n}", True, YELLOW)
    screen.blit(prog_txt, prog_txt.get_rect(center=(WIDTH // 2, HEIGHT - 45)))

    return None
