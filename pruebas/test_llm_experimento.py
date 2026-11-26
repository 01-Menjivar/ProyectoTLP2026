"""Pruebas unitarias para el módulo de experimento con LLM."""
import json
import os
import tempfile
import unittest

from comparacion import formato, llm_experimento


class TestLLMExperimento(unittest.TestCase):
    def test_prompts_zero_shot_y_few_shot(self):
        zero = llm_experimento.construir_prompt_sistema("zero-shot")
        few = llm_experimento.construir_prompt_sistema("few-shot")

        # Ambos incluyen las producciones EBNF y condiciones de concordancia.
        for regla in ("O  ::= ( PRON | SN ) SV", "SN ::= DET N { ADJ } [ SP ]", "SP ::= PREP SN"):
            self.assertIn(regla, zero)
            self.assertIn(regla, few)

        # Zero-shot no incluye ejemplos etiquetados; few-shot sí.
        self.assertNotIn("## Ejemplos etiquetados", zero)
        self.assertIn("## Ejemplos etiquetados", few)
        self.assertGreater(len(few), len(zero))

    def test_ejemplos_few_shot_sin_fuga_de_datos(self):
        """Ninguna oración de few-shot debe repetirse literalmente en pruebas/set_p2.json."""
        oraciones_set = {
            o["oracion"].strip().casefold()
            for o in formato.cargar_oraciones("pruebas/set_p2.json")
        }
        for ej in llm_experimento.EJEMPLOS_FEW_SHOT:
            self.assertNotIn(ej["oracion"].strip().casefold(), oraciones_set)

    def test_parsear_respuesta_llm_json_y_respaldo(self):
        # JSON limpio
        r1 = llm_experimento.parsear_respuesta_llm(
            '{"veredicto": "aceptada", "categoria_error": "ninguno", "motivo": "OK"}'
        )
        self.assertTrue(r1["aceptada"])
        self.assertTrue(r1["parse_ok"])
        self.assertEqual(r1["veredicto"], "aceptada")

        # JSON dentro de bloque Markdown
        r2 = llm_experimento.parsear_respuesta_llm(
            '```json\n{"veredicto": "rechazada", "categoria_error": "concordancia", "motivo": "Discrepa"}\n```'
        )
        self.assertFalse(r2["aceptada"])
        self.assertTrue(r2["parse_ok"])
        self.assertEqual(r2["categoria_error"], "concordancia")

        # Texto plano de respaldo
        r3 = llm_experimento.parsear_respuesta_llm("La oración debe ser rechazada por sujeto tácito.")
        self.assertFalse(r3["aceptada"])
        self.assertFalse(r3["parse_ok"])
        self.assertEqual(r3["veredicto"], "rechazada")

    def test_ejecutar_resumir_y_exportar_mock(self):
        oraciones = [
            {"id": 1, "oracion": "Yo leo el libro.", "nivel": 1, "esperado": True},
            {"id": 23, "oracion": "La niña de los vecinos lee los libros nuevos.", "nivel": 2, "esperado": True},
            {"id": 45, "oracion": "La niña de los vecinos leen los libros nuevos.", "nivel": 3, "esperado": False},
            {"id": 53, "oracion": "Leo el libro nuevo.", "nivel": 3, "esperado": False},
        ]
        mapa_set = {
            "1": {"id": 1, "fenomeno": "svo_pronominal_presente"},
            "23": {"id": 23, "fenomeno": "sp_sujeto_y_adjetivo"},
            "45": {"id": 45, "fenomeno": "concordancia_distancia_numero"},
            "53": {"id": 53, "fenomeno": "sujeto_tacito_fuera_cfg"},
        }

        # Simula zero-shot cometiendo FP en sujeto tácito y few-shot corrigiéndolo.
        def mock_zero(sistema, usuario):
            if "leen" in usuario:
                return json.dumps({"veredicto": "rechazada", "categoria_error": "concordancia", "motivo": "plural"})
            return json.dumps({"veredicto": "aceptada", "categoria_error": "ninguno", "motivo": "natural"})

        def mock_few(sistema, usuario):
            if "leen" in usuario or "Leo el libro nuevo" in usuario:
                return json.dumps({"veredicto": "rechazada", "categoria_error": "sintactico", "motivo": "fuera v1"})
            return json.dumps({"veredicto": "aceptada", "categoria_error": "ninguno", "motivo": "cumple v1"})

        reg_zero = llm_experimento.ejecutar_modo(oraciones, "zero-shot", mock_zero, mapa_set=mapa_set)
        reg_few = llm_experimento.ejecutar_modo(oraciones, "few-shot", mock_few, mapa_set=mapa_set)

        resumen = llm_experimento.resumir_experimento({"zero-shot": reg_zero, "few-shot": reg_few})
        self.assertEqual(resumen["modos"]["zero-shot"]["global"]["fp"], 1)
        self.assertEqual(resumen["modos"]["zero-shot"]["global"]["tn"], 1)
        self.assertEqual(resumen["modos"]["few-shot"]["global"]["fp"], 0)
        self.assertEqual(resumen["modos"]["few-shot"]["global"]["tn"], 2)
        self.assertEqual(
            resumen["modos"]["zero-shot"]["desglose_nivel_3"]["valido_espanol_fuera_v1"]["falsos_positivos"], 1
        )
        self.assertEqual(
            resumen["modos"]["few-shot"]["desglose_nivel_3"]["valido_espanol_fuera_v1"]["tasa_rechazo"], 1.0
        )

        with tempfile.TemporaryDirectory() as tmp:
            prompts = {
                "zero-shot": llm_experimento.construir_prompt_sistema("zero-shot"),
                "few-shot": llm_experimento.construir_prompt_sistema("few-shot"),
            }
            meta = {
                "proveedor": "mock",
                "modelo": "mock-v1",
                "temperatura": 0.0,
                "entrada": "mock.json",
                "total_oraciones": 4,
                "modos": ["zero-shot", "few-shot"],
                "fecha_utc": "2026-11-26T00:00:00Z",
            }
            archivos = llm_experimento.exportar_experimento(
                {"zero-shot": reg_zero, "few-shot": reg_few}, resumen, meta, prompts, tmp
            )
            nombres = {os.path.basename(a) for a in archivos}
            self.assertEqual(nombres, {"experimento_llm.json", "reporte_llm.md", "grafica_llm_zero_vs_few.svg"})

            with open(os.path.join(tmp, "experimento_llm.json"), encoding="utf-8") as f:
                log = json.load(f)
            self.assertIn("zero-shot", log["prompts"])
            self.assertEqual(len(log["respuestas"]["few-shot"]), 4)

            with open(os.path.join(tmp, "grafica_llm_zero_vs_few.svg"), encoding="utf-8") as f:
                svg = f.read()
            self.assertTrue(svg.startswith("<svg"))


if __name__ == "__main__":
    unittest.main()
