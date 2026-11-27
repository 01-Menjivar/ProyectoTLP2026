# Guion de Exposición Final — Estilo Presentador (3 Integrantes · 18 minutos)

**Universidad Centroamericana José Simeón Cañas**  
**Materia:** Teoría de Lenguajes de Programación · **Docente:** Miguel Ernesto Rivas Serrano  
**Evaluación:** *Gramáticas formales y lenguaje natural: experimentando los límites de la jerarquía de Chomsky*  
**Duración objetivo:** 17.5–18 minutos (límite del curso: 15–20 min)

> **Cómo leer este guion:**  
> - El texto entre comillas es lo que se dice en voz alta, escrito en lenguaje natural y fluido para hablar con seguridad y ritmo (no para memorizar palabra por palabra, sino para sonar como un presentador que domina el tema).  
> - Lo que aparece **(entre paréntesis)** son indicaciones escénicas: dónde dirigir la mirada del público en la diapositiva, cuándo hacer una pausa o qué dato puntualizar.

---

## Distribución de los 3 expositores

| Expositor | Slides | Enfoque | Tiempo |
|---|---|---|---:|
| **Integrante 1** | Slides 1, 2, 3, 4 | Apertura, veredicto global, Jerarquía de Chomsky + límites CFG y código del lexer (`lexer/espanol.py`) | **6.0 min** |
| **Integrante 2** | Slides 5, 6, 7, 8 | Código del parser LL(1), verificador de concordancia, adaptación NLP (`spaCy` / `BERT`) y resultados NLP | **6.0 min** |
| **Integrante 3** | Slides 9, 10, 11, 12 | Código del experimento LLM, resultados de Gemini, **demo en vivo en terminal** y cierre arquitectónico | **6.0 min** |

---

## BLOQUE 1 — INTEGRANTE 1 (Slides 1 a 4 · ~6.0 minutos)

### Slide 1 · Portada (0.5 min)
> «Muy buenos días/tardes, ingeniero Rivas y compañeros. `(sonrisa breve, contacto visual con el docente y el salón)` Hoy venimos a responder una pregunta que está justo en la frontera entre los compiladores clásicos y la inteligencia artificial moderna: **¿hasta dónde llega una gramática libre de contexto cuando la sacamos de un lenguaje de programación y la ponemos a analizar español?** `(pausa corta)` En la primera fase construimos el lexer y el analizador semántico de mini-C; hoy les mostramos cómo llevamos esa misma arquitectura al lenguaje natural, cómo la programamos desde cero en Python y qué pasó cuando la pusimos a competir contra `spaCy`, `HuggingFace` y `Gemini`.»

- **Nota para el expositor:** Entra con energía y sin leer el subtítulo completo; el título ya está en pantalla. Pasa rápido a la Slide 2 para enganchar con los resultados.

---

### Slide 2 · *Un parser LL(1) en Python puro alcanza 100% en 0.050 ms* (1.0 min)
> «Nos gusta empezar por el final, con los números sobre la mesa. `(dirigir la atención a la tabla principal)` Evaluamos cinco sistemas distintos sobre exactamente el mismo conjunto de **66 oraciones en español**. Y miren esa primera fila en rojo: `(enfocar la primera fila: 100.0% y 0.050 ms)` nuestro parser propio —escrito en Python puro, sin librerías externas— alcanzó **100% de exactitud** en apenas **0.050 milisegundos** por oración.  
>
> Ahora comparen hacia abajo. `(recorrer brevemente las filas intermedias)` `spaCy` se quedó en **83.3%** tardando 3.5 milisegundos; `HuggingFace` con BERT llegó a **84.9%** en más de 41 milisegundos. Y abajo del todo tienen a `Gemini`: en modo `zero-shot` logró **95.5%**, y cuando le dimos ejemplos en `few-shot` igualó nuestro **100%**… `(pausa dramática)` pero tardando **casi un segundo completo por oración**. Es decir, unas **20,000 veces más lento**.  
>
> `(bajar la mirada al flujo horizontal inferior: lexer/ -> parser/ -> semantico/ -> comparacion/)` Todo esto vive en cuatro módulos limpios que vamos a abrir hoy en código, respaldados por **184 pruebas unitarias en verde** y los **29 programas de mini-C** funcionando sin ninguna regresión.»

- **Nota para el expositor:** No leas columna por columna (`TP`, `FP`, `FN`, `TN`); céntrate en **Exactitud** y **Mediana**, que es el contraste que impacta de inmediato.

