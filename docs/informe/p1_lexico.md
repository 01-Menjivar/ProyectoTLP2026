# Analizador léxico (P1)

## Función dentro del compilador

El analizador léxico (lexer) es la primera fase del compilador. Recibe el programa fuente
como una sola cadena de caracteres y la convierte en una secuencia de **tokens**, que son las unidades
con significado del lenguaje el **lexema** es el texto exacto que se
leyó (`manzanas`, `3`, `=`), y el **token** es ese lexema junto con su categoría y su posición
(`ID`, `ENTERO`, `IGUAL`, con línea y columna). Los espacios y los comentarios se descartan, de modo que
el parser nunca los ve.

| Entrada | `entero` | `n` | `=` | `3` | `;` |
|---|---|---|---|---|---|
| Token | `TIPO` | `ID` | `IGUAL` | `ENTERO` | `PUNTOYCOMA` |

La lista de tokens siempre termina con un token `EOF`, y su formato `(tipo, lexema, línea, columna)`
es el contrato que comparte con el parser.

## Implementación

El lexer usa una **expresión regular** formada por grupos con nombre, uno por
categoría: comentarios, espacios, decimales, enteros, textos, identificadores, símbolos y un grupo final
que atrapa cualquier carácter no reconocido. Recorre el texto una sola vez, de izquierda a derecha, y en cada
posición prueba las alternativas en orden, quedándose con la primera que encaja.

Ese orden es una decisión de diseño: se toma la primera coincidencia y no la más larga,
`DECIMAL` debe ir antes que `ENTERO` (para leer `3.5` completo y no `3` y `.5`), y los operadores de dos
caracteres (`==`, `<=`) antes que los de uno (`=`, `<`).

Las palabras reservadas se reconocen primero como identificadores y luego se buscan en una tabla. Así
`siempre` es un `ID`. Los cuatro tipos de dato (`entero`, `decimal`, `texto`,
`booleano`) comparten el token `TIPO`.

## Relación con la jerarquía de Chomsky

Las categorías de token(números, identificadores, textos, operadores) se describen con
expresiones regulares, es decir, pertenecen a los **lenguajes regulares** (tipo 3), el nivel más simple de la
jerarquía. Las expresiones regulares son equivalentes a los autómatas finitos, que reconocen sin memoria
auxiliar: para decidir si un trozo de texto es un número o un identificador basta con mirar los caracteres
en orden, sin contar ni recordar estructuras anidadas.

## Manejo de errores

El lexer detecta tres errores: **carácter inválido** (`@`, `#`), **texto sin cerrar** y **número mal formado**
(`3a`, `3.`, `3.5.2`). En lugar de detenerse en el primero, lo registra con su fase, línea, columna y mensaje, salta el
fragmento inválido y continúa, de modo que un programa con varios errores léxicos los reporta todos en una
sola pasada. El grupo final de la expresión regular garantiza que siempre exista una coincidencia, así que
el recorrido nunca se atasca. Un número mal formado se detecta mirando el carácter que sigue al número; si es una
letra, un guion bajo o un punto, se consume la palabra completa y se reporta una sola vez.

## Pruebas

Se escribieron 20 pruebas unitarias (categorías de token, operadores, posiciones, los tres errores y la
continuación tras un error): 11 válidos y 15 inválidos, cada uno con una
primera línea `// ESPERADO: ...` que indica el resultado y, para los errores léxicos, la línea del primer error.

## Decisiones y limitaciones de la versión 1

- Los textos no admiten comillas internas ni saltos de línea.
- `y`, `o` y `no` son palabras reservadas, por lo que no pueden usarse como nombres de variable.
- Un `!` suelto (sin `=`) se reporta como carácter inválido.