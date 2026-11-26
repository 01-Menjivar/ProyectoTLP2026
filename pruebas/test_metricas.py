"""Pruebas del set oficial de oraciones y del módulo de métricas y gráficas (Fase 2).

Desde la raíz del repositorio:
    python -m unittest pruebas.test_metricas
"""
import json
import os
import tempfile
import unittest

from comparacion import formato, metricas, propio
from parser.nodo import Nodo


class PruebasSetP2(unittest.TestCase):

    def test_set_cumple_minimos_y_formato(self):
        ruta = os.path.join("pruebas", "set_p2.json")
        oraciones = formato.cargar_oraciones(ruta)
        self.assertGreaterEqual(len(oraciones), 60)
        for nivel in (1, 2, 3):
            de_nivel = [o for o in oraciones if o["nivel"] == nivel]
            self.assertGreaterEqual(len(de_nivel), 15, f"Nivel {nivel} insuficiente")

        with open(ruta, encoding="utf-8") as f:
            crudo = json.load(f)
        for o in crudo:
            palabras = o["oracion"].rstrip(".").split()
            self.assertEqual(len(palabras), len(o["etiquetas"]), f"Etiquetas desalineadas en id={o['id']}")

    def test_propio_coincide_con_esperado_en_set_p2(self):
        ruta = os.path.join("pruebas", "set_p2.json")
        oraciones = formato.cargar_oraciones(ruta)
        with open(ruta, encoding="utf-8") as f:
            fenomenos = {o["id"]: o.get("fenomeno", "") for o in json.load(f)}

        resultados = propio.ejecutar(oraciones)
        formato.validar_todos(resultados)
        for r in resultados:
            self.assertEqual(r["aceptada"], r["esperado"], f"Fallo en id={r['id']}: {r['oracion']}")
            if not r["aceptada"] and not fenomenos[r["id"]].startswith("vocabulario_cerrado"):
                self.assertFalse(r.get("detalle", "").startswith("léxico"),
                                 f"Error léxico inesperado en id={r['id']}: {r.get('detalle')}")


