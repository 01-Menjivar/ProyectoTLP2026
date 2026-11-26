"""Métricas cuantitativas, clasificación de errores y gráficas para la evaluación (Fase 2, P2).

Calcula precisión, cobertura (recall), tasa de rechazo correcto, exactitud, F1, tiempos,
clasificación de errores (TP, FP, FN, TN y causas de rechazo) y errores de etiquetado POS
a partir del JSON de resultados generado por `comparacion.ejecutar`.

Uso desde la raíz del repositorio:
    python -m comparacion.metricas --resultados salida/resultados_p2.json --set pruebas/set_p2.json
"""
import argparse
import json
import os
import statistics
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple
from xml.sax.saxutils import escape

from comparacion import formato

_PROPIO_A_UPOS = {
    "PRON": "PRON",
    "DET": "DET",
    "N": "NOUN",
    "ADJ": "ADJ",
    "PREP": "ADP",
    "ADV": "ADV",
    "V_PRES": "VERB",
    "V_PRET": "VERB",
}

_COLORES_SISTEMA = {
    "propio": "#2f5fa8",
    "spacy": "#2e7d4f",
    "hf": "#c66a00",
}
_ORDEN_SISTEMAS = ("propio", "spacy", "hf")


def _div(num: int, den: int) -> Optional[float]:
    return None if den == 0 else round(num / den, 4)


def _fmt_pct(valor: Optional[float]) -> str:
    return "N/A" if valor is None else f"{valor * 100:.1f}%"


def cargar_resultados(ruta: str) -> List[dict]:
    """Lee y valida el archivo de resultados en el formato común."""
    with open(ruta, encoding="utf-8-sig") as f:
        registros = json.load(f)
    if not isinstance(registros, list):
        raise ValueError("El archivo de resultados debe ser una lista JSON")
    formato.validar_todos(registros)
    return registros


def cargar_mapa_set(ruta: Optional[str]) -> Dict[str, dict]:
    """Carga metadatos del set (`fenomeno`, `etiquetas`) indexados por `str(id)`."""
    if not ruta or not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8-sig") as f:
        datos = json.load(f)
    return {str(o["id"]): o for o in datos}


def calcular_confusion(registros: List[dict]) -> dict:
    """Calcula matriz de confusión, métricas de clasificación y tiempos."""
    tp = sum(1 for r in registros if r["esperado"] and r["aceptada"])
    fp = sum(1 for r in registros if not r["esperado"] and r["aceptada"])
    fn = sum(1 for r in registros if r["esperado"] and not r["aceptada"])
    tn = sum(1 for r in registros if not r["esperado"] and not r["aceptada"])
    total = len(registros)

    precision = _div(tp, tp + fp)
    recall = _div(tp, tp + fn)
    f1 = None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = round(2 * precision * recall / (precision + recall), 4)

    tiempos = [r["tiempo_ms"] for r in registros]
    return {
        "total": total,
        "esperadas_aceptar": tp + fn,
        "esperadas_rechazar": tn + fp,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exactitud": _div(tp + tn, total),
        "tasa_rechazo_correcto": _div(tn, tn + fp),
        "tiempo_medio_ms": round(statistics.mean(tiempos), 3) if tiempos else 0.0,
        "tiempo_mediana_ms": round(statistics.median(tiempos), 3) if tiempos else 0.0,
        "tiempo_min_ms": round(min(tiempos), 3) if tiempos else 0.0,
        "tiempo_max_ms": round(max(tiempos), 3) if tiempos else 0.0,
    }


def clasificar_causas_rechazo(registros: List[dict], sistema: str) -> Dict[str, int]:
    """Agrupa los motivos de rechazo reportados en `detalle` según el sistema."""
    conteo: Counter = Counter()
    for r in registros:
        if r["aceptada"]:
            continue
        detalle = r.get("detalle") or ""
        if sistema == "propio":
            fase = detalle.split(" ", 1)[0].split(":", 1)[0].strip() or "sin_detalle"
            conteo[fase] += 1
        elif sistema == "spacy":
            reglas = [parte.strip().split(":", 1)[0] for parte in detalle.split(";") if parte.strip()]
            for regla in (reglas or ["sin_detalle"]):
                conteo[regla] += 1
        elif sistema == "hf":
            if "no está en la gramática" in detalle:
                conteo["etiqueta_fuera_de_gramatica"] += 1
            elif "no encaja en la gramática" in detalle:
                conteo["secuencia_incompatible"] += 1
            else:
                conteo["sin_detalle"] += 1
        else:
            conteo["otro"] += 1
    return dict(sorted(conteo.items()))


