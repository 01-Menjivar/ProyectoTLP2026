"""Pruebas del lexer del español (Fase 2). Desde la raíz del repositorio:

    python -m unittest pruebas.test_lexer_espanol
"""
import unittest

from lexer.espanol import analizar, analizar_oracion, construir_tabla
from lexer.lexicon_es import HOMOGRAFOS, LEXICON


def tipos(oracion, **kw):
    tokens, _ = analizar(oracion, **kw)
    return [t.tipo for t in tokens]


class TablaFalsa:
    """Imita TablaSimbolos para probar construir_tabla sin depender del módulo semántico."""

    def __init__(self):
        self.entradas = {}

    def declarar(self, nombre, tipo, linea, **rasgos):
        if nombre in self.entradas:
            return False
        self.entradas[nombre] = {"tipo": tipo, "linea": linea, **rasgos}
        return True


class PruebasTokens(unittest.TestCase):

    def test_oracion_simple(self):
        self.assertEqual(tipos("Yo leo el libro."),
                         ["PRON", "V_PRES", "DET", "N", "PUNTO", "EOF"])

    def test_oracion_con_sintagma_preposicional_y_adjetivo(self):
        self.assertEqual(
            tipos("La niña de los vecinos lee los libros nuevos."),
            ["DET", "N", "PREP", "DET", "N", "V_PRES", "DET", "N", "ADJ", "PUNTO", "EOF"])

    def test_pretérito_y_adverbio(self):
        self.assertEqual(tipos("Ayer tú leíste el libro."),
                         ["ADV", "PRON", "V_PRET", "DET", "N", "PUNTO", "EOF"])

    def test_sin_punto_final(self):
        self.assertEqual(tipos("Yo leo el libro."[:-1]), ["PRON", "V_PRES", "DET", "N", "EOF"])

    def test_descartar_el_punto(self):
        self.assertEqual(tipos("Yo leo el libro.", emitir_punto=False),
                         ["PRON", "V_PRES", "DET", "N", "EOF"])

    def test_siempre_termina_en_eof(self):
        self.assertEqual(analizar("")[0][-1].tipo, "EOF")
        self.assertEqual(analizar("Yo leo")[0][-1].tipo, "EOF")

    def test_el_lexema_conserva_el_texto_original(self):
        tokens, _ = analizar("LA Niña lee.")
        self.assertEqual([t.lexema for t in tokens[:3]], ["LA", "Niña", "lee"])
        self.assertEqual(tokens[0].tipo, "DET")

    def test_el_determinante_y_el_pronombre_con_tilde_son_distintos(self):
        self.assertEqual(tipos("El libro")[0], "DET")
        self.assertEqual(tipos("Él lee")[0], "PRON")

    def test_tilde_en_forma_descompuesta(self):
        # "e" + tilde combinante (como la escribe a veces macOS) debe leerse como "é"
        self.assertEqual(tipos("Tú lees el libro")[0], "PRON")


class PruebasPosiciones(unittest.TestCase):

    def test_linea_y_columna(self):
        tokens, _ = analizar("Yo leo el libro.")
        self.assertEqual([(t.linea, t.columna) for t in tokens],
                         [(1, 1), (1, 4), (1, 8), (1, 11), (1, 16), (1, 17)])

    def test_columna_con_tildes_cuenta_letras(self):
        tokens, _ = analizar("Tú leíste el libro.")
        self.assertEqual(tokens[1].columna, 4)

    def test_varias_lineas(self):
        tokens, _ = analizar("Yo leo\nel libro.")
        self.assertEqual((tokens[2].lexema, tokens[2].linea, tokens[2].columna), ("el", 2, 1))


