import pygame

# Colores
WHITE  = (255, 255, 255)
GREY   = (180, 180, 180)
DARK   = (30, 30, 30)
YELLOW = (255, 220, 0)
BLUE   = (54, 175, 250)
GREEN  = (40, 200, 100)
ORANGE = (253, 126, 20)


def _dibujar_seccion(screen, font_header, font_small, titulo, lineas, color, x, y, ancho):
    """
    Dibuja una sección con título coloreado, línea decorativa y contenido.
    Retorna la Y final del bloque.
    """
    # Fondo semitransparente de la tarjeta
    alto_estimado = 45 + 12 + len(lineas) * 30 + 20
    card = pygame.Surface((ancho, alto_estimado), pygame.SRCALPHA)
    card.fill((255, 255, 255, 18))
    screen.blit(card, (x, y))
    pygame.draw.rect(screen, color, pygame.Rect(x, y, ancho, alto_estimado), 2, border_radius=8)

    # Título
    t_surf = font_header.render(titulo, True, color)
    screen.blit(t_surf, t_surf.get_rect(centerx=x + ancho // 2, top=y + 10))

    # Línea decorativa bajo título
    pygame.draw.line(screen, color,
                     (x + 15, y + 48),
                     (x + ancho - 15, y + 48), 2)

    # Líneas de contenido
    cy = y + 58
    for linea in lineas:
        surf = font_small.render(linea, True, WHITE)
        screen.blit(surf, (x + 15, cy))
        cy += 30

    return cy + 10


def mostrar_instrucciones(screen, WIDTH, HEIGHT, font_title, font_button, event, mouse_pos):
    """
    Pantalla de instrucciones del juego.

    Muestra tres secciones:
      - Como jugar
      - Vidas y puntos
      - Metodos numericos

    Retorna:
      'menu'  -> cuando el jugador presiona 'Entendido'
      None    -> cualquier otro frame
    """

    # ── Fondo ──────────────────────────────────────────────────────────────
    try:
        bg = pygame.image.load("assets/menu_background4.png")
        bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
        screen.blit(bg, (0, 0))
    except Exception:
        screen.fill(DARK)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    center_x = WIDTH // 2
    font_small = pygame.font.SysFont("Arial", 22)

    # ── Título principal ───────────────────────────────────────────────────
    titulo_surf = font_title.render("Instrucciones", True, YELLOW)
    screen.blit(titulo_surf, titulo_surf.get_rect(center=(center_x, 50)))
    pygame.draw.line(screen, YELLOW,
                     (center_x - 210, 80),
                     (center_x + 210, 80), 2)

    # ── Distribución de columnas ───────────────────────────────────────────
    # Tres columnas de igual ancho con margen lateral
    margen   = 30
    gap      = 20
    col_w    = (WIDTH - margen * 2 - gap * 2) // 3   # ~360 px
    col_y    = 105

    col1_x = margen
    col2_x = col1_x + col_w + gap
    col3_x = col2_x + col_w + gap

    # ── Sección 1: Cómo jugar ──────────────────────────────────────────────
    como_jugar = [
        "1. Explora el mapa del Metrorrey.",
        "2. Selecciona un nivel y presiona Jugar.",
        "3. Elige el metodo numerico correcto.",
        "4. Resuelve cada paso escribiendo",
        "   el resultado intermedio.",
        "5. Completa todos los pasos",
        "   para ganar puntos.",
        "6. Avanza por las 3 lineas del metro.",
    ]
    _dibujar_seccion(screen, font_button, font_small,
                     "Como jugar", como_jugar,
                     BLUE, col1_x, col_y, col_w)

    # ── Sección 2: Vidas y puntos ──────────────────────────────────────────
    vidas_info = [
        "Comienzas con 6 vidas.",
        "Pierdes 1 vida si:",
        "  - Eliges el metodo incorrecto.",
        "  - Das una respuesta incorrecta.",
        "Al quedarte sin vidas: Game Over.",
        "",
        "Puntos por nivel completado:",
        "  Linea 1: 1,000 pts / nivel",
        "  Linea 2: 1,500 pts / nivel",
        "  Linea 3: 2,000 pts / nivel",
    ]
    _dibujar_seccion(screen, font_button, font_small,
                     "Vidas y puntos", vidas_info,
                     GREEN, col2_x, col_y, col_w)

    # ── Sección 3: Métodos numéricos ───────────────────────────────────────
    metodos_info = [
        "Interpolacion Lineal:",
        "  Estima entre dos puntos dados.",
        "",
        "Diferencias Divididas:",
        "  Tabla de Newton con intervalos",
        "  irregulares.",
        "",
        "Lagrange:",
        "  Polinomio que pasa por todos",
        "  los puntos dados.",
        "",
        "Newton Hacia Atras:",
        "  Diferencias finitas con paso h",
        "  constante desde el ultimo punto.",
    ]
    _dibujar_seccion(screen, font_button, font_small,
                     "Metodos numericos", metodos_info,
                     ORANGE, col3_x, col_y, col_w)

    # ── Botón Entendido ────────────────────────────────────────────────────
    btn = pygame.Rect(0, 0, 260, 65)
    btn.center = (center_x, HEIGHT - 65)

    btn_color = (80, 190, 255) if btn.collidepoint(mouse_pos) else BLUE
    pygame.draw.rect(screen, btn_color, btn, border_radius=15)

    label = font_button.render("Entendido  ->", True, WHITE)
    screen.blit(label, label.get_rect(center=btn.center))

    # ── Click ──────────────────────────────────────────────────────────────
    if event.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(mouse_pos):
        return "menu"

    return None
