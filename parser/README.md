# Representación mínima del programa (AST)

**Responsable:** Kattia Santana (P2)  ·  **Estado:** Listo

En la Fase 1 **no hay parser**: el PDF permite que el analizador semántico trabaje sobre "un AST mínimo
construido a mano". Este módulo define esa representación. El parser del español es de la Fase 2.

## Qué contiene
- `nodo.py`: la clase `Nodo(tipo, hijos, valor, linea, tipo_dato=None)`.
- `convertidor.py`: convierte los tokens del lexer en un AST (descenso recursivo sobre mini-C), para correr cualquier
  programa `.c` del corpus sin escribir el árbol a mano. No es el parser del proyecto: el del español es de la Fase 2.
- Los AST de ejemplo están en `pruebas/ejemplos/ast/` (ver el README de esa carpeta).

## Qué recibe y qué devuelve
El semántico (`semantico.analizar`) recibe la raíz del árbol, un `Nodo` de tipo `Programa`. Qué va en `valor` y en
`hijos` de cada tipo de nodo está en la sección 3 de `docs/contratos.md`.

## Del código `.c` al AST

```python
from parser.convertidor import codigo_a_ast

raiz, errores = codigo_a_ast(open("pruebas/ejemplos/validos/ejemplo.c", encoding="utf-8").read())
# raiz: Nodo "Programa" (o None si hubo errores);  errores: lista de {fase, linea, columna, mensaje}
```

Desde la terminal (imprime el AST en JSON, o los errores):

```
python -m parser.convertidor pruebas/ejemplos/validos/ejemplo.c
```

- Si el lexer encuentra errores, no se construye el árbol y se devuelven los errores léxicos (`fase: "lexico"`).
- Si la forma del programa no cumple la gramática (falta un `;`, un `if` sin llaves, un `}` sin cerrar), se devuelven
  errores con `fase: "sintactico"` y la raíz es `None`: un árbol a medias haría que el semántico reporte errores falsos.
- El convertidor solo revisa la **forma**. `printf(x)`, `"a" * 2` o `int n = "hola";` dan un AST normal; los rechaza el
  semántico.
- Los paréntesis solo agrupan: no dejan nodo en el árbol. Los operadores binarios son asociativos por la izquierda.
  La gramática completa y la precedencia están en el docstring de `convertidor.py`.

## Cómo se usa el AST
Desde la raíz del repositorio:

```python
from parser.nodo import Nodo

with open("pruebas/ejemplos/ast/ejemplo.json", encoding="utf-8") as f:
    ast = Nodo.desde_json(f.read())      # JSON -> Nodo

print(ast.tipo, len(ast.hijos))          # Programa 5
print(ast.a_json())                      # Nodo -> JSON
```

Para comprobar que los ejemplos son coherentes con el contrato y con el lexer:

```
python -m unittest pruebas.test_ast pruebas.test_convertidor
```

`test_convertidor` comprueba que el convertidor produce exactamente los mismos árboles que los JSON de ejemplo, que
todo el corpus se convierte, la precedencia y los errores sintácticos.

## Decisiones de diseño
- Un nodo tiene siempre las mismas cinco claves (`tipo`, `valor`, `linea`, `tipo_dato`, `hijos`), aunque algunas
  estén vacías. Así P3 y P4 recorren el árbol con una sola función, sin casos especiales por tipo de nodo.
- `linea` cuenta desde la línea 1 del archivo `.c`, incluido el comentario `// ESPERADO`, igual que los errores del lexer.
- Los literales ya traen su `tipo_dato`; el semántico lo llena en el resto de las expresiones.
- `Si` lleva `[condicion, bloque]` o `[condicion, bloque, bloque_else]`; todo cuerpo de `Si` y `Mientras` es un `Bloque`.
- Los primeros cuatro AST se escribieron a mano; los demás los genera el convertidor y se revisaron contra el contrato.
  Cada JSON corresponde a un programa del corpus. Como el convertidor reproduce los cuatro hechos a mano, los dos
  caminos coinciden.
- Los errores de forma usan `fase: "sintactico"`, que se suma a `lexico` y `semantico` del contrato.
