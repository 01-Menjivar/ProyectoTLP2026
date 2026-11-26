# Fase 2 · Gramática del español v1 y concordancia

## Gramática para el parser y el experimento con LLM

La unidad de análisis es una oración declarativa con sujeto explícito, verbo transitivo y objeto directo. La siguiente EBNF define la CFG sobre categorías léxicas. El símbolo inicial es `O`. Los corchetes indican una aparición opcional y las llaves, cero o más repeticiones.

```ebnf
O  ::= ( PRON | SN ) SV
SN ::= DET N { ADJ } [ SP ]
SP ::= PREP SN
SV ::= ( V_PRES | V_PRET ) [ ADV ] SN [ ADV ]
```

Los dos tiempos son presente y pretérito perfecto simple de indicativo. Los pronombres personales de sujeto permiten contrastar las tres personas. La gramática modela categorías y concordancia, sin comprobar selección léxica o plausibilidad. Los adjetivos van después del nombre y los adverbios modifican al verbo. Cada frase preposicional modifica al núcleo nominal precedente y puede contener otra frase nominal. Para el parser basta mirar la próxima categoría en cada alternativa. El parser debe consumir toda la entrada; el lexer puede retirar un punto final y representar el fin como `EOF` fuera del árbol.

| Oración | Resultado según v1 |
|---|---|
| Yo leo el libro. | Aceptar, sujeto de primera persona y presente. |
| Las niñas leyeron ayer los libros nuevos. | Aceptar, pretérito y modificadores. |
| La niña de los vecinos lee el libro. | Aceptar, el núcleo del sujeto es «niña». |
| La niña de los vecinos leen el libro. | Rechazo semántico por el número de «leen». |
| Yo lee el libro. | Rechazo semántico por persona. |
| La niña lee los libros nuevas. | Rechazo semántico por género en el objeto. |
| Lee el libro. | Rechazo sintáctico por ausencia de sujeto explícito. |

## Estructura del árbol y tabla léxica

El parser construye un `parser.nodo.Nodo` por cada no terminal y cada categoría terminal presente. Los hijos siguen el orden de la producción. Las opciones ausentes se omiten y las repeticiones son hijos directos. Cada hoja lleva el lexema original en `valor["lexema"]`, la columna en `valor["columna"]` y la línea en `linea`, ambas desde 1. Por ejemplo, «Yo leo el libro» da `O(PRON, SV(V_PRES, SN(DET, N)))`.

El lexer registra las formas en una `TablaSimbolos` con la clave `CATEGORIA:forma` normalizada con `forma.casefold()`. Las categorías distinguen homógrafos de clases o tiempos distintos. El léxico v1 usa una sola lectura por clave y formas con los siguientes rasgos.

| Categoría | Rasgos para concordancia |
|---|---|
| N | género, número y persona 3 |
| DET, ADJ | género y número |
| PRON, V_PRES, V_PRET | número y persona |
| PREP, ADV | sin rasgos de concordancia |

El género toma los valores `m` y `f`, el número `sg` y `pl`, y la persona los enteros 1, 2 y 3. Para esta versión se eligen determinantes y adjetivos con género marcado. El siguiente registro corresponde a la hoja `Nodo("V_PRES", valor={"lexema": "Leo", "columna": 4}, linea=1)`.

```python
tabla.declarar("V_PRES:leo", "V_PRES", 1, numero="sg", persona=1)
```

Después de un análisis sintáctico completo, el parser llama a `semantico.concordancia.verificar_concordancia(oracion, tabla)`. Una lista vacía indica concordancia válida. Cada discrepancia produce un diagnóstico con fase, línea, columna y causa en la palabra dependiente. Una entrada léxica requerida ausente o incompleta produce `ValueError` para que un fallo de integración no se contabilice como rechazo de una oración. Para la evaluación con LLM, se incorporan las producciones y estas dos condiciones de aceptación en los prompts:

1. En cada SN, DET y cada ADJ comparten género y número con su propio N, también dentro de SP.
2. El verbo comparte número y persona con el N o PRON que encabeza el sujeto.

## Sección del informe · Alcance formal y puntos de falla

La jerarquía de Chomsky distingue lenguajes regulares (tipo 3), libres de contexto (tipo 2), sensibles al contexto (tipo 1) y recursivamente enumerables (tipo 0). Cada clase incluye a la anterior. Para este proyecto, reconocer formas de un léxico finito requiere solo un autómata finito. Una producción de tipo 2 puede expandir un no terminal independientemente de sus vecinos. Así, la regla de SP permite reutilizar el mismo SN en «la niña de los vecinos de la maestra». Usar una CFG describe el método de construcción y por sí solo no establece la clase mínima del fragmento.

**Concordancia a distancia.** «La niña de los vecinos lee el libro» y su variante con «leen» tienen la misma secuencia de categorías. La CFG v1 deriva ambas. El árbol conserva qué sustantivo encabeza cada SN y permite comparar el verbo con «niña», incluso si entre ambos aparecen varios plurales. Con estos dominios finitos también sería posible especializar los no terminales por género, número y persona para obtener otra CFG. Hacer la comparación sobre el árbol evita duplicar producciones y permite localizar la discrepancia.

**Dependencias cruzadas.** Como modelo formal, el lenguaje `{ a^m b^n c^m d^n | m,n ≥ 1 }` exige emparejar el primer bloque con el tercero y el segundo con el cuarto. Para una longitud de bombeo p, la palabra con cuatro bloques de tamaño p tiene cualquier ventana bombeable de longitud a lo sumo p en uno o dos bloques contiguos. Bombear hacia abajo altera al menos un contador y deja intacta su pareja distante. Esto contradice el lema de bombeo para lenguajes libres de contexto. Un autómata linealmente acotado sí puede marcar y cotejar las parejas (tipo 1). El ejemplo delimita la capacidad formal de una CFG. El subconjunto español v1 no contiene una construcción que imponga esos dos conteos ilimitados.

**Ambigüedad estructural.** En «La niña ve el libro con los lentes», el SP puede describir qué libro ve o con qué instrumento lo ve. V1 solo deriva la adjunción nominal. Agregar una producción que permita adjuntar el SP al SV admitiría la segunda lectura y podría dar dos árboles para la misma secuencia. Ambos podrían satisfacer toda la concordancia. La elección de la interpretación requiere información adicional, mientras que generar las dos estructuras sigue estando al alcance de una CFG.
