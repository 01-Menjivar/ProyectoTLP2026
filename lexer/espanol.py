"""
Analizador léxico del español (Fase 2) para la gramática v1.

Recibe una oración como texto y devuelve:
  - una lista de tokens  -> Token(tipo, lexema, linea, columna), igual que el lexer de mini-C
  - una lista de errores -> {"fase": "lexico", "linea": ..., "columna": ..., "mensaje": ...}

Categorías: PRON, DET, N, ADJ, PREP, V_PRES, V_PRET, ADV, PUNTO y EOF. El lexema conserva
el texto original (mayúsculas incluidas); la categoría sale del léxico (lexer/lexicon_es.py).

Una palabra que no está en el léxico NO produce token: se reporta como error léxico. Si hay
errores, no se debe llamar al parser (le faltarían palabras y daría un error engañoso).

Además, construir_tabla() registra cada palabra en la TablaSimbolos con su clave normalizada
f"{categoria}:{forma.casefold()}" y sus rasgos, que es lo que necesita el verificador de
concordancia.

Uso desde la terminal (desde la raíz del repositorio):
    python -m lexer.espanol "Yo leo el libro."
    python -m lexer.espanol --archivo oracion.txt
"""
import argparse
import difflib
import os
import re
import sys
import unicodedata
from typing import List, Optional, Tuple

from lexer.lexer import Token
from lexer.lexicon_es import LEXICON

PATRON = re.compile("|".join([
    r"(?P<ESPACIO>[ \t\r\f\v]+)",
    r"(?P<SALTO>\n)",
    r"(?P<PALABRA>[^\W\d_]+)",      # letras de cualquier idioma, con tildes y ñ; sin dígitos ni _
    r"(?P<PUNTO>\.)",
    r"(?P<DESCONOCIDO>.)",
]))


def _error(linea: int, columna: int, mensaje: str) -> dict:
    return {"fase": "lexico", "linea": linea, "columna": columna, "mensaje": mensaje}


def _sin_tildes(texto: str) -> str:
    """'tú' -> 'tu', 'leíste' -> 'leiste' (la ñ se conserva)."""
    texto = texto.replace("ñ", "\0")
    base = "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))
    return base.replace("\0", "ñ")


_POR_SIN_TILDES = {}
for _forma in LEXICON:
    _POR_SIN_TILDES.setdefault(_sin_tildes(_forma), _forma)


def _sugerencia(forma: str) -> str:
    """Sugiere una palabra del léxico: primero la misma sin tildes (tu -> tú), luego la más parecida."""
    parecida = _POR_SIN_TILDES.get(_sin_tildes(forma))
    if parecida is None:
        cercanas = difflib.get_close_matches(forma, LEXICON.keys(), n=1, cutoff=0.8)
        parecida = cercanas[0] if cercanas else None
    return f" ¿Quisiste decir '{parecida}'?" if parecida else ""


def analizar(texto: str, emitir_punto: bool = True) -> Tuple[List[Token], List[dict]]:
    """Convierte la oración en (tokens, errores). No se detiene en el primer error.

    emitir_punto=False descarta el punto final; el parser acepta las dos formas.
    """
    texto = unicodedata.normalize("NFC", texto)     # una "é" separada de su tilde cuenta como una letra
    tokens: List[Token] = []
    errores: List[dict] = []
    linea, inicio_linea, pos = 1, 0, 0

    while pos < len(texto):
        m = PATRON.match(texto, pos)
        tipo, lexema = m.lastgroup, m.group()
        columna = pos - inicio_linea + 1

        if tipo == "SALTO":
            linea += 1
            inicio_linea = m.end()
        elif tipo == "PALABRA":
            forma = lexema.casefold()
            entrada = LEXICON.get(forma)
            if entrada is None:
                errores.append(_error(linea, columna,
                                      f"Palabra desconocida '{lexema}': no está en el léxico."
                                      + _sugerencia(forma)))
            else:
                tokens.append(Token(entrada.categoria, lexema, linea, columna))
        elif tipo == "PUNTO":
            if emitir_punto:
                tokens.append(Token("PUNTO", lexema, linea, columna))
        elif tipo == "DESCONOCIDO":
            if lexema.isdigit():
                errores.append(_error(linea, columna, f"Número '{lexema}' no permitido en la oración"))
            else:
                errores.append(_error(linea, columna, f"Carácter inválido '{lexema}'"))
        pos = m.end()

    tokens.append(Token("EOF", "", linea, pos - inicio_linea + 1))
    return tokens, errores


def construir_tabla(tokens: List[Token], tabla=None):
    """Registra cada palabra de la oración en la tabla de símbolos, con sus rasgos.

    Clave: f"{categoria}:{forma.casefold()}". Si la palabra ya estaba (se repite en la oración),
    declarar() devuelve False y no se vuelve a registrar.
    """
    if tabla is None:
        from semantico.tabla_simbolos import TablaSimbolos
        tabla = TablaSimbolos()
    for t in tokens:
        if t.tipo in ("PUNTO", "EOF"):
            continue
        forma = t.lexema.casefold()
        tabla.declarar(f"{t.tipo}:{forma}", t.tipo, t.linea, **LEXICON[forma].rasgos)
    return tabla


