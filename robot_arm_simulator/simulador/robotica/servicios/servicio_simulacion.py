"""
servicio_simulacion.py
----------------------
Capa de servicio que conecta entradas JSON con el motor de cinemática robótica.

"""

import numpy as np
from typing import Any, Dict, List, Optional
from simulador.robotica.articulacion import Articulacion
from simulador.robotica.brazo_robot import BrazoRobot
from simulador.robotica.cinematica_directa import (
    calcular_cinematica_directa as _calcular_cinematica_directa,
    obtener_posicion_efector,
    obtener_orientacion_efector,
)
from simulador.robotica.cinematica_inversa import resolver_cinematica_inversa


# Construcción del robot

def construir_robot(datos_articulaciones: List[Dict[str, Any]]) -> BrazoRobot:
    """
    Construye una instancia de BrazoRobot a partir de una lista de diccionarios que describen cada articulación con 
    sus parámetros Denavit-Hartenberg.

    Parámetros:
        datos_articulaciones (List[Dict[str, Any]]): Lista de diccionarios con la siguiente estructura por articulación:
                {
                    "tipo": "rotatoria" | "prismatica"
                    "theta": float
                    "d": float
                    "a": float
                    "alpha": float
                }

    Devuelve:
        BrazoRobot: Instancia del brazo robot construida con las articulaciones indicadas. El nombre del robot se asigna 
                    automáticamente.

    Lanza:
        KeyError:   Si algún diccionario de articulación omite un campo obligatorio.
        ValueError: Si el tipo de articulación no es válido o el número de articulaciones está fuera del rango permitido (1-6).
        TypeError:  Si algún elemento de la lista no produce una Articulacion válida.
    """
    articulaciones = []

    for indice, datos in enumerate(datos_articulaciones):
        # Extraer cada parámetro DH, se lanza KeyError si falta alguno
        tipo = datos["tipo"]
        theta = float(datos["theta"])
        d = float(datos["d"])
        a = float(datos["a"])
        alpha = float(datos["alpha"])

        articulacion = Articulacion(
            tipo = tipo,
            theta = theta,
            d = d,
            a = a,
            alpha = alpha,
        )
        articulaciones.append(articulacion)

    robot = BrazoRobot(
        nombre = "robot_simulado",
        articulaciones = articulaciones,
    )

    return robot

# Cinemática directa