---

### Slide 3 · *La jerarquía de Chomsky define qué resuelve cada módulo y dónde falla la CFG* (2.0 min)
> «Pero antes de entrar al código, la pregunta obligada: ¿por qué dividimos el sistema justo así? Porque estamos traduciendo literalmente la **jerarquía de Chomsky** a módulos de Python. `(dirigir la vista al bloque inferior izquierdo: División por niveles de Chomsky)`  
>
> En el **Tipo 3**, los lenguajes regulares, tenemos el lexer Unicode: reconocer palabras de un léxico finito. En el **Tipo 2**, las gramáticas libres de contexto, está nuestro parser LL(1). `(subir la atención al bloque superior izquierdo con las 4 reglas EBNF)` Aquí tienen la gramática completa v1: oraciones declarativas Sujeto-Verbo-Objeto, con sujeto explícito —pronombre o sintagma nominal—, verbo en presente o pretérito, objeto directo obligatorio, adjetivos posnominales, adverbios dentro del predicado y frases preposicionales recursivas. Y en el **Tipo 1** —la capa sensible al contexto— entra nuestro verificador semántico de concordancia.  
>
> Ahora, ¿dónde se queda corta una CFG pura? `(pasar a la columna derecha, recorriendo los tres puntos numerados)` En tres fronteras muy claras.  
> Primero, la **concordancia a distancia**: *«La niña de los vecinos lee»* y *«La niña de los vecinos leen»* tienen exactamente la misma secuencia de categorías. La gramática libre de contexto acepta las dos porque no recuerda que el núcleo era *niña* en singular.  
> Segundo, las **dependencias cruzadas**: formalmente, un lenguaje como $a^m b^n c^m d^n$ no puede ser reconocido por ninguna CFG —eso nos lo demuestra el lema de bombeo—; necesita al menos Tipo 1.  
> Y tercero, la **ambigüedad estructural**: en *«…vio al hombre con los lentes»*, la frase preposicional puede describir al hombre o al instrumento con que se mira. En nuestra gramática v1 restringimos el `SP` únicamente al `SN` para evitar dos árboles igualmente válidos cuya elección ya requiere conocimiento del mundo.»

- **Nota para el expositor:** Al mencionar las 4 reglas EBNF, no las leas símbolo por símbolo; traduce en español qué permiten construir y detente un segundo más en el punto 1 (*lee* vs *leen*), porque es el hilo conductor de toda la presentación.

---

### Slide 4 · *Código: analizador léxico Unicode y reutilización de TablaSimbolos* (2.5 min)
> «Ahora sí, vamos al código real. `(enfocar el bloque de la izquierda: lexer/espanol.py)` Lo primero que toca una oración al entrar al sistema es `lexer/espanol.py`.  
>
> Arriba ven nuestro patrón de expresiones regulares, `PATRON`. `(puntualizar la línea con [^\W\d_]+ y el bloque derecho: Normalización NFC)` Un detalle que parece pequeño pero es crucial en español: normalizamos el texto con `unicodedata.normalize("NFC")` antes de tokenizar. ¿Por qué? Porque en Unicode una letra con tilde puede venir como dos códigos separados, y sin normalización rompería palabras como *leíste* o *niña*.  
>
> `(dirigir la atención al segundo punto derecho: Recuperación sin detenerse)` Además, el lexer no se rinde al primer error: recorre toda la oración, reporta cada palabra desconocida con línea y columna, y hasta sugiere correcciones —por ejemplo, si alguien escribe *tu* sin tilde, `_sin_tildes` y `difflib` le sugieren *tú*.  
>
> `(bajar al método construir_tabla en la parte inferior del código y al tercer punto derecho)` Y aquí viene la conexión directa con la Fase 1: `construir_tabla()` reutiliza exactamente la misma clase `TablaSimbolos` que hicimos para mini-C. El truco de diseño está en la clave: `f"{t.tipo}:{forma}"`. Al prefijar la categoría gramatical antes de la palabra en minúsculas, separamos posibles homógrafos y guardamos sus rasgos morfológicos —género, número y persona— sin romper ni una sola línea de mini-C.  
>
> Con los tokens listos y la tabla cargada, le doy paso a **[Integrante 2]**, quien les va a mostrar cómo nuestro parser construye el árbol y cómo resolvemos la concordancia a distancia en menos de 50 líneas.»

