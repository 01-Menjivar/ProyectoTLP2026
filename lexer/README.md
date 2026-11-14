# Analizador léxico

**Responsable:** P1  ·  **Estado:** Listo

## Qué recibe
El texto de un programa `.c` (un `str`).

## Qué devuelve
`analizar(codigo)` devuelve `(tokens, errores)`:

- `tokens`: lista de `Token(tipo, lexema, linea, columna)` que **siempre termina con un token `EOF`**.
  Los comentarios y los espacios no generan tokens.
- `errores`: lista de `{"fase": "lexico", "linea", "columna", "mensaje"}`.
  El lexer **no se detiene** en el primer error: salta el fragmento inválido y sigue.

La especificación formal de los tokens (expresiones regulares) está en `docs/tokens.md`.
Un ejemplo completo en `tokens_ejemplo.json` (cada token como `[tipo, lexema, linea, columna]`).

## Errores léxicos que detecta
Carácter inválido, operador incompleto (`&`, `|`), cadena sin cerrar, literal de carácter mal formado,
comentario de bloque sin cerrar y número mal formado (`3a`, `3.`, `.5`, `3.5.2`). Detalle en `docs/tokens.md`.

## Cómo se ejecuta y se prueba
Desde la raíz del repositorio:

```
python -m lexer.lexer pruebas/ejemplos/validos/ejemplo.c      # imprime los tokens y crea salida/tokens.txt
python -m unittest pruebas.test_lexer                          # corre las pruebas del lexer
```

## Decisiones de diseño
- **Expresiones regulares en orden:** el patrón maestro prueba las alternativas de izquierda a derecha y toma la
  primera que encaja, así que el orden decide (comentarios antes que `/`, `FLOTANTE` antes que `ENTERO`,
  `&&` antes que `&`).
- **Un solo recorrido:** el lexer avanza por el texto una vez, llevando la cuenta de línea y columna. Los comentarios de
  bloque pueden ocupar varias líneas y también se cuentan.
- **Números mal formados:** un número pegado a una letra, a `_` o a otro punto se consume completo y se reporta una
  sola vez (así `3.5.2` no genera tres errores).
- **Palabras reservadas:** se reconocen como identificadores y después se buscan en una tabla. Así `interior` es un
  `ID` y no `int` + `erior`.
- **Identificadores ASCII:** como en C, la `ñ` o las tildes solo se permiten dentro de cadenas y comentarios.
- **Jerarquía de Chomsky:** el léxico de mini-C es un lenguaje regular, por eso alcanza con expresiones regulares
  (equivalentes a un autómata finito).
