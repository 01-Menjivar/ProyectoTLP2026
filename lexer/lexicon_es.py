"""Léxico del español para la gramática v1 (O, SN, SP, SV).

Cada forma (en minúsculas) tiene UNA entrada: su categoría y sus rasgos.
    N               genero, numero, persona=3
    DET, ADJ        genero, numero
    PRON, V_*       numero, persona
    PREP, ADV       sin rasgos

Para agregar vocabulario basta con añadir una palabra a las listas de abajo (sustantivos,
adjetivos, verbos, preposiciones, adverbios); las formas de plural, femenino y conjugación
se generan solas. Las palabras con formas irregulares se escriben a mano.

Limitaciones de la versión 1 (documentadas a propósito):
  - Una forma tiene una sola categoría. No hay palabras ambiguas entre categorías.
  - No hay adjetivos ni sustantivos invariables en género (grande, estudiante), porque
    la tabla guarda un solo género por palabra.
  - En los verbos -ar e -ir, la 1.ª persona del plural es igual en presente y en pretérito
    (compramos, abrimos). Se registra como V_PRES; la gramática acepta los dos igual.
"""
from typing import Dict, NamedTuple, Set

VOCALES = "aeiouáéíóú"
PERSONAS = [("sg", 1), ("sg", 2), ("sg", 3), ("pl", 1), ("pl", 2), ("pl", 3)]


class Entrada(NamedTuple):
    categoria: str
    rasgos: dict


LEXICON: Dict[str, Entrada] = {}
HOMOGRAFOS: Set[str] = set()      # formas que cumplen dos categorías con los mismos rasgos


def _agregar(forma: str, categoria: str, **rasgos) -> None:
    forma = forma.casefold()
    previa = LEXICON.get(forma)
    if previa is None:
        LEXICON[forma] = Entrada(categoria, rasgos)
    elif previa.rasgos == rasgos and previa.categoria != categoria:
        HOMOGRAFOS.add(forma)            # se conserva la primera categoría registrada
    else:
        raise ValueError(
            f"Léxico en conflicto: '{forma}' ya está registrada como {previa.categoria} {previa.rasgos} y se "
            f"intentó registrar como {categoria} {rasgos}. Una forma solo puede tener una categoría: "
            f"quita una de las dos palabras que la generan.")


_PLURALES_IRREGULARES = {"canción": "canciones"}     # pierden la tilde al pluralizar


def _plural(singular: str) -> str:
    if singular in _PLURALES_IRREGULARES:
        return _PLURALES_IRREGULARES[singular]
    if singular[-1] in VOCALES:
        return singular + "s"
    if singular.endswith("z"):
        return singular[:-1] + "ces"
    return singular + "es"


# --- Determinantes y pronombres (cerrados, a mano) ---------------------------------------
_DETERMINANTES = [
    ("el", "m", "sg"), ("la", "f", "sg"), ("los", "m", "pl"), ("las", "f", "pl"),
    ("un", "m", "sg"), ("una", "f", "sg"), ("unos", "m", "pl"), ("unas", "f", "pl"),
    ("este", "m", "sg"), ("esta", "f", "sg"), ("estos", "m", "pl"), ("estas", "f", "pl"),
]
for _forma, _genero, _numero in _DETERMINANTES:
    _agregar(_forma, "DET", genero=_genero, numero=_numero)

_PRONOMBRES = [
    ("yo", "sg", 1), ("tú", "sg", 2), ("él", "sg", 3), ("ella", "sg", 3), ("usted", "sg", 3),
    ("nosotros", "pl", 1), ("nosotras", "pl", 1), ("vosotros", "pl", 2), ("vosotras", "pl", 2),
    ("ellos", "pl", 3), ("ellas", "pl", 3), ("ustedes", "pl", 3),
]
for _forma, _numero, _persona in _PRONOMBRES:
    _agregar(_forma, "PRON", numero=_numero, persona=_persona)