- **Nota para el expositor:** Haz énfasis en la **reutilización real de `TablaSimbolos` de Fase 1** y en la clave `CATEGORIA:forma`; a los docentes de compiladores les encanta ver decisiones limpias de diseño. *(Ojo técnico: en la slide de Claude se omitieron los nombres de grupo `<PALABRA>` en `PATRON`, así que habla de la clase Unicode `[^\W\d_]+` y si alguien pregunta, comenta que en el archivo real son grupos nombrados `(?P<PALABRA>...)`.)*

---

## BLOQUE 2 — INTEGRANTE 2 (Slides 5 a 8 · ~6.0 minutos)

### Slide 5 · *Código: parser descendente recursivo LL(1) en O(n)* (2.0 min)
> «Gracias. Ya con los tokens en la mano, entramos al corazón sintáctico del proyecto: `ParserEspanol` en `parser/espanol.py`. `(mostrar el bloque de código completo a la izquierda)`  
>
> Lo bonito de un parser descendente recursivo bien diseñado es que el código **es un espejo directo de la gramática EBNF**. Miren los cuatro métodos: `oracion`, `sintagma_nominal`, `sintagma_preposicional` y `sintagma_verbal`.  
>
> `(enfocar la primera línea de oracion() y el primer punto a la derecha: FIRST disjuntos)` ¿Por qué decimos que es **LL(1)**? Porque en cada bifurcación nos basta mirar **un solo token hacia adelante** con `self.es(...)` —que consulta `self.actual()`—. Si el primer token es `PRON`, el sujeto es pronominal; si no, llamamos a `sintagma_nominal()`. En `sintagma_nominal()`, un `while self.es("ADJ")` consume todos los adjetivos que vengan, y un `if self.es("PREP")` dispara la recursión mutua hacia `sintagma_preposicional()`, que vuelve a llamar a `sintagma_nominal()`.  
>
> `(puntualizar las últimas líneas de oracion(): self.esperar("EOF", ...))` Y fíjense en este detalle clave al final de `oracion()`: después del punto opcional, exigimos `EOF`. Eso impide aceptar una oración válida que tenga basura o texto sobrante detrás, como *"Yo leo el libro la niña"*. Todo corre en tiempo lineal $O(n)$, sin retroceso, y cada hoja `Nodo` guarda su lexema, línea y columna exactos.»

- **Nota para el expositor:** Mantén el ritmo ágil recorriendo de arriba hacia abajo los cuatro métodos; no leas código literal línea por línea, explica **qué decisión toma** cada método.

---

### Slide 6 · *Código: concordancia a distancia en 49 líneas y resaltado SVG* (2.0 min)
> «Ahora bien, si la oración es sintácticamente válida, pasa a `semantico/concordancia.py`. `(enfocar el bloque de código a la izquierda)` Todo el verificador de concordancia cabe en **49 líneas**, y aquí está la clave de cómo resolvemos la concordancia a distancia.  
>
> Miren `verificar_sn(sn)`: `(puntualizar nucleo = sn.hijos[1] y el elif hijo.tipo == "SP")` la primera línea fija el núcleo en `sn.hijos[1]`, es decir, el sustantivo principal de ese sintagma. Luego revisa que su determinante y sus adjetivos coincidan en género y número. Y si encuentra un `SP` anidado, llama recursivamente a `verificar_sn` sobre el sintagma interno… **pero al terminar, devuelve siempre el `nucleo` original**.  
>
> `(desplazar la atención a los dos diagramas de árboles a la derecha: id=23 arriba e id=45 abajo)` ¿Qué logramos con eso? Miren la derecha. En `id=23` —*«La niña de los vecinos lee los libros nuevos»*—, aunque *vecinos* está en plural en medio de la frase, `verificar_sn(sujeto)` nos devuelve a *niña* (singular, 3.ª persona), que concuerda con *lee*. En cambio, en `id=45` —*«La niña de los vecinos leen»*—, la CFG construye exactamente el mismo árbol, pero al comparar el verbo contra *niña*, el verificador detecta la discrepancia en la columna 24 y `visualizador.py` pinta esa hoja en **rojo** en el SVG.  
>
> `(mencionar brevemente la nota inferior derecha sobre ValueError)` Además, si faltara una entrada en la tabla de símbolos, lanzamos un `ValueError` para no confundir nunca un fallo de integración con un error gramatical.»

- **Nota para el expositor:** Esta es la slide que más demuestra dominio de compiladores (35% + 30% de la nota). Haz una pausa de un segundo cuando compares el cuadro gris (`id=23`) con el cuadro rojo (`id=45`).

---

