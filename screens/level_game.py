import pygame
import re
from screens.bg_animator import BackgroundAnimator, fondo_por_linea

# Colores
WHITE      = (255, 255, 255)
DARK_GREY  = (30,  30,  30)
LIGHT_GREY = (60,  60,  60)
GREEN      = (40,  200, 100)
RED        = (200, 50,  50)
YELLOW     = (255, 220, 0)

# ── Estado interno ─────────────────────────────────────────────────────────
_paso_actual    = 0
_input_text     = ""
_feedback       = None      # None | "correcto" | "incorrecto"
_feedback_tick  = 0
FEEDBACK_MS     = 900

_animador:       BackgroundAnimator | None = None
_linea_cargada:  str = ""


def reset_level() -> None:
    global _paso_actual, _input_text, _feedback, _feedback_tick
    _paso_actual   = 0
    _input_text    = ""
    _feedback      = None
    _feedback_tick = 0


# ── Comparación ────────────────────────────────────────────────────────────
def _comparar(user_input: str, correcta: str) -> bool:
    u = user_input.strip().lower().replace(',', '.')
    c = correcta.strip().lower().replace(',', '.')
    try:
        patron = r'-?\d+\.?\d*'
        u_num  = float(re.findall(patron, u)[0])
        c_num  = float(re.findall(patron, c)[0])
        tol    = max(0.05, abs(c_num) * 0.01)
        return abs(u_num - c_num) <= tol
    except Exception:
        return u == c


def _evaluar(preguntas: list) -> None:
    """Por ahora siempre avanza al siguiente paso sin validar."""
    global _feedback, _feedback_tick
    _feedback      = "correcto"
    _feedback_tick = pygame.time.get_ticks()


