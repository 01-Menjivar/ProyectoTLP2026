"""Pruebas del visualizador de árboles (Fase 2). Desde la raíz del repositorio:

    python -m unittest pruebas.test_visualizador
"""
import unittest
import xml.etree.ElementTree as ET

from lexer.espanol import analizar_oracion
from parser.espanol import analizar
from parser.nodo import Nodo
from parser.visualizador import arbol_dot, arbol_svg, arbol_texto


def procesar(oracion):
    tokens, tabla, errores_lexicos = analizar_oracion(oracion)
    assert not errores_lexicos, errores_lexicos
    return analizar(tokens, tabla)


class PruebasTexto(unittest.TestCase):

    def test_oracion_simple(self):
        arbol, errores = procesar("Yo leo el libro.")
        self.assertEqual(arbol_texto(arbol, errores), "\n".join([
            "O",
            "├── PRON  Yo",
            "└── SV",
            "    ├── V_PRES  leo",
            "    └── SN",
            "        ├── DET  el",
            "        └── N  libro",
        ]))

    def test_sintagma_preposicional_anidado(self):
        arbol, errores = procesar("La niña de los vecinos lee los libros nuevos.")
        texto = arbol_texto(arbol, errores)
        self.assertEqual(texto.count("SN"), 3)
        self.assertEqual(texto.count("SP"), 1)
        self.assertIn("ADJ  nuevos", texto)

    def test_marca_la_palabra_con_error(self):
        arbol, errores = procesar("Yo leo los libros nuevas.")
        self.assertEqual(len(errores), 1)
        self.assertIn("ADJ  nuevas  <-- error", arbol_texto(arbol, errores))
        self.assertNotIn("<-- error", arbol_texto(arbol, []))

    def test_funciona_con_arboles_que_no_son_del_espanol(self):
        arbol = Nodo("Programa", [Nodo("Declaracion", [Nodo("Literal", valor="5", linea=1)], valor={"nombre": "x"})])
        self.assertIn("Literal  5", arbol_texto(arbol))


class PruebasSvg(unittest.TestCase):

    def test_svg_bien_formado_y_con_las_palabras(self):
        arbol, errores = procesar("La niña de los vecinos lee los libros nuevos.")
        svg = arbol_svg(arbol, errores, "La niña de los vecinos lee los libros nuevos.")
        raiz = ET.fromstring(svg)                       # falla si el XML está mal formado
        self.assertTrue(raiz.tag.endswith("svg"))
        textos = [t.text for t in raiz.iter("{http://www.w3.org/2000/svg}text")]
        for palabra in ["niña", "vecinos", "lee", "libros", "nuevos", "SN", "SP", "SV", "O"]:
            self.assertIn(palabra, textos)

    def test_error_en_rojo_y_con_mensaje(self):
        arbol, errores = procesar("Yo leo los libros nuevas.")
        svg = arbol_svg(arbol, errores)
        self.assertIn("#c62828", svg)
        self.assertIn("nuevas", svg)
        self.assertIn("discrepa en genero", svg)

    def test_sin_errores_no_hay_rojo(self):
        arbol, errores = procesar("Yo leo el libro.")
        self.assertNotIn("#c62828", arbol_svg(arbol, errores))

    def test_caracteres_especiales_se_escapan(self):
        hoja = Nodo("N", valor={"lexema": "a<b&c", "columna": 1}, linea=1)
        ET.fromstring(arbol_svg(Nodo("O", [hoja])))


class PruebasDot(unittest.TestCase):

    def test_dot_tiene_nodos_y_aristas(self):
        arbol, errores = procesar("Yo leo el libro.")
        dot = arbol_dot(arbol, errores)
        self.assertTrue(dot.startswith("digraph arbol {"))
        self.assertEqual(dot.count("->"), 6)             # 7 nodos, 6 aristas
        self.assertIn('label="N\\nlibro"', dot)


if __name__ == "__main__":
    unittest.main()
