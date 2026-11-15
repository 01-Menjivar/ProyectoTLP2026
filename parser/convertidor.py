"""Convertidor de tokens a AST (P2).

Toma la lista de tokens del lexer y construye el árbol (`Nodo`) que consume el semántico,
con el formato de docs/contratos.md, sección 3. Es un descenso recursivo sobre mini-C; no es
el parser del proyecto (el del español es de la Fase 2), solo evita escribir un AST a mano
por cada programa del corpus.

Gramática que reconoce (EBNF):

    programa   = { sentencia } EOF
    sentencia  = declaracion | asignacion | si | mientras | printf | bloque
    declaracion= TIPO ID [ "=" expresion ] ";"
    asignacion = ID "=" expresion ";"
    si         = "if" "(" expresion ")" bloque [ "else" bloque ]
    mientras   = "while" "(" expresion ")" bloque
    printf     = "printf" "(" expresion { "," expresion } ")" ";"
    bloque     = "{" { sentencia } "}"

    expresion  = o_logico
    o_logico   = y_logico { "||" y_logico }
    y_logico   = igualdad { "&&" igualdad }
    igualdad   = relacional { ("==" | "!=") relacional }
    relacional = suma { ("<" | ">" | "<=" | ">=") suma }
    suma       = termino { ("+" | "-") termino }
    termino    = unario { ("*" | "/" | "%") unario }
    unario     = ("-" | "!") unario | primario
    primario   = ENTERO | FLOTANTE | CARACTER | CADENA | ID | "(" expresion ")"

Los operadores binarios son asociativos por la izquierda. Esta gramática solo comprueba la
forma: que `printf(x)` o `"a" * 2` tengan sentido lo decide el semántico, no este módulo.

Uso desde la raíz del repositorio:
    python -m parser.convertidor pruebas/ejemplos/validos/ejemplo.c
"""
import sys
from typing import List, Optional, Tuple

from lexer.lexer import Token, analizar as analizar_lexico
from parser.nodo import Nodo

# Tipo de dato de cada clase de literal (contrato, sección 3).
TIPO_DE_LITERAL = {"ENTERO": "int", "FLOTANTE": "float", "CARACTER": "char", "CADENA": "cadena"}

# Niveles de precedencia de los operadores binarios, del que liga menos al que liga más.
NIVELES_BINARIOS = [
    {"O_LOGICO"},
    {"Y_LOGICO"},
    {"IGUAL_IGUAL", "DIFERENTE"},
    {"MENOR", "MAYOR", "MENOR_IGUAL", "MAYOR_IGUAL"},
    {"MAS", "MENOS"},
    {"POR", "DIVIDIDO", "MODULO"},
]


class ErrorSintactico(Exception):
    """La forma del programa no corresponde a la gramática. Lleva el token donde se detectó."""

    def __init__(self, token: Token, mensaje: str):
        super().__init__(mensaje)
        self.token = token
        self.mensaje = mensaje


