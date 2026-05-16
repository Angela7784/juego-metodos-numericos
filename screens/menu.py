import pygame
import sys

from managers.save_manager import SaveManager

# Colores
L1_YELLOW = (255, 193,   7)
L2_GREEN  = ( 40, 167,  69)
L3_ORANGE = (253, 126,  20)
GREEN     = ( 68, 168, 108)
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
DARK_GREY = ( 30,  30,  30)

# Imagen del mapa (cargada una sola vez al importar)
_mapa_img = None

def _get_mapa(WIDTH, HEIGHT):
    global _mapa_img
    if _mapa_img is None:
        try:
            raw = pygame.image.load("assets/mapa_oscuro.png").convert()
            # Escalar manteniendo aspecto y centrando con barras negras si hace falta
            img_w, img_h = raw.get_size()
            scale = min(WIDTH / img_w, HEIGHT / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            scaled = pygame.transform.smoothscale(raw, (new_w, new_h))
            # Pegar sobre superficie del tamaño de la ventana
            surf = pygame.Surface((WIDTH, HEIGHT))
            surf.fill((15, 15, 15))
            surf.blit(scaled, ((WIDTH - new_w) // 2, (HEIGHT - new_h) // 2))
            _mapa_img = surf
        except Exception:
            _mapa_img = None
    return _mapa_img


def draw_text(text, font, color, surface, x, y):
    obj  = font.render(text, True, color)
    rect = obj.get_rect(center=(x, y))
    surface.blit(obj, rect)


def mostrar_mapa(screen, WIDTH, HEIGHT, font_title, font_button,
                 WHITE, DARK_GREY, event, mouse_pos, game_state, nivel):

    # ── Fondo: imagen del mapa ─────────────────────────────────────────────
    mapa = _get_mapa(WIDTH, HEIGHT)
    if mapa:
        screen.blit(mapa, (0, 0))
    else:
        screen.fill(DARK_GREY)

    # Overlay semitransparente para mejorar legibilidad del HUD
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    screen.blit(overlay, (0, 0))

    # ── Título ─────────────────────────────────────────────────────────────
    draw_text("Rescate Numérico en Metrorrey", font_title, WHITE, screen, WIDTH // 2, 50)

    # ── Panel de datos (esquina superior derecha) ──────────────────────────
    panel_w, panel_h = 220, 110
    panel_x = WIDTH - panel_w - 20
    panel_y = 100
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 170))
    screen.blit(panel_surf, (panel_x, panel_y))
    pygame.draw.rect(screen, GREEN,
                     pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                     2, border_radius=12)

    datos_lbl = font_button.render("Datos", True, GREEN)
    screen.blit(datos_lbl, datos_lbl.get_rect(center=(panel_x + panel_w // 2, panel_y + 20)))

    # Vidas
    try:
        heart_img = pygame.image.load("assets/heart.png")
        heart_img = pygame.transform.scale(heart_img, (28, 28))
        screen.blit(heart_img, (panel_x + 18, panel_y + 44))
        vidas_surf = font_button.render(str(game_state.vidas), True, WHITE)
        screen.blit(vidas_surf, (panel_x + 54, panel_y + 44))
    except Exception:
        draw_text(f"Vidas: {game_state.vidas}", font_button, WHITE,
                  screen, panel_x + panel_w // 2, panel_y + 55)

    # Puntos
    pts_surf = font_button.render(f"Pts: {game_state.puntos}", True, WHITE)
    screen.blit(pts_surf, pts_surf.get_rect(
        center=(panel_x + panel_w // 2, panel_y + 88)))

    # ── HUD inferior: línea / estación + navegación + botón jugar ──────────
    linea_actual    = nivel["linea"]
    estacion_actual = nivel["estacion"]

    LINEA_COLORES = {"1": L1_YELLOW, "2": L2_GREEN, "3": L3_ORANGE}
    color_linea   = LINEA_COLORES.get(linea_actual, WHITE)

    center_x = WIDTH  // 2
    base_y   = HEIGHT - 170

    # Panel inferior semitransparente
    inf_w, inf_h = 560, 140
    inf_surf = pygame.Surface((inf_w, inf_h), pygame.SRCALPHA)
    inf_surf.fill((0, 0, 0, 160))
    screen.blit(inf_surf, (center_x - inf_w // 2, base_y - 20))
    pygame.draw.rect(screen, color_linea,
                     pygame.Rect(center_x - inf_w // 2, base_y - 20, inf_w, inf_h),
                     2, border_radius=14)

    # Texto línea y estación
    draw_text(f"Línea {linea_actual}", font_button, color_linea, screen,
              center_x, base_y + 5)
    draw_text(f"Estación: {estacion_actual}", font_button, WHITE, screen,
              center_x, base_y + 38)

    # ── Flechas de navegación ──────────────────────────────────────────────
    tri_size = 28
    arrow_y  = base_y + 38

    left_tri = [
        (center_x - 240,              arrow_y),
        (center_x - 240 + tri_size,   arrow_y - tri_size),
        (center_x - 240 + tri_size,   arrow_y + tri_size),
    ]
    right_tri = [
        (center_x + 240,              arrow_y),
        (center_x + 240 - tri_size,   arrow_y - tri_size),
        (center_x + 240 - tri_size,   arrow_y + tri_size),
    ]

    left_rect  = pygame.Rect(center_x - 240,            arrow_y - tri_size,
                              tri_size, tri_size * 2)
    right_rect = pygame.Rect(center_x + 240 - tri_size, arrow_y - tri_size,
                              tri_size, tri_size * 2)

    # Bloquear flecha izquierda si estamos en el primer nivel
    can_left  = game_state.nivel_actual > 0
    can_right = game_state.nivel_actual < game_state.ult_nivel_desbloqueado

    left_col  = (220, 220, 220) if (can_left  and left_rect.collidepoint(mouse_pos))  else \
                (WHITE if can_left else (80, 80, 80))
    right_col = (220, 220, 220) if (can_right and right_rect.collidepoint(mouse_pos)) else \
                (WHITE if can_right else (80, 80, 80))

    pygame.draw.polygon(screen, left_col,  left_tri)
    pygame.draw.polygon(screen, right_col, right_tri)

    # ── Botón Jugar ────────────────────────────────────────────────────────
    btn_rect = pygame.Rect(0, 0, 200, 52)
    btn_rect.center = (center_x, base_y + 100)
    btn_col = (240, 240, 240) if btn_rect.collidepoint(mouse_pos) else WHITE
    pygame.draw.rect(screen, btn_col, btn_rect, border_radius=18)
    jugar_surf = font_button.render("Jugar", True, (30, 30, 30))
    screen.blit(jugar_surf, jugar_surf.get_rect(center=btn_rect.center))

    # ── Eventos ────────────────────────────────────────────────────────────
    if event.type == pygame.MOUSEBUTTONDOWN:
        if can_left and left_rect.collidepoint(mouse_pos):
            game_state.nivel_actual -= 1
            SaveManager.guardar(game_state)

        if can_right and right_rect.collidepoint(mouse_pos):
            game_state.nivel_actual += 1
            SaveManager.guardar(game_state)

        if btn_rect.collidepoint(mouse_pos):
            return "select_metodo"

    return None
