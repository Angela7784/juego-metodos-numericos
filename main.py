import pygame
import sys
import time

from screens.menu              import mostrar_mapa
from screens.select_metodo     import mostrar_select_metodo
from screens.instructions      import mostrar_instrucciones
from screens.level_game        import mostrar_level_game, reset_level
from screens.minigames.cables       import mostrar_cables,       reset_cables
from screens.minigames.oscilloscope import mostrar_oscilloscope, reset_oscilloscope
from screens.minigames.semaforo     import mostrar_semaforo,     reset_semaforo
from screens.minigames.curve_fit    import mostrar_curve_fit,    reset_curve_fit
from screens.minigames.battery      import mostrar_battery,      reset_battery
from screens.minigames.train_sim    import mostrar_train_sim,    reset_train_sim
from screens.results_screen.correct       import mostrar_correcto
from screens.results_screen.incorrect     import mostrar_incorrecto
from screens.results_screen.game_over     import mostrar_game_over
from screens.results_screen.game_complete import mostrar_game_complete
from managers.level_manager    import LevelManager
from managers.save_manager     import SaveManager
from core.game_state           import GameState
from core.transitions          import ScreenTransition

level_manager = LevelManager("data/levels.json")
game_state    = GameState()
SaveManager.cargar(game_state)
game_state.ult_nivel_desbloqueado = level_manager.total_levels() - 1

pygame.init()
WIDTH, HEIGHT = 1200, 850
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rescate Numerico en Metrorrey")

background = pygame.image.load("assets/init_background.jpeg")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

BLUE_METRO = (54, 175, 250)
DARK_GREY  = (30, 30, 30)
WHITE      = (255, 255, 255)

font_title  = pygame.font.SysFont("Arial", 50, bold=True)
font_button = pygame.font.SysFont("Arial", 30, bold=True)


def draw_text(text, font, color, surface, x, y):
    obj  = font.render(text, True, color)
    rect = obj.get_rect(center=(x, y))
    surface.blit(obj, rect)


def _pantalla_para_nivel(nivel):
    return {
        "cables":       "cables",
        "osciloscopio": "osciloscopio",
        "semaforo":     "semaforo",
        "curvas":       "curvas",
        "bateria":      "bateria",
        "tren":         "tren",
    }.get(nivel.get("minijuego", ""), "level_game")


def _reset_minijuego(nivel):
    {
        "cables":       reset_cables,
        "osciloscopio": reset_oscilloscope,
        "semaforo":     reset_semaforo,
        "curvas":       reset_curve_fit,
        "bateria":      reset_battery,
        "tren":         reset_train_sim,
    }.get(nivel.get("minijuego", ""), reset_level)()


PUNTOS_POR_VIDA = 5000
MAX_VIDAS       = 9

def _nivel_superado(nivel_ref, ctx):
    gs         = ctx["game_state"]
    prev_bonus = gs.puntos // PUNTOS_POR_VIDA
    gs.puntos += nivel_ref.get("puntos", 1000)
    new_bonus  = gs.puntos // PUNTOS_POR_VIDA
    if new_bonus > prev_bonus and gs.vidas < MAX_VIDAS:
        gs.vidas += 1
        ctx["vida_ganada"] = True
    else:
        ctx["vida_ganada"] = False
    ctx["nivel_completado"] = nivel_ref
    siguiente = gs.nivel_actual + 1
    total     = level_manager.total_levels()
    if siguiente < total:
        gs.nivel_actual = siguiente
        if siguiente > gs.ult_nivel_desbloqueado:
            gs.ult_nivel_desbloqueado = siguiente
    SaveManager.guardar(gs)
    return "game_complete" if siguiente >= total else "correcto"