### Slide 7 · *Código: reglas binarias para comparar spaCy y HuggingFace* (1.0 min)
> «Para que la comparación contra herramientas modernas de NLP fuera justa, teníamos un reto: ni `spaCy` ni `HuggingFace` rechazan oraciones; siempre devuelven un análisis. Así que tuvimos que escribir reglas binarias explícitas. `(señalar la columna izquierda: spacy_sistema.py)`  
>
> En `spacy_sistema.py`, nuestra función `decidir()` evalúa cuatro reglas sobre el árbol de dependencias y el diccionario `morph`: `R1` que la raíz sea verbo, `R2` que tenga sujeto `nsubj`, `R3` objeto directo `obj`, y `R4` que coincidan género, número y persona.  
>
> `(pasar a la columna derecha: hf_sistema.py)` En cambio, en `hf_sistema.py` usamos un modelo BERT etiquetador de categorías gramaticales (UPOS). Primero recomponemos los subtokens de WordPiece (cuando BERT parte *leen* en `lee` + `##n`), y luego validamos la secuencia de etiquetas contra una expresión regular `ESQUELETO`. Fíjense en la limitación por diseño que esto implica: al leer solo categorías y no morfología, **es imposible que detecte errores de concordancia**.»

- **Nota para el expositor:** Slide rápida y directa (1 minuto). El mensaje central es: *definimos criterios objetivos en código, y cada herramienta tiene una frontera estructural clara*.

---

### Slide 8 · *El parser propio es 70× más rápido que spaCy y 830× más rápido que BERT* (1.0 min)
> «Y aquí vemos el resultado de correr esas reglas sobre las **66 oraciones** —22 simples en Nivel 1, 22 con modificadores en Nivel 2 y 22 que deben rechazarse en Nivel 3. `(enfocar la gráfica de barras de la izquierda: Exactitud por nivel)`  
>
> Nuestro parser marca **100% en los tres niveles** en 0.050 milisegundos. `spaCy` es **70 veces más lento** y, curiosamente, donde más falla es en el Nivel 1 con **72.7%**. `BERT` es **830 veces más lento**, iguala el 100% en Nivel 2, pero cae a **68.2%** en Nivel 3.  
>
> `(dirigir la mirada a la derecha: TP, TN, FP, FN y las dos notas inferiores)` ¿Por qué fallaron de forma opuesta? Miren las barras de colores a la derecha: **`spaCy` tuvo 10 falsos negativos** (naranja) porque en oraciones cortas sin contexto etiquetó palabras como *leo*, *Nosotras*, *Vosotros* y *Ellas* como nombres propios (`PROPN`), rompiendo toda la cadena `R1–R4`. **`BERT` tuvo 7 falsos positivos** (rojo) en Nivel 3 justo por esa ceguera morfológica que vimos en el código.  
>
> Con el panorama de NLP claro, le doy la palabra a **[Integrante 3]** para ver qué pasó con el modelo de lenguaje grande y pasar a la demo en vivo.»

- **Nota para el expositor:** Contrasta con la voz los dos colores de la derecha: **naranja = 10 FN en spaCy**, **rojo = 7 FP en BERT**. Queda clarísimo para el docente.

---

## BLOQUE 3 — INTEGRANTE 3 (Slides 9 a 12 + Demo en vivo · ~6.0 minutos)

### Slide 9 · *Código: cliente API sin dependencias y prueba anti-fuga del experimento LLM* (1.5 min)
> «Gracias. Para el experimento con modelos de lenguaje grande (LLM) por internet queríamos mantener la misma limpieza técnica que en el resto del proyecto. `(enfocar el bloque de código a la izquierda)` En `comparacion/llm_experimento.py` programamos la conexión usando **`urllib.request`**, que es la librería que ya viene incluida en Python para hacer peticiones web. La elegimos para no depender de librerías externas ni instalar paquetes extra, y aun así funciona con Gemini, OpenAI y Anthropic. Además, si el servidor de la IA se satura o falla temporalmente —es decir, errores `429` por exceso de peticiones o `5xx` por fallas del servidor—, el código espera unos segundos y reintenta automáticamente.  
>
> En `construir_prompt_sistema(modo)` probamos dos formas de darle instrucciones a la IA: en modo **`zero-shot`** (*sin ejemplos*), le entregamos únicamente nuestras reglas gramaticales, seis restricciones estrictas y las reglas de concordancia, pidiéndole que responda en formato JSON; y en modo **`few-shot`**, le añadimos **8 ejemplos ya resueltos** para guiarlo.  
>
> `(puntualizar la función inferior: test_ejemplos_few_shot_sin_fuga_de_datos y el bloque derecho: Cero fuga de datos)` Y aquí cuidamos un detalle clave para que la prueba fuera justa: para asegurar que la IA no memorizara ni copiara respuestas del examen, escribimos una prueba automática que verifica que **ninguno de los 8 ejemplos aparezca en nuestras 66 oraciones de evaluación (`set_p2.json`)**. Además, guardamos todas las instrucciones y las **132 respuestas completas** (66 por cada modo) en `experimento_llm.json` para que cualquiera pueda auditar el experimento.»