def calcular_cinematica_directa(datos_robot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula la cinemática directa de un brazo robot descrito en formato JSON.

    Toma la configuración articular actual del robot, calcula todas las matrices de transformación homogénea desde 
    la base hasta el efector final, y devuelve la posición y orientación del efector junto con información adicional del robot.

    Parámetros:
        datos_robot (Dict[str, Any]): Diccionario con la descripción del robot:
            {
                "nombre": str
                "articulaciones": List[Dict]
            }
            Cada articulación sigue el formato descrito en construir_robot().

    Devuelve:
        Dict[str, Any]: Diccionario serializable a JSON con los resultados:
            {
                "exito": True
                "grados_de_libertad": int
                "articulaciones":[x0,y0,z0], [x1,y1,z1], ..., [xn,yn,zn]]
                "posicion_efector":[x, y, z]
                "orientacion_efector": [[r00,r01,r02],[r10,r11,r12],[r20,r21,r22]]
                "matrices":List[List[List[float]]]
                "variables_articulares": [q1, q2, ..., qn]
                "error": null
            }

            articulacioness contiene la posición [x, y, z] de cada matriz de transformación: articulaciones[0] es la base (siempre [0,0,0]),
            articulaciones[1] es la articulación 1, ..., articulaciones[N] es el efector final (coincide con posicion_efector).

            En caso de error:
            {
                "exito": False,
                "error": "descripción del error"
            }
    """
    try:
        # Extraer la lista de articulaciones del diccionario de entrada
        datos_articulaciones = datos_robot["articulaciones"]

        # Construir el brazo robot usando los constructores reales del motor
        robot = construir_robot(datos_articulaciones)

        # Calcular la cinemática directa: devuelve lista de matrices 4x4
        matrices = _calcular_cinematica_directa(robot)

        # Extraer posición y orientación del efector final
        posicion_efector    = obtener_posicion_efector(matrices)
        orientacion_efector = obtener_orientacion_efector(matrices)

        # Obtener los valores articulares actuales
        variables_articulares = robot.obtener_variables_articulares()

        # Convertir todos los arrays NumPy a listas nativas de Python
        matrices_serializables = [
            _convertir_array_a_lista(matriz) for matriz in matrices
        ]

        # Extraer la posición [x, y, z] de cada matriz para el visualizador 3D.
        # articulaciones[0] → base del robot (origen, siempre [0, 0, 0])
        # articulaciones[i] → posición acumulada hasta la articulación i
        # articulaciones[-1] → efector final (idéntico a posicion_efector)
        posiciones_articulaciones = _extraer_posiciones_articulaciones(matrices)

        return {
            "exito": True,
            "grados_de_libertad": robot.grados_de_libertad,
            "articulaciones": posiciones_articulaciones,
            "posicion_efector": _convertir_array_a_lista(posicion_efector),
            "orientacion_efector": _convertir_array_a_lista(orientacion_efector),
            "matrices": matrices_serializables,
            "variables_articulares": _convertir_array_a_lista(variables_articulares),
            "error":                 None,
        }

    except KeyError as e:
        return _respuesta_error(
            f"Falta el campo obligatorio en los datos del robot: {e}"
        )
    except ValueError as e:
        return _respuesta_error(
            f"Error de valor al construir el robot o calcular cinemática directa: {e}"
        )
    except TypeError as e:
        return _respuesta_error(
            f"Error de tipo en los datos de entrada: {e}"
        )
    except Exception as e:
        return _respuesta_error(
            f"Error inesperado al calcular cinemática directa: {e}"
        )


# Cinemática inversa

def calcular_cinematica_inversa(
    datos_robot : Dict[str, Any],
    objetivo : List[float],
    tolerancia  : float = 1e-4,
    max_iteraciones : int   = 1000,
    tasa_aprendizaje : float = 1.0,
    valores_iniciales : Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Resuelve la cinemática inversa de un brazo robot para alcanzar una posición objetivo en el espacio cartesiano.

    Utiliza el método del Jacobiano pseudoinverso de forma iterativa para encontrar los valores articulares [q1, ..., qn] 
    que posicionan el efector final en las coordenadas [x, y, z] indicadas.

    Parámetros:
        datos_robot (Dict[str, Any]): Descripción del robot en el mismo formato
            que calcular_cinematica_directa():
                {
                    "nombre": str
                    "articulaciones": List[Dict]
                }

        objetivo (List[float]): Vector [x, y, z] con la posición cartesiana objetivo que debe alcanzar el efector final.

        tolerancia (float): Error máximo aceptable (en metros) para considerar que la solución ha convergido. Por defecto: 1e-4.

        max_iteraciones (int): Número máximo de iteraciones del algoritmo antes de detenerse aunque no haya convergido. Por defecto: 1000.

        tasa_aprendizaje (float): Factor de escala aplicado al incremento articular en cada iteración. 
                                  Valores menores dan convergencia más lenta pero más estable. Por defecto: 1.0.

        valores_iniciales (Optional[List[float]]): Configuración articular inicial para el algoritmo. Si es None, se usan 
                                                   los valores actuales de las articulaciones del robot.

    Devuelve:
        Dict[str, Any]: Diccionario serializable a JSON con los resultados:
            {
                "exito":True
                "converge": bool
                "valores_articulares": [q1, q2, ..., qn]
                "error_final": float
                "iteraciones_usadas":int
                "historial_error":[float, ...]
                "posicion_alcanzada":[x,y,z]
                "posicion_objetivo": [x,y,z]
                "error":null
            }

            En caso de error:
            {
                "exito": False
                "error": "descripción del error"
            }
    """
    try:
        # Extraer la lista de articulaciones
        datos_articulaciones = datos_robot["articulaciones"]

        # Construir el brazo robot
        robot = construir_robot(datos_articulaciones)

        # Convertir el objetivo a array de NumPy
        objetivo_np = np.array(objetivo, dtype=float)

        # Resolver la cinemática inversa usando el motor de cinemática
        resultado = resolver_cinematica_inversa(
            brazo_robot  = robot,
            objetivo  = objetivo_np,
            tolerancia = tolerancia,
            max_iteraciones = max_iteraciones,
            tasa_aprendizaje = tasa_aprendizaje,
            valores_iniciales = valores_iniciales,
        )

        # Serializar y devolver el resultado
        return {
            "exito":True,
            "converge": resultado.converge,
            "valores_articulares": _convertir_array_a_lista(resultado.valores_articulares),
            "error_final": float(resultado.error_final),
            "iteraciones_usadas": int(resultado.iteraciones_usadas),
            "historial_error": _convertir_array_a_lista(resultado.historial_error),
            "posicion_alcanzada":_convertir_array_a_lista(resultado.posicion_alcanzada),
            "posicion_objetivo": _convertir_array_a_lista(resultado.posicion_objetivo),
            "error": None,
        }

    except KeyError as e:
        return _respuesta_error(
            f"Falta el campo obligatorio en los datos del robot: {e}"
        )
    except ValueError as e:
        return _respuesta_error(
            f"Error de valor al construir el robot o resolver cinemática inversa: {e}"
        )
    except TypeError as e:
        return _respuesta_error(
            f"Error de tipo en los datos de entrada: {e}"
        )
    except Exception as e:
        return _respuesta_error(
            f"Error inesperado al calcular cinemática inversa: {e}"
        )
    
    # Funciones de conversión

