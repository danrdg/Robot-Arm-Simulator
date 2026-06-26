"""
test.py
-------
Script de demostración del motor de cinemática robótica.

Prueba los siguientes robots de ejemplo:
    1. Robot planar de 2 GDL (2 articulaciones rotatorias en el plano XY)
    2. Robot planar de 3 GDL
    3. Robot tipo SCARA de 3 GDL (mezcla rotatoria + prismática)
    4. Robot de 6 GDL tipo industrial

Para cada robot se muestra:
    - Cinemática directa (posición del efector dado los ángulos)
    - Jacobiano geométrico
    - Cinemática inversa (ángulos para llegar a una posición deseada)
"""

import numpy as np

from .articulacion import Articulacion
from .brazo_robot import BrazoRobot
from .cinematica_directa import calcular_cinematica_directa, imprimir_resultado_cinematica
from .jacobiano import calcular_jacobiano, imprimir_jacobiano
from .cinematica_inversa import resolver_cinematica_inversa, imprimir_resultado_inversa


# Separador visual


def separador(titulo: str) -> None:
    """Imprime un separador visual con un título."""
    print("\n")
    print(" " * 60)
    print(f"  {titulo}")
    print(" " * 60)


# EJEMPLO 1: Robot planar de 2 GDL

def ejemplo_robot_2gdl() -> None:
    """
    Robot planar con 2 articulaciones rotatorias (tipo RR).
    Ambos eslabones tienen longitud 1.0 m.
    Configuración inicial: ambas articulaciones a 45°.
    """
    separador("EJEMPLO 1: Robot Planar 2 GDL (RR)")

    longitud_eslabon = 1.0   # metros
    angulo_inicial   = np.pi / 4  # 45 grados en radianes

    # Crear articulaciones con parámetros DH
    art1 = Articulacion(
        tipo = "rotatoria",
        theta = angulo_inicial,
        d = 0.0,
        a = longitud_eslabon,
        alpha = 0.0
    )
    art2 = Articulacion(
        tipo  = "rotatoria",
        theta = angulo_inicial,
        d = 0.0,
        a = longitud_eslabon,
        alpha = 0.0
    )

    robot = BrazoRobot("Robot_Planar_2GDL", [art1, art2])
    print(f"\n{robot}\n")

    # Cinemática directa
    print("Calculando cinemática directa...")
    matrices = calcular_cinematica_directa(robot)
    imprimir_resultado_cinematica(matrices)

    # Jacobiano
    print("\nCalculando Jacobiano...")
    J = calcular_jacobiano(robot, matrices)
    imprimir_jacobiano(J)

    # Cinemática inversa
    objetivo = np.array([1.2, 0.8, 0.0])
    print(f"\nResolviendo cinemática inversa para objetivo {objetivo}...")

    resultado = resolver_cinematica_inversa(
        brazo_robot = robot,
        objetivo = objetivo,
        tolerancia = 1e-5,
        max_iteraciones = 500,
        tasa_aprendizaje = 0.5
    )
    imprimir_resultado_inversa(resultado)

# EJEMPLO 2: Robot planar de 3 GDL

def ejemplo_robot_3gdl() -> None:
    """
    Robot planar con 3 articulaciones rotatorias (tipo RRR).
    Eslabones de longitud 1.0, 0.8 y 0.5 metros.
    """
    separador("EJEMPLO 2: Robot Planar 3 GDL (RRR)")

    art1 = Articulacion("rotatoria", theta=np.pi/6, d=0.0, a=1.0, alpha=0.0)
    art2 = Articulacion("rotatoria", theta=np.pi/4, d=0.0, a=0.8, alpha=0.0)
    art3 = Articulacion("rotatoria", theta=np.pi/3, d=0.0, a=0.5, alpha=0.0)

    robot = BrazoRobot("Robot_Planar_3GDL", [art1,art2,art3])
    print(f"\n{robot}\n")

    # Cinemática directa
    print("Calculando cinemática directa...")
    matrices = calcular_cinematica_directa(robot)
    imprimir_resultado_cinematica(matrices)

    # Jacobiano 
    print("\n→ Calculando Jacobiano...")
    J = calcular_jacobiano(robot, matrices)
    imprimir_jacobiano(J)

    # Cinemática inversa
    objetivo = np.array([1.5, 0.5,0.0])
    print(f"\nResolviendo cinemática inversa para objetivo {objetivo}...")

    resultado = resolver_cinematica_inversa(
        brazo_robot = robot,
        objetivo = objetivo,
        tolerancia = 1e-4,
        max_iteraciones = 1000,
        tasa_aprendizaje = 0.3
    )
    imprimir_resultado_inversa(resultado)

# EJEMPLO 3: Robot con articulación prismática (tipo RPR)

