"""
Visualizador de árboles (Fase 2): dibuja el árbol de una oración como texto, SVG o DOT.

Sirve con cualquier árbol de `Nodo`, pero está pensado para el de la gramática española v1:
cada hoja es una categoría (DET, N, V_PRES...) cuyo `valor` es {"lexema", "columna"}.
No necesita ninguna librería externa: el SVG se abre en el navegador y se puede insertar en
el informe; el DOT es opcional, para quien tenga Graphviz instalado.

Uso desde la terminal (desde la raíz del repositorio):
    python -m parser.visualizador "La niña de los vecinos lee los libros nuevos."
    python -m parser.visualizador "Yo leo los libros nuevas." --svg salida/arbol.svg
    python -m parser.visualizador "Yo leo el libro." --dot salida/arbol.dot

Si la oración tiene errores de concordancia, el árbol se dibuja igual y la palabra que
discrepa sale en rojo, con el mensaje debajo.
"""
import argparse
import os
import sys
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape

from parser.nodo import Nodo

# (relleno, borde) por categoría. Las frases (O, SN, SP, SV) comparten el gris azulado.
COLORES = {
    "O": ("#e8edf3", "#5b6b7f"), "SN": ("#e8edf3", "#5b6b7f"),
    "SP": ("#e8edf3", "#5b6b7f"), "SV": ("#e8edf3", "#5b6b7f"),
    "PRON": ("#dff3e4", "#2e7d4f"), "N": ("#dff3e4", "#2e7d4f"),
    "DET": ("#dce9fb", "#2f5fa8"), "ADJ": ("#fdebd3", "#b36b00"),
    "V_PRES": ("#ecdffa", "#6a3aa3"), "V_PRET": ("#f7dff0", "#a3367f"),
    "PREP": ("#d9f1f1", "#1f7a7a"), "ADV": ("#f1e6d9", "#8a5a2b"),
}
COLOR_POR_DEFECTO = ("#f2f2f2", "#777777")
ROJO, ROJO_FONDO = "#c62828", "#fdecea"

ANCHO_CARACTER = 8.2        # aproximado, para letra de 14 px
ALTO_NIVEL = 72
ALTO_NODO = 28


# --- Utilidades ----------------------------------------------------------------------------------

def _palabra(nodo: Nodo) -> str:
    """Texto de una hoja: el lexema si el valor es {"lexema": ...}, o el valor tal cual."""
    if isinstance(nodo.valor, dict):
        return str(nodo.valor.get("lexema", ""))
    return "" if nodo.valor is None else str(nodo.valor)


def _posicion(nodo: Nodo) -> Tuple[int, Optional[int]]:
    columna = nodo.valor.get("columna") if isinstance(nodo.valor, dict) else None
    return nodo.linea, columna


def _con_error(nodo: Nodo, errores: List[dict]) -> bool:
    linea, columna = _posicion(nodo)
    return columna is not None and any(
        e.get("linea") == linea and e.get("columna") == columna for e in errores)


# --- Texto ---------------------------------------------------------------------------------------

def arbol_texto(nodo: Nodo, errores: Optional[List[dict]] = None) -> str:
    """Árbol con líneas de caja. Las palabras con error de concordancia llevan ' <-- error'."""
    errores = errores or []
    lineas: List[str] = []

    def etiqueta(n: Nodo) -> str:
        texto = n.tipo + (f"  {_palabra(n)}" if not n.hijos and _palabra(n) else "")
        return texto + ("  <-- error" if not n.hijos and _con_error(n, errores) else "")

    def recorrer(n: Nodo, prefijo: str, es_ultimo: bool, es_raiz: bool) -> None:
        if es_raiz:
            lineas.append(etiqueta(n))
            hijo_prefijo = ""
        else:
            lineas.append(prefijo + ("└── " if es_ultimo else "├── ") + etiqueta(n))
            hijo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
        for i, h in enumerate(n.hijos):
            recorrer(h, hijo_prefijo, i == len(n.hijos) - 1, False)

    recorrer(nodo, "", True, True)
    return "\n".join(lineas)


