# El subconjunto de C (mini-C)

El PDF del proyecto permite elegir "C, C++, C#, Java, un lenguaje aritmético con estructuras de control,
u otro". Elegimos **un subconjunto de C**, que está en la lista, así que no necesita aprobación aparte.

## Qué incluye

| Construcción | Ejemplo |
|---|---|
| Tipos de dato | `int`, `float`, `char` |
| Declaración, con o sin valor inicial | `int x;` · `float y = 3.5;` · `char c = 'a';` |
| Asignación | `x = x + 1;` |
| Aritmética | `+ - * / %`, paréntesis y signo negativo |
| Comparaciones | `< > <= >= == !=` |
| Operadores lógicos | `&&` `\|\|` `!` |
| Condicional | `if (cond) { ... } else { ... }` |
| Ciclo | `while (cond) { ... }` |
| Bloque (abre un ámbito) | `{ ... }` |
| Impresión | `printf("texto %d\n", x);` (única función permitida) |
| Comentarios | `// línea` y `/* bloque */` |

## Qué no incluye

Funciones propias (y por eso `main`), arreglos, punteros, `for`, `return`, `struct`, el preprocesador
(`#include`), constantes numéricas en hexadecimal o con exponente, y la secuencia `else if` sin llaves.
Un programa es una **secuencia de sentencias** (sin `main`), igual que en el equipo de la otra sección.
Los programas llevan extensión `.c`, pero no se compilan con `gcc`.

## Reglas semánticas (las revisa el analizador semántico)

En C los tipos numéricos se convierten entre sí con mucha libertad. Para que haya errores de tipos que
detectar, estas reglas son **un poco más estrictas que C real**, y esa decisión se documenta en el README.

| Regla | Qué se verifica | Ejemplo de error |
|---|---|---|
| S1 | Toda variable usada debe estar declarada antes | `total = a + 1;` sin declarar `total` |
| S2 | No se puede redeclarar una variable en el mismo ámbito | `int a = 1; int a = 2;` |
| S3 | En una asignación o inicialización solo se permite **ensanchar**: `char` a `int` a `float`. No se permite estrechar (`float` a `int`) ni guardar una cadena | `int n = 2.5;` · `int n = "hola";` |
| S4 | La aritmética `+ - * /` acepta `int`, `float` y `char`. El `%` solo acepta `int` y `char`. El resultado es `float` si algún operando lo es, y `int` en otro caso | `"a" * 2` · `2.5 % 2` |
| S5 | La condición de `if` y `while` debe ser numérica (en C, 0 es falso y lo demás verdadero) | `if ("hola")` |
| S6 | `&&`, `\|\|` y `!` aceptan solo operandos numéricos. El resultado es `int` | `"a" && 1` |
| S7 | Las comparaciones aceptan solo operandos numéricos. El resultado es `int` | `"a" == 1` |
| S8 | Cada bloque `{ }` abre un ámbito nuevo; lo declarado adentro no existe afuera | usar `dentro` fuera de su bloque |
| S9 (aviso) | Usar una variable declarada sin valor inicial | `int a; printf("%d", a);` |
| S10 | El primer argumento de `printf` debe ser una cadena literal. Una cadena no puede aparecer en ningún otro lugar | `printf(x);` |

Los tipos internos del semántico son `int`, `float`, `char` y `cadena` (este último solo para el primer
argumento de `printf`).

## Por qué una CFG no puede expresar estas reglas

La gramática solo dice en qué orden pueden aparecer los símbolos. Comprobar que un identificador usado
coincide con uno **declarado antes** exige recordar un conjunto de nombres, y eso es una dependencia de
contexto que una gramática libre de contexto no puede expresar. Por eso estas reglas viven en el analizador
semántico, con una tabla de símbolos (ver la reflexión del README).
