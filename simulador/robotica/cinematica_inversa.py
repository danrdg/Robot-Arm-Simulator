"""
cinematica_inversa.py
---------------------
Módulo para resolver la cinemática inversa de un brazo robot.

La cinemática inversa determina los valores articulares necesarios para que el efector final del robot alcance una posición
objetivo en el espacio cartesiano.

Algoritmo utilizado: Jacobiano Pseudoinverso (método iterativo).

Cada iteración:
    1. Calcular la posición actual del efector (cinemática directa).
    2. Calcular el error: diferencia entre posición objetivo y actual.
    3. Si el error < tolerancia entonces solución encontrada (convergencia).
    4. Calcular el Jacobiano (solo parte de posición, 3xn).
    5. Calcular la pseudoinversa del Jacobiano.
    6. Calcular el incremento articular: dq = J+ x error.
    7. Actualizar las variables articulares: q = q + dq.
    8. Normalizar ángulos al rango [-π, π] (solo articulaciones rotatorias).
    9. Repetir desde el paso 1.
"""

import math
import numpy as np
from typing import List, Optional
from dataclasses import dataclass

from .brazo_robot import BrazoRobot
from .articulacion import Articulacion
from .cinematica_directa import calcular_cinematica_directa, obtener_posicion_efector
from .jacobiano import calcular_jacobiano, calcular_jacobiano_posicion, calcular_pseudoinversa



# Clase de resultado
@dataclass
class ResultadoCinematicaInversa:
    """
    Almacena el resultado de la cinemática inversa.

    Atributos:
        converge (bool) : True si se encontró solución dentro de la tolerancia.
        valores_articulares (List[float]) : Valores articulares de la solución encontrada.
        error_final (float) : Error de posición en la última iteración.
        iteraciones_usadas (int) : Número de iteraciones realizadas.
        historial_error (List[float]) : Lista con el error en cada iteración.
        posicion_alcanzada (np.ndarray) : Posición cartesiana [x,y,z] alcanzada.
        posicion_objetivo (np.ndarray) : Posición cartesiana [x,y,z] objetivo.
    """
    converge : bool
    valores_articulares : List[float]
    error_final : float
    iteraciones_usadas: int
    historial_error : List[float]
    posicion_alcanzada : np.ndarray
    posicion_objetivo : np.ndarray


# Normalizaciones
def _normalizar_angulo(angulo: float) -> float:
    """
    Normaliza un ángulo al rango [-π, π].

    Usa la identidad atan2(sin(θ), cos(θ)) para encontrar el ángulo equivalente
    más cercano al origen, sin alterar la configuración cinemática del robot.

    Parámetros:
        angulo (float): Ángulo en radianes, sin límite de rango.

    Devuelve:
        float: Ángulo equivalente en el rango [-π, π].
    """
    return math.atan2(math.sin(angulo), math.cos(angulo))


PRISMATICA_MIN = 0.2  # límite inferior del rango de articulaciones prismáticas
PRISMATICA_MAX = 1.0  # límite superior del rango de articulaciones prismáticas


def _normalizar_valores_articulares(
    nuevos_valores: List[float],
    articulaciones: list,
                                   ) -> List[float]:
    """
    Aplica la normalización a [-π, π] sobre articulaciones rotatorias y el
    clamping al rango [PRISMATICA_MIN, PRISMATICA_MAX] sobre las prismáticas.

    Parámetros:
        nuevos_valores (List[float]) : Valores articulares tras el incremento.
        articulaciones (list) : Lista de objetos Articulacion del robot, usada para conocer el tipo de cada una.

    Devuelve:
        List[float]: Lista con los valores normalizados/clampados.
    """
    valores_normalizados = []

    for valor, articulacion in zip(nuevos_valores, articulaciones):
        if articulacion.tipo == Articulacion.TIPO_ROTATORIA:
            # Normalizar ángulos rotatorios al rango [-π, π]
            valores_normalizados.append(_normalizar_angulo(valor))
        else:
            # Limitar articulaciones prismáticas al rango [PRISMATICA_MIN, PRISMATICA_MAX]
            valores_normalizados.append(
                float(np.clip(valor, PRISMATICA_MIN, PRISMATICA_MAX))
            )

    return valores_normalizados