class Convertidor:
    """Recorre la lista de tokens con un índice y construye los nodos."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errores: List[dict] = []

    # --- utilidades sobre la lista de tokens ---

    def actual(self) -> Token:
        return self.tokens[self.pos]

    def avanzar(self) -> Token:
        token = self.tokens[self.pos]
        if token.tipo != "EOF":          # nunca se pasa del EOF
            self.pos += 1
        return token

    def es(self, *tipos: str) -> bool:
        return self.actual().tipo in tipos

    def esperar(self, tipo: str, descripcion: str) -> Token:
        """Consume un token del tipo dado o falla diciendo qué se esperaba."""
        if not self.es(tipo):
            raise ErrorSintactico(self.actual(), f"Se esperaba {descripcion}, pero se encontró {self.describir()}")
        return self.avanzar()

    def describir(self) -> str:
        token = self.actual()
        return "el fin del programa" if token.tipo == "EOF" else f"'{token.lexema}'"

    # --- programa y sentencias ---

    def programa(self) -> Nodo:
        raiz = Nodo("Programa", [], None, 1)
        while not self.es("EOF"):
            self.sentencia_con_recuperacion(raiz.hijos)
        return raiz

    def sentencia_con_recuperacion(self, destino: List[Nodo]) -> None:
        """Lee una sentencia; si hay error lo anota y salta hasta poder seguir (modo pánico)."""
        try:
            destino.append(self.sentencia())
        except ErrorSintactico as e:
            self.errores.append({"fase": "sintactico", "linea": e.token.linea,
                                 "columna": e.token.columna, "mensaje": e.mensaje})
            self.sincronizar()

    def sincronizar(self) -> None:
        """Salta tokens hasta después del siguiente ';' o hasta un '}' o el fin."""
        inicio = self.pos
        while not self.es("EOF", "LLAVE_DER"):
            if self.avanzar().tipo == "PUNTOYCOMA":
                return
        if self.pos == inicio and self.es("LLAVE_DER"):
            self.avanzar()               # '}' sobrante a nivel de programa: se descarta

    def sentencia(self) -> Nodo:
        if self.es("TIPO"):
            return self.declaracion()
        if self.es("ID"):
            return self.asignacion()
        if self.es("IF"):
            return self.si()
        if self.es("WHILE"):
            return self.mientras()
        if self.es("PRINTF"):
            return self.printf()
        if self.es("LLAVE_IZQ"):
            return self.bloque()
        raise ErrorSintactico(self.actual(), f"Sentencia no válida: no puede empezar con {self.describir()}")

    def declaracion(self) -> Nodo:
        tipo = self.avanzar()
        nombre = self.esperar("ID", "el nombre de la variable")
        hijos = []
        if self.es("IGUAL"):
            self.avanzar()
            hijos.append(self.expresion())
        self.esperar("PUNTOYCOMA", "';' al final de la declaración")
        return Nodo("Declaracion", hijos, {"tipo_dato": tipo.lexema, "nombre": nombre.lexema}, nombre.linea)

    def asignacion(self) -> Nodo:
        nombre = self.avanzar()
        self.esperar("IGUAL", "'=' en la asignación")
        valor = self.expresion()
        self.esperar("PUNTOYCOMA", "';' al final de la asignación")
        return Nodo("Asignacion", [valor], nombre.lexema, nombre.linea)

    def condicion(self) -> Nodo:
        self.esperar("PAREN_IZQ", "'(' antes de la condición")
        cond = self.expresion()
        self.esperar("PAREN_DER", "')' después de la condición")
        return cond

    def si(self) -> Nodo:
        palabra = self.avanzar()
        hijos = [self.condicion(), self.bloque()]
        if self.es("ELSE"):
            self.avanzar()
            hijos.append(self.bloque())
        return Nodo("Si", hijos, None, palabra.linea)

    def mientras(self) -> Nodo:
        palabra = self.avanzar()
        return Nodo("Mientras", [self.condicion(), self.bloque()], None, palabra.linea)

    def printf(self) -> Nodo:
        palabra = self.avanzar()
        self.esperar("PAREN_IZQ", "'(' después de printf")
        argumentos = [self.expresion()]
        while self.es("COMA"):
            self.avanzar()
            argumentos.append(self.expresion())
        self.esperar("PAREN_DER", "')' al cerrar printf")
        self.esperar("PUNTOYCOMA", "';' al final de printf")
        return Nodo("Printf", argumentos, None, palabra.linea)

    def bloque(self) -> Nodo:
        llave = self.esperar("LLAVE_IZQ", "'{' para abrir el bloque")
        nodo = Nodo("Bloque", [], None, llave.linea)
        while not self.es("LLAVE_DER", "EOF"):
            self.sentencia_con_recuperacion(nodo.hijos)
        self.esperar("LLAVE_DER", "'}' para cerrar el bloque")
        return nodo

    # --- expresiones ---

    def expresion(self, nivel: int = 0) -> Nodo:
        """Un nivel por cada fila de NIVELES_BINARIOS; después de la última sigue el unario."""
        if nivel == len(NIVELES_BINARIOS):
            return self.unario()
        izquierda = self.expresion(nivel + 1)
        while self.actual().tipo in NIVELES_BINARIOS[nivel]:
            operador = self.avanzar()
            derecha = self.expresion(nivel + 1)
            izquierda = Nodo("OpBinario", [izquierda, derecha], operador.lexema, operador.linea)
        return izquierda

    def unario(self) -> Nodo:
        if self.es("MENOS", "NO_LOGICO"):
            operador = self.avanzar()
            return Nodo("OpUnario", [self.unario()], operador.lexema, operador.linea)
        return self.primario()

    def primario(self) -> Nodo:
        token = self.actual()
        if token.tipo in TIPO_DE_LITERAL:
            self.avanzar()
            return Nodo("Literal", [], token.lexema, token.linea, TIPO_DE_LITERAL[token.tipo])
        if token.tipo == "ID":
            self.avanzar()
            return Nodo("Variable", [], token.lexema, token.linea)
        if token.tipo == "PAREN_IZQ":
            self.avanzar()
            interior = self.expresion()
            self.esperar("PAREN_DER", "')' para cerrar el paréntesis")
            return interior              # los paréntesis solo agrupan; no dejan nodo propio
        raise ErrorSintactico(token, f"Se esperaba una expresión, pero se encontró {self.describir()}")


def tokens_a_ast(tokens: List[Token]) -> Tuple[Optional[Nodo], List[dict]]:
    """Construye el AST desde los tokens. Devuelve (raiz, errores_sintacticos).

    Si hubo errores, la raíz es None: un árbol a medias haría que el semántico reporte
    errores falsos. Cada error es {fase: "sintactico", linea, columna, mensaje}.
    """
    conv = Convertidor(tokens)
    raiz = conv.programa()
    return (None, conv.errores) if conv.errores else (raiz, [])


def codigo_a_ast(codigo: str) -> Tuple[Optional[Nodo], List[dict]]:
    """Del texto de un programa .c al AST: lexer y después convertidor.

    Devuelve (raiz, errores). Si el lexer encontró errores, no se construye el árbol
    (raiz es None) y se devuelven solo los errores léxicos.
    """
    tokens, errores_lexicos = analizar_lexico(codigo)
    if errores_lexicos:
        return None, errores_lexicos
    return tokens_a_ast(tokens)


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("Uso: python -m parser.convertidor programa.c")
        return 2
    with open(argv[1], encoding="utf-8-sig") as f:     # utf-8-sig: tolera el BOM de Notepad/PowerShell
        raiz, errores = codigo_a_ast(f.read())
    for e in errores:
        print(f"ERROR {e['fase']} línea {e['linea']}, col {e['columna']}: {e['mensaje']}")
    if raiz is not None:
        print(raiz.a_json())
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))