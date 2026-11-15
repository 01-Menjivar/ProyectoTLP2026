"""Pruebas de P3: tabla de símbolos y reglas S1, S2, S8."""
import unittest
from pathlib import Path

from parser.convertidor import codigo_a_ast
from parser.nodo import Nodo
from semantico.semantico import analizar
from semantico.tabla_simbolos import TablaSimbolos


class PruebasTablaSimbolos(unittest.TestCase):
    def test_redeclarar_no_sobrescribe_el_simbolo(self):
        tabla = TablaSimbolos()
        self.assertTrue(tabla.declarar("x", "int", 2))
        self.assertFalse(tabla.declarar("x", "float", 3))
        self.assertEqual(tabla.buscar("x")["tipo"], "int")
        self.assertEqual(len(tabla.a_lista()), 1)

    def test_sombreado_y_restauracion(self):
        tabla = TablaSimbolos()
        tabla.declarar("x", "int", 1)
        tabla.abrir_ambito()
        tabla.declarar("x", "float", 2)
        self.assertEqual(tabla.buscar("x")["tipo"], "float")
        tabla.cerrar_ambito()
        self.assertEqual(tabla.buscar("x")["tipo"], "int")
        self.assertEqual(len(tabla.a_lista()), 2)

    def test_ambitos_hermanos_tienen_identificadores_distintos(self):
        tabla = TablaSimbolos()
        for _ in range(2):
            tabla.abrir_ambito()
            tabla.declarar("local", "int", 1)
            tabla.cerrar_ambito()
        self.assertIsNone(tabla.buscar("local"))
        self.assertEqual([s["ambito"] for s in tabla.a_lista()], [1, 2])

    def test_no_se_cierra_el_global(self):
        with self.assertRaises(ValueError):
            TablaSimbolos().cerrar_ambito()

    def test_las_consultas_no_permiten_modificar_la_tabla(self):
        tabla = TablaSimbolos()
        tabla.declarar("x", "int", 1)
        tabla.buscar("x")["tipo"] = "float"
        tabla.a_lista()[0]["tipo"] = "char"
        self.assertEqual(tabla.buscar("x")["tipo"], "int")


