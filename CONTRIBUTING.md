# Cómo trabajamos

## Reglas básicas

1. **Nadie hace push directo a `main`.** `main` siempre debe funcionar.
2. Cada quien trabaja en **su rama** (`p1-lexer`, `p2-parser`, ...). Si una rama vive más de
   dos días, se sincroniza con `main` (`git pull origin main`) para no acumular conflictos.
3. Se une a `main` por **Pull Request (PR)** revisado por otra persona.
4. **Solo se edita la carpeta propia.** Si necesitas cambiar algo de otro módulo, avísale por
   el grupo o abre un issue. Los contratos (`docs/contratos.md`) solo se cambian con aviso a todos.
5. Los archivos se suben **comentados y con pruebas que pasan**.

## Flujo de una tarea

```
git checkout main && git pull
git checkout -b p1-lexer            # o: git checkout p1-lexer && git merge main
# ...trabajar...
git add <archivos>
git commit -m "lexer: detecta numeros mal formados"
git push -u origin p1-lexer
# En GitHub: Compare & pull request -> pedir revisión -> Squash and merge
```

## Mensajes de commit

Formato `modulo: qué se hizo`, en presente y corto.
Ejemplos: `lexer: agrega errores de texto sin cerrar`, `parser: recuperación en modo pánico`,
`docs: actualiza reglas semánticas`.

## Quién revisa a quién

| Autor del PR | Revisor | Si no está disponible |
|---|---|---|
| P1 | P2 | P5 |
| P2 | P1 | P5 |
| P3 | P4 | P5 |
| P4 | P3 | P5 |
| P5 | P3 | P4 |

P1 y P2 se van el lunes 16: deben tener **todos sus PR unidos antes del domingo 15**.

El revisor debe poder **explicar el código en voz alta**. El proyecto exige defender cada línea
ante el docente, y revisar es la forma de aprender el módulo del otro.

## Antes de pedir revisión (lista de verificación)

- Las pruebas del módulo pasan.
- El código tiene comentarios y nombres claros.
- El README del módulo describe qué recibe y qué devuelve.
- No se subieron archivos generados (`__pycache__`, `tokens.txt`, etc.).
- Si cambia un contrato, está avisado en el grupo.

## Convenciones de código

- Python 3.10 o superior, nombres en español sin tildes (`analizar`, `tabla_simbolos`).
- Una función hace una cosa. Docstring corto en cada función pública.
- Las pruebas viven en `pruebas/` y se corren con `python -m unittest discover pruebas`.

## Protección de la rama main (opcional)

En GitHub: Settings > Branches > Add rule para `main`: exigir Pull Request y 1 aprobación.
Si el plan gratuito de cuentas privadas no lo permite, queda como acuerdo del grupo.
