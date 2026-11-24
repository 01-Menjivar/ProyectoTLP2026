"""Corre los sistemas sobre el conjunto de oraciones y guarda los resultados en el formato común.

Uso (desde la raíz del repositorio):
    python -m comparacion.ejecutar                                   # los tres sistemas, oraciones de ejemplo
    python -m comparacion.ejecutar --sistemas propio spacy
    python -m comparacion.ejecutar --entrada pruebas/set_p2.json --salida salida/resultados_p1.json
"""
import argparse
import sys
from typing import List

from comparacion import formato

ENTRADA_POR_DEFECTO = "comparacion/oraciones_ejemplo.json"


def resumen(registros: List[dict]) -> str:
    filas = [f"{'sistema':<8} {'oraciones':>9} {'aceptadas':>9} {'aciertos':>9} {'tiempo medio (ms)':>18}"]
    for sistema in formato.SISTEMAS:
        rs = [r for r in registros if r["sistema"] == sistema]
        if not rs:
            continue
        aciertos = sum(1 for r in rs if r["aceptada"] == r["esperado"])
        filas.append(f"{sistema:<8} {len(rs):>9} {sum(r['aceptada'] for r in rs):>9} "
                     f"{aciertos:>5}/{len(rs):<3} {sum(r['tiempo_ms'] for r in rs) / len(rs):>18.2f}")
    return "\n".join(filas)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser(description="Compara el parser propio con spaCy y HuggingFace")
    ap.add_argument("--entrada", default=ENTRADA_POR_DEFECTO, help="JSON con las oraciones")
    ap.add_argument("--salida", default="salida/resultados_p1.json", help="dónde guardar los resultados")
    ap.add_argument("--sistemas", nargs="+", default=list(formato.SISTEMAS), choices=formato.SISTEMAS)
    args = ap.parse_args(argv)

    oraciones = formato.cargar_oraciones(args.entrada)
    registros: List[dict] = []
    fallos = 0
    for sistema in args.sistemas:
        try:
            if sistema == "propio":
                from comparacion import propio as modulo
            elif sistema == "spacy":
                from comparacion import spacy_sistema as modulo
            else:
                from comparacion import hf_sistema as modulo
            registros += modulo.ejecutar(oraciones)
        except Exception as error:                      # falta la librería, el modelo, no hay red...
            fallos += 1
            print(f"No se pudo correr '{sistema}': {type(error).__name__}: {error}", file=sys.stderr)

    formato.validar_todos(registros)                    # el validador corto que pide el plan
    formato.guardar(registros, args.salida)
    print(resumen(registros))
    print(f"\n{len(registros)} resultados válidos guardados en {args.salida}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