# --- DOT (Graphviz, opcional) -----------------------------------------------------------------------

def arbol_dot(nodo: Nodo, errores: Optional[List[dict]] = None) -> str:
    errores = errores or []
    filas = ["digraph arbol {", '  node [shape=box, style="rounded,filled", fontname="Segoe UI"];']
    contador = [0]

    def recorrer(n: Nodo) -> str:
        contador[0] += 1
        nombre = f"n{contador[0]}"
        relleno, borde = COLORES.get(n.tipo, COLOR_POR_DEFECTO)
        if not n.hijos and _con_error(n, errores):
            relleno, borde = ROJO_FONDO, ROJO
        texto = n.tipo + (f"\\n{_palabra(n)}" if not n.hijos and _palabra(n) else "")
        filas.append(f'  {nombre} [label="{texto}", fillcolor="{relleno}", color="{borde}"];')
        for h in n.hijos:
            filas.append(f"  {nombre} -> {recorrer(h)};")
        return nombre

    recorrer(nodo)
    filas.append("}")
    return "\n".join(filas) + "\n"


# --- SVG ------------------------------------------------------------------------------------------------

class _Caja:
    """Posición calculada de un nodo en el dibujo."""

    def __init__(self, nodo: Nodo, nivel: int):
        self.nodo, self.nivel = nodo, nivel
        self.x = 0.0
        self.hijos: List["_Caja"] = []


def _ancho(texto: str) -> float:
    return len(texto) * ANCHO_CARACTER + 18


def arbol_svg(nodo: Nodo, errores: Optional[List[dict]] = None, oracion: str = "") -> str:
    """Devuelve el árbol como texto SVG. Las hojas llevan su palabra en una fila inferior."""
    errores = errores or []

    def construir(n: Nodo, nivel: int) -> _Caja:
        c = _Caja(n, nivel)
        c.hijos = [construir(h, nivel + 1) for h in n.hijos]
        return c

    raiz = construir(nodo, 0)
    cursor = [20.0]
    profundidad = [0]

    def colocar(c: _Caja) -> None:
        profundidad[0] = max(profundidad[0], c.nivel)
        if not c.hijos:
            ancho = max(_ancho(c.nodo.tipo), _ancho(_palabra(c.nodo))) + 14
            c.x = cursor[0] + ancho / 2
            cursor[0] += ancho
        else:
            for h in c.hijos:
                colocar(h)
            c.x = (c.hijos[0].x + c.hijos[-1].x) / 2

    colocar(raiz)
    ancho_arbol = cursor[0] + 6
    mensajes = [f"{e.get('fase', '')} (línea {e.get('linea')}, col {e.get('columna')}): {e.get('mensaje', '')}"
                for e in errores]
    ancho_total = max([ancho_arbol] + [len(m) * 7.4 + 40 for m in mensajes] + [len(oracion) * 8.5 + 40])

    y0 = 52 if oracion else 30
    y_palabras = y0 + profundidad[0] * ALTO_NIVEL + 62
    alto_total = y_palabras + 34 + (len(mensajes) * 22 + 14 if mensajes else 0)
    desplazamiento = (ancho_total - ancho_arbol) / 2     # centra el árbol si el texto es más ancho

    partes: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho_total:.0f}" height="{alto_total:.0f}" '
        f'viewBox="0 0 {ancho_total:.0f} {alto_total:.0f}" font-family="Segoe UI, Arial, sans-serif" font-size="14">',
        f'<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    if oracion:
        partes.append(f'<text x="{ancho_total / 2:.1f}" y="26" text-anchor="middle" font-size="16" '
                      f'font-weight="600" fill="#222">{escape(oracion)}</text>')

    lineas, nodos, palabras = [], [], []

    def dibujar(c: _Caja) -> None:
        x = c.x + desplazamiento
        y = y0 + c.nivel * ALTO_NIVEL
        hoja = not c.hijos
        malo = hoja and _con_error(c.nodo, errores)
        relleno, borde = (ROJO_FONDO, ROJO) if malo else COLORES.get(c.nodo.tipo, COLOR_POR_DEFECTO)
        for h in c.hijos:
            lineas.append(f'<line x1="{x:.1f}" y1="{y + ALTO_NODO / 2:.1f}" '
                          f'x2="{h.x + desplazamiento:.1f}" y2="{y0 + h.nivel * ALTO_NIVEL - ALTO_NODO / 2:.1f}" '
                          f'stroke="#9aa5b1" stroke-width="1.5"/>')
        w = _ancho(c.nodo.tipo)
        nodos.append(f'<rect x="{x - w / 2:.1f}" y="{y - ALTO_NODO / 2:.1f}" width="{w:.1f}" height="{ALTO_NODO}" '
                     f'rx="8" fill="{relleno}" stroke="{borde}" stroke-width="1.5"/>'
                     f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" font-weight="600" '
                     f'fill="{borde}">{escape(c.nodo.tipo)}</text>')
        if hoja and _palabra(c.nodo):
            lineas.append(f'<line x1="{x:.1f}" y1="{y + ALTO_NODO / 2:.1f}" x2="{x:.1f}" '
                          f'y2="{y_palabras - 16:.1f}" stroke="#c3cbd4" stroke-width="1.2" stroke-dasharray="3 3"/>')
            palabras.append(f'<text x="{x:.1f}" y="{y_palabras:.1f}" text-anchor="middle" font-size="16" '
                            f'font-weight="{700 if malo else 500}" fill="{ROJO if malo else "#222"}">'
                            f'{escape(_palabra(c.nodo))}</text>')
        for h in c.hijos:
            dibujar(h)

    dibujar(raiz)
    partes += lineas + nodos + palabras
    for i, m in enumerate(mensajes):
        partes.append(f'<text x="20" y="{y_palabras + 40 + i * 22:.1f}" fill="{ROJO}" font-size="13">'
                      f'{escape(m)}</text>')
    partes.append("</svg>")
    return "\n".join(partes) + "\n"


