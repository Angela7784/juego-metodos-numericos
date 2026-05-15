import pygame
from managers.save_manager import SaveManager

# Colores
DARK_RED  = (160, 20,  20)
RED_HOVER = (190, 40,  40)
YELLOW    = (255, 220,  0)
WHITE     = (255, 255, 255)
DARK_GREY = (30,  30,  30)


def mostrar_game_over(screen, WIDTH, HEIGHT, font_title, font_button, game_state, event, mouse_pos):
    """
    Pantalla de Game Over.

    Muestra:
      - Titulo 'GAME OVER' en rojo
      - Puntuacion final del jugador
      - Boton 'Volver al inicio' que resetea el estado y regresa a inicio

    Retorna:
      'inicio'  -> cuando el jugador presiona el boton (estado ya reseteado)
      None      -> cualquier otro frame
    """

    # Fondo
    try:
        background = pygame.image.load("assets/menu_background4.png")
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
        screen.blit(background, (0, 0))
    except Exception:
        screen.fill(DARK_GREY)

    # Overlay muy oscuro para que resalte GAME OVER
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    center_x = WIDTH  // 2
    center_y = HEIGHT // 2

    # Titulo GAME OVER
    font_big   = pygame.font.SysFont("Arial", 85, bold=True)
    title_surf = font_big.render("GAME OVER", True, DARK_RED)
    screen.blit(title_surf, title_surf.get_rect(center=(center_x, center_y - 130)))

    # Linea decorativa
    pygame.draw.line(
        screen, DARK_RED,
        (center_x - 220, center_y - 80),
        (center_x + 220, center_y - 80),
        3
    )

    # Puntuacion final
    label_surf = font_button.render("Puntuacion final", True, (180, 180, 180))
    screen.blit(label_surf, label_surf.get_rect(center=(center_x, center_y - 30)))

    score_surf = font_big.render(str(game_state.puntos), True, YELLOW)
    screen.blit(score_surf, score_surf.get_rect(center=(center_x, center_y + 55)))

    pts_surf = font_button.render("pts", True, YELLOW)
    score_rect = score_surf.get_rect(center=(center_x, center_y + 55))
    screen.blit(pts_surf, (score_rect.right + 8, score_rect.centery - pts_surf.get_height() // 2))

    # Boton Volver al inicio
    btn_rect = pygame.Rect(0, 0, 280, 65)
    btn_rect.center = (center_x, center_y + 175)

    btn_color = RED_HOVER if btn_rect.collidepoint(mouse_pos) else DARK_RED
    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=15)

    btn_label = font_button.render("Volver al inicio", True, WHITE)
    screen.blit(btn_label, btn_label.get_rect(center=btn_rect.center))

    # Click: resetear estado y volver al inicio
    if event.type == pygame.MOUSEBUTTONDOWN and btn_rect.collidepoint(mouse_pos):
        game_state.vidas                  = 6
        game_state.puntos                 = 0
        game_state.nivel_actual           = 0
        game_state.ult_nivel_desbloqueado = 0
        SaveManager.guardar(game_state)
        return "inicio"

    return None
