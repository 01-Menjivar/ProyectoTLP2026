"""Pruebas de la comparación con spaCy y HuggingFace (Fase 2, P1).

Prueban la lógica de decisión con datos hechos a mano, así que NO necesitan spaCy ni
HuggingFace instalados. Desde la raíz del repositorio:

    python -m unittest pruebas.test_comparacion
"""
import json
import os
import tempfile
import unittest

from comparacion import formato, hf_sistema, propio, spacy_sistema
from comparacion.ejecutar import main, mediana_de_corridas, resumen


def tok(i, text, pos, dep, head, **morph):
    return {"i": i, "text": text, "pos": pos, "dep": dep, "head": head, "morph": morph}


def oracion_spacy(verbo="lee", verbo_numero="Sing", adj="nuevos", adj_genero="Masc"):
    """'La niña de los vecinos lee los libros nuevos.' tal como lo analizaría spaCy."""
    return [
        tok(0, "La", "DET", "det", 1, Gender="Fem", Number="Sing"),
        tok(1, "niña", "NOUN", "nsubj", 5, Gender="Fem", Number="Sing"),
        tok(2, "de", "ADP", "case", 4),
        tok(3, "los", "DET", "det", 4, Gender="Masc", Number="Plur"),
        tok(4, "vecinos", "NOUN", "nmod", 1, Gender="Masc", Number="Plur"),
        tok(5, verbo, "VERB", "ROOT", 5, Number=verbo_numero, Person="3"),
        tok(6, "los", "DET", "det", 7, Gender="Masc", Number="Plur"),
        tok(7, "libros", "NOUN", "obj", 5, Gender="Masc", Number="Plur"),
        tok(8, adj, "ADJ", "amod", 7, Gender=adj_genero, Number="Plur"),
        tok(9, ".", "PUNCT", "punct", 5),
    ]


