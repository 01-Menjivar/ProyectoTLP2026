# Parser de español - Fase 2

`espanol.py` implementa el parser descendente recursivo de P4 para la gramática
v1 definida en `docs/gramatica_espanol.md`.

## Entrada acordada con P1

Recibe una secuencia de `lexer.lexer.Token(tipo, lexema, linea, columna)` con
las categorías `PRON`, `DET`, `N`, `ADJ`, `PREP`, `V_PRES`, `V_PRET`, `ADV`,
un `EOF` final y, opcionalmente, `PUNTO` antes de `EOF`.

## API

```python
tokens_a_arbol(tokens) -> (Nodo("O") | None, errores)
analizar(tokens, tabla) -> (Nodo("O") | None, errores)
```

`tokens_a_arbol` solo revisa sintaxis. `analizar` llama a
`verificar_concordancia` cuando el árbol es válido y conserva sus diagnósticos
semánticos. Una entrada léxica ausente o sin rasgos necesarios genera
`ValueError`, según el contrato de P3.

## Pruebas

Desde la raíz del repositorio:

```sh
python -m unittest pruebas.test_parser_espanol
python -m unittest discover pruebas
```
