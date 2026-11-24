"""Sistema propio: lexer del español + parser descendente + verificador de concordancia."""
import time
from typing import Optional, Tuple

from lexer.espanol import analizar_oracion
from parser.espanol import analizar


def evaluar(oracion: str) -> Tuple[bool, Optional[dict], str]:
    """Devuelve (aceptada, árbol como diccionario o None, detalle)."""
    tokens, tabla, errores_lexicos = analizar_oracion(oracion)
    if errores_lexicos:
        e = errores_lexicos[0]
        return False, None, f"léxico (col {e['columna']}): {e['mensaje']}"
    arbol, errores = analizar(tokens, tabla)
    if errores:
        e = errores[0]
        return False, (arbol.a_dict() if arbol else None), f"{e['fase']} (col {e['columna']}): {e['mensaje']}"
    return True, arbol.a_dict(), ""


def ejecutar(oraciones) -> list:
    from comparacion.formato import registro
    resultados = []
    for o in oraciones:
        t0 = time.perf_counter()
        aceptada, arbol, detalle = evaluar(o["oracion"])
        ms = (time.perf_counter() - t0) * 1000
        resultados.append(registro(o["id"], o["oracion"], o["nivel"], o["esperado"], "propio",
                                   aceptada, arbol, ms, detalle))
    return resultados
