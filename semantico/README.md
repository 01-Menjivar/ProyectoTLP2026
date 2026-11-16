# Analizador semántico: P3 y P4

**Responsables:** Fabio Mijango (P3) y Gabriela Sofia Quinteros Ramirez (P4).
**Estado:** reglas S1 a S10 implementadas y probadas.

## Alcance

Implementa S1 (declaración previa), S2 (no redeclarar en el mismo ámbito), S3 a S7
(compatibilidad y operaciones de tipos), S8 (ámbitos por bloque), S9 (aviso de uso sin
inicializar) y S10 (uso de cadenas en `printf`).

## Entrada y salida

`analizar(ast)` recibe un `Nodo` del convertidor de P2 o de `Nodo.desde_json(texto)`
y devuelve `(ast, tabla_simbolos, errores)` según `docs/contratos.md`.

- Anota las referencias `Variable`, los literales y los operadores con su `tipo_dato`.
  Las expresiones inválidas quedan con `tipo_dato=None`.
- La tabla es una lista de `{nombre, tipo, ambito, linea}` en orden de declaración;
  incluye los símbolos de bloques cerrados para poder mostrarlos en la demo.
- Los errores tienen `{fase, linea, columna, mensaje}`. La línea viene del AST;
  la columna es 1 porque el contrato de `Nodo` no conserva columnas.

Cada llamada crea una tabla nueva. Se devuelve y anota el mismo AST recibido.

## Ejecutar desde la raíz del repositorio

```sh
python -m semantico.semantico pruebas/ejemplos/validos/07_ambitos_y_bloques.c
python -m semantico.semantico pruebas/ejemplos/invalidos/09_redeclaracion.c
python -m semantico.semantico pruebas/ejemplos/invalidos/15_variable_fuera_de_su_ambito.c
python -m semantico.semantico pruebas/ejemplos/ast/08_variable_no_declarada.json
python -m unittest discover pruebas
```

El comando anuncia su alcance P3, imprime la tabla y los errores. Devuelve 0 sin errores
comprobados, 1 ante errores léxicos/sintácticos/semánticos y 2 por uso incorrecto o lectura
fallida. Si falla el lexer o el convertidor, no se ejecuta el semántico.

## Tabla de símbolos

`TablaSimbolos` está en `semantico/tabla_simbolos.py`:

```python
from semantico.tabla_simbolos import TablaSimbolos

tabla = TablaSimbolos()
tabla.declarar("x", "int", 1)   # True

tabla.abrir_ambito()
tabla.declarar("x", "float", 2) # True: oculta la x externa
tabla.buscar("x")              # tipo float
tabla.cerrar_ambito()
tabla.buscar("x")              # tipo int otra vez
```

Una pila de diccionarios representa los bloques activos. La declaración comprueba solo
el diccionario actual; la búsqueda recorre desde el último hacia el global. Cerrar un
bloque elimina su visibilidad, pero conserva el historial. El global tiene identificador 0;
los bloques reciben identificadores crecientes y únicos, incluidos los bloques hermanos.
Cerrar el global provoca `ValueError`. Las consultas devuelven copias para proteger la tabla.
Una redeclaración devuelve `False` y conserva la primera declaración.

## Reglas de tipos de P4

`AnalizadorSemantico.recorrer` visita las sentencias en orden. En `Si` revisa la condición
y ambas ramas; en `Mientras` revisa una vez la condición y el cuerpo, sin ejecutar código.
Cada `Bloque` abre/cierra un ámbito, también dentro de condicionales y ciclos.
El nombre declarado es visible en su propio inicializador, como en C; detectar una lectura
sin inicializar produce un aviso S9.

`semantico/tipos.py` implementa el contrato acordado:

```python
tipo_expresion(nodo, tabla, errores)  # tipo o None
asignable(tipo_destino, tipo_valor)   # bool
```

La integración conserva una sola fuente para los errores de nombres: P3 resuelve las
variables primero y P4 no repite el diagnóstico S1. Si una subexpresión ya es inválida,
P4 devuelve `None` y no encadena errores en la expresión contenedora.

- S3 permite únicamente `char -> int -> float` y rechaza cualquier estrechamiento.
- S4 permite aritmética numérica; `%` solo admite `int` y `char`.
- S5, S6 y S7 requieren operandos numéricos en condiciones, lógicos y comparaciones.
- S10 exige que el primer argumento de `printf` sea una cadena literal y prohíbe las
  cadenas en los demás contextos.

## Guion breve para explicar P3

Mostrar la pila y explicar que solo el bloque actual impide redeclaraciones. Ejecutar el
caso válido de ámbitos, después `09_redeclaracion.c` y `15_variable_fuera_de_su_ambito.c`.
Señalar la línea y causa de cada error. La tabla aporta la memoria de nombres y bloques que
la gramática no mantiene. Cerrar aclarando que P4 añade la compatibilidad de tipos.

S9 está implementado en P3. El estado de inicialización se identifica por ámbito
 y nombre, sin cambiar el formato público de la tabla. Las asignaciones se analizan
 después de leer sus operandos. Un if/else conserva solo las inicializaciones comunes
 a ambas ramas; un if sin else y un while no garantizan ejecutar su cuerpo.
 Los avisos empiezan con `Aviso:` y no hacen fallar el comando (salida 0).
 Este análisis es conservador: no evalúa condiciones constantes ni propaga valores.
Una asignación solo cuenta como escritura si no tiene errores de nombres ni de tipos;
los avisos no la invalidan.

Las pruebas de P3 incluyen también tres niveles de sombreado, recuperación después
de una redeclaración, errores dentro de inicializadores, visibilidad en condiciones
y repetición del análisis sobre el mismo AST.
