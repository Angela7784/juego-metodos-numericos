"""
solucionador.py
---------------
Genera problemas aleatorios para cada método numérico del juego,
imprime el enunciado, los pasos intermedios y el resultado final.
"""

import math
import random
import numpy as np
from metodos import MetodosCalculo

SEP  = "=" * 65
SEP2 = "-" * 65


# ─────────────────────────────────────────────────────────────────
# CLASE PRINCIPAL
# ─────────────────────────────────────────────────────────────────

class Solucionador:
    def __init__(self):
        self.mc = MetodosCalculo()

    # ── utilidades ────────────────────────────────────────────────

    @staticmethod
    def _deriv(f, x, h=1e-7):
        return (f(x + h) - f(x - h)) / (2 * h)

    @staticmethod
    def _print_mat(M, titulo=""):
        if titulo:
            print(f"  [{titulo}]")
        for fila in M:
            print("  " + "  ".join(f"{v:10.4f}" for v in fila))
        print()

    @staticmethod
    def _coef_no_cero():
        return random.choice([i for i in range(-5, 6) if i != 0])

    # ─────────────────────────────────────────────────────────────
    # 1. INTERPOLACIÓN LINEAL
    # ─────────────────────────────────────────────────────────────

    def resolver_interpolacion_lineal(self):
        print(SEP)
        print("MÉTODO: INTERPOLACIÓN LINEAL")
        print(SEP)

        tipos = [
            {"desc": "ln(3)",      "x0": 2, "y0": math.log(2),   "x1": 4, "y1": math.log(4),   "xq": 3},
            {"desc": "sin(π/4)",   "x0": 0, "y0": 0.0,           "x1": math.pi/2, "y1": 1.0,   "xq": math.pi/4},
            {"desc": "cos(π/3)",   "x0": 0, "y0": 1.0,           "x1": math.pi/2, "y1": 0.0,   "xq": math.pi/3},
            {"desc": "e¹",         "x0": 0, "y0": 1.0,           "x1": 2, "y1": math.exp(2),   "xq": 1},
            {"desc": "√2",         "x0": 1, "y0": 1.0,           "x1": 4, "y1": 2.0,           "xq": 2},
            {"desc": "log₁₀(5)",   "x0": 1, "y0": 0.0,           "x1": 10, "y1": 1.0,          "xq": 5},
        ]
        t = random.choice(tipos)
        x0, y0, x1, y1, xq = t["x0"], t["y0"], t["x1"], t["y1"], t["xq"]

        print(f"\nEncontrar {t['desc']} usando interpolación lineal.\n")
        print(f"  Datos conocidos:")
        print(f"    x₀ = {x0},  f(x₀) = {y0:.6f}")
        print(f"    x₁ = {x1:.4f},  f(x₁) = {y1:.6f}")
        print(f"  Interpolar en  x = {xq:.4f}\n")
        print(f"  Fórmula:  f(x) = f(x₀) + [f(x₁)-f(x₀)] · (x-x₀)/(x₁-x₀)\n")

        num   = y1 - y0
        denom = x1 - x0
        frac  = (xq - x0) / denom
        res   = y0 + num * frac

        print(f"  Paso 1:  f(x₁) - f(x₀)  = {y1:.6f} - {y0:.6f} = {num:.6f}")
        print(f"  Paso 2:  x₁ - x₀        = {x1:.4f} - {x0} = {denom:.4f}")
        print(f"  Paso 3:  x - x₀         = {xq:.4f} - {x0} = {xq - x0:.4f}")
        print(f"  Paso 4:  fracción        = {xq - x0:.4f} / {denom:.4f} = {frac:.6f}")
        print(f"  Paso 5:  f({xq:.4f})    = {y0:.6f} + {num:.6f} × {frac:.6f}")
        print(f"\n  ► RESULTADO: f({xq:.4f}) ≈ {res:.6f}")
        return res

    # ─────────────────────────────────────────────────────────────
    # helpers para sistemas 3×3
    # ─────────────────────────────────────────────────────────────

    def _sistema_3x3(self, diagonal_dominante=False):
        sol = [random.randint(-5, 5) for _ in range(3)]
        c = self._coef_no_cero

        if diagonal_dominante:
            a12, a13 = c(), c()
            a21, a23 = c(), c()
            a31, a32 = c(), c()
            a11 = abs(a12) + abs(a13) + random.randint(1, 3)
            a22 = abs(a21) + abs(a23) + random.randint(1, 3)
            a33 = abs(a31) + abs(a32) + random.randint(1, 3)
        else:
            a11, a12, a13 = c(), c(), c()
            a21, a22, a23 = c(), c(), c()
            a31, a32, a33 = c(), c(), c()
            det = (a11*(a22*a33 - a23*a32)
                   - a12*(a21*a33 - a23*a31)
                   + a13*(a21*a32 - a22*a31))
            if abs(det) < 0.5:
                a11, a12, a13 = 2, -3,  1
                a21, a22, a23 = -1, 2,  4
                a31, a32, a33 = 3,  1, -2

        A = [[float(a11), float(a12), float(a13)],
             [float(a21), float(a22), float(a23)],
             [float(a31), float(a32), float(a33)]]
        b = [sum(A[i][j] * sol[j] for j in range(3)) for i in range(3)]
        return A, b, sol

    def _print_sistema(self, A, b):
        vars_ = ["x", "y", "z"]
        for i in range(3):
            partes = []
            for j in range(3):
                v = int(A[i][j]) if A[i][j] == int(A[i][j]) else A[i][j]
                partes.append(f"({v}){vars_[j]}")
            print(f"    {' + '.join(partes)} = {b[i]:.4f}")
        print()

    # ─────────────────────────────────────────────────────────────
    # 2. ELIMINACIÓN GAUSSIANA
    # ─────────────────────────────────────────────────────────────

    def resolver_eliminacion_gaussiana(self):
        print(SEP)
        print("MÉTODO: ELIMINACIÓN GAUSSIANA")
        print(SEP)
        A, b, sol = self._sistema_3x3()
        n = 3
        print("\nSistema original:")
        self._print_sistema(A, b)

        M = [A[i][:] + [b[i]] for i in range(n)]
        self._print_mat(M, "Matriz aumentada inicial")

        for col in range(n):
            # Pivoteo parcial
            fila_max = max(range(col, n), key=lambda r: abs(M[r][col]))
            if fila_max != col:
                M[col], M[fila_max] = M[fila_max], M[col]
                print(f"  Intercambio: F{col+1} ↔ F{fila_max+1}")
                self._print_mat(M)

            piv = M[col][col]
            for row in range(col + 1, n):
                if abs(piv) < 1e-12:
                    continue
                factor = M[row][col] / piv
                print(f"  F{row+1} ← F{row+1} - ({factor:.4f})·F{col+1}")
                for k in range(n + 1):
                    M[row][k] -= factor * M[col][k]
                self._print_mat(M)

        print("  Sustitución regresiva:")
        x_sol = [0.0] * n
        for i in range(n - 1, -1, -1):
            x_sol[i] = M[i][n] - sum(M[i][j] * x_sol[j] for j in range(i + 1, n))
            x_sol[i] /= M[i][i]
            print(f"    {'xyz'[i]} = {x_sol[i]:.6f}")

        print(f"\n  ► RESULTADO: x={x_sol[0]:.4f}, y={x_sol[1]:.4f}, z={x_sol[2]:.4f}")
        print(f"    (esperado:   x={sol[0]}, y={sol[1]}, z={sol[2]})")
        return tuple(x_sol)

    # ─────────────────────────────────────────────────────────────
    # 3. GAUSS-JORDAN
    # ─────────────────────────────────────────────────────────────

    def resolver_gauss_jordan(self):
        print(SEP)
        print("MÉTODO: GAUSS-JORDAN")
        print(SEP)
        A, b, sol = self._sistema_3x3()
        n = 3
        print("\nSistema original:")
        self._print_sistema(A, b)

        M = [A[i][:] + [b[i]] for i in range(n)]
        self._print_mat(M, "Matriz aumentada inicial")

        for col in range(n):
            fila_max = max(range(col, n), key=lambda r: abs(M[r][col]))
            if fila_max != col:
                M[col], M[fila_max] = M[fila_max], M[col]
                print(f"  Intercambio: F{col+1} ↔ F{fila_max+1}")
                self._print_mat(M)

            piv = M[col][col]
            if abs(piv) > 1e-12:
                M[col] = [v / piv for v in M[col]]
                print(f"  F{col+1} ← F{col+1} ÷ {piv:.4f}  (normalizar)")
                self._print_mat(M)

            for row in range(n):
                if row == col:
                    continue
                factor = M[row][col]
                if abs(factor) < 1e-12:
                    continue
                print(f"  F{row+1} ← F{row+1} - ({factor:.4f})·F{col+1}")
                M[row] = [M[row][k] - factor * M[col][k] for k in range(n + 1)]
                self._print_mat(M)

        x_sol = [M[i][n] for i in range(n)]
        print(f"  ► RESULTADO: x={x_sol[0]:.4f}, y={x_sol[1]:.4f}, z={x_sol[2]:.4f}")
        print(f"    (esperado:   x={sol[0]}, y={sol[1]}, z={sol[2]})")
        return tuple(x_sol)

    # ─────────────────────────────────────────────────────────────
    # 4. MONTANTE (Bareiss)
    # ─────────────────────────────────────────────────────────────

    def resolver_montante(self):
        print(SEP)
        print("MÉTODO: MONTANTE (Bareiss)")
        print(SEP)
        A, b, sol = self._sistema_3x3()
        n = 3
        print("\nSistema original:")
        self._print_sistema(A, b)

        M = [A[i][:] + [b[i]] for i in range(n)]
        self._print_mat(M, "Matriz aumentada inicial")

        piv_prev = 1.0
        for k in range(n):
            piv = M[k][k]
            print(f"  Pivote k={k+1}: M[{k+1}][{k+1}] = {piv:.4f}  (pivote anterior = {piv_prev:.4f})")
            for i in range(n):
                if i == k:
                    continue
                for j in range(n + 1):
                    if j == k:
                        continue
                    M[i][j] = (piv * M[i][j] - M[i][k] * M[k][j]) / piv_prev
            for i in range(n):
                if i != k:
                    M[i][k] = 0.0
            self._print_mat(M, f"Después de paso k={k+1}")
            piv_prev = piv

        x_sol = [M[i][n] / M[i][i] for i in range(n)]
        print("  Solución (x = M[i][n] / M[i][i]):")
        for i, v in enumerate(x_sol):
            print(f"    {'xyz'[i]} = {M[i][n]:.4f} / {M[i][i]:.4f} = {v:.6f}")
        print(f"\n  ► RESULTADO: x={x_sol[0]:.4f}, y={x_sol[1]:.4f}, z={x_sol[2]:.4f}")
        print(f"    (esperado:   x={sol[0]}, y={sol[1]}, z={sol[2]})")
        return tuple(x_sol)

    # ─────────────────────────────────────────────────────────────
    # 5. JACOBI
    # ─────────────────────────────────────────────────────────────

    def resolver_jacobi(self, tol=1e-5, max_iter=50):
        print(SEP)
        print("MÉTODO: JACOBI")
        print(SEP)
        A, b, sol = self._sistema_3x3(diagonal_dominante=True)
        n = 3
        print("\nSistema (diagonalmente dominante):")
        self._print_sistema(A, b)
        print("  Fórmula de Jacobi:  xᵢ⁽ᵏ⁺¹⁾ = (bᵢ - Σⱼ≠ᵢ aᵢⱼ·xⱼ⁽ᵏ⁾) / aᵢᵢ\n")

        x = [0.0, 0.0, 0.0]
        print(f"  {'Iter':>4}  {'x':>13}  {'y':>13}  {'z':>13}  {'error':>10}")
        print("  " + SEP2)
        for it in range(1, max_iter + 1):
            x_new = [(b[i] - sum(A[i][j]*x[j] for j in range(n) if j != i)) / A[i][i]
                     for i in range(n)]
            err = max(abs(x_new[i] - x[i]) for i in range(n))
            print(f"  {it:>4}  {x_new[0]:>13.6f}  {x_new[1]:>13.6f}  {x_new[2]:>13.6f}  {err:>10.2e}")
            x = x_new
            if err < tol:
                break

        print(f"\n  ► RESULTADO: x={x[0]:.6f}, y={x[1]:.6f}, z={x[2]:.6f}")
        print(f"    (esperado:   x={sol[0]:.4f}, y={sol[1]:.4f}, z={sol[2]:.4f})")
        return tuple(x)

    # ─────────────────────────────────────────────────────────────
    # 6. GAUSS-SEIDEL
    # ─────────────────────────────────────────────────────────────

    def resolver_gauss_seidel(self, tol=1e-5, max_iter=50):
        print(SEP)
        print("MÉTODO: GAUSS-SEIDEL")
        print(SEP)
        A, b, sol = self._sistema_3x3(diagonal_dominante=True)
        n = 3
        print("\nSistema (diagonalmente dominante):")
        self._print_sistema(A, b)
        print("  Diferencia con Jacobi: usa los valores ya actualizados en la misma iteración.\n")

        x = [0.0, 0.0, 0.0]
        print(f"  {'Iter':>4}  {'x':>13}  {'y':>13}  {'z':>13}  {'error':>10}")
        print("  " + SEP2)
        for it in range(1, max_iter + 1):
            x_prev = x[:]
            for i in range(n):
                x[i] = (b[i] - sum(A[i][j]*x[j] for j in range(n) if j != i)) / A[i][i]
            err = max(abs(x[i] - x_prev[i]) for i in range(n))
            print(f"  {it:>4}  {x[0]:>13.6f}  {x[1]:>13.6f}  {x[2]:>13.6f}  {err:>10.2e}")
            if err < tol:
                break

        print(f"\n  ► RESULTADO: x={x[0]:.6f}, y={x[1]:.6f}, z={x[2]:.6f}")
        print(f"    (esperado:   x={sol[0]:.4f}, y={sol[1]:.4f}, z={sol[2]:.4f})")
        return tuple(x)

    # ─────────────────────────────────────────────────────────────
    # helper ecuaciones no lineales
    # ─────────────────────────────────────────────────────────────

    def _ec_no_lineal(self):
        ops = [
            {"str": "x³ - 6.5x + 2",       "f": lambda x: x**3 - 6.5*x + 2,         "a": -3.0, "b": 3.0},
            {"str": "x³ + 2x² + 10x - 20", "f": lambda x: x**3 + 2*x**2 + 10*x - 20, "a": 1.0,  "b": 2.0},
            {"str": "e^(-x) - x",           "f": lambda x: math.exp(-x) - x,           "a": 0.0,  "b": 1.5},
            {"str": "x³ - 2x² - 5x + 6",   "f": lambda x: x**3 - 2*x**2 - 5*x + 6,   "a": -2.0, "b": 4.0},
        ]
        ec = random.choice(ops)
        # garantizar cambio de signo
        f, a, b = ec["f"], ec["a"], ec["b"]
        if f(a) * f(b) > 0:
            xs = np.linspace(a, b, 200)
            for i in range(len(xs) - 1):
                if f(xs[i]) * f(xs[i+1]) < 0:
                    ec = dict(ec, a=float(xs[i]), b=float(xs[i+1]))
                    break
        return ec

    # ─────────────────────────────────────────────────────────────
    # 7. BISECCIÓN
    # ─────────────────────────────────────────────────────────────

    def resolver_biseccion(self, tol=1e-5, max_iter=40):
        print(SEP)
        print("MÉTODO: BISECCIÓN")
        print(SEP)
        ec = self._ec_no_lineal()
        f, a, b = ec["f"], ec["a"], ec["b"]

        print(f"\n  f(x) = {ec['str']}")
        print(f"  Intervalo inicial: [{a:.4f}, {b:.4f}]")
        print(f"  f({a:.4f}) = {f(a):.6f},  f({b:.4f}) = {f(b):.6f}\n")
        print(f"  {'Iter':>4}  {'a':>12}  {'b':>12}  {'c=(a+b)/2':>12}  {'f(c)':>12}  {'|b-a|/2':>10}")
        print("  " + SEP2)

        c = a
        for it in range(1, max_iter + 1):
            c = (a + b) / 2
            fc = f(c)
            err = (b - a) / 2
            print(f"  {it:>4}  {a:>12.6f}  {b:>12.6f}  {c:>12.6f}  {fc:>12.6f}  {err:>10.2e}")
            if abs(fc) < tol or err < tol:
                break
            if f(a) * fc < 0:
                b = c
            else:
                a = c

        print(f"\n  ► RESULTADO: raíz ≈ {c:.8f},  f(raíz) = {f(c):.2e}")
        return c

    # ─────────────────────────────────────────────────────────────
    # 8. FALSA POSICIÓN
    # ─────────────────────────────────────────────────────────────

    def resolver_falsa_posicion(self, tol=1e-5, max_iter=40):
        print(SEP)
        print("MÉTODO: FALSA POSICIÓN (Regula Falsi)")
        print(SEP)
        ec = self._ec_no_lineal()
        f, a, b = ec["f"], ec["a"], ec["b"]

        print(f"\n  f(x) = {ec['str']}")
        print(f"  Intervalo inicial: [{a:.4f}, {b:.4f}]\n")
        print(f"  Fórmula: c = b - f(b)·(b-a) / (f(b)-f(a))\n")
        print(f"  {'Iter':>4}  {'a':>12}  {'b':>12}  {'c':>12}  {'f(c)':>12}  {'|f(c)|':>10}")
        print("  " + SEP2)

        c = a
        for it in range(1, max_iter + 1):
            fa, fb = f(a), f(b)
            c = b - fb * (b - a) / (fb - fa)
            fc = f(c)
            print(f"  {it:>4}  {a:>12.6f}  {b:>12.6f}  {c:>12.6f}  {fc:>12.6f}  {abs(fc):>10.2e}")
            if abs(fc) < tol:
                break
            if fa * fc < 0:
                b = c
            else:
                a = c

        print(f"\n  ► RESULTADO: raíz ≈ {c:.8f},  f(raíz) = {f(c):.2e}")
        return c

    # ─────────────────────────────────────────────────────────────
    # 9. NEWTON-RAPHSON
    # ─────────────────────────────────────────────────────────────

    def resolver_newton_raphson(self, tol=1e-8, max_iter=30):
        print(SEP)
        print("MÉTODO: NEWTON-RAPHSON")
        print(SEP)
        ec = self._ec_no_lineal()
        f = ec["f"]
        raices = self.mc.encontrar_raices_reales(f, ec["a"], ec["b"])
        x = (raices[0] if raices else (ec["a"] + ec["b"]) / 2) + random.uniform(-0.4, 0.4)

        print(f"\n  f(x) = {ec['str']}")
        print(f"  f'(x) se calcula numéricamente: f'(x) ≈ [f(x+h)-f(x-h)] / 2h")
        print(f"  Valor inicial: x₀ = {x:.4f}\n")
        header_nr = "  {:>4}  {:>14}  {:>13}  {:>13}  {:>14}  {:>10}".format(
            "Iter", "x_n", "f(x_n)", "f'(x_n)", "x_{n+1}", "|Δx|")
        print(header_nr)
        print("  " + SEP2)

        for it in range(1, max_iter + 1):
            fx  = f(x)
            fpx = self._deriv(f, x)
            if abs(fpx) < 1e-14:
                print("  Derivada ≈ 0, no converge.")
                break
            x_new = x - fx / fpx
            err   = abs(x_new - x)
            print(f"  {it:>4}  {x:>14.8f}  {fx:>13.6f}  {fpx:>13.6f}  {x_new:>14.8f}  {err:>10.2e}")
            x = x_new
            if err < tol:
                break

        print(f"\n  ► RESULTADO: raíz ≈ {x:.8f},  f(raíz) = {f(x):.2e}")
        return x

    # ─────────────────────────────────────────────────────────────
    # 10. SECANTE
    # ─────────────────────────────────────────────────────────────

    def resolver_secante(self, tol=1e-8, max_iter=30):
        print(SEP)
        print("MÉTODO: SECANTE")
        print(SEP)
        ec = self._ec_no_lineal()
        f = ec["f"]
        raices = self.mc.encontrar_raices_reales(f, ec["a"], ec["b"])
        r  = raices[0] if raices else (ec["a"] + ec["b"]) / 2
        x0 = r + random.uniform(-0.8, -0.2)
        x1 = r + random.uniform(0.2,  0.8)

        print(f"\n  f(x) = {ec['str']}")
        print(f"  Valores iniciales: x₀ = {x0:.4f},  x₁ = {x1:.4f}")
        print(f"  Fórmula: x_{{n+1}} = x_n - f(x_n)·(x_n - x_{{n-1}}) / (f(x_n) - f(x_{{n-1}}))\n")
        print(f"  {'Iter':>4}  {'x_{n-1}':>13}  {'x_n':>13}  {'x_{n+1}':>13}  {'f(x_{n+1})':>13}  {'|Δx|':>10}")
        print("  " + SEP2)

        for it in range(1, max_iter + 1):
            f0, f1 = f(x0), f(x1)
            den = f1 - f0
            if abs(den) < 1e-14:
                print("  División por cero.")
                break
            x2  = x1 - f1 * (x1 - x0) / den
            err = abs(x2 - x1)
            print(f"  {it:>4}  {x0:>13.7f}  {x1:>13.7f}  {x2:>13.7f}  {f(x2):>13.6f}  {err:>10.2e}")
            x0, x1 = x1, x2
            if err < tol:
                break

        print(f"\n  ► RESULTADO: raíz ≈ {x1:.8f},  f(raíz) = {f(x1):.2e}")
        return x1

    # ─────────────────────────────────────────────────────────────
    # 11. PUNTO FIJO
    # ─────────────────────────────────────────────────────────────

    def resolver_punto_fijo(self, tol=1e-6, max_iter=80):
        print(SEP)
        print("MÉTODO: PUNTO FIJO")
        print(SEP)
        ops = [
            {"str_f": "e^(-x) - x",  "str_g": "e^(-x)",      "g": lambda x: math.exp(-x),   "x0": 0.5},
            {"str_f": "cos(x) - x",  "str_g": "cos(x)",       "g": lambda x: math.cos(x),    "x0": 0.7},
            {"str_f": "x³ - x - 1",  "str_g": "(x+1)^(1/3)", "g": lambda x: (x+1)**(1/3),   "x0": 1.5},
        ]
        op = random.choice(ops)
        g, x = op["g"], op["x0"]

        print(f"\n  f(x) = {op['str_f']}")
        print(f"  Transformación: x = g(x) = {op['str_g']}")
        print(f"  Valor inicial: x₀ = {x}\n")
        print(f"  {'Iter':>4}  {'x_n':>14}  {'g(x_n)':>14}  {'|Δx|':>12}")
        print("  " + SEP2)

        for it in range(1, max_iter + 1):
            x_new = g(x)
            err   = abs(x_new - x)
            print(f"  {it:>4}  {x:>14.8f}  {x_new:>14.8f}  {err:>12.2e}")
            x = x_new
            if err < tol:
                break

        print(f"\n  ► RESULTADO: punto fijo ≈ {x:.8f},  |g(x)-x| = {abs(g(x)-x):.2e}")
        return x

    # ─────────────────────────────────────────────────────────────
    # helper integración
    # ─────────────────────────────────────────────────────────────

    def _funcion_integracion(self):
        ops = [
            {"f": lambda x: 1 - x**2,       "a": 0, "b": 1,         "desc": "1 - x²"},
            {"f": lambda x: x**3 + 2*x,      "a": 0, "b": 2,         "desc": "x³ + 2x"},
            {"f": lambda x: math.sin(x),      "a": 0, "b": math.pi,   "desc": "sin(x)"},
            {"f": lambda x: math.exp(x),      "a": 0, "b": 1,         "desc": "eˣ"},
            {"f": lambda x: math.cos(x),      "a": 0, "b": math.pi/2, "desc": "cos(x)"},
            {"f": lambda x: 1/(1 + x**2),     "a": 0, "b": 1,         "desc": "1/(1+x²)"},
        ]
        return random.choice(ops)

    # ─────────────────────────────────────────────────────────────
    # 12. REGLA TRAPEZOIDAL
    # ─────────────────────────────────────────────────────────────

    def resolver_trapezoidal(self):
        n = random.choice([2, 4, 6])
        print(SEP)
        print(f"MÉTODO: REGLA TRAPEZOIDAL  (n = {n})")
        print(SEP)
        fn = self._funcion_integracion()
        f, a, b, desc = fn["f"], fn["a"], fn["b"], fn["desc"]
        h = (b - a) / n

        print(f"\n  ∫ f(x) dx,   f(x) = {desc}")
        print(f"  Límites: [{a}, {b:.4f}],  n = {n},  h = (b-a)/n = {h:.4f}\n")
        print(f"  Fórmula: (h/2)·[f(x₀) + 2f(x₁) + ... + 2f(xₙ₋₁) + f(xₙ)]\n")
        print(f"  {'i':>3}  {'x_i':>10}  {'f(x_i)':>12}  {'coef':>5}  {'término':>12}")
        print("  " + SEP2)

        suma = 0.0
        for i in range(n + 1):
            xi   = a + i * h
            fi   = f(xi)
            coef = 1 if (i == 0 or i == n) else 2
            suma += coef * fi
            print(f"  {i:>3}  {xi:>10.4f}  {fi:>12.6f}  {coef:>5}  {coef*fi:>12.6f}")

        res = (h / 2) * suma
        print(f"\n  Suma ponderada = {suma:.6f}")
        print(f"  Resultado = (h/2)·Suma = ({h:.4f}/2)·{suma:.6f} = {res:.6f}")
        print(f"\n  ► RESULTADO: ∫f(x)dx ≈ {res:.6f}")
        return res

    # ─────────────────────────────────────────────────────────────
    # 13. REGLA DE 1/3 DE SIMPSON
    # ─────────────────────────────────────────────────────────────

    def resolver_simpson13(self):
        n = random.choice([2, 4, 6])
        print(SEP)
        print(f"MÉTODO: REGLA DE 1/3 DE SIMPSON  (n = {n}, par)")
        print(SEP)
        fn = self._funcion_integracion()
        f, a, b, desc = fn["f"], fn["a"], fn["b"], fn["desc"]
        h = (b - a) / n

        print(f"\n  ∫ f(x) dx,   f(x) = {desc}")
        print(f"  Límites: [{a}, {b:.4f}],  n = {n},  h = {h:.4f}\n")
        print(f"  Fórmula: (h/3)·[f(x₀) + 4f(x₁) + 2f(x₂) + 4f(x₃) + ... + f(xₙ)]\n")
        print(f"  {'i':>3}  {'x_i':>10}  {'f(x_i)':>12}  {'coef':>5}  {'término':>12}")
        print("  " + SEP2)

        suma = 0.0
        for i in range(n + 1):
            xi   = a + i * h
            fi   = f(xi)
            if i == 0 or i == n:
                coef = 1
            elif i % 2 == 1:
                coef = 4
            else:
                coef = 2
            suma += coef * fi
            print(f"  {i:>3}  {xi:>10.4f}  {fi:>12.6f}  {coef:>5}  {coef*fi:>12.6f}")

        res = (h / 3) * suma
        print(f"\n  Suma ponderada = {suma:.6f}")
        print(f"  Resultado = (h/3)·Suma = ({h:.4f}/3)·{suma:.6f} = {res:.6f}")
        print(f"\n  ► RESULTADO: ∫f(x)dx ≈ {res:.6f}")
        return res

    # ─────────────────────────────────────────────────────────────
    # 14. REGLA DE 3/8 DE SIMPSON
    # ─────────────────────────────────────────────────────────────

    def resolver_simpson38(self):
        n = random.choice([3, 6, 9])
        print(SEP)
        print(f"MÉTODO: REGLA DE 3/8 DE SIMPSON  (n = {n}, múltiplo de 3)")
        print(SEP)
        fn = self._funcion_integracion()
        f, a, b, desc = fn["f"], fn["a"], fn["b"], fn["desc"]
        h = (b - a) / n

        print(f"\n  ∫ f(x) dx,   f(x) = {desc}")
        print(f"  Límites: [{a}, {b:.4f}],  n = {n},  h = {h:.4f}\n")
        print(f"  Fórmula: (3h/8)·[f(x₀) + 3f(x₁) + 3f(x₂) + 2f(x₃) + ... + f(xₙ)]\n")
        print(f"  {'i':>3}  {'x_i':>10}  {'f(x_i)':>12}  {'coef':>5}  {'término':>12}")
        print("  " + SEP2)

        suma = 0.0
        for i in range(n + 1):
            xi   = a + i * h
            fi   = f(xi)
            if i == 0 or i == n:
                coef = 1
            elif i % 3 == 0:
                coef = 2
            else:
                coef = 3
            suma += coef * fi
            print(f"  {i:>3}  {xi:>10.4f}  {fi:>12.6f}  {coef:>5}  {coef*fi:>12.6f}")

        res = (3 * h / 8) * suma
        print(f"\n  Suma ponderada = {suma:.6f}")
        print(f"  Resultado = (3h/8)·Suma = (3·{h:.4f}/8)·{suma:.6f} = {res:.6f}")
        print(f"\n  ► RESULTADO: ∫f(x)dx ≈ {res:.6f}")
        return res

    # ─────────────────────────────────────────────────────────────
    # 15. EDO  (Euler modificado, RK2, RK3, RK4)
    # ─────────────────────────────────────────────────────────────

    def resolver_edo(self, metodo=None):
        if metodo is None:
            metodo = random.choice([
                "Euler modificado",
                "Runge-Kutta de 2° orden",
                "Runge-Kutta de 3° orden",
                "Runge-Kutta de 4° orden",
            ])
        print(SEP)
        print(f"MÉTODO: {metodo.upper()}")
        print(SEP)

        ejs = [
            {"desc": "2x",    "f": lambda x, y: 2*x,    "x0": 0.0, "y0": 1.0},
            {"desc": "y",     "f": lambda x, y: y,       "x0": 0.0, "y0": 1.0},
            {"desc": "x + y", "f": lambda x, y: x + y,  "x0": 0.0, "y0": 0.0},
        ]
        ej = random.choice(ejs)
        f, x, y = ej["f"], ej["x0"], ej["y0"]
        h = random.choice([0.1, 0.2, 0.25])
        n = random.randint(3, 5)

        print(f"\n  EDO:  y' = {ej['desc']},   y({x}) = {y}")
        print(f"  Paso h = {h},   {n} iteraciones\n")

        for step in range(1, n + 1):
            print(f"  ── Paso {step}:  x = {x:.4f},  y = {y:.8f}")
            if metodo == "Euler modificado":
                k1    = f(x, y)
                y_p   = y + h * k1
                k2    = f(x + h, y_p)
                y_new = y + (h/2) * (k1 + k2)
                print(f"     k1 = f({x:.4f}, {y:.6f}) = {k1:.8f}")
                print(f"     ŷ  = y + h·k1            = {y_p:.8f}")
                print(f"     k2 = f({x+h:.4f}, {y_p:.6f}) = {k2:.8f}")
                print(f"     y_new = y + (h/2)·(k1+k2) = {y:.6f} + ({h}/2)·({k1:.6f}+{k2:.6f}) = {y_new:.8f}")
            elif metodo == "Runge-Kutta de 2° orden":
                k1    = f(x, y)
                k2    = f(x + h/2, y + (h/2)*k1)
                y_new = y + h * k2
                print(f"     k1 = f({x:.4f}, {y:.6f})       = {k1:.8f}")
                print(f"     k2 = f({x+h/2:.4f}, {y+(h/2)*k1:.6f}) = {k2:.8f}")
                print(f"     y_new = y + h·k2               = {y_new:.8f}")
            elif metodo == "Runge-Kutta de 3° orden":
                k1    = f(x,       y)
                k2    = f(x + h/2, y + (h/2)*k1)
                k3    = f(x + h,   y - h*k1 + 2*h*k2)
                y_new = y + (h/6)*(k1 + 4*k2 + k3)
                print(f"     k1 = {k1:.8f}")
                print(f"     k2 = {k2:.8f}")
                print(f"     k3 = {k3:.8f}")
                print(f"     y_new = y + (h/6)·(k1 + 4k2 + k3) = {y_new:.8f}")
            else:  # RK4
                k1    = f(x,       y)
                k2    = f(x + h/2, y + (h/2)*k1)
                k3    = f(x + h/2, y + (h/2)*k2)
                k4    = f(x + h,   y +  h   *k3)
                y_new = y + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
                print(f"     k1 = f({x:.4f},   {y:.6f})       = {k1:.8f}")
                print(f"     k2 = f({x+h/2:.4f}, {y+(h/2)*k1:.6f}) = {k2:.8f}")
                print(f"     k3 = f({x+h/2:.4f}, {y+(h/2)*k2:.6f}) = {k3:.8f}")
                print(f"     k4 = f({x+h:.4f},   {y+h*k3:.6f})   = {k4:.8f}")
                print(f"     y_new = y + (h/6)·(k1+2k2+2k3+k4) = {y_new:.8f}")
            x += h
            y  = y_new
            print()

        print(f"  ► RESULTADO: y({x:.4f}) ≈ {y:.8f}")
        return y

    # ─────────────────────────────────────────────────────────────
    # 16. MÍNIMOS CUADRADOS
    # ─────────────────────────────────────────────────────────────

    def resolver_minimos_cuadrados(self, metodo=None):
        if metodo is None:
            metodo = random.choice([
                "Mínimos cuadrados lineal",
                "Mínimos cuadrados cuadrático",
                "Mínimos cuadrados cúbico",
            ])
        grado = 1 if "lineal" in metodo else (2 if "cuadrático" in metodo else 3)
        print(SEP)
        print(f"MÉTODO: {metodo.upper()}")
        print(SEP)

        coef_real = [random.uniform(-2, 2) for _ in range(grado + 1)]
        p_real    = lambda x: sum(coef_real[i] * x**(grado-i) for i in range(grado+1))
        xs = [round(random.uniform(-3, 3), 3) for _ in range(max(5, grado + 3))]
        ys = [round(p_real(x) + random.uniform(-0.3, 0.3), 3) for x in xs]
        x_obj = round(random.uniform(-2, 2), 3)

        print(f"\n  Datos experimentales ({len(xs)} puntos):")
        for xi, yi in zip(xs, ys):
            print(f"    ({xi:>7.3f},  {yi:>8.3f})")
        print(f"\n  Objetivo: ajustar polinomio de grado {grado} y estimar y({x_obj})\n")

        # Ecuaciones normales
        m   = grado + 1
        An  = [[sum(xi**(i+j) for xi in xs) for j in range(m)] for i in range(m)]
        bn_ = [sum(ys[k] * xs[k]**i for k in range(len(xs))) for i in range(m)]

        print("  Sistema de ecuaciones normales  [A]·{a} = {b}:")
        for i in range(m):
            row = " + ".join(f"{An[i][j]:>10.4f}·a{j}" for j in range(m))
            print(f"    {row} = {bn_[i]:>10.4f}")
        print()

        coef_aj = np.polyfit(xs, ys, grado)
        print("  Coeficientes del polinomio ajustado (mayor grado primero):")
        for i, c in enumerate(coef_aj):
            print(f"    a_{grado-i} = {c:>10.6f}")

        y_obj = np.polyval(coef_aj, x_obj)
        print(f"\n  Evaluación en x = {x_obj}:")
        terminos = " + ".join(f"{coef_aj[i]:.4f}·({x_obj})^{grado-i}" for i in range(m))
        print(f"    y = {terminos}")
        print(f"    y = {y_obj:.6f}")
        print(f"\n  ► RESULTADO: y({x_obj}) ≈ {y_obj:.6f}")
        return y_obj

    # ─────────────────────────────────────────────────────────────
    # helper puntos de interpolación
    # ─────────────────────────────────────────────────────────────

    def _puntos_interp(self, n=4, equi=False):
        c = [random.uniform(-1, 1) for _ in range(3)]
        f = lambda x: c[0]*x**2 + c[1]*x + c[2]
        if equi:
            xs = list(range(1, n + 1))
        else:
            xs = sorted(random.sample(range(-5, 6), n))
        puntos = [(x, round(f(x) + random.uniform(-0.05, 0.05), 4)) for x in xs]
        x_obj  = xs[0] + (xs[-1] - xs[0]) * random.uniform(0.2, 0.8)
        return puntos, round(x_obj, 2)

    # ─────────────────────────────────────────────────────────────
    # 17. LAGRANGE
    # ─────────────────────────────────────────────────────────────

    def resolver_lagrange(self):
        print(SEP)
        print("MÉTODO: INTERPOLACIÓN DE LAGRANGE")
        print(SEP)
        puntos, x_obj = self._puntos_interp(n=4, equi=False)
        n = len(puntos)

        print(f"\n  Puntos conocidos:")
        for xi, yi in puntos:
            print(f"    ({xi:>5},  {yi:.4f})")
        print(f"\n  Interpolar en  x = {x_obj}\n")
        print(f"  Fórmula: P(x) = Σ yᵢ · Lᵢ(x),   donde  Lᵢ(x) = ∏_{{j≠i}} (x-xⱼ)/(xᵢ-xⱼ)\n")

        res = 0.0
        for i in range(n):
            xi, yi = puntos[i]
            Li = 1.0
            num_parts = []
            den_parts = []
            for j in range(n):
                if i != j:
                    xj = puntos[j][0]
                    Li *= (x_obj - xj) / (xi - xj)
                    num_parts.append(f"({x_obj}-{xj})")
                    den_parts.append(f"({xi}-{xj})")
            term = yi * Li
            res += term
            print(f"  L_{i}(x) = {'·'.join(num_parts)} / {'·'.join(den_parts)}")
            print(f"           = {Li:.6f}")
            print(f"  Término_{i} = {yi:.4f} × {Li:.6f} = {term:.6f}\n")

        print(f"  P({x_obj}) = {res:.6f}")
        print(f"\n  ► RESULTADO: P({x_obj}) ≈ {res:.6f}")
        return res

    # ─────────────────────────────────────────────────────────────
    # 18. DIFERENCIAS DIVIDIDAS (Newton)
    # ─────────────────────────────────────────────────────────────

    def resolver_diferencias_divididas(self):
        print(SEP)
        print("MÉTODO: DIFERENCIAS DIVIDIDAS (Newton)")
        print(SEP)
        puntos, x_obj = self._puntos_interp(n=4, equi=False)
        puntos = sorted(puntos)
        n = len(puntos)

        print(f"\n  Puntos conocidos:")
        for xi, yi in puntos:
            print(f"    ({xi:>5},  {yi:.4f})")
        print(f"\n  Interpolar en  x = {x_obj}\n")

        # Tabla
        tabla = [[0.0]*n for _ in range(n)]
        for i in range(n):
            tabla[i][0] = puntos[i][1]
        for j in range(1, n):
            for i in range(n - j):
                tabla[i][j] = (tabla[i+1][j-1] - tabla[i][j-1]) / (puntos[i+j][0] - puntos[i][0])

        print("  Tabla de diferencias divididas:")
        encabezado = f"  {'x':>5}  {'f[x]':>10}" + "".join(f"  {'Ord-'+str(k):>12}" for k in range(1, n))
        print(encabezado)
        print("  " + SEP2)
        for i in range(n):
            fila = f"  {puntos[i][0]:>5}  {tabla[i][0]:>10.4f}"
            for j in range(1, n - i):
                fila += f"  {tabla[i][j]:>12.6f}"
            print(fila)

        coefs = [tabla[0][j] for j in range(n)]
        print(f"\n  Coeficientes: {[f'{c:.4f}' for c in coefs]}\n")
        print(f"  P(x) = {coefs[0]:.4f}", end="")
        prod_str = ""
        for i in range(1, n):
            prod_str += f"(x-{puntos[i-1][0]})"
            print(f" + {coefs[i]:.4f}·{prod_str}", end="")
        print("\n")

        # Evaluar
        res     = coefs[0]
        prod    = 1.0
        detalle = [f"f[x₀] = {coefs[0]:.6f}"]
        for i in range(1, n):
            prod *= (x_obj - puntos[i-1][0])
            term  = coefs[i] * prod
            res  += term
            detalle.append(f"+ {coefs[i]:.4f}·{prod:.4f} = {term:.6f}")
        for d in detalle:
            print(f"    {d}")
        print(f"\n  ► RESULTADO: P({x_obj}) ≈ {res:.6f}")
        return res

    # ─────────────────────────────────────────────────────────────
    # 19. NEWTON HACIA ADELANTE
    # ─────────────────────────────────────────────────────────────

    def resolver_newton_adelante(self):
        print(SEP)
        print("MÉTODO: INTERPOLACIÓN DE NEWTON HACIA ADELANTE")
        print(SEP)
        puntos, _ = self._puntos_interp(n=random.randint(3, 5), equi=True)
        puntos = sorted(puntos)
        n  = len(puntos)
        h  = puntos[1][0] - puntos[0][0]
        x0 = puntos[0][0]
        # x_obj cerca del inicio
        x_obj = x0 + h * random.uniform(0.3, 1.8)

        s = (x_obj - x0) / h

        print(f"\n  Puntos equiespaciados (h = {h}):")
        for xi, yi in puntos:
            print(f"    ({xi:.1f},  {yi:.4f})")
        print(f"\n  Interpolar en  x = {x_obj:.3f},   s = (x-x₀)/h = {s:.4f}\n")

        tabla = self.mc.calcular_diferencias_finitas(puntos)

        print("  Tabla de diferencias finitas (Δ):")
        header = f"  {'i':>2}  {'x_i':>6}  {'y_i':>8}" + "".join(f"  {'Δ^'+str(k)+'y':>10}" for k in range(1, n))
        print(header)
        print("  " + SEP2)
        for i in range(n):
            fila = f"  {i:>2}  {puntos[i][0]:>6.1f}  {tabla[i][0]:>8.4f}"
            for j in range(1, n - i):
                fila += f"  {tabla[i][j]:>10.4f}"
            print(fila)

        print(f"\n  Fórmula: P(x) = y₀ + s·Δy₀ + s(s-1)/2!·Δ²y₀ + ...\n")
        res  = puntos[0][1]
        prod = 1.0
        print(f"    Término 0: y₀                     = {res:.6f}")
        for i in range(1, n):
            prod *= (s - (i - 1)) / i
            term  = tabla[0][i] * prod
            res  += term
            print(f"    Término {i}: [s(s-1)…/(i!)]·Δ^{i}y₀ = {prod:.4f} × {tabla[0][i]:.4f} = {term:.6f}")

        print(f"\n  ► RESULTADO: P({x_obj:.3f}) ≈ {res:.6f}")
        return res

    # ─────────────────────────────────────────────────────────────
    # 20. NEWTON HACIA ATRÁS
    # ─────────────────────────────────────────────────────────────

    def resolver_newton_atras(self):
        print(SEP)
        print("MÉTODO: INTERPOLACIÓN DE NEWTON HACIA ATRÁS")
        print(SEP)
        puntos, _ = self._puntos_interp(n=random.randint(3, 5), equi=True)
        puntos = sorted(puntos)
        n  = len(puntos)
        h  = puntos[1][0] - puntos[0][0]
        xn = puntos[-1][0]
        # x_obj cerca del final
        x_obj = xn - h * random.uniform(0.3, 1.8)

        s = (x_obj - xn) / h

        print(f"\n  Puntos equiespaciados (h = {h}):")
        for xi, yi in puntos:
            print(f"    ({xi:.1f},  {yi:.4f})")
        print(f"\n  Interpolar en  x = {x_obj:.3f},   s = (x-xₙ)/h = {s:.4f}\n")

        tabla = self.mc.calcular_diferencias_finitas(puntos)

        print("  Tabla de diferencias finitas (∇):")
        for i in range(n):
            fila = f"  {puntos[i][0]:>5.1f}: " + "  ".join(f"{tabla[i][j]:>9.4f}" for j in range(n - i))
            print(fila)

        print(f"\n  Fórmula: P(x) = yₙ + s·∇yₙ + s(s+1)/2!·∇²yₙ + ...\n")
        res  = puntos[-1][1]
        prod = 1.0
        print(f"    Término 0: yₙ                     = {res:.6f}")
        for i in range(1, n):
            prod *= (s + (i - 1)) / i
            term  = tabla[n-i-1][i] * prod
            res  += term
            print(f"    Término {i}: [s(s+1)…/(i!)]·∇^{i}yₙ = {prod:.4f} × {tabla[n-i-1][i]:.4f} = {term:.6f}")

        print(f"\n  ► RESULTADO: P({x_obj:.3f}) ≈ {res:.6f}")
        return res


