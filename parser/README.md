# Representación mínima del programa (AST)

**Responsable:** Kattia Santana (P2)  ·  **Estado:** Listo

En la Fase 1 **no hay parser**: el PDF permite que el analizador semántico trabaje sobre "un AST mínimo
construido a mano". Este módulo define esa representación. El parser del español es de la Fase 2.

## Qué contiene
- `nodo.py`: la clase `Nodo(tipo, hijos, valor, linea, tipo_dato=None)`.
- Los AST de ejemplo, hechos a mano, están en `pruebas/ejemplos/ast/` (ver el README de esa carpeta).

## Qué recibe y qué devuelve
El semántico (`semantico.analizar`) recibe la raíz del árbol, un `Nodo` de tipo `Programa`. Qué va en `valor` y en
`hijos` de cada tipo de nodo está en la sección 3 de `docs/contratos.md`.

## Cómo se usa
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
python -m unittest pruebas.test_ast
```

## Decisiones de diseño
- Un nodo tiene siempre las mismas cinco claves (`tipo`, `valor`, `linea`, `tipo_dato`, `hijos`), aunque algunas
  estén vacías. Así P3 y P4 recorren el árbol con una sola función, sin casos especiales por tipo de nodo.
- `linea` cuenta desde la línea 1 del archivo `.c`, incluido el comentario `// ESPERADO`, igual que los errores del lexer.
- Los literales ya traen su `tipo_dato`; el semántico lo llena en el resto de las expresiones.
- `Si` lleva `[condicion, bloque]` o `[condicion, bloque, bloque_else]`; todo cuerpo de `Si` y `Mientras` es un `Bloque`.
- Los AST se escriben a mano porque no hay parser en esta fase. Cada uno corresponde a un programa del corpus.
