"""Pruebas del lexer de Manzana. Desde la raíz del repositorio:

    python -m unittest discover pruebas.test_lexer
"""
import glob
import os
import unittest

from lexer.lexer import analizar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EJEMPLOS = os.path.join(RAIZ, "pruebas", "ejemplos")


def tipos(codigo):
    tokens, _ = analizar(codigo)
    return [t.tipo for t in tokens]


class PruebasLexer(unittest.TestCase):

    # ---------- entradas válidas ----------
    def test_declaracion_simple(self):
        self.assertEqual(tipos("entero n = 3;"),
                         ["TIPO", "ID", "IGUAL", "ENTERO", "PUNTOYCOMA", "EOF"])

    def test_decimal_y_texto(self):
        tokens, errores = analizar('decimal p = 2.50; texto t = "hola mundo";')
        self.assertEqual(errores, [])
        self.assertIn(("DECIMAL", "2.50"), [(t.tipo, t.lexema) for t in tokens])
        self.assertIn(("TEXTO", '"hola mundo"'), [(t.tipo, t.lexema) for t in tokens])

    def test_palabras_reservadas(self):
        self.assertEqual(tipos("si sino mientras imprimir verdadero falso y o no"),
                         ["SI", "SINO", "MIENTRAS", "IMPRIMIR", "VERDADERO", "FALSO",
                          "Y", "O", "NO", "EOF"])

    def test_los_cuatro_tipos_de_dato(self):
        tokens, _ = analizar("entero decimal texto booleano")
        self.assertEqual([t.tipo for t in tokens[:4]], ["TIPO"] * 4)

    def test_palabra_reservada_dentro_de_un_id_es_id(self):
        # "siempre" empieza con "si" pero es un identificador completo
        self.assertEqual(tipos("siempre"), ["ID", "EOF"])

    def test_operadores_de_dos_caracteres(self):
        self.assertEqual(tipos("== != <= >="),
                         ["IGUAL_IGUAL", "DIFERENTE", "MENOR_IGUAL", "MAYOR_IGUAL", "EOF"])

    def test_igual_y_comparacion_no_se_confunden(self):
        self.assertEqual(tipos("a = b == c"), ["ID", "IGUAL", "ID", "IGUAL_IGUAL", "ID", "EOF"])

    def test_operadores_aritmeticos_y_delimitadores(self):
        self.assertEqual(tipos("+ - * / % ( ) { } ; ,"),
                         ["MAS", "MENOS", "POR", "DIVIDIDO", "MODULO", "PAREN_IZQ", "PAREN_DER",
                          "LLAVE_IZQ", "LLAVE_DER", "PUNTOYCOMA", "COMA", "EOF"])

    def test_comentarios_se_ignoran(self):
        self.assertEqual(tipos("entero a; // esto no cuenta\nentero b;"),
                         ["TIPO", "ID", "PUNTOYCOMA", "TIPO", "ID", "PUNTOYCOMA", "EOF"])

    def test_identificador_con_enie_y_guion_bajo(self):
        tokens, errores = analizar("año_1")
        self.assertEqual(errores, [])
        self.assertEqual(tokens[0].tipo, "ID")

    def test_linea_y_columna(self):
        tokens, _ = analizar("entero a;\n  imprimir(a);")
        imprimir = [t for t in tokens if t.tipo == "IMPRIMIR"][0]
        self.assertEqual((imprimir.linea, imprimir.columna), (2, 3))

    def test_siempre_termina_en_eof(self):
        tokens, _ = analizar("")
        self.assertEqual([t.tipo for t in tokens], ["EOF"])

    # ---------- errores léxicos ----------
    def test_caracter_invalido(self):
        tokens, errores = analizar("entero x = 3 @ 4;")
        self.assertEqual(len(errores), 1)
        self.assertEqual((errores[0]["linea"], errores[0]["columna"]), (1, 14))
        self.assertIn("'@'", errores[0]["mensaje"])
        # el lexer sigue: los tokens de después del error existen
        self.assertEqual(tokens[-2].tipo, "PUNTOYCOMA")

    def test_texto_sin_cerrar(self):
        _, errores = analizar('texto t = "hola;')
        self.assertEqual(len(errores), 1)
        self.assertIn("sin cerrar", errores[0]["mensaje"])

    def test_numero_pegado_a_letra(self):
        _, errores = analizar("entero x = 3a;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'3a'", errores[0]["mensaje"])

    def test_numero_con_punto_final(self):
        _, errores = analizar("decimal x = 3.;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'3.'", errores[0]["mensaje"])

    def test_numero_con_dos_puntos(self):
        _, errores = analizar("decimal x = 3.5.2;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'3.5.2'", errores[0]["mensaje"])

    def test_varios_errores_en_un_mismo_programa(self):
        _, errores = analizar("entero a = 1 # 2;\nentero b = 3b;\ntexto t = \"x;")
        self.assertEqual([e["linea"] for e in errores], [1, 2, 3])

    def test_signo_de_exclamacion_solo_es_invalido(self):
        _, errores = analizar("a ! b")
        self.assertEqual(len(errores), 1)

    # ---------- programas .mz ----------
    def test_corpus_coincide_con_lo_esperado_en_lexico(self):
        """Cada .mz declara en su primera línea '// ESPERADO: ...'.
        Si espera 'error lexico', el lexer debe reportar errores; en cualquier otro caso
        (ok, error sintactico, error semantico) el lexer no debe reportar ninguno."""
        archivos = sorted(glob.glob(os.path.join(EJEMPLOS, "*", "*.mz")))
        self.assertTrue(archivos, "no se encontró ningún .mz en pruebas/ejemplos")
        for ruta in archivos:
            with self.subTest(archivo=os.path.relpath(ruta, RAIZ)):
                with open(ruta, encoding="utf-8") as f:
                    texto = f.read()
                primera = texto.splitlines()[0]
                self.assertIn("ESPERADO:", primera, "falta la línea // ESPERADO: ...")
                _, errores = analizar(texto)
                if "error lexico" in primera:
                    self.assertTrue(errores, "se esperaba al menos un error léxico")
                else:
                    self.assertEqual(errores, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
