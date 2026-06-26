class Articulacion:
    """
    Representa una articulación de un brazo robot usando parámetros Denavit-Hartenberg.

    Parámetros DH:
        theta - ángulo de rotación alrededor del eje Z del eslabón anterior.
        d - distancia de traslación a lo largo del eje Z del eslabón anterior.
        a - longitud del eslabón (distancia a lo largo del eje X común).
        alpha - ángulo de torsión del eslabón (rotación alrededor del eje X).

    Atributos:
        tipo : Tipo de articulación. Puede ser "rotatoria" o "prismatica".
        theta : Ángulo theta en radianes.
        d : Desplazamiento d en metros.
        a : Longitud del eslabón a.
        alpha : Ángulo alpha en radianes.
    """

    TIPO_ROTATORIA  = "rotatoria"
    TIPO_PRISMATICA = "prismatica"

    def __init__(
        self,
        tipo:str,
        theta:float,
        d:float,
        a:float,
        alpha:float
                ) -> None:
        """
        Inicializa una articulación con sus parámetros DH.

        Lanza:
            ValueError: Si el tipo no es "rotatoria" ni "prismatica".
        """
        tipos_validos = [self.TIPO_ROTATORIA, self.TIPO_PRISMATICA]
        if tipo not in tipos_validos:
            raise ValueError(
                f"Tipo de articulación inválido: '{tipo}'. "
                f"Debe ser uno de: {tipos_validos}"
            )

        self.tipo = tipo
        self.theta = float(theta)
        self.d = float(d)
        self.a = float(a)
        self.alpha = float(alpha)

    def obtener_variable_articular(self) -> float:
        """
        Devuelve el valor de la variable articular activa:
            theta - si la articulación es rotatoria.
            d - si la articulación es prismática.
        """
        if self.tipo == self.TIPO_ROTATORIA:
            return self.theta
        else:
            return self.d

    def establecer_variable_articular(self,valor: float) -> None:
        """
        Establece el valor de la variable articular activa:
            theta - si la articulación es rotatoria.
            d - si la articulación es prismática.

        Parámetros:
            valor (float): Nuevo valor para la variable articular.
        """
        if self.tipo == self.TIPO_ROTATORIA:
            self.theta = float(valor)
        else:
            self.d = float(valor)

    def __repr__(self) -> str:
        """Representación de la articulación."""
        return (
            f"Articulacion("
            f"tipo='{self.tipo}', "
            f"theta={self.theta:.4f}, "
            f"d={self.d:.4f}, "
            f"a={self.a:.4f}, "
            f"alpha={self.alpha:.4f})"
        )
