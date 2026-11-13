"""
Analizador léxico (lexer) del lenguaje Manzana.

Recibe el texto de un programa .mz y devuelve:
  - una lista de tokens  -> Token(tipo, lexema, linea, columna)
  - una lista de errores -> {"fase": "lexico", "linea": ..., "columna": ..., "mensaje": ...}

Contrato con el parser (P2): cada token es la tupla (tipo, lexema, linea, columna)
y la lista siempre termina con un token EOF.

Uso desde la terminal (desde la raíz del repositorio):
    python -m lexer.lexer pruebas/ejemplos/validos/ejemplo.mz
    python -m lexer.lexer programa.mz --json tokens.json     # además exporta los tokens en JSON
Escribe salida/tokens.txt y salida/errores.txt (la carpeta salida/ no se versiona).
"""
import argparse
import json
import os
import re
from typing import List, NamedTuple, Tuple


class Token(NamedTuple):
    tipo: str      # categoría: ID, ENTERO, MAS, SI, ...
    lexema: str    # texto exacto que se leyó
    linea: int     # empieza en 1
    columna: int   # empieza en 1


# --- Vocabulario del lenguaje -------------------------------------------------

# Estas cuatro palabras comparten el tipo TIPO (el lexema dice cuál es).
TIPOS_DE_DATO = {"entero", "decimal", "texto", "booleano"}

# El resto de palabras reservadas: cada una tiene su propio tipo de token.
PALABRAS_RESERVADAS = {
    "si": "SI",
    "sino": "SINO",
    "mientras": "MIENTRAS",
    "imprimir": "IMPRIMIR",
    "verdadero": "VERDADERO",
    "falso": "FALSO",
    "y": "Y",
    "o": "O",
    "no": "NO",
}

# Operadores y delimitadores: lexema -> tipo de token.
SIMBOLOS = {
    "==": "IGUAL_IGUAL", "!=": "DIFERENTE", "<=": "MENOR_IGUAL", ">=": "MAYOR_IGUAL",
    "=": "IGUAL", "<": "MENOR", ">": "MAYOR",
    "+": "MAS", "-": "MENOS", "*": "POR", "/": "DIVIDIDO", "%": "MODULO",
    "(": "PAREN_IZQ", ")": "PAREN_DER", "{": "LLAVE_IZQ", "}": "LLAVE_DER",
    ";": "PUNTOYCOMA", ",": "COMA",
}

# --- Expresiones regulares ----------------------------------------------------
# El orden importa: Python prueba las alternativas de izquierda a derecha.
#   - DECIMAL antes que ENTERO, para que 3.5 no se lea como 3 y luego .5
#   - "==" antes que "=", para que == no se lea como dos igual
#   - DESCONOCIDO al final: atrapa cualquier carácter que nadie más reconoció
PATRON = re.compile("|".join([
    r'(?P<COMENTARIO>//[^\n]*)',
    r'(?P<ESPACIO>[ \t\r]+)',
    r'(?P<SALTO>\n)',
    r'(?P<DECIMAL>\d+\.\d+)',
    r'(?P<ENTERO>\d+)',
    r'(?P<TEXTO>"[^"\n]*")',
    r'(?P<TEXTO_ABIERTO>"[^"\n]*)',          # comilla que nunca se cierra
    r'(?P<ID>[^\W\d]\w*)',                    # letra o _ y luego letras, dígitos o _
    r'(?P<SIMBOLO>==|!=|<=|>=|[=<>+\-*/%(){};,])',
    r'(?P<DESCONOCIDO>.)',
]))

# Para tragarse un número mal formado completo (3a, 3., 3.5.2) y reportarlo una sola vez.
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

        elif tipo in ("ESPACIO", "COMENTARIO"):
            pass  # se descartan, el parser nunca los ve

        elif tipo in ("ENTERO", "DECIMAL"):
            # Un número pegado a una letra, a un guion bajo o a otro punto está mal formado.
            if fin < len(codigo) and (codigo[fin].isalpha() or codigo[fin] in "_."):
                fin = RESTO_DE_PALABRA.match(codigo, fin).end()
                errores.append(_error(linea, columna,
                                      f"Número mal formado '{codigo[pos:fin]}'"))
            else:
                tokens.append(Token(tipo, lexema, linea, columna))

        elif tipo == "TEXTO":
            tokens.append(Token("TEXTO", lexema, linea, columna))  # el lexema conserva las comillas

        elif tipo == "TEXTO_ABIERTO":
            errores.append(_error(linea, columna, "Texto sin cerrar: falta la comilla de cierre"))

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
    """Cada token se guarda como [tipo, lexema, linea, columna] (el contrato con el parser)."""
    lineas = [json.dumps(list(t), ensure_ascii=False) for t in tokens]
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("[\n " + ",\n ".join(lineas) + "\n]\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Lexer del lenguaje Manzana")
    ap.add_argument("archivo", help="programa .mz a analizar")
    ap.add_argument("--json", help="exportar los tokens a este archivo JSON")
    ap.add_argument("--salida", default="salida", help="carpeta de salida (por defecto: salida)")
    args = ap.parse_args()

    with open(args.archivo, encoding="utf-8") as f:
        texto = f.read()

    toks, errs = analizar(texto)
    os.makedirs(args.salida, exist_ok=True)
    escribir_tokens(toks, os.path.join(args.salida, "tokens.txt"))
    escribir_errores(errs, os.path.join(args.salida, "errores.txt"))
    if args.json:
        tokens_a_json(toks, args.json)

    for t in toks:
        print(f"{t.linea}:{t.columna:<4} {t.tipo:<14} {t.lexema}")
    for e in errs:
        print(f"ERROR línea {e['linea']}, col {e['columna']}: {e['mensaje']}")
    print(f"\n{len(toks)} tokens, {len(errs)} errores léxicos")
