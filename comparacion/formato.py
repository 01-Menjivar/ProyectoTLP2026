"""Formato común de resultados (plan de trabajo, Fase 2) y carga del conjunto de oraciones.

Cada resultado es un diccionario con estos campos:
    id         identificador de la oración (el del conjunto de P2)
    oracion    texto de la oración
    nivel      1, 2 o 3 (nivel de dificultad)
    esperado   True si la oración debe ser aceptada, False si debe ser rechazada
    sistema    "propio", "spacy" o "hf"
    aceptada   True si el sistema la aceptó
    arbol      árbol del sistema como diccionario (Nodo.a_dict) o None si no produce árbol
    tiempo_ms  tiempo de análisis en milisegundos (sin contar la carga del modelo)
Campo opcional:
    detalle    texto con el motivo del rechazo o la lista de etiquetas (no lo exige el validador)

El conjunto de oraciones es un JSON: una lista de {id, oracion, nivel, esperado}. `esperado`
puede ser true/false o "aceptada"/"rechazada".
"""
import json
import os
from typing import List, Optional

CAMPOS = ("id", "oracion", "nivel", "esperado", "sistema", "aceptada", "arbol", "tiempo_ms")
SISTEMAS = ("propio", "spacy", "hf")


def registro(id, oracion, nivel, esperado, sistema, aceptada, arbol, tiempo_ms, detalle: Optional[str] = None) -> dict:
    r = {"id": id, "oracion": oracion, "nivel": nivel, "esperado": esperado, "sistema": sistema,
         "aceptada": aceptada, "arbol": arbol, "tiempo_ms": round(tiempo_ms, 3)}
    if detalle is not None:
        r["detalle"] = detalle
    return r


def validar(r: dict) -> None:
    """Lanza ValueError si el registro no cumple el formato común."""
    faltan = [c for c in CAMPOS if c not in r]
    if faltan:
        raise ValueError(f"Faltan campos {faltan} en {r.get('id')!r}")
    if not isinstance(r["oracion"], str) or not r["oracion"].strip():
        raise ValueError(f"'oracion' vacía en {r['id']!r}")
    if r["nivel"] not in (1, 2, 3):
        raise ValueError(f"'nivel' debe ser 1, 2 o 3 en {r['id']!r}, no {r['nivel']!r}")
    for campo in ("esperado", "aceptada"):
        if not isinstance(r[campo], bool):
            raise ValueError(f"'{campo}' debe ser true o false en {r['id']!r}, no {r[campo]!r}")
    if r["sistema"] not in SISTEMAS:
        raise ValueError(f"'sistema' debe ser uno de {SISTEMAS} en {r['id']!r}, no {r['sistema']!r}")
    if r["arbol"] is not None and not isinstance(r["arbol"], dict):
        raise ValueError(f"'arbol' debe ser un diccionario o null en {r['id']!r}")
    if isinstance(r["tiempo_ms"], bool) or not isinstance(r["tiempo_ms"], (int, float)) or r["tiempo_ms"] < 0:
        raise ValueError(f"'tiempo_ms' debe ser un número no negativo en {r['id']!r}")


def validar_todos(registros: List[dict]) -> None:
    for r in registros:
        validar(r)


def _a_bool(valor, id) -> bool:
    if isinstance(valor, bool):
        return valor
    texto = str(valor).strip().casefold()
    if texto in ("aceptada", "aceptar", "true", "si", "sí", "1"):
        return True
    if texto in ("rechazada", "rechazar", "false", "no", "0"):
        return False
    raise ValueError(f"No entiendo 'esperado'={valor!r} en la oración {id!r}")


def cargar_oraciones(ruta: str) -> List[dict]:
    """Lee el conjunto de oraciones y lo deja con esperado como booleano."""
    with open(ruta, encoding="utf-8-sig") as f:
        datos = json.load(f)
    if not isinstance(datos, list):
        raise ValueError("El archivo debe contener una lista de oraciones")
    oraciones = []
    for d in datos:
        for campo in ("id", "oracion", "nivel", "esperado"):
            if campo not in d:
                raise ValueError(f"Falta '{campo}' en {d!r}")
        oraciones.append({"id": d["id"], "oracion": d["oracion"], "nivel": d["nivel"],
                          "esperado": _a_bool(d["esperado"], d["id"])})
    return oraciones


def guardar(registros: List[dict], ruta: str) -> None:
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)
