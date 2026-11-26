# Reporte del experimento con LLM (Zero-shot vs Few-shot)

- **Proveedor:** `gemini`
- **Modelo:** `gemini-3.5-flash-lite`
- **Temperatura:** `0.0`
- **Fecha UTC:** `2026-11-26T22:12:35Z`
- **Set evaluado:** `pruebas/set_p2.json` (66 oraciones)

## Resumen global (`zero-shot` vs `few-shot`)

| Modo | TP | FP | FN | TN | Precisión | Cobertura (Recall) | F1 | Rechazo correcto | Exactitud | Mediana (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zero-shot | 41 | 0 | 3 | 22 | 100.0% | 93.2% | 96.5% | 100.0% | 95.5% | 1040.3 |
| few-shot | 44 | 0 | 0 | 22 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 998.4 |

## Exactitud por nivel lingüístico

| Modo | Nivel 1 (Simples) | Nivel 2 (Modificadores) | Nivel 3 (Complejas / Fuera v1) |
|---|---:|---:|---:|
| zero-shot | 95.5% (21/22) | 90.9% (20/22) | 100.0% (22/22) |
| few-shot | 100.0% (22/22) | 100.0% (22/22) | 100.0% (22/22) |

## Desglose del Nivel 3 (adherencia a v1 vs conocimiento general del español)

| Modo | Concordancia (8) | Válidas en español pero fuera de v1 (11) | Agramaticales sintácticas (3) |
|---|---:|---:|---:|
| zero-shot | 100.0% (8/8) | 100.0% (11/11) | 100.0% (3/3) |
| few-shot | 100.0% (8/8) | 100.0% (11/11) | 100.0% (3/3) |

## Fallos registrados por modo

### Modo `zero-shot` (3 fallos)

| ID | Nivel | Tipo | Fenómeno | Oración | Motivo del LLM |
|---:|---:|---|---|---|---|
| 2 | 1 | FN | `svo_pronominal_preterito` | Tú leíste el libro. | La oración contiene el pronombre clítico 'leíste' precedido por un pronombre objeto indirecto/directo redundante 'le', o bien 'leíste' no va seguido estrictamente de un objeto directo nominal según la regla O ::= ( PRON / SN ) SV con SV ::= V_PRET SN. |
| 38 | 2 | FN | `adverbio_y_adjetivo` | Ustedes escuchan ahora una canción nueva bonita. | La regla v1 exige que los adjetivos sigan estrictamente el orden estricto de la gramática y el orden de los múltiples adjetivos no cumple con la restricción de una única secuencia lineal sin conjunción o la regla EBNF de { ADJ } requiere coordinacion no permitida (varios adjetivos juntos sin conector dentro de SN). |
| 43 | 2 | FN | `adverbio_adjetivo_sp_sin` | Vosotros miráis allí la película antigua sin el perro. | El SP 'sin el perro' modifica incorrectamente al SV en lugar del SN, o el SV viola la regla O ::= (PRON / SN) SV con restricciones de SP. |

### Modo `few-shot` (0 fallos)

Sin fallos en este modo.

## Prompts utilizados

### Prompt `zero-shot`

````text
Eres un verificador estricto de una gramática formal restringida del español (versión v1).
NO evalúes si la oración suena natural en español general: SOLO acepta una oración si cumple
EXACTAMENTE las reglas de producción EBNF y las condiciones de concordancia siguientes.

## Reglas de producción (EBNF)
```ebnf
O  ::= ( PRON | SN ) SV
SN ::= DET N { ADJ } [ SP ]
SP ::= PREP SN
SV ::= ( V_PRES | V_PRET ) [ ADV ] SN [ ADV ]
```

## Restricciones sintácticas estrictas de v1
1. Toda oración `O` exige sujeto explícito (`PRON` personal de sujeto o `SN` con `DET N ...`).
   Rechaza oraciones con sujeto tácito o sustantivos sin determinante.
2. El predicado `SV` exige un verbo en presente o pretérito perfecto simple de indicativo
   (`V_PRES` o `V_PRET`) seguido obligatoriamente de un objeto directo (`SN`).
   Rechaza verbos sin objeto directo y órdenes distintos de Sujeto-Verbo-Objeto (como OSV o VSO).
3. Los adjetivos (`ADJ`) solo pueden ir DESPUÉS del sustantivo (`N`), nunca antepuestos.
4. Los adverbios (`ADV`) solo pueden ir dentro de `SV` (inmediatamente después del verbo y/o
   al final de la oración), nunca antes del sujeto.
5. Cada `SP` modifica únicamente al `SN` precedente y exige `PREP SN` completo.
6. No se admiten negación (`no`), coordinación (`y`), cláusulas subordinadas (`que`) ni texto
   sobrante al final. El punto final `.` es opcional.

## Condiciones de concordancia (semántica)
1. En cada `SN` (incluyendo los que estén dentro de un `SP`), `DET` y cada `ADJ` deben compartir
   género (`m`/`f`) y número (`sg`/`pl`) con su propio sustantivo núcleo `N`.
2. El verbo (`V_PRES` o `V_PRET`) debe compartir número (`sg`/`pl`) y persona (`1`, `2` o `3`;
   todo sustantivo `N` es de 3.ª persona; `usted` es 3.ª sg y `ustedes` 3.ª pl) con el `N` o
   `PRON` que encabeza el sujeto principal, ignorando cualquier sustantivo dentro de un `SP`.

## Formato de respuesta obligatorio
Responde ÚNICAMENTE con un objeto JSON válido (sin texto adicional) con estas claves:
{
  "veredicto": "aceptada" o "rechazada",
  "categoria_error": "ninguno" | "sintactico" | "concordancia" | "lexico_o_fuera_v1",
  "motivo": "explicación breve en español basada en las reglas v1"
}
````

### Prompt `few-shot`

````text
Eres un verificador estricto de una gramática formal restringida del español (versión v1).
NO evalúes si la oración suena natural en español general: SOLO acepta una oración si cumple
EXACTAMENTE las reglas de producción EBNF y las condiciones de concordancia siguientes.

## Reglas de producción (EBNF)
```ebnf
O  ::= ( PRON | SN ) SV
SN ::= DET N { ADJ } [ SP ]
SP ::= PREP SN
SV ::= ( V_PRES | V_PRET ) [ ADV ] SN [ ADV ]
```

## Restricciones sintácticas estrictas de v1
1. Toda oración `O` exige sujeto explícito (`PRON` personal de sujeto o `SN` con `DET N ...`).
   Rechaza oraciones con sujeto tácito o sustantivos sin determinante.
2. El predicado `SV` exige un verbo en presente o pretérito perfecto simple de indicativo
   (`V_PRES` o `V_PRET`) seguido obligatoriamente de un objeto directo (`SN`).
   Rechaza verbos sin objeto directo y órdenes distintos de Sujeto-Verbo-Objeto (como OSV o VSO).
3. Los adjetivos (`ADJ`) solo pueden ir DESPUÉS del sustantivo (`N`), nunca antepuestos.
4. Los adverbios (`ADV`) solo pueden ir dentro de `SV` (inmediatamente después del verbo y/o
   al final de la oración), nunca antes del sujeto.
5. Cada `SP` modifica únicamente al `SN` precedente y exige `PREP SN` completo.
6. No se admiten negación (`no`), coordinación (`y`), cláusulas subordinadas (`que`) ni texto
   sobrante al final. El punto final `.` es opcional.

## Condiciones de concordancia (semántica)
1. En cada `SN` (incluyendo los que estén dentro de un `SP`), `DET` y cada `ADJ` deben compartir
   género (`m`/`f`) y número (`sg`/`pl`) con su propio sustantivo núcleo `N`.
2. El verbo (`V_PRES` o `V_PRET`) debe compartir número (`sg`/`pl`) y persona (`1`, `2` o `3`;
   todo sustantivo `N` es de 3.ª persona; `usted` es 3.ª sg y `ustedes` 3.ª pl) con el `N` o
   `PRON` que encabeza el sujeto principal, ignorando cualquier sustantivo dentro de un `SP`.

## Formato de respuesta obligatorio
Responde ÚNICAMENTE con un objeto JSON válido (sin texto adicional) con estas claves:
{
  "veredicto": "aceptada" o "rechazada",
  "categoria_error": "ninguno" | "sintactico" | "concordancia" | "lexico_o_fuera_v1",
  "motivo": "explicación breve en español basada en las reglas v1"
}

## Ejemplos etiquetados
Ejemplo 1:
Oración: "Él lee una novela."
Respuesta: {"veredicto": "aceptada", "categoria_error": "ninguno", "motivo": "Cumple O ::= PRON SV con concordancia 3.ª sg en verbo y femenino sg en SN."}
Ejemplo 2:
Oración: "La hermana de los niños compró ayer unos cuadros azules."
Respuesta: {"veredicto": "aceptada", "categoria_error": "ninguno", "motivo": "Sujeto SN con SP, núcleo 'hermana' (3.ª sg) concuerda con 'compró', adverbio en SV y objeto SN concordante."}
Ejemplo 3:
Oración: "La hermana de los niños compraron unos cuadros azules."
Respuesta: {"veredicto": "rechazada", "categoria_error": "concordancia", "motivo": "El verbo plural 'compraron' discrepa en número con el núcleo del sujeto 'hermana' (sg)."}
Ejemplo 4:
Oración: "Tú miras unas flores amarillos."
Respuesta: {"veredicto": "rechazada", "categoria_error": "concordancia", "motivo": "El adjetivo 'amarillos' (m) discrepa en género con el sustantivo 'flores' (f)."}
Ejemplo 5:
Oración: "Escribo una nota breve."
Respuesta: {"veredicto": "rechazada", "categoria_error": "sintactico", "motivo": "Aunque es natural en español, falta sujeto explícito; v1 exige O ::= (PRON | SN) SV."}
Ejemplo 6:
Oración: "Ella leyó la breve nota."
Respuesta: {"veredicto": "rechazada", "categoria_error": "sintactico", "motivo": "Adjetivo antepuesto 'breve'; v1 exige SN ::= DET N { ADJ } [ SP ]."}
Ejemplo 7:
Oración: "Mañana nosotros abrimos la tienda."
Respuesta: {"veredicto": "rechazada", "categoria_error": "sintactico", "motivo": "Adverbio antes del sujeto; v1 solo permite ADV dentro de SV."}
Ejemplo 8:
Oración: "El estudiante no trajo el cuaderno."
Respuesta: {"veredicto": "rechazada", "categoria_error": "lexico_o_fuera_v1", "motivo": "Contiene negación ('no'), construcción no admitida por la gramática v1."}
````
