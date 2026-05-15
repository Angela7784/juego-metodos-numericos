import numpy as np


class MetodosCalculo:
    def encontrar_raices_reales(self, f, a, b, pasos=500):
        xs = np.linspace(a, b, pasos)
        raices = []
        for i in range(len(xs) - 1):
            if f(xs[i]) * f(xs[i + 1]) < 0:
                lo, hi = xs[i], xs[i + 1]
                for _ in range(60):
                    mid = (lo + hi) / 2
                    if f(lo) * f(mid) < 0:
                        hi = mid
                    else:
                        lo = mid
                raices.append((lo + hi) / 2)
        return raices

    def calcular_diferencias_finitas(self, puntos):
        n = len(puntos)
        tabla = [[0.0] * n for _ in range(n)]
        for i in range(n):
            tabla[i][0] = puntos[i][1]
        for j in range(1, n):
            for i in range(n - j):
                tabla[i][j] = tabla[i + 1][j - 1] - tabla[i][j - 1]
        return tabla