# ─────────────────────────────────────────────────────────────────
# MENÚ DE DEMOSTRACIÓN
# ─────────────────────────────────────────────────────────────────

METODOS = [
    # nombre legible                       función
    ("Interpolación lineal",               "resolver_interpolacion_lineal"),
    ("Eliminación Gaussiana",              "resolver_eliminacion_gaussiana"),
    ("Gauss-Jordan",                       "resolver_gauss_jordan"),
    ("Montante",                           "resolver_montante"),
    ("Jacobi",                             "resolver_jacobi"),
    ("Gauss-Seidel",                       "resolver_gauss_seidel"),
    ("Bisección",                          "resolver_biseccion"),
    ("Falsa Posición",                     "resolver_falsa_posicion"),
    ("Newton-Raphson",                     "resolver_newton_raphson"),
    ("Secante",                            "resolver_secante"),
    ("Punto Fijo",                         "resolver_punto_fijo"),
    ("Regla Trapezoidal",                  "resolver_trapezoidal"),
    ("Regla 1/3 de Simpson",               "resolver_simpson13"),
    ("Regla 3/8 de Simpson",               "resolver_simpson38"),
    ("EDO - Euler modificado",             None),   # se llama con parámetro
    ("EDO - Runge-Kutta 2°",               None),
    ("EDO - Runge-Kutta 3°",               None),
    ("EDO - Runge-Kutta 4°",               None),
    ("Mínimos cuadrados lineal",           None),
    ("Mínimos cuadrados cuadrático",       None),
    ("Mínimos cuadrados cúbico",           None),
    ("Lagrange",                           "resolver_lagrange"),
    ("Diferencias divididas",              "resolver_diferencias_divididas"),
    ("Newton hacia adelante",              "resolver_newton_adelante"),
    ("Newton hacia atrás",                 "resolver_newton_atras"),
]