class PruebasFormato(unittest.TestCase):

    def valido(self, **cambios):
        r = formato.registro(1, "Yo leo el libro.", 1, True, "propio", True, None, 0.5)
        r.update(cambios)
        return r

    def test_registro_valido(self):
        formato.validar(self.valido())
        formato.validar(self.valido(arbol={"tipo": "O"}, detalle="algo"))

    def test_rechaza_registros_mal_formados(self):
        malos = [
            {"nivel": 4}, {"nivel": "1"}, {"esperado": "aceptada"}, {"aceptada": 1},
            {"sistema": "otro"}, {"arbol": "texto"}, {"tiempo_ms": -1}, {"tiempo_ms": "3"}, {"oracion": "  "},
        ]
        for cambio in malos:
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                formato.validar(self.valido(**cambio))

    def test_falta_un_campo(self):
        r = self.valido()
        del r["tiempo_ms"]
        with self.assertRaises(ValueError):
            formato.validar(r)

    def test_cargar_oraciones_acepta_texto_o_booleano(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "set.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump([{"id": 1, "oracion": "a", "nivel": 1, "esperado": "aceptada"},
                           {"id": 2, "oracion": "b", "nivel": 2, "esperado": False}], f)
            self.assertEqual([o["esperado"] for o in formato.cargar_oraciones(ruta)], [True, False])

    def test_cargar_oraciones_con_valor_desconocido(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "set.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump([{"id": 1, "oracion": "a", "nivel": 1, "esperado": "quizás"}], f)
            with self.assertRaises(ValueError):
                formato.cargar_oraciones(ruta)

    def test_el_conjunto_de_ejemplo_es_valido(self):
        oraciones = formato.cargar_oraciones(os.path.join("comparacion", "oraciones_ejemplo.json"))
        self.assertGreaterEqual(len(oraciones), 12)
        self.assertEqual({o["nivel"] for o in oraciones}, {1, 2, 3})


class PruebasPropio(unittest.TestCase):

    def test_acepta_y_rechaza(self):
        self.assertTrue(propio.evaluar("Yo leo el libro.")[0])
        self.assertFalse(propio.evaluar("Yo leo los libros nuevas.")[0])
        self.assertFalse(propio.evaluar("Yo leo el libro la niña.")[0])

    def test_palabra_fuera_del_lexico_se_rechaza_con_motivo(self):
        aceptada, arbol, detalle = propio.evaluar("Yo leo el xyzzy.")
        self.assertFalse(aceptada)
        self.assertIsNone(arbol)
        self.assertIn("léxico", detalle)

    def test_el_conjunto_de_ejemplo_coincide_con_lo_esperado(self):
        oraciones = formato.cargar_oraciones(os.path.join("comparacion", "oraciones_ejemplo.json"))
        resultados = propio.ejecutar(oraciones)
        formato.validar_todos(resultados)
        for r in resultados:
            self.assertEqual(r["aceptada"], r["esperado"], r["oracion"])


class PruebasSpacy(unittest.TestCase):

    def test_oracion_correcta(self):
        self.assertEqual(spacy_sistema.decidir(oracion_spacy()), (True, []))

    def test_r4_verbo_en_plural_con_sujeto_singular(self):
        ok, motivos = spacy_sistema.decidir(oracion_spacy(verbo="leen", verbo_numero="Plur"))
        self.assertFalse(ok)
        self.assertIn("discrepa en número con 'niña'", motivos[0])

    def test_r4_adjetivo_con_otro_genero(self):
        ok, motivos = spacy_sistema.decidir(oracion_spacy(adj="nuevas", adj_genero="Fem"))
        self.assertFalse(ok)
        self.assertIn("'nuevas' discrepa en género con 'libros'", motivos[0])

    def test_r4_pronombre_y_verbo_en_distinta_persona(self):
        toks = [
            tok(0, "Yo", "PRON", "nsubj", 1, Number="Sing", Person="1"),
            tok(1, "lee", "VERB", "ROOT", 1, Number="Sing", Person="3"),
            tok(2, "el", "DET", "det", 3, Gender="Masc", Number="Sing"),
            tok(3, "libro", "NOUN", "obj", 1, Gender="Masc", Number="Sing"),
        ]
        ok, motivos = spacy_sistema.decidir(toks)
        self.assertFalse(ok)
        self.assertIn("persona", motivos[0])

    def test_r3_sin_objeto(self):
        toks = [tok(0, "Yo", "PRON", "nsubj", 1, Number="Sing", Person="1"),
                tok(1, "leo", "VERB", "ROOT", 1, Number="Sing", Person="1")]
        ok, motivos = spacy_sistema.decidir(toks)
        self.assertFalse(ok)
        self.assertIn("R3", motivos[0])

    def test_r1_la_raiz_no_es_verbo(self):
        ok, motivos = spacy_sistema.decidir([tok(0, "libro", "NOUN", "ROOT", 0)])
        self.assertFalse(ok)
        self.assertIn("R1", motivos[0])

    def test_sin_rasgos_no_se_inventa_una_discrepancia(self):
        toks = oracion_spacy()
        toks[8]["morph"] = {}                           # spaCy no dio género ni número del adjetivo
        self.assertTrue(spacy_sistema.decidir(toks)[0])

    def test_arbol_de_dependencias(self):
        nodo = spacy_sistema.a_nodo(oracion_spacy())
        self.assertEqual((nodo.tipo, nodo.valor["lexema"]), ("ROOT", "lee"))
        self.assertEqual({h.tipo for h in nodo.hijos}, {"nsubj", "obj", "punct"})


class PruebasHuggingFace(unittest.TestCase):

    def pares(self, texto):
        return [tuple(p.split("/")) for p in texto.split()]

    def test_oracion_que_encaja(self):
        pares = self.pares("La/DET niña/NOUN de/ADP los/DET vecinos/NOUN lee/VERB los/DET libros/NOUN nuevos/ADJ ./PUNCT")
        self.assertEqual(hf_sistema.decidir(pares), (True, []))

    def test_pronombre_y_adverbios(self):
        self.assertTrue(hf_sistema.decidir(self.pares("Yo/PRON leo/VERB bien/ADV el/DET libro/NOUN hoy/ADV"))[0])

    def test_no_detecta_errores_de_concordancia(self):
        # 'leen' en plural con sujeto singular: la estructura es válida, así que HF la acepta
        pares = self.pares("La/DET niña/NOUN de/ADP los/DET vecinos/NOUN leen/VERB los/DET libros/NOUN nuevos/ADJ")
        self.assertTrue(hf_sistema.decidir(pares)[0])

    def test_texto_sobrante_se_rechaza(self):
        ok, motivos = hf_sistema.decidir(self.pares("Yo/PRON leo/VERB el/DET libro/NOUN la/DET niña/NOUN"))
        self.assertFalse(ok)
        self.assertIn("PRON V DET N DET N", motivos[0])

    def test_etiqueta_fuera_de_la_gramática(self):
        ok, motivos = hf_sistema.decidir(self.pares("Yo/PRON leo/VERB tres/NUM libros/NOUN"))
        self.assertFalse(ok)
        self.assertIn("NUM", motivos[0])

    def test_etiquetas_quita_prefijos_y_acepta_entity(self):
        salida = [{"word": "Yo", "entity_group": "B-PRON"}, {"word": "leo", "entity": "I-VERB"}]
        self.assertEqual(hf_sistema.etiquetas(salida), [("Yo", "PRON"), ("leo", "VERB")])

    def test_une_los_fragmentos_de_una_palabra_partida(self):
        # BERT parte "leen" en "lee" + "##n" y etiqueta cada fragmento distinto
        salida = [{"word": "niño", "entity_group": "NOUN"}, {"word": "lee", "entity_group": "VERB"},
                  {"word": "##n", "entity_group": "AUX"}, {"word": "el", "entity_group": "DET"}]
        self.assertEqual(hf_sistema.etiquetas(salida),
                         [("niño", "NOUN"), ("leen", "VERB"), ("el", "DET")])

    def test_arbol_plano(self):
        nodo = hf_sistema.a_nodo(self.pares("Yo/PRON leo/VERB"))
        self.assertEqual([h.tipo for h in nodo.hijos], ["PRON", "VERB"])


class PruebasEjecutar(unittest.TestCase):

    def test_corre_el_sistema_propio_y_guarda_resultados_validos(self):
        with tempfile.TemporaryDirectory() as d:
            salida = os.path.join(d, "r.json")
            codigo = main(["--sistemas", "propio", "--salida", salida])
            self.assertEqual(codigo, 0)
            with open(salida, encoding="utf-8") as f:
                resultados = json.load(f)
        formato.validar_todos(resultados)
        self.assertEqual({r["sistema"] for r in resultados}, {"propio"})

    def test_repeticiones_guardan_la_mediana_del_tiempo(self):
        def corrida(*tiempos):
            return [formato.registro(i, "a", 1, True, "propio", True, None, t) for i, t in enumerate(tiempos)]
        r = mediana_de_corridas([corrida(1.0, 10.0), corrida(3.0, 30.0), corrida(2.0, 20.0)])
        self.assertEqual([x["tiempo_ms"] for x in r], [2.0, 20.0])

    def test_corre_con_repeticiones(self):
        with tempfile.TemporaryDirectory() as d:
            salida = os.path.join(d, "r.json")
            self.assertEqual(main(["--sistemas", "propio", "--repeticiones", "3", "--salida", salida]), 0)
            with open(salida, encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)), 14)       # una fila por oración, no tres

    def test_resumen(self):
        rs = [formato.registro(1, "a", 1, True, "propio", True, None, 1.0),
              formato.registro(2, "b", 1, True, "propio", False, None, 3.0)]
        texto = resumen(rs)
        self.assertIn("propio", texto)
        self.assertIn("1/2", texto)
        self.assertIn("2.00", texto)


if __name__ == "__main__":
    unittest.main()
