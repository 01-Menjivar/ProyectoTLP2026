# Guía de contribución

## Flujo de trabajo en Git

1. **No hacer push directo a `main`.** La rama `main` debe mantenerse siempre estable y con pruebas en verde.
2. Cada cambio se desarrolla en una rama dedicada (por ejemplo `feat/reglas-tipos`, `fix/lexer-numeros`, `docs/readme`). Si una rama permanece abierta varios días, se sincroniza con `main` (`git pull origin main`) para evitar conflictos.
3. Los cambios se integran a `main` mediante **Pull Request (PR)** revisado por otro integrante del equipo.
4. Todo PR debe incluir comentarios claros y pruebas que pasen.

## Flujo de una tarea

```sh
git checkout main && git pull
git checkout -b feat/descripcion-corta
# ...realizar cambios...
git add <archivos>
git commit -m "modulo: resumen del cambio"
git push -u origin feat/descripcion-corta
# En GitHub: Compare & pull request -> revisión -> Squash and merge
```

## Mensajes de commit

Formato `modulo: qué se hizo`, en presente y conciso.  
Ejemplos: `lexer: agrega errores de texto sin cerrar`, `semantico: valida compatibilidad de tipos`, `docs: actualiza reglas semánticas`.

## Lista de verificación antes de abrir un PR

- Las pruebas unitarias (`python -m unittest discover pruebas`) y el ejecutor del corpus (`python -m pruebas.ejecutor`) pasan.
- El código tiene nombres claros y docstrings en las funciones públicas.
- No se incluyen archivos generados (`__pycache__/`, `salida/`, `tokens.txt`, etc.).
- Si cambia una interfaz compartida, se actualiza `docs/contratos.md`.

## Convenciones de código

- Python 3.10 o superior, nombres en español sin tildes (`analizar`, `tabla_simbolos`).
- Funciones enfocadas en una sola responsabilidad con docstring breve.
- Las pruebas viven en `pruebas/` y se ejecutan con `python -m unittest discover pruebas`.
