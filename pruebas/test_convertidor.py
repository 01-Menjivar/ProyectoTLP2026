"""Pruebas del convertidor de tokens a AST."""
import json
import unittest
from pathlib import Path

from lexer.lexer import analizar
from parser.convertidor import codigo_a_ast, tokens_a_ast

RAIZ = Path(__file__).resolve().parent
EJEMPLOS = RAIZ / "ejemplos"


def ast_de(codigo):
    """AST (como dict) de un programa que debe ser válido."""
    raiz, errores = codigo_a_ast(codigo)
    assert not errores, errores
    return raiz


def forma(nodo):
    """Resumen corto de un nodo: 'tipo(valor)[hijos]'. Facilita comparar la estructura."""
    valor = nodo.valor["nombre"] if nodo.tipo == "Declaracion" else nodo.valor
    texto = f"{nodo.tipo}({valor})" if valor is not None else nodo.tipo
    return texto + ("[" + ", ".join(forma(h) for h in nodo.hijos) + "]" if nodo.hijos else "")


class PruebasConvertidor(unittest.TestCase):
    def test_reproduce_los_ast_hechos_a_mano(self):
        """Para cada JSON de ejemplo, el convertidor debe producir exactamente el mismo árbol."""
        for ruta in sorted((EJEMPLOS / "ast").glob("*.json")):
            with self.subTest(ruta.name):
                fuente = next(p for d in ("validos", "invalidos")
                              if (p := EJEMPLOS / d / f"{ruta.stem}.c").exists())
                raiz = ast_de(fuente.read_text(encoding="utf-8"))
                self.assertEqual(raiz.a_dict(), json.loads(ruta.read_text(encoding="utf-8")))

    def test_corpus_sin_errores_lexicos_da_un_ast(self):
        """Todo programa del corpus que el lexer acepta se convierte sin errores sintácticos."""
        for ruta in sorted(EJEMPLOS.glob("*/*.c")):
            esperado = ruta.read_text(encoding="utf-8").splitlines()[0]
            with self.subTest(ruta.name):
                raiz, errores = codigo_a_ast(ruta.read_text(encoding="utf-8"))
                if "error lexico" in esperado:
                    self.assertIsNone(raiz)
                    self.assertTrue(errores and all(e["fase"] == "lexico" for e in errores))
                else:
                    self.assertEqual(errores, [])
                    self.assertEqual(raiz.tipo, "Programa")

    def test_precedencia_multiplicar_antes_que_sumar(self):
        raiz = ast_de("int x = 2 + 3 * 4;")
        self.assertEqual(forma(raiz.hijos[0].hijos[0]),
                         "OpBinario(+)[Literal(2), OpBinario(*)[Literal(3), Literal(4)]]")

    def test_parentesis_cambian_la_precedencia_y_no_dejan_nodo(self):
        raiz = ast_de("int x = (2 + 3) * 4;")
        self.assertEqual(forma(raiz.hijos[0].hijos[0]),
                         "OpBinario(*)[OpBinario(+)[Literal(2), Literal(3)], Literal(4)]")

    def test_los_binarios_son_asociativos_por_la_izquierda(self):
        raiz = ast_de("int x = 10 - 3 - 2;")
        self.assertEqual(forma(raiz.hijos[0].hijos[0]),
                         "OpBinario(-)[OpBinario(-)[Literal(10), Literal(3)], Literal(2)]")

    def test_precedencia_de_logicos_y_comparaciones(self):
        raiz = ast_de("int x = 1 < 2 && 3 == 3 || 0;")
        self.assertEqual(forma(raiz.hijos[0].hijos[0]),
                         "OpBinario(||)[OpBinario(&&)[OpBinario(<)[Literal(1), Literal(2)], "
                         "OpBinario(==)[Literal(3), Literal(3)]], Literal(0)]")

    def test_operadores_unarios(self):
        raiz = ast_de("int a = 1; int x = -a; int y = !a; int z = - -a;")
        self.assertEqual(forma(raiz.hijos[1].hijos[0]), "OpUnario(-)[Variable(a)]")
        self.assertEqual(forma(raiz.hijos[2].hijos[0]), "OpUnario(!)[Variable(a)]")
        self.assertEqual(forma(raiz.hijos[3].hijos[0]), "OpUnario(-)[OpUnario(-)[Variable(a)]]")

    def test_el_menos_unario_liga_mas_que_la_multiplicacion(self):
        raiz = ast_de("int x = -2 * 3;")
        self.assertEqual(forma(raiz.hijos[0].hijos[0]), "OpBinario(*)[OpUnario(-)[Literal(2)], Literal(3)]")

    def test_declaracion_sin_valor_inicial_no_tiene_hijos(self):
        raiz = ast_de("int sin_valor;")
        self.assertEqual(raiz.hijos[0].hijos, [])

    def test_literales_traen_su_tipo(self):
        raiz = ast_de("int a = 1; float b = 2.5; char c = 'z'; printf(\"hola\");")
        tipos = [raiz.hijos[0].hijos[0].tipo_dato, raiz.hijos[1].hijos[0].tipo_dato,
                 raiz.hijos[2].hijos[0].tipo_dato, raiz.hijos[3].hijos[0].tipo_dato]
        self.assertEqual(tipos, ["int", "float", "char", "cadena"])

    def test_if_con_y_sin_else(self):
        raiz = ast_de("if (1) { } if (1) { } else { }")
        self.assertEqual(len(raiz.hijos[0].hijos), 2)
        self.assertEqual(len(raiz.hijos[1].hijos), 3)
        self.assertTrue(all(h.tipo == "Bloque" for h in raiz.hijos[1].hijos[1:]))

    def test_printf_con_varios_argumentos(self):
        raiz = ast_de('int a = 1; printf("%d %d", a, 2);')
        self.assertEqual(forma(raiz.hijos[1]), 'Printf[Literal("%d %d"), Variable(a), Literal(2)]')

    def test_printf_sin_cadena_es_sintacticamente_valido(self):
        """printf(x) lo rechaza el semántico (S10), no el convertidor."""
        raiz = ast_de("int x = 1; printf(x);")
        self.assertEqual(forma(raiz.hijos[1]), "Printf[Variable(x)]")

    def test_las_lineas_salen_de_los_tokens(self):
        raiz = ast_de("\n\nint a = 1;\n\nwhile (a < 3) {\n    a = a + 1;\n}\n")
        mientras = raiz.hijos[1]
        self.assertEqual((raiz.hijos[0].linea, mientras.linea, mientras.hijos[1].hijos[0].linea), (3, 5, 6))

    # --- errores sintácticos ---

    def errores_de(self, codigo):
        raiz, errores = codigo_a_ast(codigo)
        self.assertIsNone(raiz)
        return errores

    def test_falta_punto_y_coma(self):
        errores = self.errores_de("int a = 1\nint b = 2;")
        self.assertEqual(len(errores), 1)
        self.assertEqual((errores[0]["fase"], errores[0]["linea"]), ("sintactico", 2))
        self.assertIn("';'", errores[0]["mensaje"])

    def test_falta_expresion(self):
        errores = self.errores_de("int a = ;")
        self.assertIn("expresión", errores[0]["mensaje"])

    def test_if_sin_llaves_no_se_acepta(self):
        errores = self.errores_de("if (1) printf(\"x\");")
        self.assertIn("'{'", errores[0]["mensaje"])

    def test_else_if_sin_llaves_no_se_acepta(self):
        errores = self.errores_de("if (1) { } else if (2) { }")
        self.assertIn("'{'", errores[0]["mensaje"])

    def test_bloque_sin_cerrar(self):
        errores = self.errores_de("while (1) {\n int a = 1;\n")
        self.assertIn("'}'", errores[0]["mensaje"])

    def test_llave_sobrante_no_cuelga_el_convertidor(self):
        errores = self.errores_de("int a = 1; }")
        self.assertEqual(errores[0]["fase"], "sintactico")

    def test_se_recupera_y_reporta_varios_errores(self):
        errores = self.errores_de("int a = ;\nint b = 2;\nint = 3;\n")
        self.assertEqual([e["linea"] for e in errores], [1, 3])

    def test_error_lexico_impide_construir_el_arbol(self):
        raiz, errores = codigo_a_ast("int a = 1 @ 2;")
        self.assertIsNone(raiz)
        self.assertEqual(errores[0]["fase"], "lexico")

    def test_tokens_a_ast_acepta_la_lista_del_lexer(self):
        tokens, _ = analizar("int a = 1;")
        raiz, errores = tokens_a_ast(tokens)
        self.assertEqual((raiz.tipo, errores), ("Programa", []))


if __name__ == "__main__":
    unittest.main()
