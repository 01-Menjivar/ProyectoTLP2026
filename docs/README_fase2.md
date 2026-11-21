# Fase 2 · Relevo de P3 a P4

El siguiente paso es convertir una oración escrita en español en un árbol y pasarlo al verificador de concordancia. P3 ya proporciona las reglas, el formato del árbol y el verificador. P4 implementa el parser descendente recursivo y P1 aporta los tokens y sus rasgos. Mientras llega el lexer español, puedes desarrollar el parser con tokens de ejemplo y comparar su árbol con el de esta guía.

## Estado al 21 de noviembre de 2026

| Parte | Disponible en esta copia | Siguiente entrega |
|---|---|---|
| Fase 1 · mini-C | Lexer, convertidor a AST, semántico, 99 pruebas y corpus de 29 programas. | Usar la suite y el corpus para comprobar regresiones al modificar clases compartidas. [README principal](../README.md) |
| P3 · Gramática y concordancia | Gramática v1, contrato, sección teórica del informe y cinco pruebas de concordancia con árboles construidos a mano. Los cambios están en el árbol de trabajo local. | Revisar la v1 con P4 y P5 y registrar la versión compartida en Git. [Gramática y sección del informe](gramatica_espanol.md) |
| P1 y P4 · Texto a árbol | El repositorio contiene la clase de árbol y la interfaz con P3. El lexer y el convertidor actuales procesan mini-C. | P1 entrega el léxico español y sus tokens. P4 implementa el parser y conecta el verificador. P1 usa el árbol para la visualización. |
| P2 y P5 · Evaluación y entrega | Las reglas de P3 y los resultados esperados de ejemplo sirven para preparar las evaluaciones. | P2 prepara al menos 60 oraciones etiquetadas en tres niveles y calcula métricas. P1 compara dos herramientas de NLP. P5 ejecuta el LLM con y sin ejemplos, conserva los logs e integra informe y presentación. |

El trabajo de P3 añadió los parámetros opcionales `genero`, `numero` y `persona` a la tabla de símbolos. El semántico de mini-C sigue usando la firma de tres argumentos. El nuevo verificador utiliza los rasgos para comparar determinantes y adjetivos con su sustantivo, y el verbo con el núcleo del sujeto. Las pruebas incluyen modificadores anidados, ambos tiempos verbales, discrepancias y entradas léxicas incompletas. [Tabla de símbolos](../semantico/tabla_simbolos.py) · [Verificador](../semantico/concordancia.py) · [Pruebas de P3](../pruebas/test_concordancia.py)

## Cómo conectar el parser

