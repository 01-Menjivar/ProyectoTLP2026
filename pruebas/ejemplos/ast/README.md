# AST de ejemplo

Cada archivo `.json` es el árbol del programa `.c` del corpus que lleva el mismo nombre. Sirven para probar el
semántico sin pasar por el convertidor. Formato en `docs/contratos.md`, sección 3. Las líneas cuentan desde la línea 1 del `.c`.

| JSON | Programa del corpus | Qué muestra | Resultado esperado del semántico |
|---|---|---|---|
| `ejemplo.json` | `validos/ejemplo.c` | Declaraciones, operaciones, `if/else`, `while`, `printf` | ok |
| `07_ambitos_y_bloques.json` | `validos/07_ambitos_y_bloques.c` | Bloque suelto con su propio ámbito (reusa `x`) y variable local en un ciclo | ok |
| `10_cadena_en_entero.json` | `invalidos/10_cadena_en_entero.c` | `int n = "hola";` | error semántico, línea 3 (S3) |
| `15_variable_fuera_de_su_ambito.json` | `invalidos/15_variable_fuera_de_su_ambito.c` | `dentro` usada fuera de su bloque | error semántico, línea 6 (S8) |
| `08_variable_no_declarada.json` | `invalidos/08_variable_no_declarada.c` | `total` usada sin declarar | error semántico, línea 4 (S1) |
| `09_redeclaracion.json` | `invalidos/09_redeclaracion.c` | `a` declarada dos veces | error semántico, línea 4 (S2) |
| `17_printf_sin_cadena.json` | `invalidos/17_printf_sin_cadena.c` | `printf(x)` | error semántico, línea 4 (S10) |
| `02_aritmetica_y_precedencia.json` | `validos/02_aritmetica_y_precedencia.c` | `%`, signo negativo (`OpUnario`), precedencia, paréntesis | ok |
| `08_char_y_promociones.json` | `validos/08_char_y_promociones.c` | Literales `char` y promociones | ok |

Los cuatro primeros se escribieron a mano; los otros cinco los generó `parser/convertidor.py`. Para cualquier otro
programa del corpus no hace falta JSON: `codigo_a_ast(texto)` lo construye al vuelo.

Cargar uno:

```python
from parser.nodo import Nodo
ast = Nodo.desde_json(open("pruebas/ejemplos/ast/ejemplo.json", encoding="utf-8").read())
```
