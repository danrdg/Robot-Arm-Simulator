"""
jacobiano.py
------------
Módulo para calcular el Jacobiano geométrico de un brazo robot.

El Jacobiano relaciona las velocidades articulares (dq/dt) con las velocidades del efector final (velocidad lineal y angular). 
Es una matriz de 6 x n donde:
    - 6 filas -> 3 componentes de velocidad lineal (vx, vy, vz) + 3 componentes de velocidad angular (wx, wy, wz)
    - n columnas -> una por cada articulación (grado de libertad)
"""

import numpy as np
from typing import List

from .brazo_robot import BrazoRobot
from .articulacion import Articulacion


def calcular_jacobiano(
    brazo_robot : BrazoRobot,
    matrices : List[np.ndarray]
) -> np.ndarray:
    """
    Calcula el Jacobiano geométrico de 6xn del brazo robot.

    Parámetros:
        brazo_robot (BrazoRobot) : El brazo robot con sus articulaciones.
        matrices (List[np.ndarray]) : Lista de matrices de transformación obtenidas con calcular_cinematica_directa().
        Debe incluir la matriz correspondiente a la base (matrices[0]).

    Devuelve:
        np.ndarray: Matriz Jacobiana de tamaño (6xn), donde n es el número de grados de libertad del robot.

    Lanza:
        ValueError: Si la cantidad de matrices no coincide con las articulaciones + 1.

    """
    numero_gdl = brazo_robot.grados_de_libertad

    # Verificar que las matrices sean consistentes con el robot
    matrices_esperadas = numero_gdl + 1  # +1 porque la matriz 0 es la base
    if len(matrices) != matrices_esperadas:
        raise ValueError(
            f"Se esperaban {matrices_esperadas} matrices (base + {numero_gdl} articulaciones), "
            f"pero se recibieron {len(matrices)}."
        )

    # Inicializar la matriz Jacobiana con ceros (6 filas × n columnas)
    jacobiano = np.zeros((6,numero_gdl))

    # Posición del efector final: últimas 3 filas de la columna 3 de la matriz final
    posicion_efector = matrices[-1][0:3, 3]

    # Calcular cada columna del Jacobiano
    for i in range(numero_gdl):
        articulacion = brazo_robot.articulaciones[i]

        # La matriz anterior a la articulación i es matrices[i]
        matriz_anterior = matrices[i]

        # Eje Z de la matriz anterior (tercera columna de la rotación)
        eje_z = matriz_anterior[0:3, 2]

        # Posición de la matriz anterior
        posicion_anterior = matriz_anterior[0:3, 3]

        # Calcular columna según tipo de articulación
        if articulacion.tipo == Articulacion.TIPO_ROTATORIA:
            # Diferencia de posición: desde la matriz i-1 hasta el efector final
            diferencia_posicion = posicion_efector - posicion_anterior

            # Parte lineal: producto cruzado de z_{i-1} x (p_n - p_{i-1})
            parte_lineal = np.cross(eje_z, diferencia_posicion)

            # Parte angular: simplemente el eje Z
            parte_angular = eje_z

        else:
            # Articulación PRISMÁTICA
            # Parte lineal: el eje Z de la matriz anterior
            parte_lineal = eje_z

            # Parte angular: cero (traslación pura, sin rotación)
            parte_angular = np.zeros(3)

        # Ensamblar la columna i del Jacobiano
        # Filas 0-2: velocidad lineal
        # Filas 3-5: velocidad angular
        jacobiano[0:3, i] = parte_lineal
        jacobiano[3:6, i] = parte_angular

    return jacobiano


def calcular_jacobiano_posicion(jacobiano_completo: np.ndarray) -> np.ndarray:
    """
    Extrae solo la parte de posición (velocidad lineal) del Jacobiano completo.
    Esta submatriz de 3xn relaciona velocidades articulares con velocidad lineal del efector.

    Parámetros:
        jacobiano_completo (np.ndarray): Jacobiano completo de tamaño (6 x n).

    Devuelve:
        np.ndarray: Submatriz de posición de tamaño (3 x n).
    """
    # Las primeras 3 filas son la parte de velocidad lineal
    return jacobiano_completo[0:3, :]


def calcular_pseudoinversa(matriz: np.ndarray, umbral: float = 1e-10) -> np.ndarray:
    """
    Calcula la pseudoinversa de Moore-Penrose de una matriz usando SVD (Descomposición en Valores Singulares).

    Parámetros:
        matriz (np.ndarray): Matriz de entrada de tamaño (m x n).
        umbral (float): Valores singulares por debajo de este umbral
                        se tratan como cero (evita divisiones por casi-cero).

    Devuelve:
        np.ndarray: Pseudoinversa de la matriz de tamaño (n x m).
    """
    # np.linalg.pinv ya implementa la pseudoinversa con SVD internamente
    pseudoinversa = np.linalg.pinv(matriz, rcond=umbral)
    return pseudoinversa


def imprimir_jacobiano(jacobiano: np.ndarray) -> None:
    """
    Muestra el Jacobiano de forma legible en la consola.

    Parámetros:
        jacobiano (np.ndarray): Matriz Jacobiana de tamaño (6 x n).
    """
    filas, columnas = jacobiano.shape
    etiquetas_filas = ["vx", "vy", "vz", "wx", "wy", "wz"]

    print("\n" + "=" * 55)
    print("  JACOBIANO GEOMÉTRICO")
    print(f"  Dimensiones: {filas} × {columnas}")
    print("=" * 55)

    for i in range(filas):
        etiqueta = etiquetas_filas[i] if i < len(etiquetas_filas) else f"f{i}"
        valores = "   ".join(f"{v:8.4f}" for v in jacobiano[i, :])
        print(f"  {etiqueta} | {valores}")

    print("=" * 55)