def _convertir_array_a_lista(valor: Any) -> Any:
    """
    Convierte recursivamente arrays de NumPy a listas de Python, de modo que el resultado sea serializable a JSON.

    Parámetros:
        valor (Any): Valor que puede ser un np.ndarray, una lista anidada o cualquier escalar compatible con JSON.

    Devuelve:
        Any: El mismo valor convertido a tipos nativos de Python.
    """
    if isinstance(valor, np.ndarray):
        return valor.tolist()
    if isinstance(valor, list):
        return [_convertir_array_a_lista(elemento) for elemento in valor]
    # Convertir escalares NumPy a float/int nativos
    if isinstance(valor, (np.floating,)):
        return float(valor)
    if isinstance(valor, (np.integer,)):
        return int(valor)
    return valor


def _respuesta_error(mensaje: str) -> Dict[str, Any]:
    """
    Construye un diccionario de respuesta estándar para errores.

    Parámetros:
        mensaje (str): Descripción del error ocurrido.

    Devuelve:
        Dict[str, Any]: Diccionario con 'exito' en False y el mensaje de error.
    """
    return {
        "exito": False,
        "error": mensaje,
    }


def _extraer_posiciones_articulaciones(matrices: list) -> list:
    """
    Extrae la posición cartesiana [x,y,z] de cada matriz de transformación homogénea devuelta por la cinemática directa.

    La posición de cada eslabón (o de la base) se encuentra en las primeras tres filas de la cuarta columna de su matriz 4x4
    Parámetros:
        matrices (list): Lista de matrices 4x4 (np.ndarray) devuelta por calcular_cinematica_directa(). El primer elemento es
                         el marco de la base y el último es el efector final.

    Devuelve:
        list: Lista de vectores [x,y,z] como listas nativas de Python, una por cada matriz (base incluida). 
              Longitud = N + 1 para un robot de N articulaciones.
    """
    posiciones = []

    for matriz in matrices:
        # Las primeras 3 filas de la columna 3 contienen la posición [x, y, z]
        posicion_xyz = matriz[0:3, 3]
        posiciones.append(_convertir_array_a_lista(posicion_xyz))

    return posiciones
