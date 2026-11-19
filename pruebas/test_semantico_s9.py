"""Pruebas de avisos S9 y flujo de inicialización."""
import unittest
from parser.convertidor import codigo_a_ast
from semantico.semantico import analizar

class PruebasS9(unittest.TestCase):
    def test_caminos_y_ambitos(self):
        casos = [
            ('int x; printf("", x);', 1),
            ('int x; x = 1; printf("", x);', 0),
            ('int x = x;', 1),
            ('int x; if (1) { x = 1; } printf("", x);', 1),
            ('int x; if (1) { x = 1; } else { x = 2; } printf("", x);', 0),
            ('int x; if (1) { x = 1; } else { printf("", x); }', 1),
            ('int x; while (0) { x = 1; } printf("", x);', 1),
            ('int x = 1; { int x; printf("", x); } printf("", x);', 1),
            ('int x; { x = 1; } printf("", x);', 0),
            ('int x; { int x = 1; } printf("", x);', 1),
            ('printf("", desconocida);', 0),
            ('int x; x = desconocida; printf("", x);', 1),
        ]
        for codigo, cantidad in casos:
            with self.subTest(codigo=codigo):
                ast, errores = codigo_a_ast(codigo)
                self.assertEqual(errores, [])
                _, _, diagnosticos = analizar(ast)
                avisos = [e for e in diagnosticos if e["mensaje"].startswith("Aviso:")]
                self.assertEqual(len(avisos), cantidad)
                self.assertTrue(all(e["fase"] == "semantico" for e in avisos))

    def test_linea_del_aviso(self):
        ast, _ = codigo_a_ast('int x;\nprintf("", x);')
        _, tabla, errores = analizar(ast)
        self.assertEqual(errores[0]["linea"], 2)
        self.assertEqual(set(tabla[0]), {"nombre", "tipo", "ambito", "linea"})