def ejemplo_robot_rpr() -> None:
    """
    Robot con una articulación prismática en el centro (tipo RPR):
    """
    separador("EJEMPLO 3: Robot con Prismática (RPR)")

    # Articulación 1: Rotatoria, gira alrededor de Z (base)
    art1 = Articulacion(
        tipo = "rotatoria",
        theta = np.pi / 4,   # 45°
        d = 0.5,
        a = 0.0,
        alpha = np.pi / 2    # 90°, cambia el plano de trabajo
    )

    # Articulación 2: Prismática, se extiende a lo largo de su eje
    art2 = Articulacion(
        tipo = "prismatica",
        theta = 0.0,
        d = 1.0,         # longitud de extensión actual
        a = 0.0,
        alpha = 0.0
    )

    # Articulación 3: Rotatoria, giro final
    art3 = Articulacion(
        tipo = "rotatoria",
        theta = np.pi / 6,   # 30°
        d = 0.2,
        a = 0.4,
        alpha = 0.0
    )

    robot = BrazoRobot("Robot_RPR", [art1, art2, art3])
    print(f"\n{robot}\n")

    # Cinemática directa
    print("Calculando cinemática directa...")
    matrices = calcular_cinematica_directa(robot)
    imprimir_resultado_cinematica(matrices)

    # Jacobiano 
    print("\nCalculando Jacobiano...")
    J = calcular_jacobiano(robot, matrices)
    imprimir_jacobiano(J)

    # Cinemática inversa
    objetivo = np.array([0.3, 0.3, 1.2])
    print(f"\nResolviendo cinemática inversa para objetivo {objetivo}...")

    resultado = resolver_cinematica_inversa(
        brazo_robot = robot,
        objetivo = objetivo,
        tolerancia = 1e-4,
        max_iteraciones = 2000,
        tasa_aprendizaje = 0.2
    )
    imprimir_resultado_inversa(resultado)


# EJEMPLO 4: Robot industrial de 6 GDL

def ejemplo_robot_6gdl() -> None:
    """
    Robot industrial con 6 grados de libertad (tipo KUKA,ABB...).
    """
    separador("EJEMPLO 4: Robot Industrial 6 GDL")

    # Parámetros DH típicos de un robot tipo PUMA simplificado
    # (valores normalizados para el ejemplo)
    articulaciones = [
        Articulacion("rotatoria",theta=0.0,d=0.4,a=0.0,alpha=np.pi/2),
        Articulacion("rotatoria",theta=0.0,d=0.0,a=0.6,alpha=0.0),
        Articulacion("rotatoria",theta=0.0,d=0.0,a=0.0,alpha=np.pi/2),
        Articulacion("rotatoria",theta=0.0,d=0.4,a=0.0,alpha=-np.pi/2),
        Articulacion("rotatoria",theta=0.0,d=0.0,a=0.0,alpha=np.pi/2),
        Articulacion("rotatoria",theta=0.0,d=0.1,a=0.0,alpha=0.0),
    ]

    robot = BrazoRobot("Robot_Industrial_6GDL", articulaciones)
    print(f"\n{robot}\n")

    # Cinemática directa en posición cero
    print("Calculando cinemática directa (posición cero)...")
    matrices = calcular_cinematica_directa(robot)
    imprimir_resultado_cinematica(matrices)

    # Jacobiano en posición cero
    print("\nCalculando Jacobiano...")
    J = calcular_jacobiano(robot, matrices)
    imprimir_jacobiano(J)

    # Cinemática directa con ángulos distintos 
    print("\nCambiando ángulos del robot para nueva posición...")
    nuevos_angulos = [np.pi/6, np.pi/4, -np.pi/6, np.pi/3, -np.pi/4, np.pi/6]
    robot.establecer_variables_articulares(nuevos_angulos)
    matrices_nuevas = calcular_cinematica_directa(robot)
    imprimir_resultado_cinematica(matrices_nuevas)

    # Cinemática inversa 
    objetivo = np.array([0.3, 0.4, 0.9])
    robot.establecer_variables_articulares([0.0] * 6)  # volver a cero antes de intentar
    print(f"\nResolviendo cinemática inversa para objetivo {objetivo}...")

    resultado = resolver_cinematica_inversa(
        brazo_robot = robot,
        objetivo = objetivo,
        tolerancia = 1e-4,
        max_iteraciones = 2000,
        tasa_aprendizaje = 0.1
    )
    imprimir_resultado_inversa(resultado)


# PUNTO DE ENTRADA PRINCIPAL

if __name__ == "__main__":
    print("\n" + " " * 60)
    print("  MOTOR DE CINEMÁTICA ROBÓTICA — DEMOSTRACIÓN")
    print("  Parámetros Denavit-Hartenberg | Jacobiano Pseudoinverso")
    print(" " * 60)

    ejemplo_robot_2gdl()
    ejemplo_robot_3gdl()
    ejemplo_robot_rpr()
    ejemplo_robot_6gdl()

    print("\nDemostración completada.\n")
