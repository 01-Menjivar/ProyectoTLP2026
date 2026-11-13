# Analizador léxico

**Responsable:** P1  ·  **Estado:** Listo (versión base; falta ampliar el corpus de pruebas)

## Qué recibe
El texto de un programa `.mz` (un `str`).

## Qué devuelve
`analizar(codigo)` devuelve `(tokens, errores)`:

- `tokens`: lista de `Token(tipo, lexema, linea, columna)` que **siempre termina con un token `EOF`**.
  Los comentarios y los espacios no generan tokens.
- `errores`: lista de `{"fase": "lexico", "linea", "columna", "mensaje"}`.
  El lexer **no se detiene** en el primer error: salta el fragmento inválido y sigue.

Tipos de token y formato: ver `docs/contratos.md`. Un ejemplo completo en `tokens_ejemplo.json`
(cada token como `[tipo, lexema, linea, columna]`).

## Errores léxicos que detecta
| Error | Ejemplo | Mensaje |
|---|---|---|
| Carácter inválido | `3 @ 4`, `a ! b` | `Carácter inválido '@'` |
| Texto sin cerrar | `"hola;` | `Texto sin cerrar: falta la comilla de cierre` |
| Número mal formado | `3a`, `3.`, `3.5.2` | `Número mal formado '3a'` |

## Cómo se ejecuta y se prueba
Desde la raíz del repositorio:

```
python -m lexer.lexer pruebas/ejemplos/validos/ejemplo.mz     # imprime los tokens y crea salida/tokens.txt
python -m unittest discover pruebas                            # corre las pruebas del lexer
```

## Decisiones de diseño
- **Expresiones regulares en orden:** el patrón maestro prueba las alternativas de izquierda a derecha,
  así que el orden decide. `DECIMAL` va antes que `ENTERO` (para leer `3.5` completo) y `==` antes que `=`.
- **Un solo recorrido:** el lexer avanza por el texto una vez, llevando la cuenta de línea y columna.
- **Números mal formados:** un número pegado a una letra, a `_` o a otro punto se consume completo
  y se reporta una sola vez (así `3.5.2` no genera tres errores).
- **Textos:** el lexema conserva las comillas. No admiten escapes ni saltos de línea (decisión de la v1).
- **Palabras reservadas:** se reconocen como identificadores y después se buscan en una tabla. Así `siempre`
  es un `ID` y no `SI` + `empre`. Los cuatro tipos de dato comparten el token `TIPO`.
- **Jerarquía de Chomsky:** el léxico de Manzana es un lenguaje regular, por eso alcanza con expresiones regulares.
