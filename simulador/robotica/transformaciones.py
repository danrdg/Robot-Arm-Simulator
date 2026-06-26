"""
transformaciones.py
-------------------
Módulo con matrices de transformación homogénea básicas (rotación y traslación).
Cada función devuelve una matriz numpy de 4x4.
"""

import numpy as np


def identidad() -> np.ndarray:
    """
    Devuelve la matriz identidad de 4x4.
    """
    return np.eye(4)


def rotacion_x(angulo: float) -> np.ndarray:
    """
    Crea una matriz de rotación homogénea alrededor del eje X.

    Parámetros:
        angulo (float): Ángulo de rotación en radianes.

    Devuelve:
        np.ndarray: Matriz de rotación 4x4 alrededor del eje X.
    """

    c = np.cos(angulo) 
    s = np.sin(angulo)

    matriz = np.array([
        [1,0,0,0],
        [0,c,-s,0],
        [0,s,c,0],
        [0,0,0,1]
    ], dtype=float)

    return matriz



def rotacion_z(angulo: float) -> np.ndarray:
    """
    Crea una matriz de rotación homogénea alrededor del eje Z.

    Parámetros:
        angulo (float): Ángulo de rotación en radianes.

    Devuelve:
        np.ndarray: Matriz de rotación 4x4 alrededor del eje Z.
    """
    c = np.cos(angulo)
    s = np.sin(angulo)

    matriz = np.array([
        [c,-s,0,0],
        [s,c,0,0],
        [0,0,1,0],
        [0,0,0,1]
    ], dtype=float)

    return matriz


def traslacion_x(distancia: float) -> np.ndarray:
    """
    Crea una matriz de traslación homogénea a lo largo del eje X.

    Parámetros:
        distancia (float): Distancia de traslación en el eje X.

    Devuelve:
        np.ndarray: Matriz de traslación 4x4 en el eje X.
    """
    matriz = np.eye(4)
    matriz[0, 3] = distancia  # posición X en la última columna
    return matriz




def traslacion_z(distancia: float) -> np.ndarray:
    """
    Crea una matriz de traslación homogénea a lo largo del eje Z.

    Parámetros:
        distancia (float): Distancia de traslación en el eje Z.

    Devuelve:
        np.ndarray: Matriz de traslación 4x4 en el eje Z.
    """
    matriz = np.eye(4)
    matriz[2, 3] = distancia  # posición Z en la última columna
    return matriz
