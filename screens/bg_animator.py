import pygame
import os
import re


class BackgroundAnimator:
    """
    Animador de fondo que carga frames PNG individuales desde una carpeta.

    Espera archivos con el formato que genera ezgif:
        frame_00_delay-0.1s.png
        frame_01_delay-0.2s.png
        ...

    Respeta el delay de cada frame extraído del nombre del archivo.
    Los frames se pre-escalan al tamaño de pantalla al cargar (sin costo en draw).

    Convención de carpetas:
        assets/fondos/linea_1/   <- frames de la Línea 1
        assets/fondos/linea_2/   <- frames de la Línea 2
        assets/fondos/linea_3/   <- frames de la Línea 3

    Uso:
        animator = BackgroundAnimator("assets/fondos/linea_1", WIDTH, HEIGHT)
        # en el loop de dibujo:
        animator.draw(screen)
    """

    # cache: (folder, screen_w, screen_h) -> (frames, delays_ms, total_ms)
    _cache: dict = {}

    def __init__(self, folder: str, screen_w: int, screen_h: int):
        self._frames:   list[pygame.Surface] = []
        self._delays:   list[int]            = []   # duración de cada frame en ms
        self._total_ms: int                  = 0    # duración total del loop

        cache_key = (folder, screen_w, screen_h)
        if cache_key in BackgroundAnimator._cache:
            self._frames, self._delays, self._total_ms = BackgroundAnimator._cache[cache_key]
        else:
            self._cargar(folder, screen_w, screen_h)
            BackgroundAnimator._cache[cache_key] = (self._frames, self._delays, self._total_ms)

    # ── Carga ──────────────────────────────────────────────────────────────

    def _cargar(self, folder: str, tw: int, th: int) -> None:
        if not os.path.isdir(folder):
            print(f"[BackgroundAnimator] Carpeta no encontrada: '{folder}'")
            return

        # Buscar archivos PNG y ordenarlos por número de frame
        archivos = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
        archivos.sort(key=lambda f: self._numero_frame(f))

        if not archivos:
            print(f"[BackgroundAnimator] Sin archivos PNG en '{folder}'")
            return

        for nombre in archivos:
            ruta  = os.path.join(folder, nombre)
            delay = self._extraer_delay(nombre)   # ms

            try:
                img    = pygame.image.load(ruta).convert()
                scaled = pygame.transform.scale(img, (tw, th))
                self._frames.append(scaled)
                self._delays.append(delay)
            except Exception as e:
                print(f"[BackgroundAnimator] Error cargando '{ruta}': {e}")

        self._total_ms = sum(self._delays)
        print(f"[BackgroundAnimator] {len(self._frames)} frames cargados "
              f"(loop = {self._total_ms / 1000:.2f}s)")

    @staticmethod
    def _numero_frame(nombre: str) -> int:
        """Extrae el número de frame del nombre para ordenar correctamente."""
        match = re.search(r'frame_(\d+)', nombre)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _extraer_delay(nombre: str) -> int:
        """
        Extrae el delay en ms del nombre del archivo.
        Ejemplo: 'frame_02_delay-0.2s.png' → 200
        Si no encuentra delay, asume 100 ms (0.1s).
        """
        match = re.search(r'delay-([\d.]+)s', nombre)
        if match:
            return int(float(match.group(1)) * 1000)
        return 100

    # ── API pública ────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> bool:
        """
        Dibuja el frame correcto según el tiempo actual.
        Retorna True si se dibujó, False si no hay frames cargados.
        """
        if not self._frames or self._total_ms == 0:
            return False

        # Tiempo dentro del loop actual
        t = pygame.time.get_ticks() % self._total_ms

        # Encontrar qué frame corresponde a ese tiempo
        acumulado = 0
        for i, delay in enumerate(self._delays):
            acumulado += delay
            if t < acumulado:
                screen.blit(self._frames[i], (0, 0))
                return True

        # Fallback: último frame
        screen.blit(self._frames[-1], (0, 0))
        return True

    @classmethod
    def limpiar_cache(cls) -> None:
        cls._cache.clear()


# ── Helper ─────────────────────────────────────────────────────────────────

def fondo_por_linea(linea: str) -> str:
    """Retorna la carpeta de frames para la línea indicada."""
    return f"assets/fondos/linea_{linea}"
