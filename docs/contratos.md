# Contratos entre módulos

Se congelan el **primer día**. Un cambio posterior se avisa a todo el grupo antes de hacerlo.
Las secciones marcadas **(propuesta)** las confirma o ajusta su responsable.

## 1. Token (P1)

Tupla con nombre `Token(tipo, lexema, linea, columna)`. Línea y columna empiezan en 1.
La lista de tokens **siempre termina con un token `EOF`**. Los textos conservan las comillas en el lexema.

| Grupo | Tipos de token |
|---|---|
| Datos | `TIPO` (lexema: entero, decimal, texto o booleano) |
| Reservadas | `SI SINO MIENTRAS IMPRIMIR VERDADERO FALSO Y O NO` |
| Literales y nombres | `ID ENTERO DECIMAL TEXTO` |
| Operadores | `MAS MENOS POR DIVIDIDO MODULO` · `IGUAL IGUAL_IGUAL DIFERENTE MENOR MAYOR MENOR_IGUAL MAYOR_IGUAL` |
| Delimitadores | `PAREN_IZQ PAREN_DER LLAVE_IZQ LLAVE_DER PUNTOYCOMA COMA` |
| Fin | `EOF` |

En JSON cada token es `[tipo, lexema, linea, columna]`.

## 2. Error (todos)

```python
{"fase": "lexico" | "sintactico" | "semantico", "linea": 3, "columna": 14, "mensaje": "..."}
```

Los avisos (S9) usan `"fase": "semantico"` y `"mensaje"` que empieza con `Aviso:`.

## 3. AST (P2) (propuesta)

Clase `Nodo` en `parser/nodo.py`: `Nodo(tipo, hijos, valor, linea, tipo_dato=None)`.
`tipo_dato` es `None` al salir del parser; el semántico lo llena con `entero`, `decimal`,
`texto` o `booleano` en cada expresión (los literales ya lo traen puesto por el parser).
Exporta a JSON con `a_json()`.

| `tipo` del nodo | `valor` | `hijos` |
|---|---|---|
| `Programa` | | sentencias |
| `Declaracion` | `{"tipo_dato": "entero", "nombre": "x"}` | `[expresion]` o `[]` si no tiene valor inicial |
| `Asignacion` | nombre de la variable | `[expresion]` |
| `Si` | | `[condicion, bloque]` o `[condicion, bloque, bloque_sino]` |
| `Mientras` | | `[condicion, bloque]` |
| `Imprimir` | | `[expresion]` |
| `Bloque` | | sentencias |
| `OpBinario` | operador (`"+"`, `"=="`, `"y"`, ...) | `[izquierda, derecha]` |
| `OpUnario` | `"-"` o `"no"` | `[operando]` |
| `Literal` | lexema tal cual | |
| `Variable` | nombre | |

## 4. Tabla de símbolos (P3)

Lista de diccionarios, una fila por variable declarada:

```python
{"nombre": "manzanas", "tipo": "entero", "ambito": 0, "linea": 2}
```

`ambito` es el nivel de anidación: 0 es el global y cada bloque suma 1.

## 5. Funciones de cada módulo (firmas)

```python
# lexer/lexer.py            (P1)
def analizar(codigo: str) -> Tuple[List[Token], List[dict]]

# parser/parser.py          (P2)
def analizar(tokens: List[Token]) -> Tuple[Optional[Nodo], List[dict]]

# semantico/semantico.py    (P3)
def analizar(ast: Nodo) -> Tuple[Nodo, List[dict], List[dict]]
#            ^ AST anotado, tabla de simbolos, errores

# generador/generador.py    (P4)
def generar(ast: Nodo) -> str            # devuelve el codigo Python

# generador/reportes.py     (P4)
def escribir_tokens(tokens, ruta)
def escribir_tabla_simbolos(tabla, ruta)
def escribir_errores(errores, ruta)
```

Cada fase corre **solo si la anterior no dio errores** (los avisos no cuentan como errores).
Los errores de una misma fase se reportan todos juntos.

## 6. Archivos de salida

`python main.py programa.mz` escribe en `salida/`:

| Archivo | Contenido |
|---|---|
| `tokens.txt` | Un token por línea: `LINEA:COL  TIPO  LEXEMA` |
| `tabla_simbolos.txt` | Una variable por línea: nombre, tipo, ámbito, línea |
| `errores.txt` | Un error por línea: `[fase] línea N, columna M: mensaje` |
| `programa.py` | Código Python generado (solo si no hay errores) |

> Pendiente de confirmar con el profesor: si los "3 archivos" son estos tres de salida o los tres
> módulos (lexer, parser, semántico). La estructura sirve para ambos casos.

## 7. Convención del corpus de pruebas

Cada programa de `pruebas/ejemplos/` lleva en la **primera línea** el resultado esperado:

```
// ESPERADO: ok
// ESPERADO: error lexico linea 3
// ESPERADO: error sintactico linea 5
// ESPERADO: error semantico linea 2
```

Nombres de archivo: `NN_descripcion.mz` (por ejemplo `07_variable_no_declarada.mz`).
