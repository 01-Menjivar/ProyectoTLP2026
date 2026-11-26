"""Parser descendente recursivo para la gramática española v1."""
from typing import List, Optional, Sequence, Tuple

from lexer.lexer import Token
from parser.nodo import Nodo
from semantico.concordancia import verificar_concordancia
from semantico.tabla_simbolos import TablaSimbolos


class ErrorSintactico(Exception):
    """Error con el token en que la oración deja de cumplir la gramática."""

    def __init__(self, token: Token, mensaje: str):
        super().__init__(mensaje)
        self.token = token
        self.mensaje = mensaje


class ParserEspanol:
    """Construye un árbol `O` con las producciones de docs/gramatica_espanol.md."""

    def __init__(self, tokens: Sequence[Token]):
        self.tokens = list(tokens)
        self.pos = 0

    def actual(self) -> Token:
        return self.tokens[self.pos]

    def es(self, *tipos: str) -> bool:
        return self.actual().tipo in tipos

    def avanzar(self) -> Token:
        token = self.actual()
        if token.tipo != "EOF":
            self.pos += 1
        return token

    def esperar(self, tipo: str, descripcion: str) -> Token:
        """Consume un tipo de token o informa qué categoría faltó."""
        if not self.es(tipo):
            raise ErrorSintactico(
                self.actual(),
                f"Se esperaba {descripcion}, pero se encontró {self.describir()}",
            )
        return self.avanzar()

    def describir(self) -> str:
        token = self.actual()
        return "el fin de la oración" if token.tipo == "EOF" else f"'{token.lexema}'"

    @staticmethod
    def hoja(token: Token) -> Nodo:
        """Convierte un token léxico en una hoja compatible con el verificador."""
        return Nodo(
            token.tipo,
            valor={"lexema": token.lexema, "columna": token.columna},
            linea=token.linea,
        )

    def oracion(self) -> Nodo:
        """Reconoce O ::= (PRON | SN) SV y consume toda la entrada."""
        sujeto = self.hoja(self.avanzar()) if self.es("PRON") else self.sintagma_nominal()
        predicado = self.sintagma_verbal()

        # El lexer puede retirar el punto final o entregarlo como PUNTO antes del EOF.
        if self.es("PUNTO"):
            self.avanzar()
        self.esperar("EOF", "el fin de la oración")
        return Nodo("O", [sujeto, predicado])

    def sintagma_nominal(self) -> Nodo:
        """Reconoce SN ::= DET N { ADJ } [ SP ]."""
        hijos = [self.hoja(self.esperar("DET", "un determinante")),
                 self.hoja(self.esperar("N", "un sustantivo"))]
        while self.es("ADJ"):
            hijos.append(self.hoja(self.avanzar()))
        if self.es("PREP"):
            hijos.append(self.sintagma_preposicional())
        return Nodo("SN", hijos)

    def sintagma_preposicional(self) -> Nodo:
        """Reconoce SP ::= PREP SN."""
        preposicion = self.hoja(self.esperar("PREP", "una preposición"))
        return Nodo("SP", [preposicion, self.sintagma_nominal()])

    def sintagma_verbal(self) -> Nodo:
        """Reconoce SV ::= (V_PRES | V_PRET) [ ADV ] SN [ ADV ]."""
        hijos = [self.hoja(self.esperar_verbo())]
        if self.es("ADV"):
            hijos.append(self.hoja(self.avanzar()))
        hijos.append(self.sintagma_nominal())
        if self.es("ADV"):
            hijos.append(self.hoja(self.avanzar()))
        return Nodo("SV", hijos)

    def esperar_verbo(self) -> Token:
        """Consume uno de los dos tiempos verbales admitidos por la v1."""
        if not self.es("V_PRES", "V_PRET"):
            raise ErrorSintactico(
                self.actual(),
                f"Se esperaba un verbo en presente o pretérito, pero se encontró {self.describir()}",
            )
        return self.avanzar()


def _diagnostico(error: ErrorSintactico) -> dict:
    return {
        "fase": "sintactico",
        "linea": error.token.linea,
        "columna": error.token.columna,
        "mensaje": error.mensaje,
    }


def tokens_a_arbol(tokens: Sequence[Token]) -> Tuple[Optional[Nodo], List[dict]]:
    """Devuelve el árbol de la oración o un diagnóstico sintáctico."""
    if not tokens:
        return None, [{"fase": "sintactico", "linea": 1, "columna": 1,
                       "mensaje": "La oración no contiene tokens"}]
    try:
        return ParserEspanol(tokens).oracion(), []
    except ErrorSintactico as error:
        return None, [_diagnostico(error)]


def analizar(tokens: Sequence[Token], tabla: TablaSimbolos) -> Tuple[Optional[Nodo], List[dict]]:
    """Analiza la sintaxis y, si es válida, ejecuta la verificación de concordancia."""
    arbol, errores = tokens_a_arbol(tokens)
    if arbol is None:
        return None, errores
    return arbol, verificar_concordancia(arbol, tabla)