_EDO_MAP = {
    "EDO - Euler modificado":  "Euler modificado",
    "EDO - Runge-Kutta 2°":    "Runge-Kutta de 2° orden",
    "EDO - Runge-Kutta 3°":    "Runge-Kutta de 3° orden",
    "EDO - Runge-Kutta 4°":    "Runge-Kutta de 4° orden",
}
_MC_MAP = {
    "Mínimos cuadrados lineal":      "Mínimos cuadrados lineal",
    "Mínimos cuadrados cuadrático":  "Mínimos cuadrados cuadrático",
    "Mínimos cuadrados cúbico":      "Mínimos cuadrados cúbico",
}


def _llamar(sol, nombre, fn_name):
    if nombre in _EDO_MAP:
        sol.resolver_edo(_EDO_MAP[nombre])
    elif nombre in _MC_MAP:
        sol.resolver_minimos_cuadrados(_MC_MAP[nombre])
    else:
        getattr(sol, fn_name)()


def menu_interactivo():
    sol = Solucionador()
    while True:
        print("\n" + SEP)
        print("  SOLUCIONADOR DE MÉTODOS NUMÉRICOS")
        print(SEP)
        for idx, (nombre, _) in enumerate(METODOS, 1):
            print(f"  {idx:>2}. {nombre}")
        print(f"  {'0':>2}. Salir")
        print(SEP2)
        opcion = input("  Elige un método (número): ").strip()
        if opcion == "0":
            print("  Hasta luego.")
            break
        if not opcion.isdigit() or not (1 <= int(opcion) <= len(METODOS)):
            print("  Opción no válida.")
            continue
        nombre, fn_name = METODOS[int(opcion) - 1]
        print()
        try:
            _llamar(sol, nombre, fn_name)
        except Exception as e:
            print(f"  [Error al ejecutar {nombre}: {e}]")
        input("\n  Presiona Enter para continuar...")


def demo_todos():
    """Ejecuta todos los métodos en secuencia (sin interacción)."""
    sol = Solucionador()
    for nombre, fn_name in METODOS:
        try:
            _llamar(sol, nombre, fn_name)
        except Exception as e:
            print(f"\n  [Error en {nombre}: {e}]")
        print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_todos()
    else:
        menu_interactivo()
