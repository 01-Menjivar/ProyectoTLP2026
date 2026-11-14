# Corpus de programas de prueba (mini-C)

Cada programa lleva en su **primera línea** el resultado esperado (`// ESPERADO: ...`).
Un programa inválido tiene **un solo error** (salvo `07_varios_errores_lexicos`). La línea indicada cuenta desde la
línea 1 del archivo, incluidos los comentarios del encabezado. Según el PDF, las entradas inválidas deben producir
**errores léxicos o semánticos** claros, con línea y causa.

## Válidos (`validos/`)

| Archivo | Qué prueba |
|---|---|
| `ejemplo.c` | Programa completo: declaraciones, if/else, while, printf |
| `01_tipos_y_declaraciones` | Los 3 tipos, con y sin valor inicial |
| `02_aritmetica_y_precedencia` | `+ - * / %`, precedencia, paréntesis, signo negativo |
| `03_comparaciones_y_logicos` | `== != < > <= >=` y `&& \|\| !`, con resultado `int` |
| `04_if_sin_else` | `if` sin rama `else` |
| `05_if_else_anidados` | `if/else` dentro de un `else` |
| `06_while_acumulador` | Ciclo `while` con acumulador |
| `07_ambitos_y_bloques` | Bloque suelto, reusar un nombre en otro ámbito, variable local en un ciclo |
| `08_char_y_promociones` | `char` a `int` a `float` (ensanchar) |
| `09_cadenas_y_comentarios` | Escapes en cadenas, comentarios de línea y de bloque de varias líneas |
| `10_aviso_sin_inicializar` | Variable sin valor inicial usada: genera un **aviso** (S9); el programa sigue siendo válido |

## Inválidos (`invalidos/`)

| Archivo | Fase que lo detecta | Qué debe reportar |
|---|---|---|
| `01_caracter_invalido` | léxico | `Carácter inválido '@'` (línea 4) |
| `02_cadena_sin_cerrar` | léxico | cadena sin comilla de cierre (línea 4) |
| `03_numero_pegado_a_letra` | léxico | `Número mal formado '3a'` (línea 3) |
| `04_operador_incompleto` | léxico | `&` solo (línea 5) |
| `05_caracter_mal_formado` | léxico | `'ab'` (línea 3) |
| `06_comentario_sin_cerrar` | léxico | `/*` sin cierre (línea 4) |
| `07_varios_errores_lexicos` | léxico | **3 errores**, en las líneas 3, 4 y 5 |
| `08_variable_no_declarada` | semántico (S1) | `total` no declarada |
| `09_redeclaracion` | semántico (S2) | `a` declarada dos veces |
| `10_cadena_en_entero` | semántico (S3) | cadena asignada a `int` |
| `11_float_en_int` | semántico (S3) | `float` asignado a `int` (estrechar) |
| `12_aritmetica_con_cadena` | semántico (S4) | `"a" * 2` |
| `13_condicion_con_cadena` | semántico (S5) | `if ("hola")` |
| `14_logico_con_cadena` | semántico (S6) | `"a" && 1` |
| `15_variable_fuera_de_su_ambito` | semántico (S8) | `dentro` usada fuera de su bloque |
| `16_modulo_con_float` | semántico (S4) | `float % int` |
| `17_printf_sin_cadena` | semántico (S10) | `printf(x)` |
| `18_comparacion_con_cadena` | semántico (S7) | `"a" == 1` |

## Decisiones que este corpus deja abiertas
1. **Un error por programa:** el semántico no debe encadenar errores falsos (por ejemplo, en `12_aritmetica_con_cadena`
   solo debe reportar `"a" * 2`, no uno más por asignar el resultado a `int`).
2. **Reglas más estrictas que C real:** estrechar (`float` a `int`) y guardar una cadena en una variable son errores
   aquí, aunque C los permite con avisos. Está documentado en `docs/lenguaje_c.md`.