- **Nota para el expositor:** Destaca los tres pilares de la derecha (*Sin librerías externas*, *Cero fuga de datos*, *Auditoría reproducible*). No hace falta memorizar los códigos `429` o `5xx`: basta con explicar que son fallos temporales del servidor que el programa maneja solo.

---

### Slide 10 · *Gemini obedece v1 en zero-shot (95.5%) y llega a 100% en few-shot* (1.0 min)
> «Y miren lo que pasó al probar `gemini-3.5-flash-lite` con temperatura `0.0` —es decir, configurado para ser lo más preciso y constante posible, sin respuestas aleatorias—. `(enfocar la gráfica izquierda por niveles)` Esperábamos que la IA se dejara llevar por su conocimiento normal del español y aceptara frases que rompen nuestras reglas… pero ocurrió lo contrario: **incluso sin ejemplos (`zero-shot`), sacó 100% en Nivel 3 (22 de 22)**, rechazando las **11 frases perfectamente naturales en español** que violan nuestra gramática v1, como *«Leo el libro nuevo»*.  
>
> `(mover la atención a la columna derecha: LOS 3 FALSOS NEGATIVOS RESUELTOS EN FEW-SHOT)` Sus únicos tres fallos sin ejemplos ocurrieron por ser demasiado estricto con oraciones válidas: en `id=2` se confundió con el verbo *leíste* creyendo que llevaba un pronombre *le* pegado; en `id=38` rechazó dos adjetivos seguidos (*nueva bonita*), aunque nuestra regla sí permite repetir adjetivos; y en `id=43` interpretó que *sin el perro* modificaba al verbo en vez de al sustantivo —exactamente el problema de ambigüedad que vimos al inicio—.  
>
> Cuando le dimos los 8 ejemplos en `few-shot`, desaparecieron los tres fallos y llegó a **100% (66 de 66)**. `(bajar la mirada al recuadro destacado abajo a la izquierda: ~20,000×)` El precio: tardó casi un segundo por oración (**998.4 ms**), es decir, **20,000 veces más lento** que nuestro parser.»

- **Nota para el expositor:** Haz énfasis en la cifra grande **`~20,000×`** y en que `id=43` (*sin el perro*) demostró en la práctica el problema teórico de ambigüedad que explicó el Integrante 1.

---

### Slide 11 · *Demostración en vivo en terminal* (2.75 min)
> «Dejemos las diapositivas un momento y veamos el código corriendo en vivo en la terminal. `(cambiar a la terminal abierta en ProyectoTLP2026 con letra grande legible)`»

*(Ejecutar los 5 bloques en orden — cada uno está visible en la Slide 11 como respaldo):*

```sh
# 1. Suite completa (184 pruebas + 29 mini-C)
python -m unittest discover pruebas && python -m pruebas.ejecutor
```
> «Primero ejecutamos todas nuestras pruebas automáticas: **184 pruebas unitarias en verde** en fracciones de segundo y los **29 programas de mini-C** de la Fase 1 pasando sin ningún error.»

```sh
# 2. Lexer español
python -m lexer.espanol "La niña de los vecinos lee los libros nuevos."
```
> «Ahora pasamos nuestra oración de prueba por el analizador léxico en español: aquí vemos cada palabra convertida en token, con su categoría gramatical, su posición exacta y sus rasgos de género y número listos en la tabla.»

```sh
# 3. Árbol válido (id=23) y error a distancia en rojo (id=45)
python -m parser.visualizador "La niña de los vecinos lee los libros nuevos." --svg salida/demo_ok.svg
python -m parser.visualizador "La niña de los vecinos leen los libros nuevos." --svg salida/demo_error.svg
open salida/demo_ok.svg salida/demo_error.svg
```
> «Generamos los diagramas de árbol de dos oraciones casi iguales: primero la correcta con *lee* y luego la incorrecta con *leen*. `(mostrar ambos SVG abiertos en el navegador/Vista Previa)` Vean cómo la estructura del árbol es idéntica, pero en el segundo, el verificador detecta que *leen* no concuerda con *niña* y lo resalta en rojo justo en la columna 24.»