class PruebasMetricas(unittest.TestCase):

    def test_calcular_confusion_y_tasas(self):
        registros = [
            formato.registro(1, "a", 1, True, "spacy", True, None, 2.0),    # TP
            formato.registro(2, "b", 1, True, "spacy", False, None, 4.0),   # FN
            formato.registro(3, "c", 3, False, "spacy", True, None, 6.0),   # FP
            formato.registro(4, "d", 3, False, "spacy", False, None, 8.0),  # TN
            formato.registro(5, "e", 3, False, "spacy", False, None, 10.0), # TN
        ]
        m = metricas.calcular_confusion(registros)
        self.assertEqual((m["tp"], m["fp"], m["fn"], m["tn"]), (1, 1, 1, 2))
        self.assertEqual(m["precision"], 0.5)
        self.assertEqual(m["recall"], 0.5)
        self.assertEqual(m["f1"], 0.5)
        self.assertEqual(m["exactitud"], 0.6)
        self.assertEqual(m["tasa_rechazo_correcto"], round(2 / 3, 4))
        self.assertEqual(m["tiempo_mediana_ms"], 6.0)
        self.assertEqual(m["tiempo_medio_ms"], 6.0)

    def test_division_por_cero_devuelve_none(self):
        registros = [formato.registro(1, "a", 1, True, "propio", False, None, 0.1)]
        m = metricas.calcular_confusion(registros)
        self.assertIsNone(m["precision"])
        self.assertIsNone(m["tasa_rechazo_correcto"])
        self.assertEqual(m["recall"], 0.0)

    def test_evalua_errores_de_etiquetado_spacy_y_hf(self):
        arbol_spacy = Nodo("ROOT", [
            Nodo("nsubj", valor={"lexema": "Yo", "pos": "PRON"}),
            Nodo("obj", [Nodo("det", valor={"lexema": "el", "pos": "DET"})], valor={"lexema": "libro", "pos": "NOUN"}),
        ], valor={"lexema": "leo", "pos": "PROPN"}).a_dict()
        arbol_hf = Nodo("Etiquetas", [
            Nodo("ADV", valor={"lexema": "Yo", "columna": 0}),
            Nodo("VERB", valor={"lexema": "leo", "columna": 0}),
            Nodo("DET", valor={"lexema": "el", "columna": 0}),
            Nodo("NOUN", valor={"lexema": "libro", "columna": 0}),
        ]).a_dict()
        mapa = {"1": {"id": 1, "etiquetas": ["PRON", "VERB", "DET", "NOUN"]}}

        pos_spacy = metricas.evaluar_etiquetado(
            [formato.registro(1, "Yo leo el libro.", 1, True, "spacy", False, arbol_spacy, 1.0)], mapa, "spacy"
        )
        self.assertEqual(pos_spacy["errores_etiquetado"], 1)
        self.assertEqual(pos_spacy["ejemplos_errores"][0]["palabra"], "leo")
        self.assertEqual(pos_spacy["ejemplos_errores"][0]["predicha"], "PROPN")

        pos_hf = metricas.evaluar_etiquetado(
            [formato.registro(1, "Yo leo el libro.", 1, True, "hf", False, arbol_hf, 1.0)], mapa, "hf"
        )
        self.assertEqual(pos_hf["errores_etiquetado"], 1)
        self.assertEqual(pos_hf["ejemplos_errores"][0]["palabra"], "Yo")
        self.assertEqual(pos_hf["ejemplos_errores"][0]["predicha"], "ADV")

    def test_hf_con_span_agrupado_de_dos_palabras(self):
        arbol_hf = Nodo("Etiquetas", [
            Nodo("ADV", valor={"lexema": "Yo no", "columna": 0}),
            Nodo("VERB", valor={"lexema": "leo", "columna": 0}),
        ]).a_dict()
        mapa = {"1": {"id": 1, "etiquetas": ["PRON", "ADV", "VERB"]}}
        pos_hf = metricas.evaluar_etiquetado(
            [formato.registro(1, "Yo no leo.", 3, False, "hf", False, arbol_hf, 1.0)], mapa, "hf"
        )
        self.assertEqual(pos_hf["tokens_evaluados"], 3)
        self.assertEqual(pos_hf["errores_etiquetado"], 1)
        self.assertEqual(pos_hf["ejemplos_errores"][0]["palabra"], "Yo")

    def test_causas_rechazo_y_exportacion_svg_md(self):
        registros = [
            formato.registro(1, "Yo leo el libro.", 1, True, "propio", True, None, 0.1),
            formato.registro(2, "Yo lee el libro.", 3, False, "propio", False, None, 0.1,
                             detalle="semantico (col 4): discrepancia"),
            formato.registro(3, "Yo leo el libro.", 1, True, "spacy", False, None, 4.0,
                             detalle="R1: raíz no es verbo; R2: sin sujeto"),
        ]
        resumen = metricas.resumir_resultados(registros)
        self.assertEqual(resumen["sistemas"]["propio"]["causas_rechazo"], {"semantico": 1})
        self.assertEqual(resumen["sistemas"]["spacy"]["causas_rechazo"], {"R1": 1, "R2": 1})

        with tempfile.TemporaryDirectory() as d:
            ruta_res = os.path.join(d, "res.json")
            formato.guardar(registros, ruta_res)
            outdir = os.path.join(d, "out")
            self.assertEqual(metricas.main(["--resultados", ruta_res, "--outdir", outdir]), 0)
            for nombre in ("metricas_resumen.json", "metricas_tablas.md",
                           "grafica_metricas_sistemas.svg", "grafica_aciertos_por_nivel.svg",
                           "grafica_errores_sistemas.svg", "grafica_tiempos_ms.svg"):
                self.assertTrue(os.path.exists(os.path.join(outdir, nombre)), nombre)
            with open(os.path.join(outdir, "grafica_metricas_sistemas.svg"), encoding="utf-8") as f:
                self.assertIn("<svg", f.read())


if __name__ == "__main__":
    unittest.main()
