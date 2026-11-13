# Corpus de programas de prueba

Cada programa lleva en su **primera línea** el resultado esperado (`// ESPERADO: ...`).
Un programa inválido tiene **un solo error** (salvo `04_varios_errores_lexicos`), para que no haya dudas
sobre qué debe detectar cada módulo. La línea indicada cuenta desde la línea 1 del archivo,
incluidos los comentarios del encabezado.

## Válidos (`validos/`)

| Archivo | Qué prueba |
|---|---|
| `ejemplo.mz` | Programa completo del proyecto: declaraciones, si/sino, mientras |
| `01_tipos_y_declaraciones` | Los 4 tipos, con y sin valor inicial |
| `02_aritmetica_y_precedencia` | `+ - * / %`, precedencia, paréntesis, signo negativo |
| `03_logicos_y_comparaciones` | `== != < > <= >=` y `y`, `o`, `no` combinados |
| `04_si_sin_sino` | `si` sin rama `sino` |
| `05_si_sino_anidados` | `si/sino` dentro de un `sino` |
| `06_mientras_acumulador` | Ciclo `mientras` con acumulador |
| `07_ambitos_y_bloques` | Bloque suelto, reusar un nombre en otro ámbito, variable local en un ciclo |
| `08_texto_y_concatenacion` | `+` entre textos y `==` entre textos |
| `09_promocion_entero_a_decimal` | Un entero se guarda en un decimal |
| `10_aviso_sin_inicializar` | Variable sin valor inicial usada: genera un **aviso** (S9), el programa sigue siendo válido |

## Inválidos (`invalidos/`)

| Archivo | Fase que lo detecta | Qué debe reportar |
|---|---|---|
| `01_caracter_invalido` | léxico | `Carácter inválido '@'` (línea 4) |
| `02_texto_sin_cerrar` | léxico | texto sin comilla de cierre (línea 4) |
| `03_numero_pegado_a_letra` | léxico | `Número mal formado '3a'` (línea 3) |
| `04_varios_errores_lexicos` | léxico | **3 errores**, en las líneas 3, 4 y 5 |
| `05_falta_punto_y_coma` | sintáctico | falta `;`; se nota en el token `imprimir` de la línea siguiente |
| `06_falta_parentesis_de_cierre` | sintáctico | llega `{` donde se esperaba `)` |
| `07_expresion_incompleta` | sintáctico | llega `;` donde se esperaba un operando |
| `08_variable_no_declarada` | semántico (S1) | `total` no declarada |
| `09_redeclaracion` | semántico (S2) | `a` declarada dos veces |
| `10_texto_en_entero` | semántico (S3) | texto asignado a entero |
| `11_decimal_en_entero` | semántico (S3) | decimal asignado a entero |
| `12_aritmetica_con_texto` | semántico (S4) | `texto - entero` |
| `13_condicion_no_booleana` | semántico (S5) | `si (n)` con `n` entero |
| `14_logico_con_no_booleanos` | semántico (S6) | `5 y verdadero` |
| `15_variable_fuera_de_su_ambito` | semántico (S8) | `dentro` usada fuera de su bloque |

No hay caso para S7 (comparaciones entre tipos): conviene que P3 decida primero qué combinaciones
son compatibles (por ejemplo `entero == decimal`, `texto < texto`, `booleano == booleano`).

## Decisiones que este corpus deja abiertas (hablarlas en el grupo)

1. **Línea de un error sintáctico:** se asume la línea **del primer token inesperado** (por eso en
   `05_falta_punto_y_coma` es la línea de `imprimir`, no la del `5`). P2 debe confirmarlo.
2. **Declaración sin valor inicial en Python** (`entero contador;`): P4 decide qué genera
   (por ejemplo `0`, `0.0`, `""` o `False` según el tipo). Si no genera nada, `10_aviso_sin_inicializar`
   fallaría al ejecutarse.
3. **Un error por programa:** P3 no debe encadenar errores falsos (por ejemplo, en
   `12_aritmetica_con_texto` solo debe reportar el error de `t - 1`, no uno más por asignar el resultado).