```sh
# 4. Frases naturales del español rechazadas por v1
python -m parser.visualizador "Leo el libro nuevo."
python -m parser.visualizador "Yo leo el nuevo libro."
```
> «Probamos ahora dos oraciones que suenan totalmente normales en español, pero que nuestra gramática v1 prohíbe: una sin sujeto explícito y otra con el adjetivo antes del sustantivo. El parser las rechaza al instante y nos dice exactamente qué categoría esperaba.»

```sh
# 5. Corrida completa sobre las 66 oraciones oficiales
python -m comparacion.ejecutar --sistemas propio --entrada pruebas/set_p2.json --salida salida/demo_propio.json
```
> «Y cerramos la demo corriendo nuestro sistema sobre las 66 oraciones oficiales del experimento: **66 de 66 aciertos** en centésimas de milisegundo.»

- **Nota para el expositor:** Ten los comandos copiados en un bloc o en el historial (`↑`) para no teclear con nervios. Si `open` tarda, haz `Cmd+Tab` a una pestaña del navegador donde ya tengas cargados los SVG.

---

### Slide 12 · *Cuándo elegir cada arquitectura en ingeniería* (0.75 min)
> «`(volver a la presentación, enfocando la tabla de 3 filas)` Para cerrar, si algo demuestran nuestros datos es que la IA no viene a reemplazar a los compiladores clásicos. Cada herramienta tiene su terreno ideal:  
> - **Parser propio (LL(1) + semántica)**, cuando las reglas del lenguaje están bien definidas y necesitamos respuestas exactas, siempre iguales, fáciles de auditar y en microsegundos.  
> - **NLP estadístico (`spaCy` / `BERT`)**, cuando trabajamos con texto libre y vocabulario abierto, y necesitamos procesar mucho volumen en un servidor normal sin pagar una API externa.  
> - **LLM con ejemplos (`few-shot`)**, cuando las reglas cambian muy rápido o hace falta entender el sentido y contexto de la frase, y podemos permitirnos esperar casi un segundo y pagar por cada consulta.  
>
> `(dirigir la mirada al recuadro inferior: PROPUESTA DE ARQUITECTURA HÍBRIDA)` Y como cierre técnico: en un sistema real en producción, el diseño más inteligente es **híbrido** —poner nuestro parser rápido como primer filtro en `0.050 ms` para resolver al instante todo lo que sigue las reglas, y enviarle al LLM únicamente los casos abiertos o ambiguos—. Muchas gracias por su atención; quedamos abiertos a sus preguntas.»

- **Nota para el expositor:** Cierra mirando al docente, tono seguro y pausado. No agregues un *"y eso sería todo"* apresurado: termina exactamente en *"quedamos abiertos a sus preguntas"*.

---

## Banco rápido de defensa técnica (para preguntas del Ing. Rivas)

1. **«¿Por qué dicen que la concordancia excede una CFG si género/número/persona son finitos?»**  
   En dominios finitos sí existe una CFG equivalente multiplicando no terminales (`SN_m_sg`, `SN_f_pl`), pero produce explosión combinatoria de reglas y dificulta el diagnóstico. La frontera matemática estricta de Tipo 2 la probamos con $\{a^m b^n c^m d^n\}$ y el lema de bombeo.
2. **«¿Dónde evita `concordancia.py` confundirse con *vecinos* en *La niña de los vecinos lee…*?»**  
   En `verificar_sn(sn)`, `nucleo = sn.hijos[1]` fija el sustantivo raíz del `SN` del sujeto y devuelve ese nodo; los `SP` internos se validan recursivamente sin sobrescribir el núcleo principal.
3. **«¿Por qué `oracion()` exige `EOF` al final?»**  
   Para evitar que `ParserEspanol` acepte un prefijo válido y deje texto sobrante sin consumir (como `id=61`: *«Yo leo el libro la niña.»*).
4. **«¿Cómo aseguraron que `few-shot` no memorizó el set de prueba?»**  
   Los 8 ejemplos de `EJEMPLOS_FEW_SHOT` usan vocabulario distinto y la prueba unitaria `test_ejemplos_few_shot_sin_fuga_de_datos` falla si cualquier oración coincide con `pruebas/set_p2.json`.