def analizar_oracion(texto: str, tabla=None, emitir_punto: bool = True):
    """Atajo para el parser: (tokens, tabla, errores). La tabla es None si hubo errores léxicos."""
    tokens, errores = analizar(texto, emitir_punto)
    return tokens, (None if errores else construir_tabla(tokens, tabla)), errores


def _rasgos(token: Token) -> str:
    if token.tipo in ("PUNTO", "EOF"):
        return ""
    return " ".join(f"{k}={v}" for k, v in LEXICON[token.lexema.casefold()].rasgos.items())


def _imprimir_resultado_cli(toks, errs) -> None:
    """Imprime tokens y errores; usa tabla con colores ANSI si stdout es un TTY."""
    usa_color = not os.environ.get("NO_COLOR") and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if not usa_color:
        for t in toks:
            print(f"{t.linea}:{t.columna:<6} {t.tipo:<8} {t.lexema:<12} {_rasgos(t)}")
        for e in errs:
            print(f"ERROR línea {e['linea']}, col {e['columna']}: {e['mensaje']}")
        print(f"\n{len(toks)} tokens, {len(errs)} errores léxicos")
        return

    RESET = "\033[0m"
    NEGRITA = "\033[1m"
    TENUE = "\033[2m"
    ROJO = "\033[31m"
    VERDE = "\033[32m"
    AMARILLO = "\033[33m"
    AZUL = "\033[34m"
    MAGENTA = "\033[35m"
    CIAN = "\033[36m"

    colores_cat = {
        "PRON": CIAN,
        "DET": CIAN,
        "N": f"{NEGRITA}{AZUL}",
        "V_PRES": f"{NEGRITA}{MAGENTA}",
        "V_PRET": f"{NEGRITA}{MAGENTA}",
        "ADJ": VERDE,
        "ADV": AMARILLO,
        "PREP": AMARILLO,
        "PUNTO": TENUE,
    }

    filas = [(f"{t.linea}:{t.columna}", t.tipo, t.lexema, _rasgos(t) or "—") for t in toks]
    w_pos = max([3] + [len(f[0]) for f in filas])
    w_cat = max([9] + [len(f[1]) for f in filas])
    w_lex = max([6] + [len(f[2]) for f in filas])
    w_ras = max([19] + [len(f[3]) for f in filas])

    sep = f"  {TENUE}├{'─' * (w_pos + 2)}┼{'─' * (w_cat + 2)}┼{'─' * (w_lex + 2)}┼{'─' * (w_ras + 2)}┤{RESET}"
    top = f"  {TENUE}┌{'─' * (w_pos + 2)}┬{'─' * (w_cat + 2)}┬{'─' * (w_lex + 2)}┬{'─' * (w_ras + 2)}┐{RESET}"
    bot = f"  {TENUE}└{'─' * (w_pos + 2)}┴{'─' * (w_cat + 2)}┴{'─' * (w_lex + 2)}┴{'─' * (w_ras + 2)}┘{RESET}"

    print(f"\n{NEGRITA}{CIAN}=== Lexer español (gramática v1) ==={RESET}")
    print(top)
    print(
        f"  {TENUE}│{RESET} {NEGRITA}{'Pos':<{w_pos}}{RESET} "
        f"{TENUE}│{RESET} {NEGRITA}{'Categoría':<{w_cat}}{RESET} "
        f"{TENUE}│{RESET} {NEGRITA}{'Lexema':<{w_lex}}{RESET} "
        f"{TENUE}│{RESET} {NEGRITA}{'Rasgos morfológicos':<{w_ras}}{RESET} {TENUE}│{RESET}"
    )
    print(sep)
    for pos, cat, lex, ras in filas:
        c = colores_cat.get(cat, "")
        r_fmt = f"{TENUE}{ras:<{w_ras}}{RESET}" if ras == "—" else f"{ras:<{w_ras}}"
        print(
            f"  {TENUE}│{RESET} {TENUE}{pos:<{w_pos}}{RESET} "
            f"{TENUE}│{RESET} {c}{cat:<{w_cat}}{RESET} "
            f"{TENUE}│{RESET} {NEGRITA}{lex:<{w_lex}}{RESET} "
            f"{TENUE}│{RESET} {r_fmt} {TENUE}│{RESET}"
        )
    print(bot)

    for e in errs:
        print(f"  {ROJO}✗ ERROR línea {e['linea']}, col {e['columna']}: {e['mensaje']}{RESET}")

    estado = VERDE if not errs else ROJO
    marca = "✓" if not errs else "✗"
    print(f"\n  {NEGRITA}{estado}{marca} {len(toks)} tokens, {len(errs)} errores léxicos{RESET}\n")


if __name__ == "__main__":
    try:                                              # que las tildes se vean bien en Windows
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser(description="Lexer del español (gramática v1)")
    ap.add_argument("oracion", nargs="?", help="oración entre comillas")
    ap.add_argument("--archivo", help="leer la oración desde un archivo de texto")
    args = ap.parse_args()
    if args.archivo:
        with open(args.archivo, encoding="utf-8-sig") as f:
            entrada = f.read()
    elif args.oracion is not None:
        entrada = args.oracion
    else:
        ap.error("da una oración entre comillas o usa --archivo")

    toks, errs = analizar(entrada)
    _imprimir_resultado_cli(toks, errs)
