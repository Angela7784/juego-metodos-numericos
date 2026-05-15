import pygame

# Colores
RED_ERROR   = (200, 50, 50)
RED_HOVER   = (220, 70, 70)
RED_NOGAMES = (160, 30, 30)
WHITE       = (255, 255, 255)
DARK_GREY   = (30, 30, 30)


def mostrar_incorrecto(screen, WIDTH, HEIGHT, font_title, font_button, game_state, nivel, event, mouse_pos):
    """
    Pantalla de resultado incorrecto.

    Muestra:
      - Icono de equis (X) sobre un circulo rojo
      - Titulo 'Incorrecto!'
      - Mensaje con vidas restantes y corazones
      - Boton 'Reintentar' si quedan vidas, o 'Game Over' si no quedan

    Retorna:
      'select_metodo'  -> Reintentar el nivel
      'game_over'      -> Sin vidas, ir a la pantalla de Game Over
      None             -> cualquier otro frame
    """

    # Fondo
    try:
        background = pygame.image.load("assets/menu_background4.png")
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
        screen.blit(background, (0, 0))
    except Exception:
        screen.fill(DARK_GREY)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    screen.blit(overlay, (0, 0))

    center_x = WIDTH  // 2
    center_y = HEIGHT // 2

    # Icono X
    pygame.draw.circle(screen, RED_ERROR, (center_x, center_y - 140), 75)
    pygame.draw.circle(screen, WHITE,     (center_x, center_y - 140), 75, 3)

    font_icon = pygame.font.SysFont("Arial", 90, bold=True)
    icon_surf = font_icon.render("X", True, WHITE)
    screen.blit(icon_surf, icon_surf.get_rect(center=(center_x, center_y - 140)))

    # Titulo
    titulo_surf = font_title.render("Incorrecto!", True, RED_ERROR)
    screen.blit(titulo_surf, titulo_surf.get_rect(center=(center_x, center_y - 35)))

    # Mensaje de vidas
    if game_state.vidas > 0:
        msg       = f"Perdiste una vida  -  te quedan {game_state.vidas}"
        msg_color = WHITE
    else:
        msg       = "Sin vidas! Es Game Over"
        msg_color = (255, 100, 100)

    msg_surf = font_button.render(msg, True, msg_color)
    screen.blit(msg_surf, msg_surf.get_rect(center=(center_x, center_y + 30)))

    # Corazones restantes
    try:
        heart_img = pygame.image.load("assets/heart.png")
        heart_img = pygame.transform.scale(heart_img, (38, 38))

        total   = game_state.vidas
        gap     = 48
        start_x = center_x - (total * gap) // 2 + gap // 2

        for i in range(total):
            heart_rect = heart_img.get_rect(center=(start_x + i * gap, center_y + 90))
            screen.blit(heart_img, heart_rect)

    except Exception:
        vidas_surf = font_button.render(f"Vidas: {game_state.vidas}", True, WHITE)
        screen.blit(vidas_surf, vidas_surf.get_rect(center=(center_x, center_y + 88)))

    # Boton
    btn_rect = pygame.Rect(0, 0, 240, 65)
    btn_rect.center = (center_x, center_y + 185)

    if game_state.vidas > 0:
        btn_color    = RED_HOVER if btn_rect.collidepoint(mouse_pos) else RED_ERROR
        btn_texto    = "Reintentar"
        return_value = "select_metodo"
    else:
        btn_color    = RED_NOGAMES if btn_rect.collidepoint(mouse_pos) else (180, 40, 40)
        btn_texto    = "Ver resultado"
        return_value = "game_over"

    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=15)

    btn_label = font_button.render(btn_texto, True, WHITE)
    screen.blit(btn_label, btn_label.get_rect(center=btn_rect.center))

    # Click
    if event.type == pygame.MOUSEBUTTONDOWN and btn_rect.collidepoint(mouse_pos):
        return return_value

    return None
