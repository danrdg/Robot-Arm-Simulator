"""
dh.py
-----
Módulo para calcular la matriz de transformación de Denavit-Hartenberg (DH).

La convención DH estándar construye la transformación entre dos eslabones aplicando cuatro pasos en este orden:
    1. Rotar alrededor de Z (ángulo theta)
    2. Traslación a lo largo de Z (distancia d)
    3. Traslación a lo largo de X (longitud a)
    4. Rotar alrededor de X (ángulo alpha)
"""

import numpy as np
from .transformaciones import rotacion_z, traslacion_z, traslacion_x, rotacion_x


def matriz_dh(theta: float, d: float, a: float, alpha: float) -> np.ndarray:
    """
    Calcula la matriz de transformación homogénea usando los parámetros
    de Denavit-Hartenberg (DH) estándar.

    La fórmula es:
        T = Rz(theta) * Tz(d) * Tx(a) * Rx(alpha)

    Parámetros:
        theta (float): Ángulo de rotación alrededor del eje Z (en radianes). Variable articular en articulaciones rotatorias.
        d (float): Desplazamiento a lo largo del eje Z (en la unidad que uses). Variable articular en articulaciones prismáticas.
        a (float): Longitud del eslabón (distancia a lo largo del eje X).
        alpha (float): Ángulo de torsión del eslabón (rotación alrededor de X, radianes).

    Devuelve:
        np.ndarray: Matriz de transformación homogénea 4x4.
    """
    # Paso 1: rotación alrededor de Z el ángulo theta
    paso_1 = rotacion_z(theta)

    # Paso 2: traslación a lo largo de Z la distancia d
    paso_2 = traslacion_z(d)

    # Paso 3: traslación a lo largo de X la longitud del eslabón a
    paso_3 = traslacion_x(a)

    # Paso 4: rotación alrededor de X el ángulo alpha (torsión)
    paso_4 = rotacion_x(alpha)

    # Multiplicar todas las matrices en orden
    matriz_transformacion = paso_1 @ paso_2 @ paso_3 @ paso_4

    return matriz_transformacion


def imprimir_matriz_dh(matriz: np.ndarray, nombre: str = "T") -> None:
    """
    Muestra una matriz de transformación DH de forma legible en la consola.

    Parámetros:
        matriz (np.ndarray): Matriz 4x4 a mostrar.
        nombre (str): Nombre para identificar la matriz.
    """
    print(f"\n  Matriz {nombre}:")
    print("  " + "-" * 44)
    for fila in matriz:
        # Formatear cada número con 6 decimales y alineación fija
        valores_formateados = "  ".join(f"{valor:9.4f}" for valor in fila)
        print(f"  | {valores_formateados} |")
    print("  " + "-" * 44)
