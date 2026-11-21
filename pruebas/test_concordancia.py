"""Integración del árbol de P4, las entradas léxicas de P1 y las reglas de P3."""
import unittest

from parser.nodo import Nodo
from semantico.concordancia import verificar_concordancia
from semantico.tabla_simbolos import TablaSimbolos


def hoja(tipo, lexema, columna=1, linea=1):
    return Nodo(tipo, valor={"lexema": lexema, "columna": columna}, linea=linea)


def nominal(det, nombre, *modificadores):
    return Nodo("SN", [hoja("DET", det), hoja("N", nombre), *modificadores])


class TestConcordancia(unittest.TestCase):
    def setUp(self):
        self.tabla = TablaSimbolos()
        for tipo, forma, genero, numero, persona in [
            ("DET", "la", "f", "sg", None), ("DET", "los", "m", "pl", None),
            ("N", "niña", "f", "sg", 3), ("N", "libros", "m", "pl", 3),
            ("N", "vecinos", "m", "pl", 3), ("ADJ", "nuevos", "m", "pl", None),
            ("ADJ", "vieja", "f", "sg", None), ("PRON", "yo", None, "sg", 1),
            ("PRON", "tú", None, "sg", 2), ("V_PRES", "leo", None, "sg", 1),
            ("V_PRES", "lee", None, "sg", 3), ("V_PRES", "leen", None, "pl", 3),
            ("V_PRET", "leíste", None, "sg", 2),
        ]:
            self.tabla.declarar(f"{tipo}:{forma}", tipo, 1, genero=genero,
                                numero=numero, persona=persona)
        self.objeto = nominal("los", "libros", hoja("ADJ", "nuevos"))
        self.sujeto = nominal("la", "niña", Nodo("SP", [
            hoja("PREP", "de"), nominal("los", "vecinos"),
        ]))

    def verificar(self, sujeto, verbo, objeto):
        arbol = Nodo("O", [sujeto, Nodo("SV", [verbo, objeto])])
        return verificar_concordancia(arbol, self.tabla)

    def test_concordancia_a_distancia(self):
        self.assertEqual(self.verificar(self.sujeto, hoja("V_PRES", "lee"), self.objeto), [])
        errores = self.verificar(self.sujeto, hoja("V_PRES", "leen", 7, 2), self.objeto)
        self.assertEqual(len(errores), 1)
        self.assertEqual((errores[0]["fase"], errores[0]["linea"], errores[0]["columna"]),
                         ("semantico", 2, 7))
        self.assertIn("'leen' discrepa en numero con 'niña'", errores[0]["mensaje"])

    def test_pronombres_en_ambos_tiempos(self):
        for sujeto, tiempo, verbo in [("Yo", "V_PRES", "leo"), ("Tú", "V_PRET", "leíste")]:
            with self.subTest(sujeto=sujeto):
                predicado = Nodo("SV", [hoja(tiempo, verbo), hoja("ADV", "bien"),
                                        self.objeto, hoja("ADV", "hoy")])
                arbol = Nodo("O", [hoja("PRON", sujeto), predicado])
                copia = Nodo.desde_json(arbol.a_json())
                self.assertEqual(verificar_concordancia(copia, self.tabla), [])

    def test_persona_incorrecta_con_numero_correcto(self):
        errores = self.verificar(hoja("PRON", "yo"), hoja("V_PRET", "leíste"), self.objeto)
        self.assertEqual(len(errores), 1)
        self.assertIn("persona", errores[0]["mensaje"])

    def test_diagnosticos_en_objeto_y_sp_anidado(self):
        interior = nominal("la", "libros")
        sp = Nodo("SP", [hoja("PREP", "de"), interior])
        self.sujeto.hijos[-1].hijos[1].hijos.append(sp)
        self.objeto.hijos.append(hoja("ADJ", "vieja", 12))
        errores = self.verificar(self.sujeto, hoja("V_PRES", "lee"), self.objeto)
        self.assertEqual(len(errores), 4)
        for error, palabra, campo in zip(errores, ["la", "la", "vieja", "vieja"],
                                         ["genero", "numero", "genero", "numero"]):
            self.assertIn(f"'{palabra}' discrepa en {campo} con 'libros'", error["mensaje"])

    def test_entrada_ausente_o_incompleta(self):
        hoja_verbo = hoja("V_PRES", "mira")
        with self.assertRaisesRegex(ValueError, "Falta la entrada"):
            self.verificar(self.sujeto, hoja_verbo, self.objeto)
        self.tabla.declarar("V_PRES:mira", "V_PRES", 1, numero="sg")
        with self.assertRaisesRegex(ValueError, "Rasgos incompletos"):
            self.verificar(self.sujeto, hoja_verbo, self.objeto)
