# Informe Final — Fase 2: Gramática Formal del Español, Análisis Sintáctico-Semántico y Comparación con Herramientas de NLP y LLM

**Curso:** Teoría de Lenguajes de Programación (TLP02-2026)  
**Integrantes:** Fabio Mijango · Gabriela Sofia Quinteros Ramirez · Juan Carlos Sibrian · Kattia Sarai Santan Soriano · Oscar Ernesto Menjivar Ayala

---

## 1. Introducción y objetivos

En la Fase 1 del proyecto se construyó un analizador léxico y semántico para **mini-C**, evidenciando cómo un compilador separa las responsabilidades entre lenguajes regulares (tipo 3), libres de contexto (tipo 2) y restricciones sensibles al contexto (tipo 1). En esta **Fase 2** trasladamos ese mismo marco formal al **lenguaje natural (español)** para responder una pregunta central: *hasta dónde llega una gramática libre de contexto (CFG) combinada con verificación semántica sobre árboles, y cómo se compara con enfoques modernos de Procesamiento de Lenguaje Natural (NLP) y Modelos de Lenguaje Grandes (LLM)*.

Los objetivos específicos fueron:
1. Definir una gramática formal restringida del español (**v1**) junto con reglas de concordancia nominal y verbal a distancia.
2. Implementar un **parser descendente recursivo** (`parser/espanol.py`), un **lexer léxico-morfológico** (`lexer/espanol.py`), un **verificador de concordancia** (`semantico/concordancia.py`) y un **visualizador de árboles** (`parser/visualizador.py`) sin dependencias externas.
3. Evaluar cuantitativamente el sistema propio frente a **spaCy** (`es_core_news_sm`) y **HuggingFace** (`mrm8488/bert-spanish-cased-finetuned-pos-16-tags`) sobre un conjunto oficial de **66 oraciones** en tres niveles de complejidad (`pruebas/set_p2.json`).
4. Diseñar y ejecutar un **experimento controlado con un LLM vía API** comparando prompting `zero-shot` y `few-shot` para medir su adherencia a una especificación formal frente a su conocimiento general del español.

---

## 2. Marco teórico y límites de las CFG

### 2.1 La Jerarquía de Chomsky aplicada al proyecto

La jerarquía de Chomsky clasifica las gramáticas formales en cuatro niveles inclusivos:
- **Tipo 3 (Lenguajes regulares):** reconocidos por autómatas finitos. En este proyecto, identificar tokens de un léxico finito y clasificar sus categorías léxicas corresponde al nivel regular.
- **Tipo 2 (Lenguajes libres de contexto — CFG):** generados por producciones de la forma `A → γ`, donde la expansión de un no terminal no depende de su contexto adyacente. Permiten expresar recursión estructural, como sintagmas preposicionales anidados (`la niña de los vecinos de la maestra`).
- **Tipo 1 (Lenguajes sensibles al contexto):** reconocidos por autómatas linealmente acotados. Permiten dependencias que cruzan fronteras de subárboles o exigen cotejar múltiples contadores no locales.
- **Tipo 0 (Recursivamente enumerables):** equivalentes a máquinas de Turing.

### 2.2 Gramática formal del español v1

La unidad de análisis es una oración declarativa en orden `SVO` con sujeto explícito, verbo transitivo en presente (`V_PRES`) o pretérito perfecto simple (`V_PRET`) de indicativo y objeto directo obligatorio. La EBNF oficial (`docs/gramatica_espanol.md`) es:

```ebnf
O  ::= ( PRON | SN ) SV
SN ::= DET N { ADJ } [ SP ]
SP ::= PREP SN
SV ::= ( V_PRES | V_PRET ) [ ADV ] SN [ ADV ]
```

Las categorías léxicas se registran en `TablaSimbolos` con clave `CATEGORIA:forma` (normalizada con `casefold()`) y los siguientes rasgos morfológicos:
- `N`: género (`m`/`f`), número (`sg`/`pl`), persona `3`.
- `DET`, `ADJ`: género (`m`/`f`), número (`sg`/`pl`).
- `PRON`, `V_PRES`, `V_PRET`: número (`sg`/`pl`), persona (`1`, `2`, `3`).
- `PREP`, `ADV`: sin rasgos de concordancia.

Sobre el árbol sintáctico completo, `semantico/concordancia.py` comprueba dos invariantes semánticas:
1. **Concordancia nominal:** en cada `SN` (incluyendo los anidados dentro de `SP`), `DET` y cada `ADJ` comparten género y número con su propio sustantivo núcleo `N`.
2. **Concordancia verbal:** el verbo comparte número y persona con el `N` o `PRON` que encabeza el sujeto principal, ignorando sustantivos intermedios dentro de un `SP`.