# ── Pantalla ───────────────────────────────────────────────────────────────
def mostrar_level_game(
    screen,
    WIDTH,
    HEIGHT,
    font_title,
    font_button,
    game_state,
    nivel,
    all_events,   # lista completa de eventos del frame
    mouse_pos,
):
    """
    Pantalla de resolución de pasos del nivel.

    Recibe ALL_EVENTS (lista) para no perder eventos de teclado.

    Retorna:
      'nivel_completo'  -> todos los pasos correctos
      'incorrecto'      -> respuesta incorrecta
      None              -> sin acción este frame
    """
    global _paso_actual, _input_text, _feedback, _feedback_tick
    global _animador, _linea_cargada

    preguntas   = nivel.get("preguntas", [])
    total_pasos = len(preguntas)
    if total_pasos == 0:
        return "nivel_completo"

    now      = pygame.time.get_ticks()
    center_x = WIDTH  // 2
    center_y = HEIGHT // 2

    # ── Resolver transición después del feedback ───────────────────────────
    if _feedback is not None:
        if now - _feedback_tick >= FEEDBACK_MS:
            _feedback   = None
            _input_text = ""
            _paso_actual += 1
            if _paso_actual >= total_pasos:
                reset_level()
                return "nivel_completo"
        # Durante el flash no procesamos input

    else:
        # ── Procesar TODOS los eventos del frame ───────────────────────────
        for ev in all_events:

            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if _input_text.strip():
                        _evaluar(preguntas)
                        break  # evaluar solo una vez por frame
                elif ev.key == pygame.K_BACKSPACE:
                    _input_text = _input_text[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(_input_text) < 25:
                    _input_text += ev.unicode

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                btn_back = pygame.Rect(20, HEIGHT - 68, 250, 44)
                if btn_back.collidepoint(mouse_pos):
                    reset_level()
                    return "volver_menu"

                btn = pygame.Rect(0, 0, 240, 55)
                btn.center = (center_x, center_y + 80)
                if btn.collidepoint(mouse_pos) and _input_text.strip():
                    _evaluar(preguntas)
                    break

    # ══════════════════════════════════════════════════════════════════════
    # DIBUJO
    # ══════════════════════════════════════════════════════════════════════
    linea = nivel.get("linea", "1")

    # Fondo animado (comparte el mismo animador que select_metodo)
    if linea != _linea_cargada or _animador is None:
        _animador      = BackgroundAnimator(fondo_por_linea(linea), WIDTH, HEIGHT)
        _linea_cargada = linea

    if not _animador.draw(screen):
        screen.fill(DARK_GREY)

    # Overlay oscuro para legibilidad
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    screen.blit(overlay, (0, 0))

    # ── HUD: línea y estación ──────────────────────────────────────────────
    screen.blit(font_button.render(f"Linea: {linea}", True, WHITE), (30, 20))
    screen.blit(font_button.render(f"Estacion: {nivel['estacion']}", True, WHITE), (30, 55))

    # ── HUD: corazones ─────────────────────────────────────────────────────
    try:
        heart = pygame.image.load("assets/heart.png")
        heart = pygame.transform.scale(heart, (30, 30))
        for i in range(game_state.vidas):
            screen.blit(heart, (WIDTH - 45 - i * 38, 22))
    except Exception:
        screen.blit(font_button.render(f"Vidas: {game_state.vidas}", True, WHITE), (WIDTH - 200, 20))

    # ── Indicador de paso ──────────────────────────────────────────────────
    paso_surf = font_button.render(f"Paso {_paso_actual + 1} de {total_pasos}", True, YELLOW)
    screen.blit(paso_surf, paso_surf.get_rect(center=(center_x, center_y - 210)))

    # Bolitas de progreso
    dot_gap     = 44
    dot_start_x = center_x - (total_pasos * dot_gap) // 2 + dot_gap // 2
    for i in range(total_pasos):
        if i < _paso_actual:
            pygame.draw.circle(screen, GREEN,      (dot_start_x + i * dot_gap, center_y - 170), 10)
            pygame.draw.circle(screen, WHITE,      (dot_start_x + i * dot_gap, center_y - 170), 10, 2)
        elif i == _paso_actual:
            pygame.draw.circle(screen, WHITE,      (dot_start_x + i * dot_gap, center_y - 170), 10)
        else:
            pygame.draw.circle(screen, LIGHT_GREY, (dot_start_x + i * dot_gap, center_y - 170), 8)

    # ── Pregunta actual ────────────────────────────────────────────────────
    pregunta_txt = preguntas[_paso_actual]["pregunta"]
    preg_surf    = font_title.render(f"Calcula:  {pregunta_txt}", True, WHITE)
    screen.blit(preg_surf, preg_surf.get_rect(center=(center_x, center_y - 100)))

    # ── Campo de texto ─────────────────────────────────────────────────────
    field_rect = pygame.Rect(0, 0, 520, 70)
    field_rect.center = (center_x, center_y)

    if _feedback == "correcto":
        field_color, border_color = (20, 150, 60), GREEN
    elif _feedback == "incorrecto":
        field_color, border_color = (160, 30, 30), RED
    else:
        field_color, border_color = LIGHT_GREY, WHITE

    pygame.draw.rect(screen, field_color,  field_rect, border_radius=12)
    pygame.draw.rect(screen, border_color, field_rect, 2, border_radius=12)

    cursor     = "|" if (now // 500) % 2 == 0 else " "
    input_surf = font_title.render(_input_text + cursor, True, WHITE)
    screen.set_clip(field_rect.inflate(-20, -10))
    screen.blit(input_surf, input_surf.get_rect(center=field_rect.center))
    screen.set_clip(None)

    # ── Botón Confirmar ────────────────────────────────────────────────────
    if _feedback is None:
        btn = pygame.Rect(0, 0, 240, 55)
        btn.center = (center_x, center_y + 80)
        btn_color = (80, 80, 80) if btn.collidepoint(mouse_pos) else LIGHT_GREY
        pygame.draw.rect(screen, btn_color, btn, border_radius=10)
        label = font_button.render("Confirmar  [Enter]", True, WHITE)
        screen.blit(label, label.get_rect(center=btn.center))

    # ── Botón Volver al mapa ───────────────────────────────────────────────
    font_back  = pygame.font.SysFont("Arial", 22, bold=True)
    back_label = font_back.render("< Volver al mapa", True, WHITE)
    btn_back   = pygame.Rect(20, HEIGHT - 68, back_label.get_width() + 36, 44)
    back_color = (130, 35, 35) if btn_back.collidepoint(mouse_pos) else (85, 22, 22)
    pygame.draw.rect(screen, back_color, btn_back, border_radius=10)
    screen.blit(back_label, back_label.get_rect(center=btn_back.center))

    # ── Flash de feedback ──────────────────────────────────────────────────
    if _feedback == "correcto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((0, 200, 80, 45))
        screen.blit(fb, (0, 0))
        screen.blit(font_title.render("Correcto!", True, GREEN),
                    font_title.render("Correcto!", True, GREEN).get_rect(center=(center_x, center_y + 175)))

    elif _feedback == "incorrecto":
        fb = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fb.fill((200, 0, 0, 45))
        screen.blit(fb, (0, 0))
        screen.blit(font_title.render("Incorrecto...", True, RED),
                    font_title.render("Incorrecto...", True, RED).get_rect(center=(center_x, center_y + 175)))

    return None
