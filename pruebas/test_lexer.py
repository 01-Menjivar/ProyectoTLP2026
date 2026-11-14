"""Pruebas del lexer de mini-C. Desde la raíz del repositorio:

    python -m unittest pruebas.test_lexer          # solo las del lexer
    python -m unittest discover pruebas            # todas las del proyecto
"""
import glob
import os
import re
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
        self.assertEqual(tipos("int n = 3;"),
                         ["TIPO", "ID", "IGUAL", "ENTERO", "PUNTOYCOMA", "EOF"])

    def test_los_tres_tipos_de_dato(self):
        tokens, _ = analizar("int float char")
        self.assertEqual([t.tipo for t in tokens[:3]], ["TIPO"] * 3)

    def test_palabras_reservadas(self):
        self.assertEqual(tipos("if else while printf"),
                         ["IF", "ELSE", "WHILE", "PRINTF", "EOF"])

    def test_palabra_reservada_dentro_de_un_id_es_id(self):
        # "interior" empieza con "int" y "iffy" con "if", pero son identificadores completos
        self.assertEqual(tipos("interior iffy whiled"), ["ID", "ID", "ID", "EOF"])

    def test_flotante_entero_y_caracter(self):
        tokens, errores = analizar("2.50 42 'a'")
        self.assertEqual(errores, [])
        self.assertEqual([(t.tipo, t.lexema) for t in tokens[:3]],
                         [("FLOTANTE", "2.50"), ("ENTERO", "42"), ("CARACTER", "'a'")])

    def test_cadena_conserva_las_comillas(self):
        tokens, errores = analizar('printf("hola mundo");')
        self.assertEqual(errores, [])
        self.assertIn(("CADENA", '"hola mundo"'), [(t.tipo, t.lexema) for t in tokens])

    def test_escapes_en_cadenas_y_caracteres(self):
        tokens, errores = analizar(r'"a\"b\n" ' + r"'\n' '\''")
        self.assertEqual(errores, [])
        self.assertEqual([t.tipo for t in tokens], ["CADENA", "CARACTER", "CARACTER", "EOF"])

    def test_operadores_de_dos_caracteres(self):
        self.assertEqual(tipos("== != <= >= && ||"),
                         ["IGUAL_IGUAL", "DIFERENTE", "MENOR_IGUAL", "MAYOR_IGUAL",
                          "Y_LOGICO", "O_LOGICO", "EOF"])

    def test_igual_y_comparacion_no_se_confunden(self):
        self.assertEqual(tipos("a = b == c"), ["ID", "IGUAL", "ID", "IGUAL_IGUAL", "ID", "EOF"])

    def test_negacion_y_diferente_no_se_confunden(self):
        self.assertEqual(tipos("!a != b"), ["NO_LOGICO", "ID", "DIFERENTE", "ID", "EOF"])

    def test_operadores_aritmeticos_y_delimitadores(self):
        self.assertEqual(tipos("+ - * / % ( ) { } ; ,"),
                         ["MAS", "MENOS", "POR", "DIVIDIDO", "MODULO", "PAREN_IZQ", "PAREN_DER",
                          "LLAVE_IZQ", "LLAVE_DER", "PUNTOYCOMA", "COMA", "EOF"])

    def test_division_no_se_confunde_con_comentario(self):
        self.assertEqual(tipos("a / b"), ["ID", "DIVIDIDO", "ID", "EOF"])

    def test_comentario_de_linea_se_ignora(self):
        self.assertEqual(tipos("int a; // esto no cuenta\nint b;"),
                         ["TIPO", "ID", "PUNTOYCOMA", "TIPO", "ID", "PUNTOYCOMA", "EOF"])

    def test_comentario_de_bloque_se_ignora(self):
        self.assertEqual(tipos("int /* en medio */ a;"), ["TIPO", "ID", "PUNTOYCOMA", "EOF"])

    def test_comentario_de_bloque_de_varias_lineas_cuenta_las_lineas(self):
        tokens, errores = analizar("/* uno\ndos\ntres */ int x;")
        self.assertEqual(errores, [])
        tipo = tokens[0]
        self.assertEqual((tipo.tipo, tipo.linea, tipo.columna), ("TIPO", 3, 9))

    def test_cadena_con_ene_y_tildes(self):
        tokens, errores = analizar('"Compra pequeña"')
        self.assertEqual(errores, [])
        self.assertEqual(tokens[0].tipo, "CADENA")

    def test_linea_y_columna(self):
        tokens, _ = analizar("int a;\n  printf(a);")
        printf = [t for t in tokens if t.tipo == "PRINTF"][0]
        self.assertEqual((printf.linea, printf.columna), (2, 3))

    def test_siempre_termina_en_eof(self):
        tokens, _ = analizar("")
        self.assertEqual([t.tipo for t in tokens], ["EOF"])

    # ---------- errores léxicos ----------
    def test_caracter_invalido(self):
        tokens, errores = analizar("int x = 3 @ 4;")
        self.assertEqual(len(errores), 1)
        self.assertEqual((errores[0]["linea"], errores[0]["columna"]), (1, 11))
        self.assertIn("'@'", errores[0]["mensaje"])
        # el lexer sigue: los tokens de después del error existen
        self.assertEqual(tokens[-2].tipo, "PUNTOYCOMA")

    def test_la_enie_fuera_de_cadenas_es_invalida_en_c(self):
        _, errores = analizar("int año;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'ñ'", errores[0]["mensaje"])

    def test_ampersand_solo(self):
        _, errores = analizar("a & b")
        self.assertEqual(len(errores), 1)
        self.assertIn("&&", errores[0]["mensaje"])

    def test_barra_vertical_sola(self):
        _, errores = analizar("a | b")
        self.assertEqual(len(errores), 1)
        self.assertIn("||", errores[0]["mensaje"])

    def test_cadena_sin_cerrar(self):
        _, errores = analizar('printf("hola;')
        self.assertEqual(len(errores), 1)
        self.assertIn("sin cerrar", errores[0]["mensaje"])

    def test_caracter_con_dos_letras(self):
        _, errores = analizar("char c = 'ab';")
        self.assertEqual(len(errores), 1)
        self.assertIn("'ab'", errores[0]["mensaje"])

    def test_caracter_vacio(self):
        _, errores = analizar("char c = '';")
        self.assertEqual(len(errores), 1)

    def test_comentario_de_bloque_sin_cerrar(self):
        _, errores = analizar("int x;\n/* nunca se cierra\nint y;")
        self.assertEqual(len(errores), 1)
        self.assertEqual(errores[0]["linea"], 2)
        self.assertIn("*/", errores[0]["mensaje"])

    def test_numero_pegado_a_letra(self):
        _, errores = analizar("int x = 3a;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'3a'", errores[0]["mensaje"])

    def test_numero_con_punto_final(self):
        _, errores = analizar("float x = 3.;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'3.'", errores[0]["mensaje"])

    def test_numero_que_empieza_con_punto(self):
        _, errores = analizar("float x = .5;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'.5'", errores[0]["mensaje"])

    def test_numero_con_dos_puntos(self):
        _, errores = analizar("float x = 3.5.2;")
        self.assertEqual(len(errores), 1)
        self.assertIn("'3.5.2'", errores[0]["mensaje"])

    def test_varios_errores_en_un_mismo_programa(self):
        _, errores = analizar("int a = 1 # 2;\nint b = 3b;\nprintf(\"x;")
        self.assertEqual([e["linea"] for e in errores], [1, 2, 3])

    # ---------- corpus de programas .c ----------
    def test_corpus_coincide_con_lo_esperado_en_lexico(self):
        """Cada .c declara en su primera línea '// ESPERADO: ...'.
        Si espera 'error lexico', el lexer debe reportar errores (y el primero, en la línea indicada);
        en cualquier otro caso (ok, error semantico) no debe reportar ninguno."""
        archivos = sorted(glob.glob(os.path.join(EJEMPLOS, "*", "*.c")))
        self.assertTrue(archivos, "no se encontró ningún .c en pruebas/ejemplos")
        for ruta in archivos:
            with self.subTest(archivo=os.path.relpath(ruta, RAIZ)):
                with open(ruta, encoding="utf-8-sig") as f:
                    texto = f.read()
                primera = texto.splitlines()[0]
                self.assertIn("ESPERADO:", primera, "falta la línea // ESPERADO: ...")
                _, errores = analizar(texto)
                if "error lexico" in primera:
                    self.assertTrue(errores, "se esperaba al menos un error léxico")
                    linea = re.search(r"linea (\d+)", primera)
                    if linea:  # el primer error léxico debe estar en la línea indicada
                        self.assertEqual(errores[0]["linea"], int(linea.group(1)))
                else:
                    self.assertEqual(errores, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
