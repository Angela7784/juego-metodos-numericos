"""
core/transitions.py

Fade-to-black / fade-from-black entre pantallas.

Uso en main.py:
  1. transition.request("nueva_pantalla")  cuando quieres cambiar
  2. new = transition.update(now)          retorna el nombre al punto medio visual
  3. if new: current_screen = new
  4. transition.draw(screen, WIDTH, HEIGHT, now)  al final del frame, sobre todo
"""

import pygame

FADE_MS = 320   # duracion de cada fase (salida o entrada), en ms


class ScreenTransition:

    def __init__(self):
        self._state   = "idle"      # idle | fading_out | fading_in
        self._tick    = 0
        self._pending = None
        self._surf    = None
        self._color   = (6, 10, 20)  # azul-negro metro

    # ------------------------------------------------------------------
    def request(self, new_screen: str):
        """Inicia la transicion. Ignorado si ya hay una en curso."""
        if self._state == "idle":
            self._pending = new_screen
            self._state   = "fading_out"
            self._tick    = pygame.time.get_ticks()

    # ------------------------------------------------------------------
    def update(self, now: int):
        """
        Llama una vez por frame.
        Retorna el nombre de la nueva pantalla exactamente una vez
        (en el punto en que la pantalla esta totalmente negra).
        Retorna None el resto del tiempo.
        """
        if self._state == "idle":
            return None
        elapsed = now - self._tick
        if self._state == "fading_out" and elapsed >= FADE_MS:
            self._state = "fading_in"
            self._tick  = now
            return self._pending
        if self._state == "fading_in" and elapsed >= FADE_MS:
            self._state = "idle"
        return None

    # ------------------------------------------------------------------
    def draw(self, screen, WIDTH, HEIGHT, now: int):
        """Dibuja el overlay de fade encima de todo. Llamar al final del frame."""
        if self._state == "idle":
            return
        elapsed = now - self._tick
        ratio   = min(1.0, elapsed / FADE_MS)
        alpha   = int(255 * ratio) if self._state == "fading_out" else int(255 * (1.0 - ratio))
        if self._surf is None or self._surf.get_size() != (WIDTH, HEIGHT):
            self._surf = pygame.Surface((WIDTH, HEIGHT))
            self._surf.fill(self._color)
        self._surf.set_alpha(alpha)
        screen.blit(self._surf, (0, 0))

    # ------------------------------------------------------------------
    @property
    def is_busy(self):
        """True mientras cualquier fase de fade esta activa."""
        return self._state != "idle"
