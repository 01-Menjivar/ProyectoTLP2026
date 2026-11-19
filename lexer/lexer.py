"""
Analizador léxico (lexer) del subconjunto de C (mini-C) del proyecto TLP02-2026.

Recibe el texto de un programa .c y devuelve:
  - una lista de tokens  -> Token(tipo, lexema, linea, columna)
  - una lista de errores -> {"fase": "lexico", "linea": ..., "columna": ..., "mensaje": ...}

La lista de tokens siempre termina con un token EOF. Los comentarios (// y /* */) y los
espacios se descartan. El lexer no se detiene en el primer error: lo registra y sigue.

Uso desde la terminal (desde la raíz del repositorio):
    python -m lexer.lexer pruebas/ejemplos/validos/ejemplo.c
    python -m lexer.lexer programa.c --json tokens.json
Escribe salida/tokens.txt y salida/errores.txt (la carpeta salida/ no se versiona).
"""
import argparse
import json
import os
import re
from typing import List, NamedTuple, Tuple


class Token(NamedTuple):
    tipo: str      # categoría: ID, ENTERO, MAS, IF, ...
    lexema: str    # texto exacto que se leyó
    linea: int     # empieza en 1
    columna: int   # empieza en 1


# --- Vocabulario del lenguaje -------------------------------------------------

# Los tres tipos de dato comparten el tipo de token TIPO (el lexema dice cuál es).
TIPOS_DE_DATO = {"int", "float", "char"}

# Las demás palabras reservadas: cada una tiene su propio tipo de token.
PALABRAS_RESERVADAS = {
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "printf": "PRINTF",
}

# Operadores y delimitadores: lexema -> tipo de token.
SIMBOLOS = {
    "&&": "Y_LOGICO", "||": "O_LOGICO", "!": "NO_LOGICO",
    "==": "IGUAL_IGUAL", "!=": "DIFERENTE", "<=": "MENOR_IGUAL", ">=": "MAYOR_IGUAL",
    "=": "IGUAL", "<": "MENOR", ">": "MAYOR",
    "+": "MAS", "-": "MENOS", "*": "POR", "/": "DIVIDIDO", "%": "MODULO",
    "(": "PAREN_IZQ", ")": "PAREN_DER", "{": "LLAVE_IZQ", "}": "LLAVE_DER",
    ";": "PUNTOYCOMA", ",": "COMA",
}

# --- Expresiones regulares ----------------------------------------------------
# El orden importa: Python prueba las alternativas de izquierda a derecha y toma la primera
# que encaja. Por eso:
#   - los comentarios van antes que "/" (si no, "//" serían dos divisiones)
#   - FLOTANTE antes que ENTERO, para leer 3.5 completo y no como 3 y .5
#   - "&&", "||", "==", "!=" antes que los símbolos de un solo carácter
#   - las versiones "abiertas" (sin cerrar) van justo después de las cerradas
#   - DESCONOCIDO al final: atrapa cualquier carácter que nadie más reconoció
PATRON = re.compile("|".join([
    r'(?P<COMENTARIO_LINEA>//[^\n]*)',
    r'(?P<COMENTARIO_BLOQUE>(?s:/\*.*?\*/))',
    r'(?P<COMENTARIO_ABIERTO>(?s:/\*.*))',               # /* que nunca se cierra
    r'(?P<ESPACIO>[ \t\r]+)',
    r'(?P<SALTO>\n)',
    r'(?P<FLOTANTE>[0-9]+\.[0-9]+)',
    r'(?P<ENTERO>[0-9]+)',
    r'(?P<CADENA>"(?:[^"\\\n]|\\[^\n])*")',
    r'(?P<CADENA_ABIERTA>"(?:[^"\\\n]|\\[^\n])*)',       # comilla que nunca se cierra
    r"(?P<CARACTER>'(?:[^'\\\n]|\\[^\n])')",
    r"(?P<CARACTER_MALO>'[^'\n]*'?)",                     # '', 'ab', 'a sin cerrar
    r'(?P<ID>[A-Za-z_][A-Za-z0-9_]*)',
    r'(?P<SIMBOLO>&&|\|\||==|!=|<=|>=|[=<>+\-*/%(){};,!])',
    r'(?P<DESCONOCIDO>.)',
]))

# Para tragarse un número mal formado completo (3a, 3., 3.5.2, .5) y reportarlo una sola vez.
RESTO_DE_PALABRA = re.compile(r'[\w.]*')


def _error(linea: int, columna: int, mensaje: str) -> dict:
    return {"fase": "lexico", "linea": linea, "columna": columna, "mensaje": mensaje}


