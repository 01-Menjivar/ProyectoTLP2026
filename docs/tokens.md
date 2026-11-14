# Especificación formal de tokens de mini-C

Los tokens se definen con **expresiones regulares** (lenguajes regulares, tipo 3 de Chomsky), que es
exactamente lo que implementa `lexer/lexer.py`. Las expresiones usan la sintaxis de Python (`re`).
Ver el alcance del lenguaje en `docs/lenguaje_c.md`.

## Tokens que llegan al resto del compilador

| Tipo de token | Expresión regular | Ejemplos |
|---|---|---|
| `TIPO` | `int` \| `float` \| `char` | `int`, `float` |
| `IF` `ELSE` `WHILE` `PRINTF` | la palabra exacta (`if`, `else`, `while`, `printf`) | `while` |
| `ID` | `[A-Za-z_][A-Za-z0-9_]*`, excepto palabras reservadas | `total`, `_x1` |
| `ENTERO` | `[0-9]+` | `0`, `42` |
| `FLOTANTE` | `[0-9]+\.[0-9]+` | `2.50` |
| `CARACTER` | `'([^'\\\n]\|\\[^\n])'` | `'a'`, `'\n'` |
| `CADENA` | `"([^"\\\n]\|\\[^\n])*"` | `"hola\n"` |
| `MAS` `MENOS` `POR` `DIVIDIDO` `MODULO` | `+` `-` `*` `/` `%` | |
| `IGUAL` | `=` | |
| `IGUAL_IGUAL` `DIFERENTE` | `==` `!=` | |
| `MENOR` `MAYOR` `MENOR_IGUAL` `MAYOR_IGUAL` | `<` `>` `<=` `>=` | |
| `Y_LOGICO` `O_LOGICO` `NO_LOGICO` | `&&` `\|\|` `!` | |
| `PAREN_IZQ` `PAREN_DER` | `(` `)` | |
| `LLAVE_IZQ` `LLAVE_DER` | `{` `}` | |
| `PUNTOYCOMA` `COMA` | `;` `,` | |
| `EOF` | lo agrega el lexer al final | |

Las palabras reservadas se reconocen primero como `ID` y luego se buscan en una tabla. Así `interior`
es un `ID` y no `int` seguido de `erior`. Los literales `CARACTER` y `CADENA` conservan sus comillas en el lexema.

## Lo que el lexer descarta

| Categoría | Expresión regular |
|---|---|
| Comentario de línea | `//[^\n]*` |
| Comentario de bloque | `/\*(.\|\n)*?\*/` (puede ocupar varias líneas) |
| Espacios | `[ \t\r]+` |
| Salto de línea | `\n` (se descarta, pero se cuenta para la línea) |

## Errores léxicos

| Error | Cuándo ocurre | Mensaje |
|---|---|---|
| Carácter inválido | Cualquier carácter fuera del lenguaje (`@`, `#`, `$`, `ñ` fuera de cadenas...) | `Carácter inválido '@'` |
| Operador incompleto | Un `&` o un `\|` solitario | `Operador incompleto '&': ¿quiso decir '&&'?` |
| Cadena sin cerrar | Comilla `"` sin cierre en la misma línea | `Cadena sin cerrar: falta la comilla de cierre` |
| Carácter mal formado | `''`, `'ab'`, `'a` | `Literal de carácter mal formado 'ab': debe contener exactamente un carácter` |
| Comentario sin cerrar | `/*` sin su `*/` | `Comentario de bloque sin cerrar: falta '*/'` |
| Número mal formado | `3a`, `3.`, `.5`, `3.5.2` | `Número mal formado '3a'` |

## Orden de las alternativas (importa)

El lexer prueba los patrones de izquierda a derecha y toma el **primero** que encaja:

1. Comentarios antes que `/`: si no, `//` se leería como dos divisiones.
2. `FLOTANTE` antes que `ENTERO`: para leer `3.5` completo.
3. `&&`, `||`, `==`, `!=`, `<=`, `>=` antes que los símbolos de un carácter.
4. Las versiones "sin cerrar" justo después de las cerradas.
5. `DESCONOCIDO` (cualquier carácter) al final: garantiza que el recorrido nunca se atasca.

## Autómata finito de los números (ENTERO y FLOTANTE)

| Estado | Dígito | `.` | Otro carácter |
|---|---|---|---|
| `q0` (inicio) | `q1` | error | error |
| `q1` **acepta ENTERO** | `q1` | `q2` | termina el token |
| `q2` (tras el punto) | `q3` | error | error |
| `q3` **acepta FLOTANTE** | `q3` | error (`3.5.2`) | termina el token |

Un número seguido de una letra o un guion bajo también es error (`3a`). Esto muestra que el léxico
no necesita memoria auxiliar: un autómata finito alcanza.