class PruebasSemanticoP3(unittest.TestCase):
    def analizar_codigo(self, codigo):
        ast, errores = codigo_a_ast(codigo)
        self.assertEqual(errores, [])
        ast, tabla, errores = analizar(ast)
        return ast, tabla, [e for e in errores if not e["mensaje"].startswith("Aviso:")]

    def test_destino_y_operandos_no_declarados(self):
        _, tabla, errores = self.analizar_codigo("total = a + -b;")
        self.assertEqual(tabla, [])
        self.assertEqual(len(errores), 3)
        for error, nombre in zip(errores, ("total", "a", "b")):
            self.assertIn(f"'{nombre}'", error["mensaje"])
            self.assertEqual((error["fase"], error["linea"], error["columna"]),
                             ("semantico", 1, 1))

    def test_declaracion_posterior_no_valida_el_uso_previo(self):
        _, _, errores = self.analizar_codigo("printf(\"%d\", x);\nint x = 1;")
        self.assertEqual(len(errores), 1)
        self.assertEqual(errores[0]["linea"], 1)

    def test_redeclaracion_informa_la_linea_original(self):
        _, tabla, errores = self.analizar_codigo("int x = 1;\nfloat x = 2.0;")
        self.assertEqual(len(errores), 1)
        self.assertIn("Redeclaración", errores[0]["mensaje"])
        self.assertIn("línea 1", errores[0]["mensaje"])
        self.assertEqual(errores[0]["linea"], 2)
        self.assertEqual(len(tabla), 1)

    def test_bloque_no_exporta_variables(self):
        _, _, errores = self.analizar_codigo("{ int local = 1; }\nlocal = 2;")
        self.assertEqual(len(errores), 1)
        self.assertEqual(errores[0]["linea"], 2)

    def test_sombreado_anota_el_tipo_visible_y_restaura_el_externo(self):
        ast, tabla, errores = self.analizar_codigo(
            'int x = 1; { float x = 2.0; printf("%f", x); } printf("%d", x);')
        self.assertEqual(errores, [])
        self.assertEqual(ast.hijos[1].hijos[1].hijos[1].tipo_dato, "float")
        self.assertEqual(ast.hijos[2].hijos[1].tipo_dato, "int")
        self.assertEqual([s["ambito"] for s in tabla], [0, 1])

    def test_revisa_condicion_y_ambas_ramas_sin_compartir_locales(self):
        _, _, errores = self.analizar_codigo(
            'if (cond) { int x = 1; } else { printf("%d", x); }')
        self.assertEqual(len(errores), 2)
        self.assertIn("'cond'", errores[0]["mensaje"])
        self.assertIn("'x'", errores[1]["mensaje"])

    def test_while_se_analiza_una_vez_y_cierra_su_ambito(self):
        _, tabla, errores = self.analizar_codigo(
            'int n = 1; while (n) { int local = n; n = n - 1; } printf("%d", local);')
        self.assertEqual(len(tabla), 2)
        self.assertEqual(len(errores), 1)
        self.assertIn("'local'", errores[0]["mensaje"])

    def test_se_puede_declarar_sin_inicializador_y_asignar_despues(self):
        _, _, errores = self.analizar_codigo('int x; x = 1; printf("%d", x);')
        self.assertEqual(errores, [])

    def test_el_nombre_es_visible_en_su_inicializador_como_en_c(self):
        _, _, errores = self.analizar_codigo("int x = x;")
        self.assertEqual(errores, [])  # La visibilidad no produce error; S9 se prueba por separado.

    def test_cada_analisis_tiene_tabla_independiente(self):
        self.analizar_codigo("int x = 1;")
        _, tabla, errores = self.analizar_codigo("x = 2;")
        self.assertEqual(tabla, [])
        self.assertEqual(len(errores), 1)

    def test_ast_manual_y_ast_del_convertidor(self):
        ejemplos = Path(__file__).parent / "ejemplos"
        for nombre, carpeta, cantidad in (("07_ambitos_y_bloques", "validos", 0),
                                          ("08_variable_no_declarada", "invalidos", 1),
                                          ("09_redeclaracion", "invalidos", 1),
                                          ("15_variable_fuera_de_su_ambito", "invalidos", 1)):
            with self.subTest(nombre=nombre):
                manual = Nodo.desde_json((ejemplos / "ast" / f"{nombre}.json").read_text(encoding="utf-8"))
                automatico, tabla, errores = self.analizar_codigo(
                    (ejemplos / carpeta / f"{nombre}.c").read_text(encoding="utf-8"))
                _, tabla_manual, errores_manual = analizar(manual)
                self.assertEqual(len(errores), cantidad)
                self.assertEqual((tabla_manual, errores_manual), (tabla, errores))
                self.assertEqual(manual.a_dict(), automatico.a_dict())

    def test_corpus_valido_no_tiene_errores_de_p3(self):
        for ruta in (Path(__file__).parent / "ejemplos" / "validos").glob("*.c"):
            with self.subTest(programa=ruta.name):
                _, _, errores = self.analizar_codigo(ruta.read_text(encoding="utf-8"))
                self.assertEqual(errores, [])



    def test_tres_niveles_restauran_el_nombre_mas_cercano(self):
        ast, _, errores = self.analizar_codigo(
            'int x; { float x; { char x; printf("", x); } printf("", x); } printf("", x);')
        self.assertEqual(errores, [])
        bloque = ast.hijos[1]
        self.assertEqual(bloque.hijos[1].hijos[1].hijos[1].tipo_dato, "char")
        self.assertEqual(bloque.hijos[2].hijos[1].tipo_dato, "float")
        self.assertEqual(ast.hijos[2].hijos[1].tipo_dato, "int")

    def test_error_en_bloque_no_impide_revisar_sentencias_posteriores(self):
        _, tabla, errores = self.analizar_codigo(
            '{ int x; int x; }\nint x;\ny = x;')
        self.assertEqual([e["linea"] for e in errores], [1, 3])
        self.assertEqual([s["ambito"] for s in tabla], [1, 0])

    def test_redeclaracion_no_oculta_errores_del_inicializador(self):
        _, tabla, errores = self.analizar_codigo('int x; float x = desconocida;')
        self.assertEqual(len(errores), 2)
        self.assertEqual(tabla[0]["tipo"], "int")
        self.assertIn("desconocida", errores[1]["mensaje"])

    def test_declaracion_del_cuerpo_no_es_visible_en_condicion(self):
        _, _, errores = self.analizar_codigo('while (x) { int x = 0; }')
        self.assertEqual(len(errores), 1)
        self.assertIn("'x'", errores[0]["mensaje"])

    def test_reanalizar_el_mismo_ast_no_duplica_diagnosticos(self):
        ast, tabla, errores = self.analizar_codigo('int x; { int x; } y = x;')
        _, tabla, errores = analizar(ast)
        _, segunda_tabla, segundos_errores = analizar(ast)
        self.assertEqual((segunda_tabla, segundos_errores), (tabla, errores))


if __name__ == "__main__":
    unittest.main()