def analizar(codigo: str) -> Tuple[List[Token], List[dict]]:
    """Convierte el texto fuente en (tokens, errores). No se detiene en el primer error."""
    tokens: List[Token] = []
    errores: List[dict] = []

    pos = 0            # posición actual dentro del texto
    linea = 1          # línea actual
    inicio_linea = 0   # posición donde empezó la línea actual (para calcular la columna)

    while pos < len(codigo):
        m = PATRON.match(codigo, pos)
        tipo = m.lastgroup
        lexema = m.group()
        fin = m.end()
        columna = pos - inicio_linea + 1

        if tipo == "SALTO":
            linea += 1
            inicio_linea = fin

        elif tipo in ("ESPACIO", "COMENTARIO_LINEA"):
            pass  # se descartan, nadie más los ve

        elif tipo in ("COMENTARIO_BLOQUE", "COMENTARIO_ABIERTO"):
            if tipo == "COMENTARIO_ABIERTO":
                errores.append(_error(linea, columna,
                                      "Comentario de bloque sin cerrar: falta '*/'"))
            saltos = lexema.count("\n")        # un comentario puede ocupar varias líneas
            if saltos:
                linea += saltos
                inicio_linea = pos + lexema.rfind("\n") + 1

        elif tipo in ("ENTERO", "FLOTANTE"):
            # Un número pegado a una letra, a un guion bajo o a otro punto está mal formado.
            if fin < len(codigo) and (codigo[fin].isalpha() or codigo[fin] in "_."):
                fin = RESTO_DE_PALABRA.match(codigo, fin).end()
                errores.append(_error(linea, columna,
                                      f"Número mal formado '{codigo[pos:fin]}'"))
            else:
                tokens.append(Token(tipo, lexema, linea, columna))

        elif tipo == "CADENA":
            tokens.append(Token("CADENA", lexema, linea, columna))      # conserva las comillas

        elif tipo == "CADENA_ABIERTA":
            errores.append(_error(linea, columna, "Cadena sin cerrar: falta la comilla de cierre"))

        elif tipo == "CARACTER":
            tokens.append(Token("CARACTER", lexema, linea, columna))    # conserva las comillas

        elif tipo == "CARACTER_MALO":
            errores.append(_error(linea, columna,
                                  f"Literal de carácter mal formado {lexema}: debe contener exactamente un carácter"))

        elif tipo == "ID":
            if lexema in TIPOS_DE_DATO:
                tokens.append(Token("TIPO", lexema, linea, columna))
            elif lexema in PALABRAS_RESERVADAS:
                tokens.append(Token(PALABRAS_RESERVADAS[lexema], lexema, linea, columna))
            else:
                tokens.append(Token("ID", lexema, linea, columna))

        elif tipo == "SIMBOLO":
            tokens.append(Token(SIMBOLOS[lexema], lexema, linea, columna))

        else:  # DESCONOCIDO
            if lexema in ("&", "|"):
                errores.append(_error(linea, columna,
                                      f"Operador incompleto '{lexema}': ¿quiso decir '{lexema * 2}'?"))
            elif lexema == "." and fin < len(codigo) and codigo[fin].isdigit():
                fin = RESTO_DE_PALABRA.match(codigo, fin).end()          # .5 no es un número válido
                errores.append(_error(linea, columna,
                                      f"Número mal formado '{codigo[pos:fin]}'"))
            else:
                errores.append(_error(linea, columna, f"Carácter inválido '{lexema}'"))

        pos = fin

    tokens.append(Token("EOF", "", linea, pos - inicio_linea + 1))
    return tokens, errores


# --- Archivos de salida -------------------------------------------------------

def escribir_tokens(tokens: List[Token], ruta: str = "tokens.txt") -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"{'LINEA:COL':<10} {'TIPO':<14} LEXEMA\n")
        for t in tokens:
            f.write(f"{str(t.linea) + ':' + str(t.columna):<10} {t.tipo:<14} {t.lexema}\n")


def escribir_errores(errores: List[dict], ruta: str = "errores.txt") -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        if not errores:
            f.write("Sin errores léxicos.\n")
        for e in errores:
            f.write(f"[{e['fase']}] línea {e['linea']}, columna {e['columna']}: {e['mensaje']}\n")


def tokens_a_json(tokens: List[Token], ruta: str) -> None:
    """Cada token se guarda como [tipo, lexema, linea, columna] según el contrato de tokens."""
    lineas = [json.dumps(list(t), ensure_ascii=False) for t in tokens]
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("[\n " + ",\n ".join(lineas) + "\n]\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Lexer de mini-C")
    ap.add_argument("archivo", help="programa .c a analizar")
    ap.add_argument("--json", help="exportar los tokens a este archivo JSON")
    ap.add_argument("--salida", default="salida", help="carpeta de salida (por defecto: salida)")
    args = ap.parse_args()

    with open(args.archivo, encoding="utf-8-sig") as f:   # utf-8-sig tolera la marca BOM de Windows
        texto = f.read()

    toks, errs = analizar(texto)
    os.makedirs(args.salida, exist_ok=True)
    escribir_tokens(toks, os.path.join(args.salida, "tokens.txt"))
    escribir_errores(errs, os.path.join(args.salida, "errores.txt"))
    if args.json:
        tokens_a_json(toks, args.json)

    for t in toks:
        print(f"{t.linea}:{t.columna:<6} {t.tipo:<14} {t.lexema}")
    for e in errs:
        print(f"ERROR línea {e['linea']}, col {e['columna']}: {e['mensaje']}")
    print(f"\n{len(toks)} tokens, {len(errs)} errores léxicos")
