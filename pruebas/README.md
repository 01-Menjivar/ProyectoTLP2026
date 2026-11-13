# Pruebas

- `ejemplos/validos/` y `ejemplos/invalidos/`: el corpus de programas `.mz`.
- Pruebas unitarias por módulo: `test_lexer.py`, `test_parser.py`, `test_semantico.py`,
  `test_generador.py`. Se corren desde la raíz con:

```
python -m unittest discover pruebas
```

- El ejecutor del corpus (lo escribe P5) corre cada `.mz` por `main.py` y compara con la
  línea `// ESPERADO: ...` del archivo. Convención completa en `docs/contratos.md`, sección 7.

Nombres de archivo del corpus: `NN_descripcion.mz` (por ejemplo `07_variable_no_declarada.mz`).
