# Compilador de mini-C: lexer y analizador semántico

Proyecto TLP02-2026 (Teoría de Lenguajes de Programación). La **Fase 1** consiste en un **analizador léxico**
y un **analizador semántico** para un subconjunto de **C** (mini-C). El parser para el español es de la Fase 2.

```
int total = base @ 2;        ->   ERROR línea 4, col 18: Carácter inválido '@'     (lo detecta el lexer)
int n = "hola";              ->   error semántico: no se puede guardar una cadena en un int
```

## Equipo

| Rol | Nombre | Módulo |
|---|---|---|
| P1 | Juan Carlos Sibrian | Analizador léxico, especificación de tokens y corpus de pruebas |
| P2 | Kattia Sarai Santan Soriano | Representación mínima (AST) para el semántico y reflexión sobre CFG |
| P3 | Gabriela Sofia Quinteros Ramirez | Analizador semántico: tabla de símbolos, ámbitos, declaración y redeclaración |
| P4 | Fabio Mijango | Reglas de tipos y casos de prueba semánticos |
| P5 | Oscar Ernesto Menjivar Ayala | Ejecutor de pruebas, README, video y entrega |

## El lenguaje

Un subconjunto de C: tipos `int`, `float` y `char`; declaraciones y asignaciones; aritmética; comparaciones;
operadores lógicos `&&` `||` `!`; `if/else`, `while`, bloques con ámbito; `printf`; y comentarios `//` y `/* */`.
Un programa es una secuencia de sentencias (sin `main` ni funciones propias). El detalle y las reglas semánticas
(S1 a S10) están en [docs/lenguaje_c.md](docs/lenguaje_c.md).

## Estructura del repositorio

```
ProyectoTLP2026/
├── lexer/          lexer.py: analizador léxico (P1)
├── semantico/      semantico.py: analizador semántico, tabla de símbolos y reglas de tipos (P3 y P4)
├── parser/         nodo.py: AST mínimo que consume el semántico (P2)
├── pruebas/        test_lexer.py y el corpus de programas .c (ejemplos/validos, ejemplos/invalidos)
├── docs/           especificación de tokens, lenguaje, contratos, tablero, plan e informe
├── generador/      heredado del plan anterior; no es objetivo de la Fase 1
├── main.py         heredado del plan anterior; no es objetivo de la Fase 1
├── CONTRIBUTING.md     cómo trabajamos con Git (leer antes de empezar)
└── README.md
```

## Cómo ejecutar

Requisitos: Python 3.10 o superior. No hay dependencias externas en la Fase 1.
Todos los comandos se corren desde la raíz del repositorio.

```
# Analizador léxico: imprime los tokens y los errores léxicos, y crea salida/tokens.txt y salida/errores.txt
python -m lexer.lexer pruebas/ejemplos/validos/ejemplo.c

# Pruebas del lexer y del corpus (deben terminar en OK)
python -m unittest discover pruebas

# Analizador semántico: (P3 completa el comando cuando entregue el módulo)
```

## Casos de prueba

El corpus está en `pruebas/ejemplos/`: programas **válidos** que deben analizarse sin errores e **inválidos** que
deben producir errores léxicos o semánticos claros, con línea y causa. La primera línea de cada programa declara lo
esperado (`// ESPERADO: ok`, `// ESPERADO: error lexico linea 4`). El índice completo está en
[pruebas/ejemplos/INDICE.md](pruebas/ejemplos/INDICE.md).

## Estado de los módulos

| Módulo | Responsable | Estado |
|---|---|---|
| Léxico y especificación de tokens | P1 | Listo |
| Corpus de pruebas | P1 | Listo |
| AST mínimo | P2 | Pendiente |
| Semántico: tabla de símbolos y ámbitos | P3 | Pendiente |
| Semántico: reglas de tipos | P4 | Pendiente |
| Ejecutor de pruebas y video | P5 | Pendiente |

(Actualizar esta tabla al unir cada módulo a `main`: Pendiente, En curso, Listo.)

## Reflexión: qué verificaciones no puede expresar una CFG

_Pendiente: la redacta P2 (viernes 13 a domingo 15)._ Debe explicar, con ejemplos, por qué reglas como estas no caben
en una gramática libre de contexto y se resuelven en el analizador semántico, y conectarlo con los lenguajes sensibles
al contexto:

- "Toda variable usada debe haber sido declarada antes."
- "No se puede redeclarar una variable en el mismo ámbito."
- La compatibilidad de tipos en asignaciones y expresiones.

## Video de la Fase 1

_Enlace pendiente (máximo 10 minutos; lo sube P5)._

## Documentación

- [Especificación formal de tokens](docs/tokens.md): expresiones regulares de cada token y errores léxicos.
- [El lenguaje mini-C](docs/lenguaje_c.md): alcance y reglas semánticas S1 a S10.
- [Contratos entre módulos](docs/contratos.md): formatos de token, error, AST, tabla de símbolos y funciones.
- [Tablero de tareas de la Fase 1](docs/tablero_fase1.md)
- [Plan de trabajo (PDF)](docs/plan_de_trabajo.pdf)
- [Informe](docs/informe/): material de la Fase 2.