### 2.3 Puntos de falla y límites formales de las CFG

1. **Concordancia a distancia:** *"La niña de los vecinos lee el libro"* y *"La niña de los vecinos leen el libro"* comparten exactamente la misma secuencia de categorías léxicas; por tanto, la CFG v1 deriva ambas. Aunque con dominios finitos de género/número/persona sería teóricamente posible multiplicar no terminales (`SN_f_sg`, `SN_m_pl`, etc.), separar el análisis en árbol CFG + verificación semántica evita la explosión combinatoria de producciones y permite localizar con precisión la palabra discordante (línea, columna y causa).
2. **Dependencias cruzadas:** El lenguaje formal `{ a^m b^n c^m d^n | m, n ≥ 1 }` requiere emparejar bloques entrelazados. Por el lema de bombeo para lenguajes libres de contexto, ninguna CFG puede reconocerlo; se requiere al menos poder de tipo 1. Aunque el fragmento v1 del español no contiene dependencias cruzadas ilimitadas, el ejemplo delimita formalmente la frontera de las CFG frente a lenguajes naturales con construcciones cruzadas (como ciertas subordinaciones en suizo-alemán).
3. **Ambigüedad estructural:** En *"La niña ve el libro con los lentes"*, el sintagma preposicional `con los lentes` puede adjuntarse al sustantivo `libro` (descripción) o al verbo `ve` (instrumento). La gramática v1 evita la ambigüedad restringiendo `SP` a adjunción nominal; permitir también adjunción verbal generaría dos árboles sintácticos distintos —ambos con concordancia válida— cuya desambiguación requiere conocimiento semántico o pragmático fuera del alcance de una CFG.

---

## 3. Implementación del sistema propio

### 3.1 Arquitectura de extremo a extremo

El flujo de análisis para español replica la separación por fases de un compilador clásico:

```text
Oración (str)
  └─> lexer/espanol.py + lexicon_es.py     (tokens + TablaSimbolos con rasgos morfológicos)
        └─> parser/espanol.py              (ParserEspanol descendente recursivo LL(1) -> Nodo)
              └─> semantico/concordancia.py (verificación nominal y verbal a distancia)
                    └─> parser/visualizador.py (árbol en texto, SVG o DOT con errores en rojo)
```

### 3.2 Parser descendente recursivo (`parser/espanol.py`)

La gramática v1 es **LL(1)**: cada decisión del parser se resuelve inspeccionando un único token de anticipación (`actual()`):
- `oracion()`: elige entre `PRON` o `sintagma_nominal()`, continúa con `sintagma_verbal()`, consume opcionalmente `PUNTO` y exige `EOF` para rechazar texto sobrante.
- `sintagma_nominal()`: consume `DET`, `N`, cero o más `ADJ` en bucle `while`, y opcionalmente `sintagma_preposicional()` si el siguiente token es `PREP`.
- `sintagma_preposicional()`: consume `PREP` y llama recursivamente a `sintagma_nominal()`.
- `sintagma_verbal()`: consume `V_PRES` o `V_PRET`, un `ADV` opcional, el objeto directo `sintagma_nominal()`, y un `ADV` final opcional.

Cada hoja conserva `valor={"lexema": ..., "columna": ...}` y `linea`, permitiendo que los diagnósticos sintácticos y semánticos apunten exactamente a la columna del error.

### 3.3 Visualizador de árboles (`parser/visualizador.py`)

Implementado sin librerías externas, genera tres salidas a partir de cualquier `Nodo`:
- **Texto en consola** con conectores Unicode (`├──`, `└──`) y marcador `<-- error` en hojas con discrepancia de concordancia.
- **SVG vectorial** con paleta diferenciada por categoría gramatical y resaltado en rojo (`#c62828`) para errores de concordancia junto con el mensaje diagnóstico al pie.
- **DOT (Graphviz)** opcional para exportación académica.

Ejemplo reproducible:
```sh
python -m parser.visualizador "La niña de los vecinos lee los libros nuevos." --svg salida/arbol.svg
```

---

## 4. Metodología de evaluación y set oficial de 66 oraciones

El set oficial (`pruebas/set_p2.json`) consta de **66 oraciones** equilibradas en 3 niveles (22 por nivel), cada una anotada con `esperado` (`aceptada`/`rechazada`), `fenomeno` y la secuencia de etiquetas universales `etiquetas` (UPOS) por palabra:

| Nivel | Cantidad | Esperado | Fenómenos evaluados |
|---|---:|---|---|
| **Nivel 1** | 22 | `aceptada` | Oraciones declarativas simples `SVO` (sujeto pronominal y nominal, presente y pretérito). |
| **Nivel 2** | 22 | `aceptada` | Modificadores: adjetivos múltiples, adverbios pre/post-objeto y `SP` simples y anidados. |
| **Nivel 3** | 22 | `rechazada` | 8 errores de concordancia (incluyendo a distancia), 11 estructuras naturales del español fuera de v1 (sujeto tácito, OSV, VSO, adjetivo antepuesto, adverbio preverbal, sin objeto directo, texto sobrante, `SP` incompleto, sin determinantes) y 3 casos fuera del léxico cerrado (negación, coordinación, subordinada relativa). |

### Adaptación de `spaCy` y `HuggingFace` a decisión binaria

Dado que las herramientas de NLP no rechazan oraciones de forma nativa, el equipo definió criterios explícitos en `comparacion/spacy_sistema.py` y `comparacion/hf_sistema.py`:
- **spaCy (`es_core_news_sm`):** aplica 4 reglas sobre el árbol de dependencias y morfología: `R1` raíz verbal, `R2` presencia de sujeto (`nsubj`), `R3` presencia de objeto directo (`obj`), y `R4` concordancia nominal y sujeto-verbo según `morph`.
- **HuggingFace (`mrm8488/bert-spanish-cased-finetuned-pos-16-tags`):** mapea las etiquetas UPOS predichas a categorías de v1 y verifica mediante expresión regular si la secuencia encaja en el esqueleto sintáctico de v1. Por construcción, un etiquetador POS no verifica concordancia morfológica.

Los tiempos se midieron con **5 repeticiones** (`--repeticiones 5`) excluyendo la carga inicial del modelo y reportando la mediana por oración.

---

## 5. Resultados experimentales: Sistema propio vs spaCy vs HuggingFace

### 5.1 Resumen global (66 oraciones × 3 sistemas = 198 evaluaciones)