def _hojas_en_orden(nodo: dict) -> List[Tuple[str, str]]:
    hijos = nodo.get("hijos") or []
    if not hijos:
        valor = nodo.get("valor")
        lexema = str(valor.get("lexema", "")) if isinstance(valor, dict) else ""
        return [(lexema, nodo.get("tipo", ""))]
    pares: List[Tuple[str, str]] = []
    for h in hijos:
        pares.extend(_hojas_en_orden(h))
    return pares


def _nodos_spacy(nodo: dict) -> List[Tuple[str, str]]:
    valor = nodo.get("valor")
    pares: List[Tuple[str, str]] = []
    if isinstance(valor, dict) and "lexema" in valor and "pos" in valor:
        if valor["pos"] != "PUNCT":
            pares.append((str(valor["lexema"]), str(valor["pos"])))
    for h in (nodo.get("hijos") or []):
        pares.extend(_nodos_spacy(h))
    return pares


def _extraer_upos(sistema: str, oracion: str, arbol: Optional[dict]) -> Optional[List[str]]:
    if not arbol:
        return None
    palabras = [p for p in oracion.rstrip(".").split() if p]
    if sistema == "propio":
        hojas = _hojas_en_orden(arbol)
        etiquetas = [_PROPIO_A_UPOS.get(cat, cat) for _, cat in hojas if cat not in ("PUNTO", "EOF")]
        return etiquetas if len(etiquetas) == len(palabras) else None
    if sistema == "hf":
        hijos = arbol.get("hijos") or []
        etiquetas = []
        for h in hijos:
            tipo = h.get("tipo", "X")
            lexema = str((h.get("valor") or {}).get("lexema", ""))
            if tipo == "PUNCT" or lexema == ".":
                continue
            # aggregation_strategy="simple" puede unir dos palabras seguidas con la misma etiqueta.
            partes = lexema.split() or [lexema]
            etiquetas.extend([tipo] * len(partes))
        return etiquetas if len(etiquetas) == len(palabras) else None
    if sistema == "spacy":
        restantes = _nodos_spacy(arbol)
        if len(restantes) != len(palabras):
            return None
        etiquetas = []
        for palabra in palabras:
            objetivo = palabra.casefold()
            idx = next((i for i, (lex, _) in enumerate(restantes) if lex.casefold() == objetivo), 0)
            _, pos = restantes.pop(idx)
            etiquetas.append(pos)
        return etiquetas
    return None


def evaluar_etiquetado(registros: List[dict], mapa_set: Dict[str, dict], sistema: str) -> Optional[dict]:
    """Compara las etiquetas UPOS del sistema contra las esperadas en `set_p2.json`."""
    if not mapa_set:
        return None
    tokens_eval = 0
    tokens_ok = 0
    oraciones_eval = 0
    ejemplos = []

    for r in registros:
        meta = mapa_set.get(str(r["id"]))
        if not meta or "etiquetas" not in meta:
            continue
        esperadas = meta["etiquetas"]
        predichas = _extraer_upos(sistema, r["oracion"], r.get("arbol"))
        if predichas is None or len(predichas) != len(esperadas):
            continue
        oraciones_eval += 1
        palabras = r["oracion"].rstrip(".").split()
        for palabra, esp, pred in zip(palabras, esperadas, predichas):
            tokens_eval += 1
            if esp == pred:
                tokens_ok += 1
            elif len(ejemplos) < 15:
                ejemplos.append({"id": r["id"], "palabra": palabra, "esperada": esp, "predicha": pred})

    if tokens_eval == 0:
        return None
    return {
        "oraciones_evaluadas": oraciones_eval,
        "tokens_evaluados": tokens_eval,
        "tokens_correctos": tokens_ok,
        "errores_etiquetado": tokens_eval - tokens_ok,
        "exactitud_etiquetado": _div(tokens_ok, tokens_eval),
        "ejemplos_errores": ejemplos,
    }


