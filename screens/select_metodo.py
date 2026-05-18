import pygame
import time
import random
from screens.bg_animator import BackgroundAnimator, fondo_por_linea

WHITE = (255, 255, 255)

LINEA_COLORES = {
    "1": (255, 193,  7),   # amarillo L1
    "2": ( 40, 167, 69),   # verde    L2
    "3": (253, 126, 20),   # naranja  L3
}

# Animador (se reutiliza mientras no cambia la línea)
_animador: BackgroundAnimator | None = None
_linea_cargada: str = ""

# Feedback visual de selección
_seleccion_opcion: str | None = None
_seleccion_correcta: bool | None = None
_seleccion_tick: int = 0
FEEDBACK_MS = 700


def mostrar_select_metodo(
    screen,
    WIDTH,
    HEIGHT,
    font_title,
    font_button,
    WHITE,
    DARK_GREY,
    event,
    mouse_pos,
    game_state,
    nivel,
    start_time,
):
    """
    Pantalla de selección de método numérico.

    Retorna:
      'metodo_correcto'  -> método elegido correcto  → ir a level_game
      'incorrecto'       -> método elegido incorrecto → descontar vida
      None               -> sin acción este frame
    """
    global _animador, _linea_cargada
    global _seleccion_opcion, _seleccion_correcta, _seleccion_tick

    now   = pygame.time.get_ticks()
    linea = nivel.get("linea", "1")

    # ── Tiempo agotado ─────────────────────────────────────────────────────
    elapsed   = int(time.time() - start_time)
    remaining = max(0, 1800 - elapsed)
    if remaining <= 0:
        return "tiempo_agotado"

    # ── Resolver feedback pendiente ────────────────────────────────────────
    if _seleccion_opcion is not None and now - _seleccion_tick >= FEEDBACK_MS:
        resultado = "metodo_correcto" if _seleccion_correcta else "incorrecto"
        _seleccion_opcion   = None
        _seleccion_correcta = None
        return resultado

    # ── Fondo animado ──────────────────────────────────────────────────────
    if linea != _linea_cargada or _animador is None:
        _animador      = BackgroundAnimator(fondo_por_linea(linea), WIDTH, HEIGHT)
        _linea_cargada = linea

    if not _animador.draw(screen):
        screen.fill((30, 30, 30))

    # Overlay oscuro
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # ── HUD: vidas (corazones de derecha a izquierda) ──────────────────────
    try:
        heart = pygame.image.load("assets/heart.png")
        heart = pygame.transform.scale(heart, (35, 35))
        for i in range(game_state.vidas):
            screen.blit(heart, (WIDTH - 45 - i * 42, 20))
    except Exception:
        screen.blit(font_title.render(str(game_state.vidas), True, WHITE), (WIDTH - 125, 25))

    # ── HUD: temporizador (a la izquierda de los corazones) ───────────────
    timer_surf = font_title.render(f"{remaining // 60:02}:{remaining % 60:02}", True, WHITE)
    hearts_left_x = WIDTH - 45 - (max(game_state.vidas, 1) - 1) * 42
    timer_rect = timer_surf.get_rect(right=hearts_left_x - 18, centery=38)
    screen.blit(timer_surf, timer_rect)

    # ── HUD: línea y estación ──────────────────────────────────────────────
    color_linea = LINEA_COLORES.get(linea, WHITE)
    screen.blit(font_button.render(f"Linea: {linea}", True, color_linea), (30, 20))
    screen.blit(font_button.render(f"Estacion: {nivel['estacion']}", True, WHITE), (30, 55))

    # ── Seleccionar problema aleatorio (una sola vez por intento) ──────────
    problemas = nivel.get("problemas", [])
    if "problema_seleccionado" not in nivel and problemas:
        nivel["problema_seleccionado"] = random.choice(problemas)
    problema_actual = nivel.get("problema_seleccionado", problemas[0] if problemas else {})
    enunciado = problema_actual.get("enunciado", "Sin enunciado disponible.")

    panel_w, panel_h = 700, 240
    panel_x = WIDTH  // 2 - panel_w // 2
    panel_y = 150
    panel   = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((20, 20, 20, 200))
    screen.blit(panel, (panel_x, panel_y))
    pygame.draw.rect(screen, (100, 100, 100), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

    label = font_button.render("Enunciado del problema:", True, (200, 200, 200))
    screen.blit(label, (panel_x + 20, panel_y + 15))

    # Word-wrap manual (respeta \n y preserva espacios internos si la línea cabe)
    font_txt  = pygame.font.SysFont("Arial", 24)
    max_chars = panel_w - 40
    lines = []
    for raw in enunciado.split('\n'):
        if font_txt.size(raw)[0] <= max_chars:
            lines.append(raw)
        else:
            words = raw.split()
            line  = ""
            for word in words:
                test = (line + " " + word).strip()
                if font_txt.size(test)[0] <= max_chars:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)

    for j, ln in enumerate(lines[:6]):
        surf = font_txt.render(ln, True, WHITE)
        screen.blit(surf, (panel_x + 20, panel_y + 55 + j * 30))

    # ── Pregunta de selección ──────────────────────────────────────────────
    titulo = font_title.render("¿Qué método aplica para este problema?", True, WHITE)
    screen.blit(titulo, titulo.get_rect(center=(WIDTH // 2, 430)))

    # Mezclar opciones solo una vez por nivel
    opciones_data = nivel["seleccion_metodo"][0]
    if "opciones_mezcladas" not in nivel:
        opciones = [
            opciones_data["correcto"],
            opciones_data["incorrecto1"],
            opciones_data["incorrecto2"],
            opciones_data["incorrecto3"],
        ]
        random.shuffle(opciones)
        nivel["opciones_mezcladas"] = opciones

    opciones       = nivel["opciones_mezcladas"]
    correct_option = opciones_data["correcto"]
    start_y        = 510

    # ── Botones de opciones ────────────────────────────────────────────────
    for i, opcion in enumerate(opciones):
        btn = pygame.Rect(0, 0, 320, 60)
        btn.center = (
            WIDTH // 2 - 190 if i % 2 == 0 else WIDTH // 2 + 190,
            start_y + (i // 2) * 100,
        )

        if _seleccion_opcion == opcion:
            color = (30, 160, 60) if _seleccion_correcta else (190, 35, 35)
        elif btn.collidepoint(mouse_pos) and _seleccion_opcion is None:
            color = (70, 70, 70)
        else:
            color = (45, 45, 45)
        pygame.draw.rect(screen, color, btn, border_radius=12)
        font_size = 21
        font_opcion = pygame.font.SysFont("Arial", font_size, bold=True)
        while font_opcion.size(opcion)[0] > btn.width - 16 and font_size > 11:
            font_size -= 1
            font_opcion = pygame.font.SysFont("Arial", font_size, bold=True)
        texto = font_opcion.render(opcion, True, WHITE)
        screen.blit(texto, texto.get_rect(center=btn.center))

        if (event.type == pygame.MOUSEBUTTONDOWN
                and btn.collidepoint(mouse_pos)
                and _seleccion_opcion is None):
            _seleccion_opcion   = opcion
            _seleccion_correcta = (opcion == correct_option)
            _seleccion_tick     = now

    # ── Botón Volver al mapa ───────────────────────────────────────────────
    font_back  = pygame.font.SysFont("Arial", 22, bold=True)
    back_label = font_back.render("< Volver al mapa", True, WHITE)
    btn_back   = pygame.Rect(20, HEIGHT - 68, back_label.get_width() + 36, 44)
    back_color = (130, 35, 35) if btn_back.collidepoint(mouse_pos) else (85, 22, 22)
    pygame.draw.rect(screen, back_color, btn_back, border_radius=10)
    screen.blit(back_label, back_label.get_rect(center=btn_back.center))

    if event.type == pygame.MOUSEBUTTONDOWN and btn_back.collidepoint(mouse_pos):
        return "volver_menu"

    return None