| Sistema | TP | FP | FN | TN | Precisión | Cobertura (Recall) | F1 | Rechazo correcto | Exactitud | Mediana (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **propio** | 44 | 0 | 0 | 22 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.050 |
| **spacy** | 34 | 1 | 10 | 21 | 97.1% | 77.3% | 86.1% | 95.5% | 83.3% | 3.517 |
| **hf** | 41 | 7 | 3 | 15 | 85.4% | 93.2% | 89.1% | 68.2% | 84.9% | 41.565 |

### 5.2 Exactitud por nivel de complejidad

| Sistema | Nivel 1 (Simples) | Nivel 2 (Modificadores) | Nivel 3 (Complejas / Fuera CFG) |
|---|---:|---:|---:|
| **propio** | 100.0% (22/22) | 100.0% (22/22) | 100.0% (22/22) |
| **spacy** | 72.7% (16/22) | 81.8% (18/22) | 95.5% (21/22) |
| **hf** | 86.4% (19/22) | 100.0% (22/22) | 68.2% (15/22) |

### 5.3 Etiquetado gramatical (POS) y causas de rechazo

| Sistema | Oraciones evaluadas | Tokens evaluados | Tokens correctos | Errores POS | Exactitud POS | Causas de rechazo registradas |
|---|---:|---:|---:|---:|---:|---|
| **propio** | 52 | 343 | 343 | 0 | 100.0% | `sintactico`: 11, `semantico`: 8, `léxico`: 3 |
| **spacy** | 66 | 421 | 400 | 21 | 95.0% | `R1`: 12, `R2`: 1, `R3`: 2, `R4`: 17 |
| **hf** | 66 | 421 | 412 | 9 | 97.9% | `etiqueta_fuera_de_gramatica`: 2, `secuencia_incompatible`: 16 |

*(Las gráficas vectoriales y PNG correspondientes se generan en `salida/grafica_metricas_sistemas.svg`, `salida/grafica_aciertos_por_nivel.svg`, `salida/grafica_errores_sistemas.svg` y `salida/grafica_tiempos_ms.svg` mediante `python -m comparacion.metricas`.)*

---

## 6. Análisis comparativo: Propio vs spaCy vs HuggingFace

1. **Precisión y robustez:** El sistema **propio** logra **100.0%** en todas las métricas dentro del alcance de v1, porque aplica exactamente las reglas formales y un léxico cerrado sin incertidumbre estadística. Sin embargo, es frágil ante cualquier palabra fuera del léxico (`no`, `y`, `que`) o variación válida del español natural. Por su parte, **spaCy** sufrió **10 falsos negativos** en Niveles 1–2 debido a errores de etiquetado en oraciones cortas (p. ej., etiquetar `leo`, `Nosotras`, `Vosotros` o `Ellas` como `PROPN`, o asignar 2.ª persona a `abrió` con `Usted`) y **1 falso positivo** en Nivel 3 (`id=66`, subordinada relativa aceptada porque la raíz tenía sujeto y objeto). **HuggingFace** obtuvo 22/22 en Nivel 2 y una exactitud POS superior (`97.9%`), pero registró **7 falsos positivos** en Nivel 3 (`68.2%` de rechazo correcto) al carecer de verificación morfológica de concordancia, además de 3 falsos negativos en Nivel 1 (`Yo`/`Tú` etiquetados como `ADV` y `Él` como `PROPN`).
2. **Manejo de ambigüedad:** El parser propio elimina la ambigüedad por diseño (adjunción única de `SP` al `SN` y una lectura por clave léxica). `spaCy` y `HuggingFace` desambiguan probabilísticamente según contexto aprendido en grandes corpus, lo que les permite procesar texto abierto pero introduce errores impredecibles en oraciones breves descontextualizadas.
3. **Escalabilidad y mantenimiento:** Ampliar el sistema propio requiere añadir entradas léxicas y nuevas producciones LL(1) cuidando no introducir conflictos; en cambio, `spaCy` y `HuggingFace` cubren vocabulario abierto sin mantenimiento manual, aunque adaptar sus salidas a una especificación formal exige capas de posprocesamiento (`R1–R4` o expresiones regulares).
4. **Costo computacional:** La diferencia de latencia es de órdenes de magnitud: el sistema propio tarda **0.050 ms** por oración (~**70×** más rápido que `spaCy` con **3.517 ms** y ~**830×** más rápido que `HuggingFace` con **41.565 ms** en CPU), además de no requerir pesos neuronales ni memoria GPU/RAM elevada.
5. **Aplicabilidad práctica:** Un compilador/parser formal es ideal para lenguajes de programación, DSLs, validación estricta de formatos y enseñanza de reglas gramaticales explícitas. Las herramientas de NLP son insustituibles en texto libre, extracción de información y análisis lingüístico a gran escala donde el vocabulario y las construcciones son abiertos.

---

## 7. Experimento con LLM vía API (`zero-shot` vs `few-shot`)

### 7.1 Diseño experimental

Para evaluar si un Modelo de Lenguaje Grande (LLM) puede actuar como verificador estricto de una gramática formal, se implementó el módulo `comparacion/llm_experimento.py` que consulta una API de LLM (`gemini`, `openai` o `anthropic`) con temperatura `0.0` sobre las mismas **66 oraciones** de `pruebas/set_p2.json` en dos configuraciones:
- **Zero-shot:** recibe únicamente las reglas EBNF de `docs/gramatica_espanol.md`, las restricciones sintácticas explícitas de v1 y las dos condiciones de concordancia, sin ejemplos.
- **Few-shot:** recibe exactamente las mismas reglas más **8 ejemplos etiquetados** (2 aceptadas y 6 rechazadas cubriendo concordancia a distancia, concordancia de género, sujeto tácito, adjetivo antepuesto, adverbio preverbal y negación). Ninguna oración de ejemplo aparece en `pruebas/set_p2.json` para evitar fuga de datos.

El script registra automáticamente los prompts íntegros, cada respuesta cruda del modelo, los veredictos normalizados y las métricas en `comparacion/logs_llm/experimento_llm.json`, `comparacion/logs_llm/reporte_llm.md` y `comparacion/logs_llm/grafica_llm_zero_vs_few.svg`.

### 7.2 Resultados obtenidos (`gemini-3.5-flash-lite`, temperatura `0.0`)

El experimento completo sobre las **66 oraciones** de `pruebas/set_p2.json` se ejecutó el `2026-11-26T22:12:35Z` con el modelo `gemini-3.5-flash-lite` (logs completos en `comparacion/logs_llm/experimento_llm.json`, `comparacion/logs_llm/reporte_llm.md` y gráfica en `comparacion/logs_llm/grafica_llm_zero_vs_few.svg`).

| Modo | TP | FP | FN | TN | Precisión | Cobertura (Recall) | F1 | Rechazo correcto | Exactitud | Mediana (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `zero-shot` | 41 | 0 | 3 | 22 | 100.0% | 93.2% | 96.5% | 100.0% | 95.5% | 1040.3 |
| `few-shot` | 44 | 0 | 0 | 22 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 998.4 |

**Exactitud por nivel lingüístico:**

| Modo | Nivel 1 (Simples) | Nivel 2 (Modificadores) | Nivel 3 (Complejas / Fuera v1) |
|---|---:|---:|---:|
| `zero-shot` | 95.5% (21/22) | 90.9% (20/22) | 100.0% (22/22) |
| `few-shot` | 100.0% (22/22) | 100.0% (22/22) | 100.0% (22/22) |

**Desglose del Nivel 3 (adherencia a v1 vs conocimiento general del español):**

| Modo | Concordancia (8) | Válidas en español pero fuera de v1 (11) | Agramaticales sintácticas (3) |
|---|---:|---:|---:|
| `zero-shot` | 100.0% (8/8) | 100.0% (11/11) | 100.0% (3/3) |
| `few-shot` | 100.0% (8/8) | 100.0% (11/11) | 100.0% (3/3) |

### 7.3 Análisis de los resultados del LLM

- **(a) Adherencia a v1 vs conocimiento general del español:** `gemini-3.5-flash-lite` obtuvo **100.0% (22/22)** de rechazo correcto en Nivel 3 desde `zero-shot`, rechazando las 11 oraciones válidas en español pero fuera de v1 (como *"Leo el libro nuevo."* o *"Yo leo el nuevo libro."*). Las reglas explícitas en el prompt fueron suficientes para evitar que el modelo aceptara oraciones por naturalidad.
- **(b) Patrones de acierto y fallo:** En `zero-shot` no hubo falsos positivos (`FP = 0`), pero sí **3 falsos negativos** (`FN = 3`) en oraciones válidas de Nivel 1 y Nivel 2 por sobre-interpretación de reglas:
  1. `id=2` (Nivel 1, *"Tú leíste el libro."*): confundió la forma verbal `leíste` con un pronombre clítico `'le'` redundante.
  2. `id=38` (Nivel 2, *"Ustedes escuchan ahora una canción nueva bonita."*): asumió que `{ ADJ }` requería coordinación explícita entre múltiples adjetivos.
  3. `id=43` (Nivel 2, *"Vosotros miráis allí la película antigua sin el perro."*): interpretó `sin el perro` como adjunto al `SV` en lugar de al `SN` (`la película antigua sin el perro`), reflejando la ambigüedad de adjunción de `SP`.
- **(c) Impacto de `few-shot` frente a `zero-shot`:** Incluir 8 ejemplos etiquetados eliminó los 3 falsos negativos, elevando la **cobertura (recall) de 93.2% a 100.0%**, el **F1 de 96.5% a 100.0%** y la **exactitud global de 95.5% a 100.0%** (66/66 aciertos), manteniendo `0` falsos positivos y una mediana de latencia similar (`1040.3 ms` vs `998.4 ms`). Ese desempeño implica una latencia **~20,000× mayor** que la del parser propio (`998.4 ms` frente a `0.050 ms`).

---

## 8. Conclusiones

1. **Separación de fases en lenguaje natural:** Al igual que en mini-C, combinar un lexer finito (tipo 3), un parser descendente LL(1) (tipo 2) y un verificador semántico sobre el árbol permite resolver fenómenos no locales como la concordancia a distancia con **100% de exactitud** dentro de la especificación y una latencia de **0.050 ms**.
2. **Compromiso entre rigor formal, cobertura y costo:** `spaCy` (`83.3%`) y `HuggingFace` (`84.9%`) aportan cobertura de vocabulario abierto, pero fallan al hacer cumplir reglas formales estrictas: `spaCy` pierde cobertura por errores de etiquetado en oraciones breves y `HuggingFace` no puede detectar violaciones de concordancia. Por su parte, el LLM (`gemini-3.5-flash-lite`) alcanza **95.5%** en `zero-shot` y **100.0%** en `few-shot`, demostrando que puede seguir una gramática formal si se delimita bien el prompt, pero a un costo de ~**1 segundo por oración** (~20,000× más lento que el parser propio) y dependencia de API externa.
3. **Verificabilidad del repositorio:** Toda la implementación de ambas fases queda respaldada por **184 pruebas unitarias** (`python -m unittest discover pruebas`), **29/29 programas mini-C** (`python -m pruebas.ejecutor`) y los logs completos de `comparacion/logs_llm/`, garantizando reproducibilidad total de árboles, tablas, gráficas y respuestas del LLM.
