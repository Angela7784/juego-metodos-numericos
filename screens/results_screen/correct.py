import pygame

# Colores
GREEN_SUCCESS = (40, 200, 100)
GREEN_HOVER   = (60, 220, 120)
YELLOW_POINTS = (255, 220, 0)
HEART_RED     = (220, 60,  60)
WHITE         = (255, 255, 255)
DARK_GREY     = (30, 30, 30)


def mostrar_correcto(screen, WIDTH, HEIGHT, font_title, font_button, game_state, nivel, event, mouse_pos,
                     vida_ganada=False):
    """
    Pantalla de resultado correcto.

    Muestra:
      - Ícono de palomita (✓) sobre un círculo verde
      - Título '¡Correcto!'
      - Puntos ganados en el nivel y total acumulado
      - Botón 'Continuar' que regresa al mapa

    Retorna:
      'menu'  -> cuando el jugador presiona Continuar
      None    -> cualquier otro frame
    """

    # Fondo
    try:
        background = pygame.image.load("assets/menu_background4.png")
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
        screen.blit(background, (0, 0))
    except Exception:
        screen.fill(DARK_GREY)

    # Overlay oscuro semitransparente para legibilidad
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    screen.blit(overlay, (0, 0))

    center_x = WIDTH  // 2
    center_y = HEIGHT // 2

    # Icono checkmark
    pygame.draw.circle(screen, GREEN_SUCCESS, (center_x, center_y - 140), 75)
    pygame.draw.circle(screen, WHITE,         (center_x, center_y - 140), 75, 3)

    font_icon = pygame.font.SysFont("Arial", 90, bold=True)
    icon_surf = font_icon.render("v", True, WHITE)
    screen.blit(icon_surf, icon_surf.get_rect(center=(center_x, center_y - 140)))

    # Titulo
    titulo_surf = font_title.render("Correcto!", True, GREEN_SUCCESS)
    screen.blit(titulo_surf, titulo_surf.get_rect(center=(center_x, center_y - 35)))

    # Puntos ganados
    puntos_nivel = nivel.get("puntos", 1000)
    puntos_surf  = font_button.render(f"+ {puntos_nivel} puntos", True, YELLOW_POINTS)
    screen.blit(puntos_surf, puntos_surf.get_rect(center=(center_x, center_y + 30)))

    # Total acumulado
    total_surf = font_button.render(f"Total: {game_state.puntos} pts", True, WHITE)
    screen.blit(total_surf, total_surf.get_rect(center=(center_x, center_y + 75)))

    # Notificación de vida ganada
    if vida_ganada:
        font_vida  = pygame.font.SysFont("Arial", 26, bold=True)
        vida_surf  = font_vida.render("+1 vida por tus puntos!", True, WHITE)
        icon_w     = 32
        padding    = 16
        panel_w    = icon_w + vida_surf.get_width() + padding * 3
        panel_h    = 50
        panel      = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((180, 40, 40, 210))
        panel_rect = panel.get_rect(center=(center_x, center_y + 135))
        screen.blit(panel, panel_rect)
        pygame.draw.rect(screen, HEART_RED, panel_rect, 2, border_radius=10)
        try:
            heart_img = pygame.image.load("assets/heart.png")
            heart_img = pygame.transform.scale(heart_img, (icon_w - 4, icon_w - 4))
            screen.blit(heart_img, (panel_rect.left + padding, panel_rect.centery - (icon_w - 4) // 2))
        except Exception:
            pass
        screen.blit(vida_surf, vida_surf.get_rect(midleft=(panel_rect.left + padding + icon_w, panel_rect.centery)))

    # Boton Continuar
    btn_rect = pygame.Rect(0, 0, 240, 65)
    btn_rect.center = (center_x, center_y + (215 if vida_ganada else 185))

    btn_color = GREEN_HOVER if btn_rect.collidepoint(mouse_pos) else GREEN_SUCCESS
    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=15)

    btn_label = font_button.render("Continuar  ->", True, WHITE)
    screen.blit(btn_label, btn_label.get_rect(center=btn_rect.center))

    # Click
    if event.type == pygame.MOUSEBUTTONDOWN and btn_rect.collidepoint(mouse_pos):
        return "menu"

    return None
