# AST de ejemplo (hechos a mano)

Cada archivo `.json` es el árbol del programa `.c` del corpus que lleva el mismo nombre. Sirven para probar el
semántico sin parser. Formato en `docs/contratos.md`, sección 3. Las líneas cuentan desde la línea 1 del `.c`.

| JSON | Programa del corpus | Qué muestra | Resultado esperado del semántico |
|---|---|---|---|
| `ejemplo.json` | `validos/ejemplo.c` | Declaraciones, operaciones, `if/else`, `while`, `printf` | ok |
| `07_ambitos_y_bloques.json` | `validos/07_ambitos_y_bloques.c` | Bloque suelto con su propio ámbito (reusa `x`) y variable local en un ciclo | ok |
| `10_cadena_en_entero.json` | `invalidos/10_cadena_en_entero.c` | `int n = "hola";` | error semántico, línea 3 (S3) |
| `15_variable_fuera_de_su_ambito.json` | `invalidos/15_variable_fuera_de_su_ambito.c` | `dentro` usada fuera de su bloque | error semántico, línea 6 (S8) |

Cargar uno:

```python
from parser.nodo import Nodo
ast = Nodo.desde_json(open("pruebas/ejemplos/ast/ejemplo.json", encoding="utf-8").read())
```
