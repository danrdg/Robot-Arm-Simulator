from typing import List
from .articulacion import Articulacion


class BrazoRobot:
    """
    Representa un brazo robot compuesto por una cadena de articulaciones.
    Soporta robots de 1 a 6 grados de libertad (GDL).

    Atributos:
        nombre (str): Nombre descriptivo del robot.
        articulaciones (List[Articulacion]): Lista ordenada de articulaciones.
    """

    MAX_GDL = 6  # máximo de grados de libertad soportados
    MIN_GDL = 1  # mínimo de grados de libertad soportados

    def __init__(
        self,
        nombre:str,
        articulaciones:List[Articulacion]
                ) -> None:
        """
        Inicializa el brazo robot.

        Parámetros:
            nombre : Nombre del robot.
            articulaciones : Lista de articulaciones en orden desde la base hasta el efector final.

        Lanza:
            ValueError: Si el número de articulaciones está fuera del rango 1-6.
            TypeError: Si algún elemento de la lista no es una Articulacion.
        """
        numero_gdl = len(articulaciones)

        # Validar rango de GDL
        if not (self.MIN_GDL <= numero_gdl <= self.MAX_GDL):
            raise ValueError(
                f"El robot debe tener entre {self.MIN_GDL} y {self.MAX_GDL} "
                f"articulaciones. Se recibieron: {numero_gdl}."
            )

        # Validar que todos los elementos sean Articulacion
        for indice, art in enumerate(articulaciones):
            if not isinstance(art, Articulacion):
                raise TypeError(
                    f"El elemento en la posición {indice} no es una "
                    f"instancia de Articulacion (es {type(art).__name__})."
                )

        self.nombre = nombre
        self.articulaciones = list(articulaciones)


    @property
    def grados_de_libertad(self) -> int:
        """
        Devuelve el número de grados de libertad del robot.
        """
        return len(self.articulaciones)

    def obtener_variables_articulares(self) -> List[float]:
        """
        Devuelve una lista con los valores actuales de todas las variables articulares.
        """
        valores = []
        for articulacion in self.articulaciones:
            valores.append(articulacion.obtener_variable_articular())
        return valores

    def establecer_variables_articulares(self, valores: List[float]) -> None:
        """
        Establece todas las variables articulares del robot a la vez.

        Parámetros:
            valores (List[float]): Lista de nuevos valores articulares. Debe tener la misma longitud que las articulaciones.

        Lanza:
            ValueError: Si el número de valores no coincide con el número de articulaciones.
        """
        if len(valores) != self.grados_de_libertad:
            raise ValueError(
                f"Se esperaban {self.grados_de_libertad} valores, "
                f"pero se han recibido {len(valores)}."
            )

        for articulacion, valor in zip(self.articulaciones, valores):
            articulacion.establecer_variable_articular(valor)

    def __repr__(self) -> str:
        """Representación del brazo robot."""
        lineas = [f"BrazoRobot(nombre='{self.nombre}', GDL={self.grados_de_libertad})"]
        for i, art in enumerate(self.articulaciones):
            lineas.append(f"  Articulacion {i + 1}: {art}")
        return "\n".join(lineas)