def resolver_cinematica_inversa(
    brazo_robot: BrazoRobot,
    objetivo: np.ndarray,
    tolerancia: float = 1e-4,
    max_iteraciones: int   = 1000,
    tasa_aprendizaje: float = 1.0,
    valores_iniciales: Optional[List[float]] = None
                               ) -> ResultadoCinematicaInversa:
    """
    Resuelve la cinemática inversa usando el método del Jacobiano pseudoinverso.

    Encuentra los valores articulares [q1, q2, ..., qn] para que el efector final del robot alcance 
    la posición objetivo [x,y,z].

    Los ángulos de las articulaciones rotatorias se normalizan al rango [-π, π] después de cada actualización,
    los de las prismáticas en el rango [0.2, 2].

    Parámetros:
        brazo_robot (BrazoRobot): Robot con sus articulaciones.
        objetivo (np.ndarray): Vector [x,y,z] de la posición objetivo.
        tolerancia (float): Error máximo aceptable (metros), por defecto: 1e-4.
        max_iteraciones (int): Límite de iteraciones antes de parar. Por defecto: 1000.
        tasa_aprendizaje (float): Factor que escala el paso de actualización. Valores menores hacen la convergencia más
                                  lenta pero más estable. Por defecto: 1.0.
        valores_iniciales (Optional[List[float]]): Configuración articular inicial. Si es None, se usan los valores actuales.

    Devuelve:
        ResultadoCinematicaInversa: Objeto con los resultados, incluyendo si converge, los ángulos solución, 
                                    el error final, etc. Los valores articulares de la solución siempre están 
                                    en el rango los rangos admitidos según sean rotatorias o prismáticas.

    """
    # Guardar los valores articulares originales del robot para poder restaurarlos
    valores_originales = brazo_robot.obtener_variables_articulares()

    # Si se dan valores iniciales, aplicarlos al robot
    if valores_iniciales is not None:
        brazo_robot.establecer_variables_articulares(valores_iniciales)

    # Convertir el objetivo a array numpy
    objetivo = np.array(objetivo, dtype=float)

    # Verificar que el objetivo tenga 3 componentes [x,y,z]
    if objetivo.shape != (3,):
        raise ValueError(
            f"El objetivo debe ser un vector de 3 elementos [x,y,z], "
            f"pero se ha recibido {objetivo.shape}."
        )

    # Lista para guardar el historial del error en cada iteración
    historial_error = []

    # Variables para el bucle
    iteracion_actual = 0
    converger = False
    error_actual = float("inf")

    #  Bucle iterativo
    while iteracion_actual < max_iteraciones:

        # 1. Calcular cinemática directa con la configuración actual
        matrices = calcular_cinematica_directa(brazo_robot)

        # 2. Obtener posición actual del efector final
        posicion_actual = obtener_posicion_efector(matrices)

        # 3. Calcular el error de posición (diferencia vectorial)
        vector_error = objetivo - posicion_actual

        # 4. Calcular la norma (magnitud) del error
        error_actual = float(np.linalg.norm(vector_error))

        # Guardar en el historial
        historial_error.append(error_actual)

        # Avanzar al siguiente ciclo
        iteracion_actual += 1

        # 5. Comprobar si converge
        if error_actual < tolerancia:
            converger = True
            break

        # 6. Calcular el Jacobiano completo (6xn)
        jacobiano_completo = calcular_jacobiano(brazo_robot, matrices)

        # 7. Extraer solo la parte de posición (3×n)
        jacobiano_posicion = calcular_jacobiano_posicion(jacobiano_completo)

        # 8. Calcular la pseudoinversa del Jacobiano de posición (n×3)
        jacobiano_pseudoinverso = calcular_pseudoinversa(jacobiano_posicion)

        # 9. Calcular el incremento articular usando la regla: dq = J+ x error
        incremento_articular = tasa_aprendizaje * (jacobiano_pseudoinverso @ vector_error)

        # 10. Actualizar las variables articulares del robot
        valores_actuales = brazo_robot.obtener_variables_articulares()

        nuevos_valores = [
            valores_actuales[i] + incremento_articular[i]
            for i in range(brazo_robot.grados_de_libertad)
                         ]

        # 11. Normalizar ángulos al rango [-π, π] para articulaciones rotatorias.
        nuevos_valores = _normalizar_valores_articulares(
            nuevos_valores,
            brazo_robot.articulaciones,
        )

        brazo_robot.establecer_variables_articulares(nuevos_valores)

    # Fin del bucle

    # Calcular la posición final alcanzada con la configuración resultante
    matrices_finales = calcular_cinematica_directa(brazo_robot)
    posicion_alcanzada = obtener_posicion_efector(matrices_finales)

    # Guardar los valores articulares de la solución (ya normalizados)
    solucion_articular = brazo_robot.obtener_variables_articulares()

    # Restaurar el robot a su configuración original
    brazo_robot.establecer_variables_articulares(valores_originales)

    # Construir y devolver el objeto de resultado
    resultado = ResultadoCinematicaInversa(
        converge = converger,
        valores_articulares = solucion_articular,
        error_final = error_actual,
        iteraciones_usadas = iteracion_actual,
        historial_error = historial_error,
        posicion_alcanzada  = posicion_alcanzada,
        posicion_objetivo = objetivo
    )

    return resultado



def imprimir_resultado_inversa(resultado: ResultadoCinematicaInversa) -> None:
    """
    Muestra en consola los resultados de la cinemática inversa.

    Parámetros:
        resultado (ResultadoCinematicaInversa): Resultado devuelto por resolver_cinematica_inversa.
    """
    print("\n" + "=" * 55)
    print("  RESULTADO DE CINEMÁTICA INVERSA")
    print("=" * 55)

    estado = "CONVERGE" if resultado.converge else "NO CONVERGE"
    print(f"\n  Estado           : {estado}")
    print(f"  Iteraciones      : {resultado.iteraciones_usadas}")
    print(f"  Error final      : {resultado.error_final:.8f}")

    print("\n  Posición objetivo   : "
          f"x={resultado.posicion_objetivo[0]:.4f}, "
          f"y={resultado.posicion_objetivo[1]:.4f}, "
          f"z={resultado.posicion_objetivo[2]:.4f}")

    print("  Posición alcanzada  : "
          f"x={resultado.posicion_alcanzada[0]:.4f}, "
          f"y={resultado.posicion_alcanzada[1]:.4f}, "
          f"z={resultado.posicion_alcanzada[2]:.4f}")

    print("\n  Valores articulares solución:")
    for i, valor in enumerate(resultado.valores_articulares):
        print(f"    q{i + 1} = {valor:.6f} rad  ({np.degrees(valor):.4f}°)")

    print("=" * 55)