def main():
    current_screen   = "inicio"
    start_time       = None
    nivel_completado = None
    clock            = pygame.time.Clock()
    ctx              = {"game_state": game_state, "nivel_completado": None, "vida_ganada": False}
    transition       = ScreenTransition()

    # Fade-in inicial al arrancar el juego
    transition.request("inicio")

    while True:
        now        = pygame.time.get_ticks()
        mouse_pos  = pygame.mouse.get_pos()
        nivel      = level_manager.get_level(game_state.nivel_actual)

        all_events = pygame.event.get()
        for ev in all_events:
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Evento principal (primer no-motion)
        event = pygame.event.Event(pygame.NOEVENT)
        for ev in all_events:
            if ev.type not in (pygame.MOUSEMOTION,):
                event = ev
                break

        # ── Actualizar transicion ─────────────────────────────────────────
        new_screen = transition.update(now)
        if new_screen is not None:
            current_screen = new_screen

        # Durante fade-out bloqueamos input para evitar doble-trigger
        busy = transition.is_busy

        # ══════════════════════════════════════════════════════════════════
        # RENDERIZADO DE PANTALLAS
        # ══════════════════════════════════════════════════════════════════

        # INICIO
        if current_screen == "inicio":
            screen.blit(background, (0, 0))

            btn_iniciar = pygame.Rect(0, 0, 200, 60)
            btn_iniciar.center = (WIDTH // 2, HEIGHT // 2 + 250)
            color_i = (80, 190, 255) if btn_iniciar.collidepoint(mouse_pos) else BLUE_METRO
            pygame.draw.rect(screen, color_i, btn_iniciar, border_radius=12)
            draw_text("INICIAR", font_button, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 250)

            btn_inst = pygame.Rect(0, 0, 220, 50)
            btn_inst.center = (WIDTH // 2, HEIGHT // 2 + 325)
            color_inst = (60, 60, 60) if btn_inst.collidepoint(mouse_pos) else (40, 40, 40)
            pygame.draw.rect(screen, color_inst, btn_inst, border_radius=10)
            draw_text("Instrucciones", font_button, (180, 180, 180), screen, WIDTH // 2, HEIGHT // 2 + 325)

            if not busy and event.type == pygame.MOUSEBUTTONDOWN:
                if btn_iniciar.collidepoint(mouse_pos):
                    transition.request("menu")
                elif btn_inst.collidepoint(mouse_pos):
                    transition.request("instrucciones")

        # INSTRUCCIONES
        elif current_screen == "instrucciones":
            result = mostrar_instrucciones(screen, WIDTH, HEIGHT, font_title, font_button, event, mouse_pos)
            if not busy and result == "menu":
                transition.request("menu")

        # MAPA
        elif current_screen == "menu":
            result = mostrar_mapa(screen, WIDTH, HEIGHT, font_title, font_button,
                                  WHITE, DARK_GREY, event, mouse_pos, game_state, nivel)
            if not busy and result == "select_metodo":
                if nivel and "opciones_mezcladas" in nivel:
                    del nivel["opciones_mezcladas"]
                if nivel and "problema_seleccionado" in nivel:
                    del nivel["problema_seleccionado"]
                start_time = time.time()
                transition.request("select_metodo")

        # SELECCION DE METODO
        elif current_screen == "select_metodo":
            result = mostrar_select_metodo(screen, WIDTH, HEIGHT, font_title, font_button,
                                           WHITE, DARK_GREY, event, mouse_pos,
                                           game_state, nivel, start_time)
            if not busy:
                if result == "metodo_correcto":
                    _reset_minijuego(nivel)
                    transition.request(_pantalla_para_nivel(nivel))
                elif result == "incorrecto":
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")
                elif result == "tiempo_agotado":
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")
                elif result == "volver_menu":
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    if nivel and "opciones_mezcladas" in nivel:
                        del nivel["opciones_mezcladas"]
                    if nivel and "problema_seleccionado" in nivel:
                        del nivel["problema_seleccionado"]
                    transition.request("game_over" if game_state.vidas <= 0 else "menu")

        # CABLES
        elif current_screen == "cables":
            result = mostrar_cables(screen, WIDTH, HEIGHT, font_title, font_button,
                                    game_state, nivel, all_events, mouse_pos, start_time)
            if not busy:
                if result == "nivel_completo":
                    next_s = _nivel_superado(nivel, ctx)
                    nivel_completado = ctx["nivel_completado"]
                    transition.request(next_s)
                elif result == "tiempo_agotado":
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")

        # OSCILOSCOPIO
        elif current_screen == "osciloscopio":
            result = mostrar_oscilloscope(screen, WIDTH, HEIGHT, font_title, font_button,
                                          game_state, nivel, all_events, mouse_pos, start_time)
            if not busy:
                if result == "nivel_completo":
                    next_s = _nivel_superado(nivel, ctx)
                    nivel_completado = ctx["nivel_completado"]
                    transition.request(next_s)
                elif result in ("incorrecto", "tiempo_agotado"):
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")

        # SEMAFORO
        elif current_screen == "semaforo":
            result = mostrar_semaforo(screen, WIDTH, HEIGHT, font_title, font_button,
                                      game_state, nivel, all_events, mouse_pos, start_time)
            if not busy:
                if result == "nivel_completo":
                    next_s = _nivel_superado(nivel, ctx)
                    nivel_completado = ctx["nivel_completado"]
                    transition.request(next_s)
                elif result in ("incorrecto", "tiempo_agotado"):
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")

        # CURVAS
        elif current_screen == "curvas":
            result = mostrar_curve_fit(screen, WIDTH, HEIGHT, font_title, font_button,
                                       game_state, nivel, all_events, mouse_pos, start_time)
            if not busy:
                if result == "nivel_completo":
                    next_s = _nivel_superado(nivel, ctx)
                    nivel_completado = ctx["nivel_completado"]
                    transition.request(next_s)
                elif result in ("incorrecto", "tiempo_agotado"):
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")

        # BATERIA
        elif current_screen == "bateria":
            result = mostrar_battery(screen, WIDTH, HEIGHT, font_title, font_button,
                                     game_state, nivel, all_events, mouse_pos, start_time)
            if not busy:
                if result == "nivel_completo":
                    next_s = _nivel_superado(nivel, ctx)
                    nivel_completado = ctx["nivel_completado"]
                    transition.request(next_s)
                elif result in ("incorrecto", "tiempo_agotado"):
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")

        # TREN
        elif current_screen == "tren":
            result = mostrar_train_sim(screen, WIDTH, HEIGHT, font_title, font_button,
                                       game_state, nivel, all_events, mouse_pos, start_time)
            if not busy:
                if result == "nivel_completo":
                    next_s = _nivel_superado(nivel, ctx)
                    nivel_completado = ctx["nivel_completado"]
                    transition.request(next_s)
                elif result in ("incorrecto", "tiempo_agotado"):
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")

        # LEVEL GAME GENERICO
        elif current_screen == "level_game":
            result = mostrar_level_game(screen, WIDTH, HEIGHT, font_title, font_button,
                                        game_state, nivel, all_events, mouse_pos)
            if not busy:
                if result == "nivel_completo":
                    next_s = _nivel_superado(nivel, ctx)
                    nivel_completado = ctx["nivel_completado"]
                    transition.request(next_s)
                elif result == "incorrecto":
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "incorrecto")
                elif result == "volver_menu":
                    game_state.vidas -= 1
                    SaveManager.guardar(game_state)
                    transition.request("game_over" if game_state.vidas <= 0 else "menu")

        # CORRECTO
        elif current_screen == "correcto":
            result = mostrar_correcto(screen, WIDTH, HEIGHT, font_title, font_button,
                                      game_state, nivel_completado or nivel, event, mouse_pos,
                                      vida_ganada=ctx["vida_ganada"])
            if not busy and result == "menu":
                ctx["vida_ganada"] = False
                transition.request("menu")

        # INCORRECTO
        elif current_screen == "incorrecto":
            result = mostrar_incorrecto(screen, WIDTH, HEIGHT, font_title, font_button,
                                        game_state, nivel, event, mouse_pos)
            if not busy:
                if result == "select_metodo":
                    if nivel and "opciones_mezcladas" in nivel:
                        del nivel["opciones_mezcladas"]
                    if nivel and "problema_seleccionado" in nivel:
                        del nivel["problema_seleccionado"]
                    start_time = time.time()
                    transition.request("select_metodo")
                elif result == "game_over":
                    transition.request("game_over")

        # JUEGO COMPLETO
        elif current_screen == "game_complete":
            result = mostrar_game_complete(screen, WIDTH, HEIGHT, font_title, font_button,
                                           game_state, event, mouse_pos)
            if not busy and result == "inicio":
                nivel_completado                  = None
                ctx["nivel_completado"]           = None
                game_state.ult_nivel_desbloqueado = level_manager.total_levels() - 1
                SaveManager.guardar(game_state)
                transition.request("inicio")

        # GAME OVER
        elif current_screen == "game_over":
            result = mostrar_game_over(screen, WIDTH, HEIGHT, font_title, font_button,
                                       game_state, event, mouse_pos)
            if not busy and result == "inicio":
                nivel_completado = None
                transition.request("inicio")

        # ── Overlay de transicion (siempre al final, sobre todo) ──────────
        transition.draw(screen, WIDTH, HEIGHT, now)

        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
