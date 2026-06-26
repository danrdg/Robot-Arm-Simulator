"""
views.py
--------
Vistas Django para el simulador.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from simulador.robotica.servicios.servicio_simulacion import (
    calcular_cinematica_directa,
    calcular_cinematica_inversa,
)


# Robots predefinidos disponibles en el simulador

ROBOTS_PREDEFINIDOS = {
    "robot_3dof": {
        "nombre": "Simple 3GDL",
        "articulaciones": [
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.5, "a": 0.0, "alpha": 1.5708},
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.0, "a": 0.8, "alpha": 0.0},
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.0, "a": 0.5, "alpha": 0.0},
        ],
    },
    "robot_scara": {
        "nombre": "SCARA 4GDL",
        "articulaciones": [
            {"tipo": "rotatoria",  "theta": 0.0, "d": 1, "a": 1, "alpha":  0.0},
            {"tipo": "rotatoria",  "theta": 0.0, "d": 0.0, "a": 0.3, "alpha":  3.1416},
            {"tipo": "prismatica", "theta": 0.0, "d": 0.2, "a": 0.0, "alpha":  0.0},
            {"tipo": "rotatoria",  "theta": 0.0, "d": 0.0, "a": 0.0, "alpha":  0.0},
        ],
    },
    "robot_industrial": {
        "nombre": "Industrial 6GDL",
        "articulaciones": [
            {"tipo": "rotatoria", "theta": 0.0, "d": 1.0, "a": 0.0,  "alpha": 1.5708},
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.0, "a": 1.0,  "alpha": 0.0},
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.0, "a": 0.8,  "alpha": 1.5708},
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.6, "a": 0.0,  "alpha": -1.5708},
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.0, "a": 0.0,  "alpha": 1.5708},
            {"tipo": "rotatoria", "theta": 0.0, "d": 0.2, "a": 0.0,  "alpha": 0.0},
        ],
    },
}


# Vistas de página (MVT)

def cinematica_directa(request):
    """Renderiza la página de cinemática directa con los robots disponibles."""
    contexto = {
        "titulo": "Cinemática Directa",
        "robots": [
            {"id": id_robot, "nombre": datos["nombre"]}
            for id_robot, datos in ROBOTS_PREDEFINIDOS.items()
        ],
        "robots_json": json.dumps(ROBOTS_PREDEFINIDOS),
    }
    return render(request, "simulador/cinematica_directa.html", contexto)


def cinematica_inversa(request):
    """Renderiza la página de cinemática inversa con los robots disponibles."""
    contexto = {
        "titulo": "Cinemática Inversa",
        "robots": [
            {"id": id_robot, "nombre": datos["nombre"]}
            for id_robot, datos in ROBOTS_PREDEFINIDOS.items()
        ],
        "robots_json": json.dumps(ROBOTS_PREDEFINIDOS),
    }
    return render(request, "simulador/cinematica_inversa.html", contexto)


def constructor_robot(request):
    """Renderiza la página del constructor de robots personalizado."""
    contexto = {
        "titulo": "Constructor de Robot",
    }
    return render(request, "simulador/constructor_robot.html", contexto)


# Vistas API (endpoints JSON)

@csrf_exempt
@require_http_methods(["POST"])
def api_cinematica_directa(request):
    """
    Endpoint API para cinemática directa.

    Recibe un JSON con la descripción del robot y devuelve la posición de cada articulación y el efector final.

    Body esperado:
        { "nombre": str, "articulaciones": [...] }

    Respuesta:
        { "exito": bool, "articulaciones": [...], "posicion_efector": [...], ... }
    """
    try:
        datos_robot = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"exito": False, "error": "JSON inválido en el cuerpo de la petición."}, status=400)

    resultado = calcular_cinematica_directa(datos_robot)
    return JsonResponse(resultado)


@csrf_exempt
@require_http_methods(["POST"])
def api_cinematica_inversa(request):
    """
    Endpoint API para cinemática inversa.

    Recibe un JSON con la descripción del robot y la posición objetivo [x,y,z]. Devuelve los valores articulares 
    y la posición alcanzada.

    Body esperado:
        { "robot": {...}, "objetivo": [x, y, z] }

    Respuesta:
        { "exito": bool, "convergió": bool, "valores_articulares": [...], ... }
    """
    try:
        cuerpo = json.loads(request.body)
        datos_robot = cuerpo["robot"]
        objetivo = cuerpo["objetivo"]
    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse({"exito": False, "error": f"Petición inválida: {e}"}, status=400)

    resultado = calcular_cinematica_inversa(datos_robot, objetivo)
    return JsonResponse(resultado)
