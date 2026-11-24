"""Integración lexer español -> parser español -> concordancia (casos del relevo de P4).

    python -m unittest pruebas.test_integracion_espanol

Se omite sola si todavía no existe parser/espanol.py (hay que hacer git pull).
"""
import unittest

from lexer.espanol import analizar_oracion

try:
    from parser.espanol import analizar as analizar_sintaxis
except ImportError:
    analizar_sintaxis = None


def procesar(oracion):
    tokens, tabla, errores_lexicos = analizar_oracion(oracion)
    assert not errores_lexicos, errores_lexicos
    return analizar_sintaxis(tokens, tabla)


@unittest.skipIf(analizar_sintaxis is None, "falta parser/espanol.py: haz git pull")
class PruebasIntegracion(unittest.TestCase):

    def test_oraciones_aceptadas(self):
        for oracion in ["Yo leo el libro.",
                        "Tú leíste el libro.",
                        "La niña de los vecinos lee los libros nuevos.",
                        "Yo leo el libro"]:
            with self.subTest(oracion=oracion):
                arbol, errores = procesar(oracion)
                self.assertEqual(errores, [])
                self.assertEqual(arbol.tipo, "O")

    def test_error_de_concordancia_en_el_verbo(self):
        oracion = "La niña de los vecinos leen los libros nuevos."
        _, errores = procesar(oracion)
        self.assertEqual(errores[0]["fase"], "semantico")
        self.assertEqual(errores[0]["columna"], oracion.index("leen") + 1)

    def test_error_de_concordancia_en_el_adjetivo(self):
        oracion = "Yo leo los libros nuevas."
        _, errores = procesar(oracion)
        self.assertEqual(errores[0]["fase"], "semantico")
        self.assertEqual(errores[0]["columna"], oracion.index("nuevas") + 1)

    def test_error_sintactico_por_texto_sobrante(self):
        oracion = "Yo leo el libro la niña."
        _, errores = procesar(oracion)
        self.assertEqual(errores[0]["fase"], "sintactico")
        self.assertEqual(errores[0]["columna"], oracion.index("la niña") + 1)


if __name__ == "__main__":
    unittest.main()
