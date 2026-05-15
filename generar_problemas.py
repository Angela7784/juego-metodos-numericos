"""
Genera 3 problemas de cada método y guarda la salida en un archivo de texto.
"""
import sys
import io
import random
random.seed(42)

from solucionador import Solucionador, METODOS, _EDO_MAP, _MC_MAP

def capturar(sol, nombre, fn_name):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        if nombre in _EDO_MAP:
            sol.resolver_edo(_EDO_MAP[nombre])
        elif nombre in _MC_MAP:
            sol.resolver_minimos_cuadrados(_MC_MAP[nombre])
        else:
            getattr(sol, fn_name)()
    except Exception as e:
        print(f"[Error: {e}]")
    finally:
        sys.stdout = old
    return buf.getvalue()

results = {}
sol = Solucionador()

for nombre, fn_name in METODOS:
    problemas = []
    for _ in range(3):
        salida = capturar(sol, nombre, fn_name)
        problemas.append(salida)
    results[nombre] = problemas

# Guardar en texto plano para usar después
import json
# Solo guardamos texto
with open("problemas_salida.txt", "w", encoding="utf-8") as f:
    for nombre, problemas in results.items():
        for idx, prob in enumerate(problemas, 1):
            f.write(f"===METODO:{nombre}===PROBLEMA:{idx}===\n")
            f.write(prob)
            f.write("\n")

print("Generado: problemas_salida.txt")