def resumir_resultados(registros: List[dict], mapa_set: Optional[Dict[str, dict]] = None) -> dict:
    """Genera el diccionario completo de métricas globales, por nivel y de etiquetado."""
    mapa_set = mapa_set or {}
    presentes = [s for s in _ORDEN_SISTEMAS if any(r["sistema"] == s for r in registros)]
    for r in registros:
        if r["sistema"] not in presentes:
            presentes.append(r["sistema"])

    sistemas = {}
    for sistema in presentes:
        rs = [r for r in registros if r["sistema"] == sistema]
        por_nivel = {}
        for nivel in (1, 2, 3):
            rs_nivel = [r for r in rs if r["nivel"] == nivel]
            if rs_nivel:
                por_nivel[str(nivel)] = calcular_confusion(rs_nivel)
        sistemas[sistema] = {
            "global": calcular_confusion(rs),
            "por_nivel": por_nivel,
            "causas_rechazo": clasificar_causas_rechazo(rs, sistema),
            "etiquetado_pos": evaluar_etiquetado(rs, mapa_set, sistema),
            "fallos_oracion": [
                {
                    "id": r["id"],
                    "nivel": r["nivel"],
                    "oracion": r["oracion"],
                    "esperado": r["esperado"],
                    "aceptada": r["aceptada"],
                    "tipo_error": "FP" if r["aceptada"] else "FN",
                    "fenomeno": (mapa_set.get(str(r["id"])) or {}).get("fenomeno"),
                    "detalle": r.get("detalle", ""),
                }
                for r in rs
                if r["aceptada"] != r["esperado"]
            ],
        }
    return {"sistemas": sistemas}


def formatear_tablas_markdown(resumen: dict) -> str:
    """Devuelve tablas en Markdown listas para consola o el informe final."""
    sistemas = resumen["sistemas"]
    lineas = [
        "## Resumen global por sistema",
        "",
        "| Sistema | TP | FP | FN | TN | Precisión | Cobertura (Recall) | F1 | Rechazo correcto | Exactitud | Mediana (ms) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for nombre, datos in sistemas.items():
        g = datos["global"]
        lineas.append(
            f"| {nombre} | {g['tp']} | {g['fp']} | {g['fn']} | {g['tn']} | "
            f"{_fmt_pct(g['precision'])} | {_fmt_pct(g['recall'])} | {_fmt_pct(g['f1'])} | "
            f"{_fmt_pct(g['tasa_rechazo_correcto'])} | {_fmt_pct(g['exactitud'])} | {g['tiempo_mediana_ms']:.3f} |"
        )

    lineas += [
        "",
        "## Exactitud por nivel de complejidad",
        "",
        "| Sistema | Nivel 1 (Simples) | Nivel 2 (Modificadores) | Nivel 3 (Complejas/Fuera CFG) |",
        "|---|---|---|---|",
    ]
    for nombre, datos in sistemas.items():
        celdas = []
        for n in ("1", "2", "3"):
            m = datos["por_nivel"].get(n)
            celdas.append("N/A" if not m else f"{_fmt_pct(m['exactitud'])} ({m['tp'] + m['tn']}/{m['total']})")
        lineas.append(f"| {nombre} | {celdas[0]} | {celdas[1]} | {celdas[2]} |")

    lineas += [
        "",
        "## Errores de etiquetado gramatical (POS) por palabra",
        "",
        "| Sistema | Oraciones evaluadas | Tokens evaluados | Tokens correctos | Errores de etiquetado | Exactitud POS |",
        "|---|---|---|---|---|---|",
    ]
    for nombre, datos in sistemas.items():
        pos = datos.get("etiquetado_pos")
        if not pos:
            lineas.append(f"| {nombre} | N/A | N/A | N/A | N/A | N/A |")
        else:
            lineas.append(
                f"| {nombre} | {pos['oraciones_evaluadas']} | {pos['tokens_evaluados']} | "
                f"{pos['tokens_correctos']} | {pos['errores_etiquetado']} | {_fmt_pct(pos['exactitud_etiquetado'])} |"
            )

    lineas += ["", "## Causas de rechazo registradas", ""]
    for nombre, datos in sistemas.items():
        causas = ", ".join(f"`{k}`: {v}" for k, v in datos["causas_rechazo"].items()) or "ninguna"
        lineas.append(f"- **{nombre}:** {causas}")
    return "\n".join(lineas)


# --- Generación de gráficas SVG (sin dependencias externas) -------------------------------------

def _barras_agrupadas_svg(
    titulo: str,
    categorias: List[str],
    series: List[Tuple[str, List[float], str]],
    sufijo_valor: str = "%",
    max_valor: Optional[float] = 100.0,
) -> str:
    """Construye una gráfica de barras agrupadas en SVG."""
    ancho, alto = 760, 400
    izq, der, arr, aba = 70, 30, 65, 85
    w_area = ancho - izq - der
    h_area = alto - arr - aba

    tope = max_valor if max_valor is not None else max(
        [v for _, vals, _ in series for v in vals] + [1.0]
    ) * 1.15
    tope = max(tope, 1e-6)

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}" style="background:#ffffff;font-family:Segoe UI,Arial,sans-serif">',
        f'<text x="{ancho / 2:.1f}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1f2937">{escape(titulo)}</text>',
    ]

    # Leyenda horizontal arriba
    x_ley = izq
    for nombre, _, color in series:
        partes.append(f'<rect x="{x_ley}" y="40" width="12" height="12" rx="2" fill="{color}"/>')
        partes.append(f'<text x="{x_ley + 17}" y="50" font-size="12" fill="#374151">{escape(nombre)}</text>')
        x_ley += 95 + len(nombre) * 6

    # Rejilla horizontal
    for paso in range(6):
        val = tope * paso / 5
        y = arr + h_area - (val / tope) * h_area
        partes.append(f'<line x1="{izq}" y1="{y:.1f}" x2="{ancho - der}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1"/>')
        etiqueta = f"{val:.0f}{sufijo_valor}" if tope >= 10 else f"{val:.2f}{sufijo_valor}"
        partes.append(f'<text x="{izq - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#6b7280">{escape(etiqueta)}</text>')

    partes.append(f'<line x1="{izq}" y1="{arr}" x2="{izq}" y2="{arr + h_area}" stroke="#9ca3af" stroke-width="1.2"/>')
    partes.append(f'<line x1="{izq}" y1="{arr + h_area}" x2="{ancho - der}" y2="{arr + h_area}" stroke="#9ca3af" stroke-width="1.2"/>')

    n_cat = max(len(categorias), 1)
    n_ser = max(len(series), 1)
    ancho_grupo = w_area / n_cat
    ancho_barra = min(36.0, (ancho_grupo * 0.72) / n_ser)
    margen_grupo = (ancho_grupo - ancho_barra * n_ser) / 2

    for i, cat in enumerate(categorias):
        x_base = izq + i * ancho_grupo
        partes.append(
            f'<text x="{x_base + ancho_grupo / 2:.1f}" y="{arr + h_area + 22}" '
            f'text-anchor="middle" font-size="12" fill="#1f2937">{escape(cat)}</text>'
        )
        for j, (_, vals, color) in enumerate(series):
            val = vals[i] if i < len(vals) else 0.0
            h_bar = (val / tope) * h_area
            x = x_base + margen_grupo + j * ancho_barra
            y = arr + h_area - h_bar
            partes.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho_barra - 3:.1f}" height="{h_bar:.1f}" rx="3" fill="{color}"/>')
            texto_val = f"{val:.1f}" if sufijo_valor == "%" else f"{val:.2f}"
            partes.append(
                f'<text x="{x + (ancho_barra - 3) / 2:.1f}" y="{max(arr + 12, y - 5):.1f}" '
                f'text-anchor="middle" font-size="10" fill="#111827">{texto_val}</text>'
            )

    partes.append("</svg>")
    return "\n".join(partes)


