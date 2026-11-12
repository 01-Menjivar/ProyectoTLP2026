# Manzana: compilador de Manzana a Python

Proyecto TLP02-2026 (Teoría de Lenguajes de Programación). **Manzana** es un mini lenguaje
inventado con palabras clave en español. Este compilador lo analiza (léxico, sintáctico,
semántico) y lo traduce a **Python**.

```
entero manzanas = 3;                  manzanas = 3
si (manzanas > 2) {          ->       if manzanas > 2:
    imprimir("Hay muchas");               print("Hay muchas")
}
```

## Equipo

| Rol | Nombre | Módulo | Rama de trabajo |
|---|---|---|---|
| P1 | Juan Carlos Sibrian | Analizador léxico + corpus de pruebas | `p1-lexer` |
| P2 | _______________ | Parser, AST y errores sintácticos | `p2-parser` |
| P3 | _______________ | Analizador semántico y tabla de símbolos | `p3-semantico` |
| P4 | _______________ | Generador de código Python y reportes | `p4-generador` |
| P5 | _______________ | Integración, pruebas, informe y presentación | `p5-integracion` |

## Estructura del repositorio

```
tlp02-manzana/
├── lexer/          P1   lexer.py
├── parser/         P2   parser.py, nodo.py
├── semantico/      P3   semantico.py
├── generador/      P4   generador.py, reportes.py
├── pruebas/        P1 y P5   ejemplos/validos, ejemplos/invalidos, runner
├── docs/           lenguaje, contratos, tablero, informe/
├── main.py         P5   punto de entrada del compilador
├── CONTRIBUTING.md      cómo trabajamos con Git (leer antes de empezar)
└── README.md
```

## Cómo ejecutar

Requisitos: Python 3.10 o superior. No hay dependencias externas en la Fase 1.

```
python main.py pruebas/ejemplos/validos/ejemplo.mz
```

Produce en `salida/`: `tokens.txt`, `tabla_simbolos.txt`, `errores.txt` y, si no hay
errores, `programa.py`.

## Estado de los módulos

| Módulo | Responsable | Estado |
|---|---|---|
| Léxico | P1 | Pendiente |
| Parser y AST | P2 | Pendiente |
| Semántico | P3 | Pendiente |
| Generador y reportes | P4 | Pendiente |
| Integración y pruebas | P5 | Pendiente |

(Actualizar esta tabla al unir cada módulo a `main`: Pendiente, En curso, Listo.)

## Documentación

- [Lenguaje Manzana](docs/lenguaje_manzana.md): tokens, gramática, reglas semánticas y traducción a Python.
- [Contratos entre módulos](docs/contratos.md): formatos de token, AST, errores y firmas de funciones.
- [Tablero de tareas de la Fase 1](docs/tablero_fase1.md)
- [Plan de trabajo (PDF)](docs/plan_de_trabajo.pdf)
- [Informe](docs/informe/): una sección por integrante.
