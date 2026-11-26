# Guion de Presentación Final y Demo en Vivo (15–20 minutos)

**Requisitos de exposición:** Duración total de 15 a 20 minutos · Asistencia mínima de **50% + 1** del equipo (al menos 3 de los 5 integrantes).

---

## 1. Estructura de diapositivas (10 láminas · ~14 min + 4 min de demo)

| # | Lámina | Tiempo | Contenido y apoyos visuales |
|---|---|---:|---|
| 1 | **Portada y objetivo** | 1 min | Título del proyecto, integrantes y pregunta guía: comparación entre parser formal CFG, spaCy, HuggingFace y LLM. |
| 2 | **Marco teórico: Jerarquía de Chomsky** | 2 min | Tipos 3, 2 y 1 aplicados a mini-C (Fase 1) y Español v1 (Fase 2). Concordancia a distancia, dependencias cruzadas y ambigüedad estructural. |
| 3 | **Gramática del español v1 y concordancia** | 2 min | Producciones EBNF (`O`, `SN`, `SP`, `SV`), rasgos morfológicos en `TablaSimbolos` y condiciones de concordancia nominal y verbal. |
| 4 | **Arquitectura e implementación del parser** | 2 min | Flujo `lexer/espanol.py → parser/espanol.py → semantico/concordancia.py → parser/visualizador.py`. Ejemplo de árbol SVG válido y con error en rojo. |
| 5 | **Set oficial de prueba (66 oraciones)** | 1.5 min | Desglose de los 3 niveles (22 simples, 22 con modificadores/SP, 22 rechazadas: 8 concordancia, 11 español natural fuera de v1, 3 fuera del léxico cerrado). |
| 6 | **Resultados cuantitativos (Propio vs spaCy vs HF)** | 2 min | Tabla global (Exactitud: 100.0% / 83.3% / 84.9%; Mediana: 0.050 ms / 3.517 ms / 41.565 ms) y gráficas SVG/PNG. |
| 7 | **Análisis de errores NLP** | 1.5 min | Causas de los 10 FN de `spaCy` (etiquetado POS/morfología en oraciones cortas) y los 7 FP de `HuggingFace` en Nivel 3 (sin concordancia morfológica). |
| 8 | **Experimento con LLM (`zero-shot` vs `few-shot`)** | 2 min | `gemini-3.5-flash-lite`: `zero-shot` (95.5%, 3 FN en N1–N2, 100% rechazo en N3) vs `few-shot` (100.0%, 66/66, mediana ~1.0 s) y gráfica `grafica_llm_zero_vs_few.svg`. |
| 9 | **Demo en vivo** | 4 min | Ejecución en terminal de los comandos de la Sección 2. |
| 10 | **Conclusiones y cierre** | 1.5 min | Balance entre rigor formal, velocidad, cobertura abierta y preguntas. |

---

## 2. Guion de Demo en Vivo (comandos listos para ejecutar)

Ejecutar desde la raíz del repositorio (`ProyectoTLP2026/`):

### Paso 1 — Verificar suite completa (Fase 1 + Fase 2)
```sh
python -m unittest discover pruebas
python -m pruebas.ejecutor
```
*Mensaje clave:* 184 pruebas unitarias en verde y 29/29 programas mini-C sin regresiones.

### Paso 2 — Árbol válido con modificadores y SP en sujeto (Nivel 2, `id=23`)
```sh
python -m parser.visualizador "La niña de los vecinos lee los libros nuevos." --svg salida/demo_ok.svg
```
*Mensaje clave:* El parser construye el árbol `O → SN(DET, N, SP(...)) SV(...)` y el verificador comprueba que `lee` concuerda con `niña` (singular), no con `vecinos` (plural).

### Paso 3 — Error de concordancia a distancia (Nivel 3, `id=45`)
```sh
python -m parser.visualizador "La niña de los vecinos leen los libros nuevos." --svg salida/demo_error.svg
```
*Mensaje clave:* La CFG acepta la estructura, pero `semantico/concordancia.py` marca `leen` en rojo indicando discrepancia de número con `niña`.

### Paso 4 — Oración natural del español rechazada por v1 (Nivel 3, `id=53` y `id=59`)
```sh
python -m parser.visualizador "Leo el libro nuevo."
python -m parser.visualizador "Yo leo el nuevo libro."
```
*Mensaje clave:* Ambas son válidas en español general, pero nuestro parser las rechaza por falta de sujeto explícito y por adjetivo antepuesto, respectivamente — el mismo caso donde los LLMs suelen desviarse en `zero-shot`.

### Paso 5 — Evaluación sobre el set oficial de 66 oraciones
```sh
python -m comparacion.ejecutar --sistemas propio --entrada pruebas/set_p2.json --salida salida/demo_propio.json
```
*Mensaje clave:* 66/66 aciertos en ~0.05 ms por oración. Abrir `salida/demo_ok.svg` y `salida/demo_error.svg` en el navegador para mostrar los árboles visuales.