def grafica_metricas_svg(resumen: dict) -> str:
    """Gráfica de barras: Precisión, Cobertura, Rechazo correcto y Exactitud por sistema."""
    categorias = ["Precisión", "Cobertura (Recall)", "Rechazo correcto", "Exactitud"]
    claves = ("precision", "recall", "tasa_rechazo_correcto", "exactitud")
    series = []
    for nombre, datos in resumen["sistemas"].items():
        g = datos["global"]
        vals = [round((g[c] or 0.0) * 100, 1) for c in claves]
        series.append((nombre, vals, _COLORES_SISTEMA.get(nombre, "#5b6b7f")))
    return _barras_agrupadas_svg("Comparación cuantitativa global (%)", categorias, series, "%", 100.0)


def grafica_niveles_svg(resumen: dict) -> str:
    """Gráfica de barras: Exactitud por nivel de complejidad (1, 2 y 3)."""
    categorias = ["Nivel 1 (Simples)", "Nivel 2 (Modificadores)", "Nivel 3 (Complejas)"]
    series = []
    for nombre, datos in resumen["sistemas"].items():
        vals = [
            round(((datos["por_nivel"].get(n) or {}).get("exactitud") or 0.0) * 100, 1)
            for n in ("1", "2", "3")
        ]
        series.append((nombre, vals, _COLORES_SISTEMA.get(nombre, "#5b6b7f")))
    return _barras_agrupadas_svg("Exactitud por nivel lingüístico (%)", categorias, series, "%", 100.0)


