"""Pruebas de compatibilidad, expresiones y reglas S3 a S7/S10."""
import unittest
import re
from pathlib import Path

from parser.convertidor import codigo_a_ast
from parser.nodo import Nodo
from semantico.semantico import analizar
from semantico.tipos import asignable, tipo_expresion


class TablaSimulada:
    """Tabla mínima para probar el contrato de tipos de forma aislada."""

    def __init__(self, simbolos=None):
        self.simbolos = simbolos or {}

    def buscar(self, nombre):
        return self.simbolos.get(nombre)


class PruebasTiposAisladas(unittest.TestCase):
    def test_asignable_solo_ensancha(self):
        casos_validos = (("char", "char"), ("int", "char"), ("float", "char"),
                         ("int", "int"), ("float", "int"), ("float", "float"))
        casos_invalidos = (("char", "int"), ("char", "float"), ("int", "float"),
                           ("int", "cadena"), ("cadena", "cadena"))
        for destino, valor in casos_validos:
            with self.subTest(destino=destino, valor=valor):
                self.assertTrue(asignable(destino, valor))
        for destino, valor in casos_invalidos:
            with self.subTest(destino=destino, valor=valor):
                self.assertFalse(asignable(destino, valor))

    def test_variable_consulta_la_tabla_simulada(self):
        variable = Nodo("Variable", valor="x", linea=4)
        self.assertEqual(tipo_expresion(variable, TablaSimulada({"x": {"tipo": "float"}}), []),
                         "float")
        self.assertEqual(variable.tipo_dato, "float")

    def test_operadores_anotan_su_resultado(self):
        suma = Nodo("OpBinario", [Nodo("Literal", valor="1", linea=1, tipo_dato="int"),
                                   Nodo("Literal", valor="2.0", linea=1, tipo_dato="float")],
                    valor="+", linea=1)
        negacion = Nodo("OpUnario", [suma], valor="!", linea=1)
        errores = []
        self.assertEqual(tipo_expresion(negacion, TablaSimulada(), errores), "int")
        self.assertEqual(suma.tipo_dato, "float")
        self.assertEqual(errores, [])


class PruebasTiposIntegradas(unittest.TestCase):
    def analizar_codigo(self, codigo):
        ast, errores = codigo_a_ast(codigo)
        self.assertEqual(errores, [])
        return analizar(ast)

    def errores_semanticos(self, codigo):
        _, _, errores = self.analizar_codigo(codigo)
        return [error for error in errores if not error["mensaje"].startswith("Aviso:")]

    def test_promociones_y_expresiones_validas(self):
        ast, _, errores = self.analizar_codigo(
            "char c = 'a'; int n = c; float f = n + 2.5; "
            "if (f >= c && !n) { printf(\"%f\", f); }")
        self.assertEqual(errores, [])
        self.assertEqual(ast.hijos[2].hijos[0].tipo_dato, "float")
        self.assertEqual(ast.hijos[3].hijos[0].tipo_dato, "int")

    def test_s3_rechaza_estrechamiento_y_cadena(self):
        for codigo, esperado in (("int n = 2.5;", "asignar un float a una variable int"),
                                  ('int n = "hola";', "asignar un cadena a una variable int")):
            with self.subTest(codigo=codigo):
                errores = self.errores_semanticos(codigo)
                self.assertEqual(len(errores), 1)
                self.assertIn(esperado, errores[0]["mensaje"])

    def test_s4_rechaza_cadena_y_modulo_con_float(self):
        for codigo, esperado in (("int n = \"a\" * 2;", "operador '*'"),
                                  ("int n = 2.5 % 2;", "operador '%'")):
            with self.subTest(codigo=codigo):
                errores = self.errores_semanticos(codigo)
                self.assertEqual(len(errores), 1)
                self.assertIn(esperado, errores[0]["mensaje"])

    def test_s5_s6_y_s7_rechazan_cadenas(self):
        casos = (("if (\"hola\") { }", "condición de if"),
                 ('int n = "a" && 1;', "operador '&&'"),
                 ('int n = "a" == 1;', "comparación '=='"),
                 ('int n = !"a";', "operador '!'") )
        for codigo, esperado in casos:
            with self.subTest(codigo=codigo):
                errores = self.errores_semanticos(codigo)
                self.assertEqual(len(errores), 1)
                self.assertIn(esperado, errores[0]["mensaje"])

    def test_s10_exige_cadena_literal_y_no_permite_cadenas_despues(self):
        for codigo, esperado in (("int n = 1; printf(n);", "primer argumento de printf"),
                                  ('printf("%s", "extra");', "cadena solo se permite")):
            with self.subTest(codigo=codigo):
                errores = self.errores_semanticos(codigo)
                self.assertEqual(len(errores), 1)
                self.assertIn(esperado, errores[0]["mensaje"])

    def test_no_encadena_el_error_de_una_subexpresion(self):
        for codigo in ('int n = "a" * 2;', 'printf("a" * 2);'):
            with self.subTest(codigo=codigo):
                errores = self.errores_semanticos(codigo)
                self.assertEqual(len(errores), 1)
                self.assertIn("operador '*'", errores[0]["mensaje"])

    def test_corpus_de_tipos_respeta_su_linea_esperada(self):
        ejemplos = Path(__file__).parent / "ejemplos"
        casos = (("validos", "08_char_y_promociones.c", 0),
                 ("invalidos", "10_cadena_en_entero.c", 1),
                 ("invalidos", "11_float_en_int.c", 1),
                 ("invalidos", "12_aritmetica_con_cadena.c", 1),
                 ("invalidos", "13_condicion_con_cadena.c", 1),
                 ("invalidos", "14_logico_con_cadena.c", 1),
                 ("invalidos", "16_modulo_con_float.c", 1),
                 ("invalidos", "17_printf_sin_cadena.c", 1),
                 ("invalidos", "18_comparacion_con_cadena.c", 1))
        for carpeta, nombre, cantidad in casos:
            with self.subTest(programa=nombre):
                ruta = ejemplos / carpeta / nombre
                codigo = ruta.read_text(encoding="utf-8")
                errores = self.errores_semanticos(codigo)
                self.assertEqual(len(errores), cantidad)
                if cantidad:
                    esperada = re.search(r"error semantico linea (\d+)", codigo.splitlines()[0])
                    self.assertIsNotNone(esperada)
                    self.assertEqual(errores[0]["linea"], int(esperada.group(1)))


if __name__ == "__main__":
    unittest.main()
