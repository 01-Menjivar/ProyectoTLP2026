# Fase 2 · Gramática del español v1 y concordancia

## Gramática formal (EBNF)

La unidad de análisis es una oración declarativa con sujeto explícito, verbo transitivo (presente `V_PRES` o pretérito perfecto simple `V_PRET` de indicativo) y objeto directo. El símbolo inicial es `O`; los corchetes indican opcionalidad y las llaves, cero o más repeticiones.

```ebnf
O  ::= ( PRON | SN ) SV
SN ::= DET N { ADJ } [ SP ]
SP ::= PREP SN
SV ::= ( V_PRES | V_PRET ) [ ADV ] SN [ ADV ]
```

Los adjetivos van después del sustantivo, los adverbios modifican al verbo y cada frase preposicional modifica al núcleo nominal precedente. El parser es `LL(1)` y consume toda la entrada (con punto final opcional).

| Oración | Resultado según v1 |
|---|---|
| Yo leo el libro. | Aceptar (sujeto 1.ª sg, presente). |
| Las niñas leyeron ayer los libros nuevos. | Aceptar (pretérito y modificadores). |
| La niña de los vecinos lee el libro. | Aceptar (núcleo del sujeto: «niña»). |
| La niña de los vecinos leen el libro. | Rechazo semántico por número en «leen». |
| Yo lee el libro. | Rechazo semántico por persona. |
| La niña lee los libros nuevas. | Rechazo semántico por género en el objeto. |
| Lee el libro. | Rechazo sintáctico por falta de sujeto explícito. |

## Rasgos y reglas de concordancia

Las categorías léxicas se registran en `TablaSimbolos` bajo la clave `CATEGORIA:forma` (normalizada con `casefold()`) con los siguientes rasgos:

| Categoría | Rasgos |
|---|---|
| `N` | `genero` (`m`/`f`), `numero` (`sg`/`pl`), `persona` (`3`) |
| `DET`, `ADJ` | `genero` (`m`/`f`), `numero` (`sg`/`pl`) |
| `PRON`, `V_PRES`, `V_PRET` | `numero` (`sg`/`pl`), `persona` (`1`, `2`, `3`) |
| `PREP`, `ADV` | sin rasgos de concordancia |

Tras el análisis sintáctico, `semantico.concordancia.verificar_concordancia(oracion, tabla)` valida:
1. **Concordancia nominal:** en cada `SN` (incluyendo los internos a un `SP`), `DET` y cada `ADJ` comparten género y número con su propio `N`.
2. **Concordancia verbal:** el verbo comparte número y persona con el `N` o `PRON` que encabeza el sujeto principal.

## Alcance formal y puntos de falla de la CFG

- **Jerarquía de Chomsky:** reconocer formas de un léxico finito requiere un autómata finito (tipo 3); la recursión estructural de `SP` dentro de `SN` corresponde a una gramática libre de contexto (tipo 2); la concordancia no local se resuelve en la fase semántica sobre el árbol construido.
- **Concordancia a distancia:** la CFG deriva tanto *"La niña de los vecinos lee el libro"* como *"La niña de los vecinos leen el libro"*. Verificar sobre el árbol evita duplicar no terminales por rasgos y localiza la palabra discordante.
- **Dependencias cruzadas:** lenguajes como `{ a^m b^n c^m d^n | m,n ≥ 1 }` exceden las CFG por el lema de bombeo y requieren capacidad de tipo 1 (autómata linealmente acotado).
- **Ambigüedad estructural:** en *"La niña ve el libro con los lentes"*, v1 solo deriva adjunción nominal para evitar dos árboles válidos cuya desambiguación requiere información semántica externa.
