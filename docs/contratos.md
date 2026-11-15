# Contratos entre módulos (Fase 1)

Se congelan lo antes posible. Un cambio posterior se avisa a todo el grupo antes de hacerlo.
Las secciones marcadas **(propuesta)** las confirma o ajusta su responsable (la 3 ya fue confirmada por P2).

## 1. Token (P1)

Tupla con nombre `Token(tipo, lexema, linea, columna)`. Línea y columna empiezan en 1.
La lista de tokens **siempre termina con un token `EOF`**. Los literales `CARACTER` y `CADENA` conservan las comillas.
La especificación formal (expresiones regulares) está en `docs/tokens.md`.

| Grupo | Tipos de token |
|---|---|
| Tipos de dato | `TIPO` (lexema: `int`, `float` o `char`) |
| Reservadas | `IF ELSE WHILE PRINTF` |
| Nombres y literales | `ID ENTERO FLOTANTE CARACTER CADENA` |
| Aritméticos | `MAS MENOS POR DIVIDIDO MODULO` |
| Asignación y comparación | `IGUAL IGUAL_IGUAL DIFERENTE MENOR MAYOR MENOR_IGUAL MAYOR_IGUAL` |
| Lógicos | `Y_LOGICO O_LOGICO NO_LOGICO` |
| Delimitadores | `PAREN_IZQ PAREN_DER LLAVE_IZQ LLAVE_DER PUNTOYCOMA COMA` |
| Fin | `EOF` |

En JSON cada token es `[tipo, lexema, linea, columna]`. Ejemplo: `lexer/tokens_ejemplo.json`.

## 2. Error (todos)

```python
{"fase": "lexico" | "sintactico" | "semantico", "linea": 3, "columna": 14, "mensaje": "..."}
```

`sintactico` lo produce `parser/convertidor.py` cuando la forma del programa no cumple la gramática.
El mensaje indica **la causa**. Los avisos (S9) usan `"fase": "semantico"` y un mensaje que empieza con `Aviso:`.

## 3. Representación para el semántico: AST mínimo (P2)

El PDF permite que el semántico trabaje sobre "un AST mínimo construido a mano". Clase `Nodo` en
`parser/nodo.py`: `Nodo(tipo, hijos, valor, linea, tipo_dato=None)`. El semántico llena `tipo_dato`
(`int`, `float`, `char` o `cadena`) en cada expresión; los literales ya lo traen puesto.

| `tipo` del nodo | `valor` | `hijos` |
|---|---|---|
| `Programa` | | sentencias |
| `Declaracion` | `{"tipo_dato": "int", "nombre": "x"}` | `[expresion]` o `[]` si no tiene valor inicial |
| `Asignacion` | nombre de la variable | `[expresion]` |
| `Si` | | `[condicion, bloque]` o `[condicion, bloque, bloque_else]` |
| `Mientras` | | `[condicion, bloque]` |
| `Printf` | | `[cadena, argumento1, argumento2, ...]` |
| `Bloque` | | sentencias |
| `OpBinario` | operador (`"+"`, `"=="`, `"&&"`, ...) | `[izquierda, derecha]` |
| `OpUnario` | `"-"` o `"!"` | `[operando]` |
| `Literal` | lexema tal cual | |
| `Variable` | nombre | |

El tipo de un `Literal` sale del token: `ENTERO` es `int`, `FLOTANTE` es `float`, `CARACTER` es `char`, `CADENA` es `cadena`.

Los AST de ejemplo, hechos a mano, están en `pruebas/ejemplos/ast/` como JSON con las claves de `Nodo.a_dict()` (`tipo`, `valor`, `linea`, `tipo_dato`, `hijos`). Se cargan con `Nodo.desde_json(texto)` y se escriben con `nodo.a_json()`. Todo cuerpo de `Si` y `Mientras` es un `Bloque`, y `linea` cuenta desde la línea 1 del `.c`.

## 4. Tabla de símbolos (P3) y reglas de tipos (P4)

```python
# Tabla de símbolos
tabla.abrir_ambito()                   tabla.cerrar_ambito()
tabla.declarar(nombre, tipo, linea)    # False si ya existe en el ámbito actual
tabla.buscar(nombre)                   # {'tipo': ..., 'linea': ...} o None

# Reglas de tipos
tipo_expresion(nodo, tabla, errores)   # 'int' | 'float' | 'char' | 'cadena' | None (si hubo error)
asignable(tipo_destino, tipo_valor)    # True si el valor cabe en el destino (solo ensanchar)
```

Un error de tipo no se encadena: si una subexpresión ya dio error, `tipo_expresion` devuelve `None` y no se reportan más errores por ella.

## 5. Funciones de cada módulo

```python
# parser/convertidor.py     (P2)
def codigo_a_ast(codigo: str) -> Tuple[Optional[Nodo], List[dict]]   # (AST o None, errores léxicos/sintácticos)
def tokens_a_ast(tokens: List[Token]) -> Tuple[Optional[Nodo], List[dict]]

# lexer/lexer.py            (P1)
def analizar(codigo: str) -> Tuple[List[Token], List[dict]]

# semantico/semantico.py    (P3)
def analizar(ast: Nodo) -> Tuple[Nodo, List[dict], List[dict]]
#            ^ AST anotado, tabla de símbolos (lista de dicts), errores y avisos
```

La tabla de símbolos que devuelve el semántico es una lista de `{"nombre", "tipo", "ambito", "linea"}`.

## 6. Convención del corpus de pruebas

Cada programa de `pruebas/ejemplos/` lleva en la **primera línea** el resultado esperado:

```
// ESPERADO: ok
// ESPERADO: error lexico linea 3
// ESPERADO: error semantico linea 4
```

Nombres de archivo: `NN_descripcion.c`. Un programa inválido tiene **un solo error** (salvo
`07_varios_errores_lexicos`). La línea cuenta desde la línea 1 del archivo, incluidos los comentarios del encabezado.