class PruebasErrores(unittest.TestCase):

    def test_palabra_desconocida(self):
        tokens, errores = analizar("Yo leo el xyzzy.")
        self.assertEqual(len(errores), 1)
        self.assertEqual(errores[0]["fase"], "lexico")
        self.assertEqual((errores[0]["linea"], errores[0]["columna"]), (1, 11))
        self.assertIn("xyzzy", errores[0]["mensaje"])
        self.assertNotIn("xyzzy", [t.lexema for t in tokens])

    def test_sugiere_la_palabra_con_tilde(self):
        _, errores = analizar("Tu leo el libro.")
        self.assertIn("tú", errores[0]["mensaje"])

    def test_caracter_invalido_y_numero(self):
        _, errores = analizar("Yo leo 3 libros @")
        self.assertEqual(len(errores), 2)
        self.assertIn("3", errores[0]["mensaje"])
        self.assertIn("@", errores[1]["mensaje"])

    def test_varios_errores_en_una_pasada(self):
        _, errores = analizar("Qwe leo asd libro.")
        self.assertEqual([e["columna"] for e in errores], [1, 9])

    def test_con_errores_no_se_construye_la_tabla(self):
        _, tabla, errores = analizar_oracion("Yo leo el xyzzy.")
        self.assertIsNone(tabla)
        self.assertTrue(errores)


class PruebasTabla(unittest.TestCase):

    def test_claves_y_rasgos(self):
        tokens, _ = analizar("Yo leo el libro.")
        tabla = construir_tabla(tokens, TablaFalsa())
        self.assertEqual(set(tabla.entradas),
                         {"PRON:yo", "V_PRES:leo", "DET:el", "N:libro"})
        self.assertEqual(tabla.entradas["PRON:yo"]["persona"], 1)
        self.assertEqual(tabla.entradas["N:libro"]["genero"], "m")
        self.assertEqual(tabla.entradas["DET:el"]["numero"], "sg")

    def test_la_clave_usa_minusculas(self):
        tokens, _ = analizar("LA Niña lee el libro.")
        tabla = construir_tabla(tokens, TablaFalsa())
        self.assertIn("DET:la", tabla.entradas)
        self.assertIn("N:niña", tabla.entradas)

    def test_palabra_repetida_se_registra_una_vez(self):
        tokens, _ = analizar("Yo leo el libro y el libro.")  # "y" no existe: se ignora el token
        tabla = construir_tabla(tokens, TablaFalsa())
        self.assertEqual(sum(1 for k in tabla.entradas if k == "DET:el"), 1)

    def test_con_la_tabla_real(self):
        from semantico.tabla_simbolos import TablaSimbolos
        tabla = TablaSimbolos()
        try:
            tabla.declarar("PRON:prueba", "PRON", 1, numero="sg", persona=1)
        except TypeError:
            self.skipTest("TablaSimbolos.declarar todavía no acepta rasgos: falta hacer git pull")
        tokens, _ = analizar("Yo leo el libro.")
        tabla = construir_tabla(tokens, TablaSimbolos())
        self.assertEqual(tabla.buscar("N:libro")["tipo"], "N")


class PruebasLexicon(unittest.TestCase):
    """El léxico es datos: estas pruebas evitan que alguien lo rompa al agregar palabras."""

    RASGOS = {
        "N": {"genero", "numero", "persona"},
        "DET": {"genero", "numero"},
        "ADJ": {"genero", "numero"},
        "PRON": {"numero", "persona"},
        "V_PRES": {"numero", "persona"},
        "V_PRET": {"numero", "persona"},
        "PREP": set(),
        "ADV": set(),
    }
    VALORES = {"genero": {"m", "f"}, "numero": {"sg", "pl"}, "persona": {1, 2, 3}}

    def test_cada_entrada_tiene_los_rasgos_requeridos(self):
        for forma, entrada in LEXICON.items():
            with self.subTest(forma=forma):
                self.assertEqual(set(entrada.rasgos), self.RASGOS[entrada.categoria])
                for k, v in entrada.rasgos.items():
                    self.assertIn(v, self.VALORES[k])

    def test_las_formas_estan_en_minusculas(self):
        for forma in LEXICON:
            self.assertEqual(forma, forma.casefold())

    def test_formas_irregulares(self):
        self.assertEqual(LEXICON["leyeron"].categoria, "V_PRET")
        self.assertEqual(LEXICON["veo"].rasgos, {"numero": "sg", "persona": 1})
        self.assertEqual(LEXICON["canciones"].rasgos["numero"], "pl")

    def test_homografos_documentados(self):
        self.assertIn("compramos", HOMOGRAFOS)
        self.assertEqual(LEXICON["compramos"].categoria, "V_PRES")
        self.assertEqual(tipos("Nosotros compramos el libro")[1], "V_PRES")


if __name__ == "__main__":
    unittest.main()