1. **Recibe de P1 la secuencia de tokens y su tabla léxica.** Cada token aporta categoría, lexema original, línea y columna desde 1. La clave para buscar una forma es `f"{categoria}:{lexema.casefold()}"`. Los rasgos y valores admitidos por categoría están en el contrato. Acuerda con P1 cómo recibirá el parser el punto final y el fin de entrada. [Contrato del español](gramatica_espanol.md#contrato-entre-p1-p3-y-p4)
2. **Construye un árbol completo desde el símbolo inicial `O`.** Sigue las producciones v1. Representa cada categoría presente con un `Nodo`, conserva el orden de los hijos y omite los elementos opcionales ausentes. Un sujeto pronominal es hijo directo de `O`. Los adjetivos son hijos directos del sintagma nominal `SN`, y la frase preposicional `SP` pertenece al `SN` que modifica. Conserva la posición original en cada hoja. Antes de aceptar la estructura, comprueba que has consumido toda la oración. [Producciones y ejemplos](gramatica_espanol.md) · [Clase Nodo](../parser/nodo.py)
3. **Llama a `verificar_concordancia(arbol, tabla)` tras un análisis sintáctico válido.** Una lista vacía permite aceptar la oración. Si devuelve diagnósticos, conserva su fase, línea, columna y mensaje. Si lanza `ValueError` por una entrada ausente o incompleta, revisa la clave y los rasgos con P1 antes de contabilizar el caso en las métricas. Los errores léxicos o sintácticos se reportan en su propia etapa.
4. **Entrega el resultado a P1 y P2.** El visualizador puede recorrer `arbol.hijos` y el evaluador puede serializar el árbol con `arbol.a_dict()`. El plan prevé un registro común por oración con los campos `id, oracion, nivel, esperado, sistema, aceptada, arbol, tiempo_ms`. P2 aporta la etiqueta esperada. El resultado observado sale de ejecutar el flujo completo.

## Primera comprobación ejecutable

Desde la raíz del repositorio, abre Python 3.10 o superior con `python` y ejecuta este bloque. Las cuatro llamadas a `declarar` representan el léxico que aportará P1. La asignación a `arbol` representa la salida que deberá producir P4 para «Yo leo el libro». Este ejemplo solo requiere la biblioteca estándar.

```python
from parser.nodo import Nodo
from semantico.concordancia import verificar_concordancia
from semantico.tabla_simbolos import TablaSimbolos

tabla = TablaSimbolos()
tabla.declarar("PRON:yo", "PRON", 1, numero="sg", persona=1)
tabla.declarar("V_PRES:leo", "V_PRES", 1, numero="sg", persona=1)
tabla.declarar("DET:el", "DET", 1, genero="m", numero="sg")
tabla.declarar("N:libro", "N", 1, genero="m", numero="sg", persona=3)

def hoja(categoria, lexema, columna):
    return Nodo(categoria, valor={"lexema": lexema, "columna": columna}, linea=1)

sujeto = hoja("PRON", "Yo", 1)
objeto = Nodo("SN", [hoja("DET", "el", 8), hoja("N", "libro", 11)])
predicado = Nodo("SV", [hoja("V_PRES", "leo", 4), objeto])
arbol = Nodo("O", [sujeto, predicado])
assert verificar_concordancia(arbol, tabla) == []

# Segunda entrada: «Yo lee el libro». Solo cambia la persona del verbo.
tabla.declarar("V_PRES:lee", "V_PRES", 1, numero="sg", persona=3)
predicado.hijos[0] = hoja("V_PRES", "lee", 4)
errores = verificar_concordancia(arbol, tabla)
assert len(errores) == 1
assert (errores[0]["fase"], errores[0]["linea"], errores[0]["columna"]) == ("semantico", 1, 4)
print(errores[0]["mensaje"])
```

La última línea imprime `'lee' discrepa en persona con 'Yo': se esperaba 1 y se obtuvo 3`. Cuando el lexer y el parser estén disponibles, repite ambos casos desde texto y compara el árbol y los diagnósticos con los del ejemplo.

## Cómo verificar la integración

Ejecuta estos comandos desde la raíz del repositorio, en orden. El estado comprobado en el relevo es de 5 pruebas de P3, 104 pruebas totales (incluidas esas 5) y 29 de 29 programas mini-C con su resultado esperado.

```sh
python -m unittest pruebas.test_concordancia -v
python -m unittest discover pruebas
python -m pruebas.ejecutor
```

Para la primera prueba de extremo a extremo, incluye las siguientes oraciones en el léxico de prueba y pásalas como texto al nuevo punto de entrada. Estos resultados son criterios para la integración pendiente.

| Entrada | Resultado esperado | Qué comprueba |
|---|---|---|
| Tú leíste el libro. | Aceptada | Pretérito, tilde y segunda persona. |
| La niña de los vecinos lee los libros nuevos. | Aceptada | El verbo concuerda con «niña» y el adjetivo con «libros». |
| La niña de los vecinos leen los libros nuevos. | Error semántico en «leen» | El plural de «vecinos» está dentro del SP del sujeto. |
| Yo leo los libros nuevas. | Error semántico en «nuevas» | Concordancia de género dentro del objeto. |
| Yo leo el libro la niña. | Error sintáctico al llegar a «la» | El parser detecta texto sobrante después de una oración completa. |
