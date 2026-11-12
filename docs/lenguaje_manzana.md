# El lenguaje Manzana (versión 1)

## Ejemplo

```
// Programa de ejemplo
entero manzanas = 3;
decimal precio = 2.50;
decimal total = manzanas * precio;

si (total > 5) {
    imprimir("Compra grande");
} sino {
    imprimir("Compra pequeña");
}

mientras (manzanas > 0) {
    manzanas = manzanas - 1;
}
```

## Tokens

| Categoría | Contenido |
|---|---|
| Palabras reservadas | `entero decimal texto booleano si sino mientras imprimir verdadero falso y o no` |
| Identificadores | Letra o `_`, seguido de letras, dígitos o `_` |
| Literales | entero `42`, decimal `3.14`, texto `"hola"`, booleano `verdadero` / `falso` |
| Operadores | `+ - * / %` · `== != < > <= >=` · `=` · lógicos `y o no` |
| Delimitadores | `( ) { } ; ,` |
| Comentarios | `//` hasta el fin de línea (el lexer los descarta) |

Errores léxicos a detectar: carácter inválido, texto sin cerrar, número mal formado (`3.`, `3a`, `3.5.2`).
Decisiones de la versión 1: los textos no admiten escapes ni saltos de línea; `!` solo es inválido.

## Gramática (BNF, diseñada para LL(1), sin recursión izquierda)

```
programa     -> sentencia*
sentencia    -> declaracion | asignacion | condicional | ciclo | impresion | bloque
declaracion  -> TIPO ID ( '=' expresion )? ';'
asignacion   -> ID '=' expresion ';'
condicional  -> 'si' '(' expresion ')' bloque ( 'sino' bloque )?
ciclo        -> 'mientras' '(' expresion ')' bloque
impresion    -> 'imprimir' '(' expresion ')' ';'
bloque       -> '{' sentencia* '}'

expresion    -> or_expr
or_expr      -> and_expr ( 'o' and_expr )*
and_expr     -> not_expr ( 'y' not_expr )*
not_expr     -> 'no' not_expr | rel_expr
rel_expr     -> arit ( ('==' | '!=' | '<' | '>' | '<=' | '>=') arit )?
arit         -> term ( ('+' | '-') term )*
term         -> factor ( ('*' | '/' | '%') factor )*
factor       -> '-' factor | ENTERO | DECIMAL | TEXTO | 'verdadero' | 'falso'
              | ID | '(' expresion ')'
```

## Reglas semánticas (las revisa P3)

| Regla | Qué se verifica | Ejemplo de error |
|---|---|---|
| S1 | Toda variable usada debe estar declarada antes | `y = 5;` sin declarar `y` |
| S2 | No se puede redeclarar una variable en el mismo ámbito | `entero a; entero a;` |
| S3 | La asignación respeta el tipo (entero a decimal se permite; decimal a entero no) | `entero n = "hola";` |
| S4 | Aritmética solo con entero o decimal; `+` también une texto con texto | `texto t = "a" - 1;` |
| S5 | La condición de `si` y `mientras` debe ser booleana | `si (5) { ... }` |
| S6 | Los operadores `y o no` solo aceptan booleanos | `5 y verdadero` |
| S7 | Las comparaciones son entre tipos compatibles y dan booleano | `"a" < 3` |
| S8 | Cada bloque abre un ámbito nuevo; lo declarado dentro no existe afuera | usar `x` fuera de su bloque |
| S9 (aviso) | Variable sin valor inicial usada, o división entre cero literal | `entero a; imprimir(a);` |

## Traducción a Python (la implementa P4)

| Manzana | Python | Nota |
|---|---|---|
| `entero x = 5;` | `x = 5` | Sin declaración de tipo |
| `si (c) {...} sino {...}` | `if c: ... else: ...` | Las llaves pasan a indentación |
| `mientras (c) {...}` | `while c: ...` | |
| `imprimir(e);` | `print(e)` | |
| `y` `o` `no` | `and` `or` `not` | |
| `verdadero` `falso` | `True` `False` | |
| `a / b` con dos enteros | `a // b` | Para que entero / entero siga siendo entero |