# --- Terminal ------------------------------------------------------------------------------------------

def _escribir(ruta: str, contenido: str) -> None:
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)


def main(argv: Optional[List[str]] = None) -> int:
    try:                                              # que las tildes y las líneas se vean bien en Windows
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser(description="Dibuja el árbol de una oración en español")
    ap.add_argument("oracion", help="oración entre comillas")
    ap.add_argument("--svg", default="salida/arbol.svg", help="dónde guardar el SVG (por defecto: salida/arbol.svg)")
    ap.add_argument("--dot", help="guardar también el árbol en formato DOT (Graphviz)")
    args = ap.parse_args(argv)

    from lexer.espanol import analizar_oracion
    from parser.espanol import analizar

    tokens, tabla, errores_lexicos = analizar_oracion(args.oracion)
    if errores_lexicos:
        for e in errores_lexicos:
            print(f"ERROR léxico, línea {e['linea']}, col {e['columna']}: {e['mensaje']}")
        return 1
    arbol, errores = analizar(tokens, tabla)
    if arbol is None:
        for e in errores:
            print(f"ERROR sintáctico, línea {e['linea']}, col {e['columna']}: {e['mensaje']}")
        return 1

    print(arbol_texto(arbol, errores))
    for e in errores:
        print(f"ERROR {e['fase']}, línea {e['linea']}, col {e['columna']}: {e['mensaje']}")
    _escribir(args.svg, arbol_svg(arbol, errores, args.oracion))
    print(f"\nSVG guardado en {args.svg}")
    if args.dot:
        _escribir(args.dot, arbol_dot(arbol, errores))
        print(f"DOT guardado en {args.dot}")
    return 0 if not errores else 2


if __name__ == "__main__":
    sys.exit(main())
