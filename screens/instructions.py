import pygame

# Colores
WHITE  = (255, 255, 255)
GREY   = (180, 180, 180)
DARK   = (30, 30, 30)
YELLOW = (255, 220, 0)
BLUE   = (54, 175, 250)
GREEN  = (40, 200, 100)
ORANGE = (253, 126, 20)


def _wrap_lineas(font, lineas, max_w):
    """Parte las líneas que no caben en max_w preservando la indentación."""
    resultado = []
    for linea in lineas:
        if not linea.strip():
            resultado.append("")
            continue
        if font.size(linea)[0] <= max_w:
            resultado.append(linea)
            continue
        stripped = linea.lstrip()
        indent   = linea[:len(linea) - len(stripped)]
        cont     = indent + "  "
        words    = stripped.split()
        cur      = indent
        for word in words:
            test = cur + word if cur == indent else cur + " " + word
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur.strip():
                    resultado.append(cur)
                cur = cont + word
        if cur.strip():
            resultado.append(cur)
    return resultado


def _dibujar_seccion(screen, font_header, font_small, titulo, lineas, color, x, y, ancho):
    """
    Dibuja una sección con título coloreado, línea decorativa y contenido.
    Retorna la Y final del bloque.
    """
    max_text_w   = ancho - 30
    lineas_wrap  = _wrap_lineas(font_small, lineas, max_text_w)

    alto_estimado = 45 + 12 + len(lineas_wrap) * 30 + 20
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

    # Líneas de contenido (ya wrapeadas)
    cy = y + 58
    for linea in lineas_wrap:
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
    # Se escala más alto y se desplaza hacia abajo para que la simbología
    # de la imagen quede por debajo de las tarjetas de instrucciones.
    try:
        bg       = pygame.image.load("assets/menu_background4.png")
        bg_shift = 100
        bg       = pygame.transform.scale(bg, (WIDTH, HEIGHT + bg_shift))
        screen.fill(DARK)
        screen.blit(bg, (0, bg_shift))
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
    # Dos columnas centradas
    margen = 40
    gap    = 30
    col_w  = (WIDTH - margen * 2 - gap) // 2
    col_y  = 105

    col1_x = margen
    col2_x = col1_x + col_w + gap

    # ── Sección 1: Cómo jugar ──────────────────────────────────────────────
    como_jugar = [
        "1. Explora el mapa del Metrorrey.",
        "2. Selecciona un nivel y presiona Jugar.",
        "3. Elige el metodo numerico correcto.",
        "4. Resuelve cada paso escribiendo",
        "   el resultado intermedio.",
        "5. Completa todos los pasos",
        "   para ganar puntos y vidas.",
        "6. Usa 'Volver al mapa' si necesitas",
        "   cambiar de nivel (cuesta 1 vida).",
        "7. Avanza por las 3 lineas del metro.",
    ]
    _dibujar_seccion(screen, font_button, font_small,
                     "Como jugar", como_jugar,
                     BLUE, col1_x, col_y, col_w)

    # ── Sección 2: Vidas y puntos ──────────────────────────────────────────
    vidas_info = [
        "Comienzas con 6 vidas (maximo 9).",
        "Pierdes 1 vida si:",
        "  - Eliges el metodo incorrecto.",
        "  - Das una respuesta incorrecta.",
        "  - Usas 'Volver al mapa'.",
        "Al quedarte sin vidas: Game Over.",
        "",
        "Ganas +1 vida cada 5,000 puntos.",
        "",
        "Puntos por nivel completado:",
        "  1,000 pts / nivel",
    ]
    _dibujar_seccion(screen, font_button, font_small,
                     "Vidas y puntos", vidas_info,
                     GREEN, col2_x, col_y, col_w)

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
