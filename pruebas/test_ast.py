"""Pruebas del AST de ejemplo: cada JSON cumple el contrato y coincide con su programa .c."""
import json
import unittest
from pathlib import Path

from lexer.lexer import analizar
from parser.nodo import Nodo

RAIZ = Path(__file__).resolve().parent
CARPETA_AST = RAIZ / "ejemplos" / "ast"
TIPOS_VALIDOS = {"Programa", "Declaracion", "Asignacion", "Si", "Mientras", "Printf",
                "Bloque", "OpBinario", "OpUnario", "Literal", "Variable"}
TIPO_DE_LITERAL = {"int", "float", "char", "cadena"}


def recorrer(nodo):
    """Genera el nodo y todos sus descendientes."""
    yield nodo
    for hijo in nodo.hijos:
        yield from recorrer(hijo)


def buscar_programa(nombre):
    """Busca el .c del corpus que corresponde al JSON."""
    for carpeta in ("validos", "invalidos"):
        ruta = RAIZ / "ejemplos" / carpeta / f"{nombre}.c"
        if ruta.exists():
            return ruta
    raise FileNotFoundError(f"No hay programa {nombre}.c en el corpus")


class PruebasAST(unittest.TestCase):
    def setUp(self):
        self.archivos = sorted(CARPETA_AST.glob("*.json"))

    def test_hay_ejemplos(self):
        self.assertGreaterEqual(len(self.archivos), 3)

    def test_se_cargan_y_se_vuelven_a_escribir_igual(self):
        for ruta in self.archivos:
            with self.subTest(ruta.name):
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                self.assertEqual(Nodo.desde_dict(datos).a_dict(), datos)

    def test_cumplen_el_contrato(self):
        """Tipos de nodo y número de hijos según docs/contratos.md, sección 3."""
        for ruta in self.archivos:
            with self.subTest(ruta.name):
                raiz = Nodo.desde_json(ruta.read_text(encoding="utf-8"))
                self.assertEqual(raiz.tipo, "Programa")
                for n in recorrer(raiz):
                    self.assertIn(n.tipo, TIPOS_VALIDOS)
                    if n.tipo == "Declaracion":
                        self.assertIn(len(n.hijos), (0, 1))
                        self.assertEqual(set(n.valor), {"tipo_dato", "nombre"})
                    elif n.tipo == "Asignacion":
                        self.assertEqual(len(n.hijos), 1)
                    elif n.tipo == "Si":
                        self.assertIn(len(n.hijos), (2, 3))
                        self.assertTrue(all(h.tipo == "Bloque" for h in n.hijos[1:]))
                    elif n.tipo == "Mientras":
                        self.assertEqual(len(n.hijos), 2)
                        self.assertEqual(n.hijos[1].tipo, "Bloque")
                    elif n.tipo == "Printf":
                        self.assertGreaterEqual(len(n.hijos), 1)
                    elif n.tipo == "OpBinario":
                        self.assertEqual(len(n.hijos), 2)
                    elif n.tipo == "OpUnario":
                        self.assertEqual(len(n.hijos), 1)
                    elif n.tipo in ("Literal", "Variable"):
                        self.assertEqual(n.hijos, [])
                    if n.tipo == "Literal":
                        self.assertIn(n.tipo_dato, TIPO_DE_LITERAL)

    def test_lineas_coinciden_con_el_lexer(self):
        """Cada dato del AST aparece en el programa .c en la misma línea que dice el nodo."""
        for ruta in self.archivos:
            with self.subTest(ruta.name):
                codigo = buscar_programa(ruta.stem).read_text(encoding="utf-8")
                tokens, _ = analizar(codigo)
                existentes = {(t.tipo, t.lexema, t.linea) for t in tokens}
                raiz = Nodo.desde_json(ruta.read_text(encoding="utf-8"))
                for n in recorrer(raiz):
                    if n.tipo == "Variable":
                        esperado = ("ID", n.valor, n.linea)
                    elif n.tipo == "Literal":
                        esperado = None
                        self.assertTrue(any(t[1] == n.valor and t[2] == n.linea for t in existentes),
                                        f"Literal {n.valor} no está en la línea {n.linea}")
                    elif n.tipo == "Declaracion":
                        esperado = ("ID", n.valor["nombre"], n.linea)
                    elif n.tipo == "Asignacion":
                        esperado = ("ID", n.valor, n.linea)
                    elif n.tipo == "Si":
                        esperado = ("IF", "if", n.linea)
                    elif n.tipo == "Mientras":
                        esperado = ("WHILE", "while", n.linea)
                    elif n.tipo == "Printf":
                        esperado = ("PRINTF", "printf", n.linea)
                    elif n.tipo == "Bloque":
                        esperado = ("LLAVE_IZQ", "{", n.linea)
                    elif n.tipo == "OpBinario":
                        self.assertTrue(any(t[1] == n.valor and t[2] == n.linea for t in existentes),
                                        f"Operador {n.valor} no está en la línea {n.linea}")
                        esperado = None
                    else:
                        esperado = None
                    if esperado is not None:
                        self.assertIn(esperado, existentes, f"{n.tipo} en la línea {n.linea}")


if __name__ == "__main__":
    unittest.main()