def grafica_errores_svg(resumen: dict) -> str:
    """Gráfica de barras: conteo de TP, TN, FP y FN por sistema."""
    categorias = ["Verdadero Pos. (TP)", "Rechazo Corr. (TN)", "Falso Pos. (FP)", "Falso Neg. (FN)"]
    claves = ("tp", "tn", "fp", "fn")
    series = []
    for nombre, datos in resumen["sistemas"].items():
        g = datos["global"]
        vals = [float(g[c]) for c in claves]
        series.append((nombre, vals, _COLORES_SISTEMA.get(nombre, "#5b6b7f")))
    return _barras_agrupadas_svg("Clasificación de decisiones por sistema (oraciones)", categorias, series, "", None)


def grafica_tiempos_svg(resumen: dict) -> str:
    """Gráfica de barras: tiempo mediano y medio (ms) por oración."""
    nombres = list(resumen["sistemas"].keys())
    medianas = [resumen["sistemas"][n]["global"]["tiempo_mediana_ms"] for n in nombres]
    medias = [resumen["sistemas"][n]["global"]["tiempo_medio_ms"] for n in nombres]
    series = [
        ("Mediana (ms)", medianas, "#2f5fa8"),
        ("Media (ms)", medias, "#6b7280"),
    ]
    return _barras_agrupadas_svg("Tiempo de análisis por oración (ms)", nombres, series, " ms", None)


def exportar_reportes(resumen: dict, outdir: str) -> List[str]:
    """Escribe tablas Markdown, JSON de métricas y gráficas SVG (y PNG si hay matplotlib)."""
    os.makedirs(outdir, exist_ok=True)
    archivos = []

    salidas = {
        "metricas_resumen.json": json.dumps(resumen, ensure_ascii=False, indent=2),
        "metricas_tablas.md": formatear_tablas_markdown(resumen),
        "grafica_metricas_sistemas.svg": grafica_metricas_svg(resumen),
        "grafica_aciertos_por_nivel.svg": grafica_niveles_svg(resumen),
        "grafica_errores_sistemas.svg": grafica_errores_svg(resumen),
        "grafica_tiempos_ms.svg": grafica_tiempos_svg(resumen),
    }
    for nombre, contenido in salidas.items():
        ruta = os.path.join(outdir, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        archivos.append(ruta)

    archivos.extend(_intentar_png_matplotlib(resumen, outdir))
    return archivos


def _intentar_png_matplotlib(resumen: dict, outdir: str) -> List[str]:
    """Genera gráficas PNG adicionales solo si matplotlib está instalado."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    sistemas = list(resumen["sistemas"].keys())
    if not sistemas:
        return []

    ruta_png = os.path.join(outdir, "grafica_metricas_sistemas.png")
    claves = ("precision", "recall", "tasa_rechazo_correcto", "exactitud")
    etiquetas = ("Precisión", "Cobertura", "Rechazo corr.", "Exactitud")
    x = list(range(len(etiquetas)))
    ancho = 0.8 / max(len(sistemas), 1)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, nombre in enumerate(sistemas):
        g = resumen["sistemas"][nombre]["global"]
        vals = [(g[c] or 0.0) * 100 for c in claves]
        despl = [xi + (i - (len(sistemas) - 1) / 2) * ancho for xi in x]
        ax.bar(despl, vals, width=ancho, label=nombre, color=_COLORES_SISTEMA.get(nombre))
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas)
    ax.set_ylim(0, 108)
    ax.set_ylabel("Porcentaje (%)")
    ax.set_title("Comparación cuantitativa global (%)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(ruta_png, dpi=150)
    plt.close(fig)
    return [ruta_png]


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser(description="Calcula métricas y gráficas sobre resultados de comparación")
    ap.add_argument("--resultados", default="salida/resultados_p2.json", help="JSON en formato común")
    ap.add_argument("--set", default="pruebas/set_p2.json", help="Set original para analizar fenómeno y POS")
    ap.add_argument("--outdir", default="salida", help="Carpeta donde guardar tablas, JSON y gráficas")
    args = ap.parse_args(argv)

    registros = cargar_resultados(args.resultados)
    mapa_set = cargar_mapa_set(args.set)
    resumen = resumir_resultados(registros, mapa_set)
    archivos = exportar_reportes(resumen, args.outdir)

    print(formatear_tablas_markdown(resumen))
    print("\nArchivos generados:")
    for a in archivos:
        print(" -", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
