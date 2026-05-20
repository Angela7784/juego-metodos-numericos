import pygame
import time
import random
from screens.bg_animator import BackgroundAnimator, fondo_por_linea
from core.math_fmt import fmt_math

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

# Diálogo de repaso
_dialogo_repaso: bool = False


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
    global _dialogo_repaso

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
    enunciado = fmt_math(problema_actual.get("enunciado", "Sin enunciado disponible."))

    panel_w  = 740
    panel_x  = WIDTH // 2 - panel_w // 2
    panel_y  = 140
    line_h   = 36
    pad_top  = 58   # espacio bajo el label "Enunciado del problema:"
    pad_bot  = 18

    font_txt  = pygame.font.SysFont("Arial", 24)
    max_chars = panel_w - 48
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

    panel_h = max(pad_top + 2 * line_h + pad_bot, pad_top + len(lines) * line_h + pad_bot)
    panel   = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((20, 20, 20, 210))
    screen.blit(panel, (panel_x, panel_y))
    pygame.draw.rect(screen, (110, 110, 110), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)

    label = font_button.render("Enunciado del problema:", True, (200, 200, 200))
    screen.blit(label, (panel_x + 20, panel_y + 14))
    pygame.draw.line(screen, (80, 80, 80), (panel_x + 16, panel_y + 46), (panel_x + panel_w - 16, panel_y + 46), 1)

    for j, ln in enumerate(lines):
        surf = font_txt.render(ln, True, WHITE)
        screen.blit(surf, (panel_x + 24, panel_y + pad_top + j * line_h))

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

    # ── Botón "?" (repaso) ─────────────────────────────────────────────────
    circ_cx = WIDTH - 46
    circ_cy = HEIGHT - 46
    circ_r  = 26
    circ_hovering = (mouse_pos[0] - circ_cx) ** 2 + (mouse_pos[1] - circ_cy) ** 2 <= circ_r ** 2
    circ_color    = (80, 120, 200) if circ_hovering and _dialogo_repaso is False else (50, 80, 160)
    pygame.draw.circle(screen, circ_color, (circ_cx, circ_cy), circ_r)
    pygame.draw.circle(screen, (150, 190, 255), (circ_cx, circ_cy), circ_r, 2)
    font_q = pygame.font.SysFont("Arial", 28, bold=True)
    q_surf = font_q.render("?", True, WHITE)
    screen.blit(q_surf, q_surf.get_rect(center=(circ_cx, circ_cy)))

    if (event.type == pygame.MOUSEBUTTONDOWN and circ_hovering
            and _seleccion_opcion is None and not _dialogo_repaso):
        _dialogo_repaso = True

    # ── Diálogo de repaso ──────────────────────────────────────────────────
    if _dialogo_repaso:
        dlg_w, dlg_h = 420, 190
        dlg_x = WIDTH  // 2 - dlg_w // 2
        dlg_y = HEIGHT // 2 - dlg_h // 2

        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        screen.blit(dim, (0, 0))

        dlg = pygame.Surface((dlg_w, dlg_h), pygame.SRCALPHA)
        dlg.fill((25, 28, 45, 240))
        screen.blit(dlg, (dlg_x, dlg_y))
        pygame.draw.rect(screen, (100, 140, 255), (dlg_x, dlg_y, dlg_w, dlg_h), 2, border_radius=14)

        font_dlg = pygame.font.SysFont("Arial", 26, bold=True)
        txt      = font_dlg.render("¿Necesitas un repaso?", True, WHITE)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, dlg_y + 52)))

        font_opt = pygame.font.SysFont("Arial", 23, bold=True)

        btn_si = pygame.Rect(0, 0, 140, 50)
        btn_si.center = (WIDTH // 2 - 80, dlg_y + 130)
        si_color = (30, 160, 60) if btn_si.collidepoint(mouse_pos) else (22, 110, 44)
        pygame.draw.rect(screen, si_color, btn_si, border_radius=10)
        screen.blit(font_opt.render("Sí", True, WHITE), font_opt.render("Sí", True, WHITE).get_rect(center=btn_si.center))

        btn_no = pygame.Rect(0, 0, 140, 50)
        btn_no.center = (WIDTH // 2 + 80, dlg_y + 130)
        no_color = (160, 40, 40) if btn_no.collidepoint(mouse_pos) else (110, 28, 28)
        pygame.draw.rect(screen, no_color, btn_no, border_radius=10)
        screen.blit(font_opt.render("No", True, WHITE), font_opt.render("No", True, WHITE).get_rect(center=btn_no.center))

        if event.type == pygame.MOUSEBUTTONDOWN:
            if btn_si.collidepoint(mouse_pos):
                _dialogo_repaso = False
                return "ir_repaso"
            elif btn_no.collidepoint(mouse_pos):
                _dialogo_repaso = False

    return None
