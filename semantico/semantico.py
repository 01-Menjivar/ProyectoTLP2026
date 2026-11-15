"""Núcleo del analizador semántico de mini-C (P3): reglas S1, S2 y S8."""
import json
import sys
from pathlib import Path
from typing import List, Tuple

from parser.nodo import Nodo
from semantico.tabla_simbolos import TablaSimbolos


class AnalizadorSemantico:
    """Recorre el AST en orden de aparición, sin ejecutar condiciones ni ciclos."""

    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores = []

    def _error(self, nodo: Nodo, mensaje: str) -> None:
        # El contrato del AST no conserva columnas: 1 es la referencia de línea.
        self.errores.append({"fase": "semantico", "linea": nodo.linea,
                             "columna": 1, "mensaje": mensaje})

    def _variable(self, nodo: Nodo, nombre: str):
        simbolo = self.tabla.buscar(nombre)
        nodo.tipo_dato = simbolo["tipo"] if simbolo else None
        if simbolo is None:
            self._error(nodo, f"Variable '{nombre}' no declarada antes de su uso")
        return simbolo

    def _expresion(self, nodo: Nodo) -> None:
        """Resuelve nombres en todos los operandos; P4 completará los tipos."""
        if nodo.tipo == "Variable":
            self._variable(nodo, nodo.valor)
        elif nodo.tipo in ("OpBinario", "OpUnario"):
            nodo.tipo_dato = None
            for hijo in nodo.hijos:
                self._expresion(hijo)
        elif nodo.tipo != "Literal":
            raise ValueError(f"Expresión no soportada: {nodo.tipo}")

    def recorrer(self, nodo: Nodo) -> None:
        """Comprueba declaraciones, destinos de asignación y usos en cada sentencia."""
        if nodo.tipo == "Programa":
            for hijo in nodo.hijos:
                self.recorrer(hijo)
        elif nodo.tipo == "Bloque":
            self.tabla.abrir_ambito()
            try:
                for hijo in nodo.hijos:
                    self.recorrer(hijo)
            finally:
                self.tabla.cerrar_ambito()
        elif nodo.tipo == "Declaracion":
            nombre = nodo.valor["nombre"]
            tipo = nodo.valor["tipo_dato"]
            # Como en C, el nombre ya es visible en su propio inicializador.
            if not self.tabla.declarar(nombre, tipo, nodo.linea):
                anterior = self.tabla.buscar(nombre)
                self._error(nodo, f"Redeclaración de '{nombre}' en el mismo ámbito "
                            f"(declarada en línea {anterior['linea']})")
            for expresion in nodo.hijos:
                self._expresion(expresion)
        elif nodo.tipo == "Asignacion":
            self._variable(nodo, nodo.valor)
            self._expresion(nodo.hijos[0])
        elif nodo.tipo in ("Si", "Mientras"):
            self._expresion(nodo.hijos[0])
            # Ambas ramas se analizan; el ciclo se visita una sola vez.
            for bloque in nodo.hijos[1:]:
                self.recorrer(bloque)
        elif nodo.tipo == "Printf":
            for expresion in nodo.hijos:
                self._expresion(expresion)
        else:
            raise ValueError(f"Sentencia no soportada: {nodo.tipo}")


def analizar(ast: Nodo) -> Tuple[Nodo, List[dict], List[dict]]:
    """Devuelve (AST, declaraciones, errores) de S1/S2/S8; tipos pendientes de P4."""
    analizador = AnalizadorSemantico()
    analizador.recorrer(ast)
    return ast, analizador.tabla.a_lista(), analizador.errores


def main(argv: List[str]) -> int:
    """Analiza un .c o un AST .json; devuelve 0 sin errores, 1 con errores y 2 por uso."""
    if len(argv) != 2:
        print("Uso: python -m semantico.semantico programa.c|ast.json")
        return 2
    ruta = Path(argv[1])
    try:
        texto = ruta.read_text(encoding="utf-8-sig")
        if ruta.suffix.lower() == ".json":
            ast, errores = Nodo.desde_json(texto), []
        else:
            from parser.convertidor import codigo_a_ast
            ast, errores = codigo_a_ast(texto)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"ERROR de entrada: {error}", file=sys.stderr)
        return 2
    print("Alcance P3: S1, S2 y S8. Reglas de tipos y avisos pendientes de integración.")
    if ast is not None:
        _, tabla, errores = analizar(ast)
        print(json.dumps(tabla, ensure_ascii=False, indent=2))
    for error in errores:
        print(f"ERROR {error['fase']} línea {error['linea']}, col {error['columna']}: "
              f"{error['mensaje']}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
