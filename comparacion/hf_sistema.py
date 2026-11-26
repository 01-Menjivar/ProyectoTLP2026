"""HuggingFace (etiquetador de categorías gramaticales) como sistema a comparar.

Un modelo de HuggingFace para español, como este, solo ETIQUETA cada palabra con su categoría
gramatical (sustantivo, verbo...). No analiza la estructura ni la concordancia. Para compararlo con
la gramática se convierte esa secuencia de etiquetas en "aceptada" o "rechazada": se acepta si las
categorías, en orden, encajan en el esqueleto de la gramática v1. Por construcción, este sistema no
puede detectar errores de concordancia: eso es justo lo que se quiere mostrar en la comparación.

    O  ::= (PRON | SN) V [ADV] SN [ADV]
    SN ::= DET N {ADJ} {PREP DET N {ADJ}}

El modelo puede cambiarse si se requiere probar otro etiquetador de UPOS para español.

Uso:
    python -m comparacion.hf_sistema "La niña de los vecinos lee los libros nuevos."
"""
import re
import sys
import time
from typing import List, Optional, Tuple

from parser.nodo import Nodo

MODELO = "mrm8488/bert-spanish-cased-finetuned-pos-16-tags"
_pipeline = None

# Etiqueta universal -> categoría de la gramática. Lo que no está aquí no encaja en la gramática.
UPOS_A_CATEGORIA = {
    "DET": "DET", "NOUN": "N", "PROPN": "N", "ADJ": "ADJ", "ADP": "PREP", "PRON": "PRON",
    "VERB": "V", "AUX": "V", "ADV": "ADV", "PUNCT": "PUNTO",
}

_SN = r"DET N(?: ADJ)*(?: PREP DET N(?: ADJ)*)*"
ESQUELETO = re.compile(rf"^(?:PRON|{_SN}) V(?: ADV)? {_SN}(?: ADV)?$")


def cargar_modelo(nombre: str = MODELO):
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        _pipeline = pipeline("token-classification", model=nombre, aggregation_strategy="simple")
        _pipeline("Yo leo el libro.")      # calentamiento
    return _pipeline


def etiquetas(salida: List[dict]) -> List[Tuple[str, str]]:
    """Del resultado del pipeline saca [(palabra, etiqueta UPOS)] sin los prefijos B-/I-.

    BERT parte las palabras raras en fragmentos ("leen" -> "lee" + "##n"), y cada fragmento puede
    traer una etiqueta distinta. Se unen al fragmento anterior y la palabra conserva la etiqueta
    de su primer fragmento (la práctica habitual al evaluar etiquetadores).
    """
    pares: List[Tuple[str, str]] = []
    for e in salida:
        palabra = str(e.get("word", "")).strip()
        etiqueta = re.sub(r"^[BI]-", "", str(e.get("entity_group") or e.get("entity") or "X")).upper()
        if palabra.startswith("##") and pares:
            pares[-1] = (pares[-1][0] + palabra[2:], pares[-1][1])
        else:
            pares.append((palabra, etiqueta))
    return pares


def decidir(pares: List[Tuple[str, str]]) -> Tuple[bool, List[str]]:
    """Aplica el esqueleto de la gramática a las etiquetas. Devuelve (aceptada, motivos)."""
    categorias = []
    for palabra, upos in pares:
        categoria = UPOS_A_CATEGORIA.get(upos)
        if categoria is None:
            return False, [f"la etiqueta {upos} de '{palabra}' no está en la gramática"]
        if categoria != "PUNTO":
            categorias.append(categoria)
    secuencia = " ".join(categorias)
    if ESQUELETO.match(secuencia):
        return True, []
    return False, [f"la secuencia de categorías no encaja en la gramática: {secuencia}"]


def a_nodo(pares: List[Tuple[str, str]]) -> Nodo:
    """Árbol plano: una hoja por palabra con su etiqueta. El modelo no produce estructura."""
    return Nodo("Etiquetas", [Nodo(u, valor={"lexema": p, "columna": 0}, linea=1) for p, u in pares])


def evaluar(oracion: str) -> Tuple[bool, Optional[dict], str]:
    pares = etiquetas(cargar_modelo()(oracion))
    aceptada, motivos = decidir(pares)
    return aceptada, a_nodo(pares).a_dict(), "; ".join(motivos) or " ".join(f"{p}/{u}" for p, u in pares)


def ejecutar(oraciones) -> list:
    from comparacion.formato import registro
    cargar_modelo()
    resultados = []
    for o in oraciones:
        t0 = time.perf_counter()
        aceptada, arbol, detalle = evaluar(o["oracion"])
        ms = (time.perf_counter() - t0) * 1000
        resultados.append(registro(o["id"], o["oracion"], o["nivel"], o["esperado"], "hf",
                                   aceptada, arbol, ms, detalle))
    return resultados


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    if len(sys.argv) < 2:
        sys.exit('Uso: python -m comparacion.hf_sistema "oración entre comillas"')
    pares = etiquetas(cargar_modelo()(sys.argv[1]))
    for palabra, upos in pares:
        print(f"{palabra:<12} {upos}")
    ok, motivos = decidir(pares)
    print("\nDecisión:", "ACEPTADA" if ok else "RECHAZADA")
    for m in motivos:
        print(" -", m)
