"""
urls.py
-------
Definición de rutas del simulador de robótica.
"""

from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "simulador"

urlpatterns = [

    path('', lambda request: redirect('simulador:cinematica_directa')),

    path(
        'cinematica-directa/',
        views.cinematica_directa,
        name='cinematica_directa'
    ),

    path(
        'cinematica-inversa/',
        views.cinematica_inversa,
        name='cinematica_inversa'
    ),

    path(
        'constructor/',
        views.constructor_robot,
        name='constructor_robot'
    ),

    path(
        'api/cinematica-directa/',
        views.api_cinematica_directa,
        name='api_cinematica_directa'
    ),

    path(
        'api/cinematica-inversa/',
        views.api_cinematica_inversa,
        name='api_cinematica_inversa'
    ),
]