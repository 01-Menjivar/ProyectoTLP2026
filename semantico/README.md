# Analizador semántico: núcleo de P3

**Responsable:** Fabio Mijango. **Estado:** núcleo P3 implementado y probado; integración conjunta P3/P4 pendiente.

## Alcance

Implementa S1 (declaración previa), S2 (no redeclarar en el mismo ámbito) y S8
(ámbitos por bloque). No implementa las reglas de tipos S3 a S7/S10. El aviso S9 está implementado.
Un programa sin errores de P3 todavía puede contener errores de tipos.

## Entrada y salida

`analizar(ast)` recibe un `Nodo` del convertidor de P2 o de `Nodo.desde_json(texto)`
y devuelve `(ast, tabla_simbolos, errores)` según `docs/contratos.md`.

- Anota las referencias `Variable` con el tipo de la declaración visible. Los literales
  conservan el tipo que trae el AST. Los operadores quedan con `tipo_dato=None` hasta P4.
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

## Recorrido e integración con P4

`AnalizadorSemantico.recorrer` visita las sentencias en orden. En `Si` revisa la condición
y ambas ramas; en `Mientras` revisa una vez la condición y el cuerpo, sin ejecutar código.
Cada `Bloque` abre/cierra un ámbito, también dentro de condicionales y ciclos.
El nombre declarado es visible en su propio inicializador, como en C; detectar una lectura
sin inicializar produce un aviso S9.

P4 puede usar directamente `tabla.buscar(nombre)` con su contrato acordado:

```python
tipo_expresion(nodo, tabla, errores)  # tipo o None
asignable(tipo_destino, tipo_valor)   # bool
```

Puntos de conexión en `semantico.py` al integrar `semantico/tipos.py`:

1. `_expresion` resuelve S1 y los tipos de las variables; se debe coordinar con
   `tipo_expresion` para que un nombre no declarado produzca un solo diagnóstico.
2. `Declaracion` y `Asignacion`: verificar S3 solo cuando la expresión tenga tipo válido.
3. `Si`/`Mientras`: verificar S5 después de analizar su condición.
4. `Printf`: verificar S10 y analizar todos los argumentos.

No se cambió el contrato ni se agregó una dependencia a un módulo de P4 que aún no existe.
La suite de P3 cubre la interfaz pública, sombreado, bloques hermanos, aislamiento entre
ramas, destinos y operandos no declarados, AST manual/automático y el corpus válido.

## Guion breve para explicar P3

Mostrar la pila y explicar que solo el bloque actual impide redeclaraciones. Ejecutar el
caso válido de ámbitos, después `09_redeclaracion.c` y `15_variable_fuera_de_su_ambito.c`.
Señalar la línea y causa de cada error. La tabla aporta la memoria de nombres y bloques que
la gramática no mantiene. Cerrar aclarando que P4 añade la compatibilidad de tipos.

## Pendientes para cerrar el semántico de la Fase 1

El núcleo de P3 está listo, pero el hito de integración que el plan asigna a P3
requiere recibir `semantico/tipos.py` de P4. Los puntos de conexión anteriores son
una guía; todavía no constituyen una integración ejecutable. Al recibirlo, P3 debe
conectar el recorrido y verificar junto con P4 los casos inválidos de tipos del corpus,
la anotación de operadores y la ausencia de diagnósticos duplicados.

S9 está implementado en P3. El estado de inicialización se identifica por ámbito
 y nombre, sin cambiar el formato público de la tabla. Las asignaciones se analizan
 después de leer sus operandos. Un if/else conserva solo las inicializaciones comunes
 a ambas ramas; un if sin else y un while no garantizan ejecutar su cuerpo.
 Los avisos empiezan con `Aviso:` y no hacen fallar el comando (salida 0).
 Este análisis es conservador: no evalúa condiciones constantes ni propaga valores.
 Una asignación sin errores de nombres cuenta como escritura, incluso si su expresión
 produjo un aviso. Cuando se integre P4, también deberá comprobarse su validez de tipos.

Las pruebas de P3 incluyen también tres niveles de sombreado, recuperación después
de una redeclaración, errores dentro de inicializadores, visibilidad en condiciones
y repetición del análisis sobre el mismo AST.
