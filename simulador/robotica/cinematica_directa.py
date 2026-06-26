"""
cinematica_directa.py
---------------------
Módulo para calcular la cinemática directa de un brazo robot.

La cinemática directa permite conocer la posición y orientación del efector final
dado un conjunto de valores articulares. Se calcula multiplicando en cadena
todas las matrices de transformación DH de cada articulación.
"""

import numpy as np
from typing import List

from .brazo_robot import BrazoRobot
from .dh import matriz_dh


def calcular_cinematica_directa(brazo_robot: BrazoRobot) -> List[np.ndarray]:
    """
    Calcula la cinemática directa del brazo robot y devuelve todas las matrices
    de transformación intermedias (desde la base hasta cada articulación).

    Cada matriz representa la posición y orientación acumulada desde la base hasta esa articulación.

    Parámetros:
        brazo_robot (BrazoRobot): El brazo robot con sus articulaciones configuradas.

    Devuelve:
        List[np.ndarray]: Lista de matrices de transformación 4x4.

    """
    # Lista donde se guardan todas las matrices de transformación
    todas_las_matrices = []

    # Matriz 0 correspondiente con la base del robot (sin transformación, es la identidad)
    matriz_base = np.eye(4)
    todas_las_matrices.append(matriz_base)

    # Empezamos desde la matriz de la base y vamos acumulando transformaciones
    matriz_acumulada = matriz_base.copy()

    # Recorrer cada articulación y multiplicar su matriz DH
    for numero, articulacion in enumerate(brazo_robot.articulaciones):

        # Calcular la matriz DH de esta articulación con sus parámetros actuales
        matriz_articulacion = matriz_dh(
            theta = articulacion.theta,
            d = articulacion.d,
            a = articulacion.a,
            alpha = articulacion.alpha
                                       )

        # Acumular la transformación multiplicando con la matriz anterior
        matriz_acumulada = matriz_acumulada @ matriz_articulacion

        # Guardar una copia de la matriz acumulada hasta este punto
        todas_las_matrices.append(matriz_acumulada.copy())

    return todas_las_matrices


def obtener_posicion_efector(matrices: List[np.ndarray]) -> np.ndarray:
    """
    Extrae la posición cartesiana (x,y,z) del efector final a partir de la lista calculada por la cinemática directa.
    La posición está en la última columna de la última matriz de transformación.

    Parámetros:
        matrices (List[np.ndarray]): Lista de matrices devuelta por calcular_cinematica_directa.

    Devuelve:
        np.ndarray: Vector de 3 elementos [x,y,z] con la posición del efector.
    """
    # La última matriz es la transformación total hasta el efector
    matriz_efector = matrices[-1]

    # Las primeras 3 filas de la columna 3 son la posición (x,y,z)
    posicion = matriz_efector[0:3,3]

    return posicion


def obtener_orientacion_efector(matrices: List[np.ndarray]) -> np.ndarray:
    """
    Extrae la matriz de rotación (orientación) del efector final a partir de la lista de matrices de la cinemática directa.

    Parámetros:
        matrices (List[np.ndarray]): Lista de matrices devuelta por calcular_cinematica_directa.

    Devuelve:
        np.ndarray: Matriz de rotación 3x3 del efector final.
    """
    matriz_efector = matrices[-1]

    # Las primeras 3 filas y 3 columnas forman la matriz de rotación
    matriz_rotacion = matriz_efector[0:3, 0:3]

    return matriz_rotacion


def imprimir_resultado_cinematica(matrices: List[np.ndarray]) -> None:
    """
    Muestra en consola los resultados de la cinemática directa de forma legible.

    Parámetros:
        matrices (List[np.ndarray]): Lista de matrices de la cinemática directa.
    """
    print("\n" + "=" * 55)
    print("  RESULTADO DE CINEMÁTICA DIRECTA")
    print("=" * 55)

    numero_articulaciones = len(matrices) - 1  # Matriz 0 es la base

    print(f"  Número de articulaciones: {numero_articulaciones}")

    # Mostrar posición de cada articulación
    print("\n  Posiciones de cada articulación:")
    print("  " + "-" * 40)
    for i, matriz in enumerate(matrices):
        posicion = matriz[0:3, 3]
        if i == 0:
            etiqueta = "Base"
        elif i == numero_articulaciones:
            etiqueta = f"Efector final (Art. {i})"
        else:
            etiqueta = f"Articulación {i}"
        print(f"  {etiqueta:30s}  x={posicion[0]:7.4f}, y={posicion[1]:7.4f}, z={posicion[2]:7.4f}")

    # Mostrar posición y orientación del efector final
    posicion_final    = obtener_posicion_efector(matrices)
    orientacion_final = obtener_orientacion_efector(matrices)

    print("\n  Posición del efector final [x,y,z]:")
    print(f"    x = {posicion_final[0]:.6f}")
    print(f"    y = {posicion_final[1]:.6f}")
    print(f"    z = {posicion_final[2]:.6f}")

    print("\n  Orientación del efector final (Matriz de Rotación 3x3):")
    for fila in orientacion_final:
        print("    " + "  ".join(f"{v:9.4f}" for v in fila))

    print("=" * 55)
