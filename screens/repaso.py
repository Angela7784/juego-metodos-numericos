"""
screens/repaso.py

Pantalla de Repaso: muestra todos los PDFs organizados por carpeta.
Al hacer clic en un PDF se abre con el visor predeterminado del sistema.
"""

import os
import sys
import subprocess
import pygame

WHITE      = (255, 255, 255)
DARK       = (20,  22,  30)
PANEL      = (35,  40,  55)
YELLOW     = (255, 220,   0)
CYAN       = ( 70, 195, 255)
GREEN      = ( 50, 220,  90)
ORANGE     = (255, 148,  28)
PURPLE     = (180, 100, 255)
PINK       = (255, 100, 160)
LIGHT_GREY = (160, 165, 180)
HOVER_COL  = ( 55,  62,  82)

PDF_ROOT = "pdfs"

# Nombres legibles para cada carpeta
_NOMBRES_CARPETA = {
    "ecuaciones_no_lineales":          "Ecuaciones No Lineales",
    "ecuaciones_lineales":             "Ecuaciones Lineales",
    "interpolacion":                   "Interpolación",
    "minimos_cuadrados":               "Mínimos Cuadrados",
    "integracion":                     "Integración",
    "ecuaciones_diferenciales_ordinarias": "Ec. Diferenciales Ordinarias",
}

# Color de encabezado por categoría
_COLORES = {
    "ecuaciones_no_lineales":          CYAN,
    "ecuaciones_lineales":             GREEN,
    "interpolacion":                   YELLOW,
    "minimos_cuadrados":               ORANGE,
    "integracion":                     PURPLE,
    "ecuaciones_diferenciales_ordinarias": PINK,
}

# Orden fijo de las dos columnas
_COLUMNA_1 = [
    "ecuaciones_no_lineales",
    "ecuaciones_lineales",
    "interpolacion",
]
_COLUMNA_2 = [
    "minimos_cuadrados",
    "integracion",
    "ecuaciones_diferenciales_ordinarias",
]


def _nombre_pdf(filename: str) -> str:
    """Quita la extensión .pdf para mostrar el nombre."""
    return os.path.splitext(filename)[0]


def _abrir_pdf(path: str) -> None:
    """Minimiza el juego y abre el PDF; el usuario vuelve desde el Dock."""
    try:
        pygame.display.iconify()
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def _cargar_pdfs() -> dict:
    """Devuelve {carpeta: [ruta_absoluta, ...]} ordenado."""
    resultado = {}
    for carpeta in (_COLUMNA_1 + _COLUMNA_2):
        carpeta_path = os.path.join(PDF_ROOT, carpeta)
        if os.path.isdir(carpeta_path):
            archivos = sorted(
                f for f in os.listdir(carpeta_path) if f.lower().endswith(".pdf")
            )
            resultado[carpeta] = [os.path.join(carpeta_path, f) for f in archivos]
        else:
            resultado[carpeta] = []
    return resultado


def mostrar_repaso(screen, WIDTH, HEIGHT, font_title, font_button, event, mouse_pos):
    """
    Pantalla de Repaso.

    Retorna:
      'inicio'  -> al presionar Volver
      None      -> sin acción
    """
    pdfs = _cargar_pdfs()

    # ── Fondo ─────────────────────────────────────────────────────────────
    screen.fill(DARK)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))

    # ── Título ─────────────────────────────────────────────────────────────
    font_small   = pygame.font.SysFont("Arial", 16)
    font_header  = pygame.font.SysFont("Arial", 16, bold=True)
    font_pdf     = pygame.font.SysFont("Arial", 14)

    title_surf = font_title.render("Repaso", True, YELLOW)
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 46)))
    pygame.draw.line(screen, YELLOW, (WIDTH // 2 - 140, 76), (WIDTH // 2 + 140, 76), 2)

    # ── Columnas ───────────────────────────────────────────────────────────
    gap      = 24
    col_w    = (WIDTH - 80 - gap) // 2
    col1_x   = 40
    col2_x   = col1_x + col_w + gap
    start_y  = 95

    btn_rects = []   # [(rect, pdf_path), ...]

    for col_idx, carpetas in enumerate((_COLUMNA_1, _COLUMNA_2)):
        cx = col1_x if col_idx == 0 else col2_x
        cy = start_y

        for carpeta in carpetas:
            color  = _COLORES.get(carpeta, WHITE)
            nombre = _NOMBRES_CARPETA.get(carpeta, carpeta)
            archivos = pdfs.get(carpeta, [])

            # Encabezado de categoría
            hdr_rect = pygame.Rect(cx, cy, col_w, 26)
            pygame.draw.rect(screen, (30, 35, 50), hdr_rect, border_radius=5)
            pygame.draw.rect(screen, color, hdr_rect, 2, border_radius=5)
            hdr_surf = font_header.render(nombre, True, color)
            screen.blit(hdr_surf, hdr_surf.get_rect(midleft=(cx + 8, cy + 13)))
            cy += 31

            # Botones de PDF
            for pdf_path in archivos:
                nombre_archivo = _nombre_pdf(os.path.basename(pdf_path))
                btn = pygame.Rect(cx + 6, cy, col_w - 6, 23)

                hovering = btn.collidepoint(mouse_pos)
                bg = HOVER_COL if hovering else PANEL
                pygame.draw.rect(screen, bg, btn, border_radius=4)

                lbl = font_pdf.render(f"  {nombre_archivo}", True, WHITE if hovering else LIGHT_GREY)
                screen.blit(lbl, lbl.get_rect(midleft=(btn.left + 5, btn.centery)))

                btn_rects.append((btn, pdf_path))
                cy += 26

            cy += 8   # espacio entre categorías

    # ── Botón Volver ───────────────────────────────────────────────────────
    btn_back = pygame.Rect(0, 0, 160, 38)
    btn_back.bottomright = (WIDTH - 16, HEIGHT - 12)
    bc = (50, 55, 75) if btn_back.collidepoint(mouse_pos) else (35, 38, 55)
    pygame.draw.rect(screen, bc,   btn_back, border_radius=8)
    pygame.draw.rect(screen, CYAN, btn_back, 2, border_radius=8)
    font_back = pygame.font.SysFont("Arial", 18, bold=True)
    lbl_back = font_back.render("< Volver", True, WHITE)
    screen.blit(lbl_back, lbl_back.get_rect(center=btn_back.center))

    # ── Eventos ────────────────────────────────────────────────────────────
    if event.type == pygame.MOUSEBUTTONDOWN:
        if btn_back.collidepoint(mouse_pos):
            return "volver"
        for btn, pdf_path in btn_rects:
            if btn.collidepoint(mouse_pos):
                _abrir_pdf(pdf_path)
                break

    return None
