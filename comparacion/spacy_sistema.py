"""spaCy (es_core_news_sm) como sistema a comparar.

spaCy NO rechaza oraciones: siempre devuelve un análisis. Para compararlo con una gramática
hay que convertir ese análisis en "aceptada" o "rechazada". Esa conversión sigue la siguiente regla:

    R1  la raíz del análisis es un verbo
    R2  la raíz tiene sujeto (nsubj)
    R3  la raíz tiene objeto directo (obj)
    R4  concordancia, con los rasgos morfológicos que da spaCy:
        - determinantes y adjetivos coinciden en género y número con su sustantivo
        - el verbo coincide en número y persona con el sujeto (un sustantivo es 3.ª persona)

Si alguna falla, la oración se rechaza y el motivo queda en `detalle`.

Uso:
    python -m comparacion.spacy_sistema "La niña de los vecinos lee los libros nuevos."
"""
import sys
import time
from typing import Dict, List, Optional, Tuple

from parser.nodo import Nodo

MODELO = "es_core_news_sm"
_nlp = None


def cargar_modelo(nombre: str = MODELO):
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load(nombre)
        _nlp("Yo leo el libro.")          # calentamiento: la primera llamada es más lenta
    return _nlp


def extraer(doc) -> List[dict]:
    """Pasa un Doc de spaCy a una lista de diccionarios simples (así la decisión se puede probar sin spaCy)."""
    return [{"i": t.i, "text": t.text, "pos": t.pos_, "dep": t.dep_, "head": t.head.i,
             "morph": t.morph.to_dict()} for t in doc]


def _hijos(tokens: List[dict], i: int) -> List[dict]:
    return [t for t in tokens if t["head"] == i and t["i"] != i]


def decidir(tokens: List[dict]) -> Tuple[bool, List[str]]:
    """Aplica R1 a R4. Devuelve (aceptada, motivos del rechazo)."""
    motivos: List[str] = []
    raices = [t for t in tokens if t["dep"] == "ROOT"]
    if not raices:
        return False, ["spaCy no encontró raíz"]
    raiz = raices[0]
    if raiz["pos"] not in ("VERB", "AUX"):
        return False, [f"R1: la raíz '{raiz['text']}' no es un verbo ({raiz['pos']})"]
    hijos = _hijos(tokens, raiz["i"])
    sujetos = [t for t in hijos if t["dep"] in ("nsubj", "nsubj:pass")]
    objetos = [t for t in hijos if t["dep"] in ("obj", "dobj")]
    if not sujetos:
        motivos.append(f"R2: '{raiz['text']}' no tiene sujeto")
    if not objetos:
        motivos.append(f"R3: '{raiz['text']}' no tiene objeto directo")

    def comparar(a: dict, b: dict, rasgos: Dict[str, str], etiqueta: str) -> None:
        for rasgo, nombre in rasgos.items():
            va, vb = a["morph"].get(rasgo), b["morph"].get(rasgo)
            if va and vb and va != vb:
                motivos.append(f"R4: '{b['text']}' discrepa en {nombre} con '{a['text']}' ({etiqueta}: {va} frente a {vb})")

    for t in tokens:                                    # R4: determinantes y adjetivos con su sustantivo
        if t["dep"] in ("det", "amod") and t["head"] != t["i"]:
            nucleo = tokens[t["head"]]
            if nucleo["pos"] in ("NOUN", "PROPN"):
                comparar(nucleo, t, {"Gender": "género", "Number": "número"}, "nominal")

    for s in sujetos:                                   # R4: verbo con sujeto
        persona_sujeto = s["morph"].get("Person") if s["pos"] == "PRON" else "3"
        if s["morph"].get("Number") and raiz["morph"].get("Number") and s["morph"]["Number"] != raiz["morph"]["Number"]:
            motivos.append(f"R4: '{raiz['text']}' discrepa en número con '{s['text']}' "
                           f"({s['morph']['Number']} frente a {raiz['morph']['Number']})")
        if persona_sujeto and raiz["morph"].get("Person") and persona_sujeto != raiz["morph"]["Person"]:
            motivos.append(f"R4: '{raiz['text']}' discrepa en persona con '{s['text']}' "
                           f"({persona_sujeto} frente a {raiz['morph']['Person']})")
    return (not motivos), motivos


def a_nodo(tokens: List[dict], i: Optional[int] = None) -> Nodo:
    """Árbol de dependencias como Nodo: el tipo es la relación (nsubj, obj...) y el valor, la palabra."""
    if i is None:
        i = next((t["i"] for t in tokens if t["dep"] == "ROOT"), 0)
    t = tokens[i]
    return Nodo(t["dep"], [a_nodo(tokens, h["i"]) for h in _hijos(tokens, i)],
                valor={"lexema": t["text"], "pos": t["pos"]}, linea=1)


def evaluar(oracion: str) -> Tuple[bool, Optional[dict], str]:
    tokens = extraer(cargar_modelo()(oracion))
    aceptada, motivos = decidir(tokens)
    return aceptada, a_nodo(tokens).a_dict(), "; ".join(motivos)


def ejecutar(oraciones) -> list:
    from comparacion.formato import registro
    cargar_modelo()
    resultados = []
    for o in oraciones:
        t0 = time.perf_counter()
        aceptada, arbol, detalle = evaluar(o["oracion"])
        ms = (time.perf_counter() - t0) * 1000
        resultados.append(registro(o["id"], o["oracion"], o["nivel"], o["esperado"], "spacy",
                                   aceptada, arbol, ms, detalle))
    return resultados


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    if len(sys.argv) < 2:
        sys.exit('Uso: python -m comparacion.spacy_sistema "oración entre comillas"')
    toks = extraer(cargar_modelo()(sys.argv[1]))
    print(f"{'palabra':<12} {'pos':<6} {'dep':<8} {'cabeza':<10} morfología")
    for t in toks:
        print(f"{t['text']:<12} {t['pos']:<6} {t['dep']:<8} {toks[t['head']]['text']:<10} {t['morph']}")
    ok, motivos = decidir(toks)
    print("\nDecisión:", "ACEPTADA" if ok else "RECHAZADA")
    for m in motivos:
        print(" -", m)