# --- Sustantivos: (singular, género); el plural se genera ------------------------------------
_SUSTANTIVOS = [
    ("libro", "m"), ("niño", "m"), ("niña", "f"), ("vecino", "m"), ("vecina", "f"),
    ("amigo", "m"), ("amiga", "f"), ("maestro", "m"), ("maestra", "f"),
    ("profesor", "m"), ("profesora", "f"), ("casa", "f"), ("perro", "m"), ("gato", "m"),
    ("carta", "f"), ("mesa", "f"), ("ciudad", "f"), ("mensaje", "m"), ("informe", "m"),
    ("computadora", "f"), ("manzana", "f"), ("película", "f"), ("cuaderno", "m"),
    ("tarea", "f"), ("pan", "m"), ("café", "m"), ("canción", "f"), ("periódico", "m"),
    ("ventana", "f"), ("puerta", "f"), ("regalo", "m"), ("historia", "f"),
]
for _sg, _genero in _SUSTANTIVOS:
    _agregar(_sg, "N", genero=_genero, numero="sg", persona=3)
    _agregar(_plural(_sg), "N", genero=_genero, numero="pl", persona=3)

# --- Adjetivos en -o/-a (cuatro formas cada uno) ------------------------------------------
_RAICES_ADJETIVO = [
    "nuev", "viej", "larg", "cort", "bonit", "pequeñ", "roj", "buen", "mal",
    "antigu", "limpi", "alt", "baj", "rápid", "lent",
]
for _raiz in _RAICES_ADJETIVO:
    _agregar(_raiz + "o", "ADJ", genero="m", numero="sg")
    _agregar(_raiz + "a", "ADJ", genero="f", numero="sg")
    _agregar(_raiz + "os", "ADJ", genero="m", numero="pl")
    _agregar(_raiz + "as", "ADJ", genero="f", numero="pl")

# --- Preposiciones y adverbios ----------------------------------------------------------------
for _forma in ["de", "con", "en", "para", "sin", "sobre", "por", "a", "desde", "hasta"]:
    _agregar(_forma, "PREP")

for _forma in ["ayer", "hoy", "bien", "mal", "mañana", "ahora", "siempre", "anoche",
               "temprano", "rápidamente", "lentamente", "allí", "aquí"]:
    _agregar(_forma, "ADV")

# --- Verbos transitivos --------------------------------------------------------------------------
_TERMINACIONES_PRES = {
    "ar": ["o", "as", "a", "amos", "áis", "an"],
    "er": ["o", "es", "e", "emos", "éis", "en"],
    "ir": ["o", "es", "e", "imos", "ís", "en"],
}
_TERMINACIONES_PRET = {
    "ar": ["é", "aste", "ó", "amos", "asteis", "aron"],
    "er": ["í", "iste", "ió", "imos", "isteis", "ieron"],
    "ir": ["í", "iste", "ió", "imos", "isteis", "ieron"],
}
_VERBOS = ["leer", "comer", "escribir", "comprar", "abrir", "ver", "buscar", "tomar",
           "escuchar", "preparar", "mirar", "llevar", "cerrar", "vender", "recibir"]

# Formas irregulares: se escriben las seis personas completas, en el orden de PERSONAS.
_IRREGULARES = {
    ("ver", "pres"): ["veo", "ves", "ve", "vemos", "veis", "ven"],
    ("ver", "pret"): ["vi", "viste", "vio", "vimos", "visteis", "vieron"],
    ("leer", "pret"): ["leí", "leíste", "leyó", "leímos", "leísteis", "leyeron"],
    ("buscar", "pret"): ["busqué", "buscaste", "buscó", "buscamos", "buscasteis", "buscaron"],
    ("cerrar", "pres"): ["cierro", "cierras", "cierra", "cerramos", "cerráis", "cierran"],
}


def _conjugar(verbo: str, tiempo: str):
    if (verbo, tiempo) in _IRREGULARES:
        return _IRREGULARES[(verbo, tiempo)]
    raiz, modelo = verbo[:-2], verbo[-2:]
    tabla = _TERMINACIONES_PRES if tiempo == "pres" else _TERMINACIONES_PRET
    return [raiz + t for t in tabla[modelo]]


for _verbo in _VERBOS:
    for _tiempo, _categoria in (("pres", "V_PRES"), ("pret", "V_PRET")):
        for _forma, (_numero, _persona) in zip(_conjugar(_verbo, _tiempo), PERSONAS):
            _agregar(_forma, _categoria, numero=_numero, persona=_persona)
