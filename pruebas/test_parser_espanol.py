"""Pruebas unitarias para el parser descendente recursivo del español v1."""
import unittest

from lexer.lexer import Token
from parser.espanol import analizar, tokens_a_arbol
from semantico.tabla_simbolos import TablaSimbolos


def tokens(*pares):
    """Crea tokens de ejemplo; el punto final se representa como PUNTO."""
    resultado = []
    columna = 1
    for tipo, lexema in pares:
        resultado.append(Token(tipo, lexema, 1, columna))
        columna += len(lexema) + 1
    return resultado + [Token("EOF", "", 1, columna)]


class PruebasParserEspanol(unittest.TestCase):
    def setUp(self):
        self.tabla = TablaSimbolos()
        for tipo, forma, genero, numero, persona in [
            ("PRON", "yo", None, "sg", 1),
            ("PRON", "tú", None, "sg", 2),
            ("DET", "la", "f", "sg", None),
            ("DET", "el", "m", "sg", None),
            ("DET", "los", "m", "pl", None),
            ("N", "niña", "f", "sg", 3),
            ("N", "vecinos", "m", "pl", 3),
            ("N", "libro", "m", "sg", 3),
            ("N", "libros", "m", "pl", 3),
            ("ADJ", "nuevos", "m", "pl", None),
            ("ADJ", "nuevas", "f", "pl", None),
            ("V_PRES", "leo", None, "sg", 1),
            ("V_PRES", "lee", None, "sg", 3),
            ("V_PRES", "leen", None, "pl", 3),
            ("V_PRET", "leíste", None, "sg", 2),
        ]:
            self.tabla.declarar(f"{tipo}:{forma}", tipo, 1, genero=genero,
                                numero=numero, persona=persona)

    def test_construye_arbol_para_pronombre_y_presente(self):
        arbol, errores = analizar(tokens(
            ("PRON", "Yo"), ("V_PRES", "leo"), ("DET", "el"),
            ("N", "libro"), ("PUNTO", "."),
        ), self.tabla)
        self.assertEqual(errores, [])
        self.assertEqual([h.tipo for h in arbol.hijos], ["PRON", "SV"])
        self.assertEqual([h.tipo for h in arbol.hijos[1].hijos], ["V_PRES", "SN"])
        self.assertEqual(arbol.hijos[1].hijos[1].hijos[1].valor["lexema"], "libro")

    def test_admite_pretérito_adverbios_y_sp_anidado(self):
        arbol, errores = analizar(tokens(
            ("PRON", "Tú"), ("V_PRET", "leíste"), ("ADV", "ayer"),
            ("DET", "el"), ("N", "libro"), ("PUNTO", "."),
        ), self.tabla)
        self.assertEqual(errores, [])
        self.assertEqual([h.tipo for h in arbol.hijos[1].hijos], ["V_PRET", "ADV", "SN"])

        arbol, errores = analizar(tokens(
            ("DET", "La"), ("N", "niña"), ("PREP", "de"),
            ("DET", "los"), ("N", "vecinos"), ("V_PRES", "lee"),
            ("DET", "los"), ("N", "libros"), ("ADJ", "nuevos"),
        ), self.tabla)
        self.assertEqual(errores, [])
        self.assertEqual(arbol.hijos[0].hijos[-1].tipo, "SP")

    def test_devuelve_el_diagnostico_semantico_de_concordancia(self):
        arbol, errores = analizar(tokens(
            ("DET", "La"), ("N", "niña"), ("PREP", "de"),
            ("DET", "los"), ("N", "vecinos"), ("V_PRES", "leen"),
            ("DET", "el"), ("N", "libro"),
        ), self.tabla)
        self.assertIsNotNone(arbol)
        self.assertEqual(len(errores), 1)
        self.assertEqual(errores[0]["fase"], "semantico")
        self.assertIn("'leen' discrepa en numero con 'niña'", errores[0]["mensaje"])

    def test_rechaza_sujeto_ausente_y_texto_sobrante(self):
        arbol, errores = tokens_a_arbol(tokens(
            ("V_PRES", "lee"), ("DET", "el"), ("N", "libro"),
        ))
        self.assertIsNone(arbol)
        self.assertEqual(errores[0]["fase"], "sintactico")
        self.assertIn("determinante", errores[0]["mensaje"])

        arbol, errores = tokens_a_arbol(tokens(
            ("PRON", "Yo"), ("V_PRES", "leo"), ("DET", "el"),
            ("N", "libro"), ("DET", "la"), ("N", "niña"),
        ))
        self.assertIsNone(arbol)
        self.assertEqual(errores[0]["columna"], 17)
        self.assertIn("fin de la oración", errores[0]["mensaje"])

    def test_rechaza_sintagma_nominal_incompleto(self):
        arbol, errores = tokens_a_arbol(tokens(
            ("PRON", "Yo"), ("V_PRES", "leo"), ("DET", "el"),
        ))
        self.assertIsNone(arbol)
        self.assertEqual(errores[0]["fase"], "sintactico")
        self.assertIn("sustantivo", errores[0]["mensaje"])

    def test_la_tabla_incompleta_señala_un_error_de_integración(self):
        tabla = TablaSimbolos()
        tabla.declarar("PRON:yo", "PRON", 1, numero="sg", persona=1)
        tabla.declarar("V_PRES:leo", "V_PRES", 1, numero="sg", persona=1)
        with self.assertRaisesRegex(ValueError, "Falta la entrada léxica"):
            analizar(tokens(
                ("PRON", "Yo"), ("V_PRES", "leo"), ("DET", "el"),
                ("N", "libro"),
            ), tabla)


if __name__ == "__main__":
    unittest.main()
