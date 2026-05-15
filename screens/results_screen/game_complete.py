"""
screens/results_screen/game_complete.py

Pantalla de victoria total: el jugador completo todos los niveles.
Coloca assets/game_complete.png para mostrar una imagen celebratoria.
"""

import pygame
import math
import random

WHITE      = (255, 255, 255)
DARK_GREY  = (15,  18,  24)
GOLD       = (255, 200,  30)
GREEN      = ( 50, 225,  90)
CYAN       = ( 70, 195, 255)
LIGHT_GREY = (180, 185, 200)
PANEL      = (28,  33,  48)
ORANGE     = (255, 145,  30)

_STAR_SEED = 42


def _draw_stars(screen, WIDTH, HEIGHT, now):
    rng = random.Random(_STAR_SEED)
    for _ in range(55):
        sx    = rng.randint(0, WIDTH)
        sy    = rng.randint(0, HEIGHT)
        phase = rng.uniform(0, math.pi * 2)
        size  = rng.randint(1, 4)
        b     = int(abs(math.sin(now / 900 + phase)) * 180 + 40)
        col   = (b, b, min(255, b + 50))
        pygame.draw.circle(screen, col, (sx, sy), size)


def _draw_metro_lines(screen, WIDTH, HEIGHT, now):
    """Dos lineas de metro animadas en la parte inferior."""
    for lane, y_off in enumerate([60, 28]):
        y         = HEIGHT - y_off
        seg_w     = 55
        gap       = 18
        cycle     = (seg_w + gap) * 3
        offset    = int(now / (10 + lane * 3)) % cycle
        cols      = [CYAN, GREEN, GOLD]
        col       = cols[int(now / 500 + lane) % 3]
        for sx in range(-cycle, WIDTH + cycle, seg_w + gap):
            x = sx + offset
            pygame.draw.rect(screen, col, (x, y - 4, seg_w, 8), border_radius=4)
        pygame.draw.line(screen, (70, 80, 100), (0, y - 12), (WIDTH, y - 12), 3)
        pygame.draw.line(screen, (70, 80, 100), (0, y + 12), (WIDTH, y + 12), 3)


def _draw_check(screen, cx, cy, r, color):
    """Dibuja un check (palomita) como forma geometrica."""
    pygame.draw.circle(screen, color, (cx, cy), r)
    pygame.draw.circle(screen, DARK_GREY, (cx, cy), r - 4)
    # Palomita interior
    pts = [
        (cx - r // 3, cy),
        (cx - r // 8, cy + r // 3),
        (cx + r // 3, cy - r // 4),
    ]
    pygame.draw.lines(screen, color, False, pts, 3)


def mostrar_game_complete(
    screen,
    WIDTH,
    HEIGHT,
    font_title,
    font_button,
    game_state,
    event,
    mouse_pos,
):
    """
    Retorna:
      'inicio'  -> volver al inicio
      None      -> sin accion este frame
    """
    now      = pygame.time.get_ticks()
    center_x = WIDTH  // 2

    # FONDO
    screen.fill(DARK_GREY)
    _draw_stars(screen, WIDTH, HEIGHT, now)

    # Gradiente sutil
    grad = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for row in range(0, HEIGHT, 2):
        a = int(55 * row / HEIGHT)
        pygame.draw.line(grad, (0, 20, 50, a), (0, row), (WIDTH, row))
    screen.blit(grad, (0, 0))

    _draw_metro_lines(screen, WIDTH, HEIGHT, now)

    # IMAGEN (opcional)
    y_top = 80
    img_loaded = False
    try:
        img   = pygame.image.load("assets/game_complete.png")
        img_w = min(400, img.get_width())
        img_h = int(img.get_height() * img_w / img.get_width())
        img   = pygame.transform.scale(img, (img_w, img_h))
        screen.blit(img, img.get_rect(center=(center_x, y_top + img_h // 2)))
        y_top += img_h + 20
        img_loaded = True
    except Exception:
        pass

    # TITULO
    font_big  = pygame.font.SysFont("Arial", 64, bold=True)
    pulse     = int(abs(math.sin(now / 700)) * 6)
    title1    = font_big.render("METRO REPARADO!", True, GOLD)
    screen.blit(title1, title1.get_rect(center=(center_x, y_top + 45)))

    title2 = font_title.render("La linea del Metro esta completamente operativa", True, CYAN)
    screen.blit(title2, title2.get_rect(center=(center_x, y_top + 110)))

    # PANEL DE LOGROS
    panel_rect = pygame.Rect(0, 0, 800, 220)
    panel_rect.center = (center_x, y_top + 245)
    pygame.draw.rect(screen, PANEL, panel_rect, border_radius=16)
    pygame.draw.rect(screen, GOLD,  panel_rect, 2,  border_radius=16)

    lineas = [
        ("Linea 1", CYAN,  "Reconstruccion de Datos"),
        ("Linea 2", GREEN, "Sincronizacion de Red"),
        ("Linea 3", ORANGE,"Estabilidad del Sistema"),
    ]
    for i, (nombre, col, desc) in enumerate(lineas):
        y    = panel_rect.top + 28 + i * 58
        cr   = 18
        pulse_r = int(cr + abs(math.sin(now / 600 + i * 1.2)) * 5)
        cx_dot  = panel_rect.left + 40
        _draw_check(screen, cx_dot, y + 12, pulse_r, col)
        lbl = font_button.render(f"{nombre}  -  {desc}", True, col)
        screen.blit(lbl, (cx_dot + pulse_r + 14, y))

    # PUNTOS
    pts_surf = font_title.render(f"Puntuacion final:  {game_state.puntos:,} pts", True, GOLD)
    screen.blit(pts_surf, pts_surf.get_rect(center=(center_x, panel_rect.bottom + 40)))

    # MENSAJE
    msg = font_button.render(
        "Gracias a tu conocimiento en Metodos Numericos, el Metrorrey vuelve a circular.",
        True, LIGHT_GREY,
    )
    screen.blit(msg, msg.get_rect(center=(center_x, panel_rect.bottom + 95)))

    # BOTON
    btn = pygame.Rect(0, 0, 300, 62)
    btn.center = (center_x, panel_rect.bottom + 160)
    hover   = btn.collidepoint(mouse_pos)
    btn_col = (55, 80, 45) if hover else PANEL
    border  = GREEN if hover else (70, 110, 60)
    pygame.draw.rect(screen, btn_col, btn, border_radius=14)
    pygame.draw.rect(screen, border,  btn, 2, border_radius=14)
    lbl = font_button.render("Volver al Inicio", True, WHITE)
    screen.blit(lbl, lbl.get_rect(center=btn.center))

    if event.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(mouse_pos):
        game_state.puntos       = 0
        game_state.vidas        = 6
        game_state.nivel_actual = 0
        game_state.ult_nivel_desbloqueado = 0
        return "inicio"

    return None
