"""Experimento de evaluación con LLM vía API en modos zero-shot y few-shot (Fase 2).

Evalúa las oraciones de `pruebas/set_p2.json` usando un LLM por API (Gemini, OpenAI o
Anthropic/Claude) únicamente con la biblioteca estándar de Python (`urllib.request`),
sin dependencias externas obligatorias.

Guarda en el repositorio (por defecto en `comparacion/logs_llm/`):
  - `experimento_llm.json`: metadatos, prompts exactos, todas las respuestas crudas y
    parseadas por oración y las métricas comparativas `zero-shot` vs `few-shot`.
  - `reporte_llm.md`: tablas Markdown (reutilizando las fórmulas de `comparacion.metricas`),
    desglose de adherencia a la gramática v1 en Nivel 3 y registro de prompts y fallos.
  - `grafica_llm_zero_vs_few.svg`: gráfica comparativa SVG entre ambos modos.

Uso (desde la raíz del repositorio):
    export GEMINI_API_KEY="tu_api_key"
    python -m comparacion.llm_experimento --proveedor gemini

    export OPENAI_API_KEY="tu_api_key"
    python -m comparacion.llm_experimento --proveedor openai --modelo gpt-4o-mini

    export ANTHROPIC_API_KEY="tu_api_key"
    python -m comparacion.llm_experimento --proveedor anthropic --modelo claude-3-5-haiku-latest
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from comparacion import formato, metricas

PROVEEDORES = ("gemini", "openai", "anthropic")
MODOS = ("zero-shot", "few-shot")

MODELO_POR_DEFECTO = {
    "gemini": "gemini-3.5-flash-lite",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
}

ENV_API_KEY = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

REGLAS_GRAMATICA_V1 = """\
Eres un verificador estricto de una gramática formal restringida del español (versión v1).
NO evalúes si la oración suena natural en español general: SOLO acepta una oración si cumple
EXACTAMENTE las reglas de producción EBNF y las condiciones de concordancia siguientes.

## Reglas de producción (EBNF)
```ebnf
O  ::= ( PRON | SN ) SV
SN ::= DET N { ADJ } [ SP ]
SP ::= PREP SN
SV ::= ( V_PRES | V_PRET ) [ ADV ] SN [ ADV ]
```

## Restricciones sintácticas estrictas de v1
1. Toda oración `O` exige sujeto explícito (`PRON` personal de sujeto o `SN` con `DET N ...`).
   Rechaza oraciones con sujeto tácito o sustantivos sin determinante.
2. El predicado `SV` exige un verbo en presente o pretérito perfecto simple de indicativo
   (`V_PRES` o `V_PRET`) seguido obligatoriamente de un objeto directo (`SN`).
   Rechaza verbos sin objeto directo y órdenes distintos de Sujeto-Verbo-Objeto (como OSV o VSO).
3. Los adjetivos (`ADJ`) solo pueden ir DESPUÉS del sustantivo (`N`), nunca antepuestos.
4. Los adverbios (`ADV`) solo pueden ir dentro de `SV` (inmediatamente después del verbo y/o
   al final de la oración), nunca antes del sujeto.
5. Cada `SP` modifica únicamente al `SN` precedente y exige `PREP SN` completo.
6. No se admiten negación (`no`), coordinación (`y`), cláusulas subordinadas (`que`) ni texto
   sobrante al final. El punto final `.` es opcional.

## Condiciones de concordancia (semántica)
1. En cada `SN` (incluyendo los que estén dentro de un `SP`), `DET` y cada `ADJ` deben compartir
   género (`m`/`f`) y número (`sg`/`pl`) con su propio sustantivo núcleo `N`.
2. El verbo (`V_PRES` o `V_PRET`) debe compartir número (`sg`/`pl`) y persona (`1`, `2` o `3`;
   todo sustantivo `N` es de 3.ª persona; `usted` es 3.ª sg y `ustedes` 3.ª pl) con el `N` o
   `PRON` que encabeza el sujeto principal, ignorando cualquier sustantivo dentro de un `SP`.

## Formato de respuesta obligatorio
Responde ÚNICAMENTE con un objeto JSON válido (sin texto adicional) con estas claves:
{
  "veredicto": "aceptada" o "rechazada",
  "categoria_error": "ninguno" | "sintactico" | "concordancia" | "lexico_o_fuera_v1",
  "motivo": "explicación breve en español basada en las reglas v1"
}"""

# Ejemplos etiquetados para few-shot (ninguna oración se repite en pruebas/set_p2.json).
EJEMPLOS_FEW_SHOT: Tuple[dict, ...] = (
    {
        "oracion": "Él lee una novela.",
        "respuesta": {
            "veredicto": "aceptada",
            "categoria_error": "ninguno",
            "motivo": "Cumple O ::= PRON SV con concordancia 3.ª sg en verbo y femenino sg en SN.",
        },
    },
    {
        "oracion": "La hermana de los niños compró ayer unos cuadros azules.",
        "respuesta": {
            "veredicto": "aceptada",
            "categoria_error": "ninguno",
            "motivo": "Sujeto SN con SP, núcleo 'hermana' (3.ª sg) concuerda con 'compró', adverbio en SV y objeto SN concordante.",
        },
    },
    {
        "oracion": "La hermana de los niños compraron unos cuadros azules.",
        "respuesta": {
            "veredicto": "rechazada",
            "categoria_error": "concordancia",
            "motivo": "El verbo plural 'compraron' discrepa en número con el núcleo del sujeto 'hermana' (sg).",
        },
    },
    {
        "oracion": "Tú miras unas flores amarillos.",
        "respuesta": {
            "veredicto": "rechazada",
            "categoria_error": "concordancia",
            "motivo": "El adjetivo 'amarillos' (m) discrepa en género con el sustantivo 'flores' (f).",
        },
    },
    {
        "oracion": "Escribo una nota breve.",
        "respuesta": {
            "veredicto": "rechazada",
            "categoria_error": "sintactico",
            "motivo": "Aunque es natural en español, falta sujeto explícito; v1 exige O ::= (PRON | SN) SV.",
        },
    },
    {
        "oracion": "Ella leyó la breve nota.",
        "respuesta": {
            "veredicto": "rechazada",
            "categoria_error": "sintactico",
            "motivo": "Adjetivo antepuesto 'breve'; v1 exige SN ::= DET N { ADJ } [ SP ].",
        },
    },
    {
        "oracion": "Mañana nosotros abrimos la tienda.",
        "respuesta": {
            "veredicto": "rechazada",
            "categoria_error": "sintactico",
            "motivo": "Adverbio antes del sujeto; v1 solo permite ADV dentro de SV.",
        },
    },
    {
        "oracion": "El estudiante no trajo el cuaderno.",
        "respuesta": {
            "veredicto": "rechazada",
            "categoria_error": "lexico_o_fuera_v1",
            "motivo": "Contiene negación ('no'), construcción no admitida por la gramática v1.",
        },
    },
)

# Clasificación de fenómenos de Nivel 3 para analizar si el LLM se desvía al español general.
_FENOMENOS_CONCORDANCIA = {
    "concordancia_distancia_numero",
    "concordancia_persona_verbo",
    "concordancia_persona_numero_verbo",
    "concordancia_genero_adjetivo",
    "concordancia_genero_determinante",
    "concordancia_numero_sujeto_verbo",
    "concordancia_numero_adjetivo",
}
_FENOMENOS_VALIDO_ESPANOL_FUERA_V1 = {
    "sujeto_tacito_fuera_cfg",
    "verbo_sin_objeto_fuera_cfg",
    "verbo_sin_objeto_directo",
    "orden_osv_fuera_cfg",
    "orden_vso_fuera_cfg",
    "adjetivo_antepuesto_fuera_cfg",
    "adverbio_preverbal_fuera_cfg",
    "vocabulario_cerrado_negacion",
    "vocabulario_cerrado_coordinacion",
    "vocabulario_cerrado_subordinada",
}


def construir_prompt_sistema(modo: str) -> str:
    """Devuelve el prompt de sistema exacto para `zero-shot` o `few-shot`."""
    if modo == "zero-shot":
        return REGLAS_GRAMATICA_V1
    if modo == "few-shot":
        bloques = [REGLAS_GRAMATICA_V1, "", "## Ejemplos etiquetados"]
        for i, ej in enumerate(EJEMPLOS_FEW_SHOT, 1):
            bloques.append(f'Ejemplo {i}:')
            bloques.append(f'Oración: "{ej["oracion"]}"')
            bloques.append(f'Respuesta: {json.dumps(ej["respuesta"], ensure_ascii=False)}')
        return "\n".join(bloques)
    raise ValueError(f"Modo no soportado: {modo!r}. Usa uno de {MODOS}.")


def construir_prompt_usuario(oracion: str) -> str:
    """Construye el mensaje de usuario para evaluar una oración individual."""
    return f'Evalúa estrictamente según la gramática v1 la siguiente oración:\n"{oracion}"'


def _extraer_json_texto(texto: str) -> Optional[dict]:
    """Intenta extraer un objeto JSON de una respuesta que puede incluir bloques Markdown."""
    limpio = texto.strip()
    bloque = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", limpio, flags=re.DOTALL | re.IGNORECASE)
    candidato = bloque.group(1) if bloque else limpio
    try:
        dato = json.loads(candidato)
        if isinstance(dato, dict):
            return dato
    except json.JSONDecodeError:
        pass
    inicio = candidato.find("{")
    fin = candidato.rfind("}")
    if inicio != -1 and fin > inicio:
        try:
            dato = json.loads(candidato[inicio : fin + 1])
            if isinstance(dato, dict):
                return dato
        except json.JSONDecodeError:
            pass
    return None


def parsear_respuesta_llm(texto: str) -> dict:
    """Normaliza la respuesta cruda del LLM a {aceptada, veredicto, categoria_error, motivo, parse_ok}."""
    dato = _extraer_json_texto(texto)
    if dato is not None and "veredicto" in dato:
        veredicto_raw = str(dato.get("veredicto", "")).strip().casefold()
        if veredicto_raw in ("aceptada", "aceptar", "valida", "válida", "true", "si", "sí"):
            aceptada = True
            veredicto = "aceptada"
        elif veredicto_raw in ("rechazada", "rechazar", "invalida", "inválida", "false", "no"):
            aceptada = False
            veredicto = "rechazada"
        else:
            aceptada = "aceptad" in veredicto_raw and "rechazad" not in veredicto_raw
            veredicto = "aceptada" if aceptada else "rechazada"
        return {
            "aceptada": aceptada,
            "veredicto": veredicto,
            "categoria_error": str(dato.get("categoria_error", "ninguno" if aceptada else "sin_categoria")),
            "motivo": str(dato.get("motivo", "")).strip(),
            "parse_ok": True,
        }

    # Respaldo si el modelo no respetó estrictamente JSON.
    bajo = texto.casefold()
    pos_ac = bajo.find("aceptad")
    pos_re = bajo.find("rechazad")
    if pos_ac != -1 and (pos_re == -1 or pos_ac < pos_re):
        aceptada = True
    elif pos_re != -1:
        aceptada = False
    else:
        aceptada = False
    return {
        "aceptada": aceptada,
        "veredicto": "aceptada" if aceptada else "rechazada",
        "categoria_error": "ninguno" if aceptada else "respuesta_no_json",
        "motivo": texto.strip()[:300],
        "parse_ok": False,
    }


def _http_post_json(url: str, headers: Dict[str, str], payload: dict, timeout: int = 60, reintentos: int = 3) -> dict:
    """Envía una petición POST JSON usando urllib con reintento exponencial ante 429/5xx."""
    cuerpo = json.dumps(payload).encode("utf-8")
    ultimo_error: Optional[Exception] = None
    for intento in range(reintentos):
        req = urllib.request.Request(url, data=cuerpo, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            detalle = err.read().decode("utf-8", errors="replace")
            ultimo_error = RuntimeError(f"HTTP {err.code} en API: {detalle[:400]}")
            if err.code in (429, 500, 502, 503, 504) and intento < reintentos - 1:
                time.sleep(2 ** intento)
                continue
            raise ultimo_error from err
        except (urllib.error.URLError, TimeoutError) as err:
            ultimo_error = RuntimeError(f"Error de red o timeout al consultar API: {err}")
            if intento < reintentos - 1:
                time.sleep(2 ** intento)
                continue
            raise ultimo_error from err
    raise ultimo_error or RuntimeError("Fallo desconocido en la llamada a la API")


def llamar_api_llm(
    proveedor: str,
    modelo: str,
    api_key: str,
    prompt_sistema: str,
    prompt_usuario: str,
    temperatura: float = 0.0,
) -> str:
    """Invoca la API del proveedor elegido y devuelve el texto generado."""
    if proveedor == "gemini":
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{modelo}:generateContent?key={api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": prompt_sistema}]},
            "contents": [{"role": "user", "parts": [{"text": prompt_usuario}]}],
            "generationConfig": {
                "temperature": temperatura,
                "responseMimeType": "application/json",
            },
        }
        resp = _http_post_json(url, {"Content-Type": "application/json"}, payload)
        candidatos = resp.get("candidates") or []
        if not candidatos:
            raise RuntimeError(f"Gemini no devolvió candidatos: {resp}")
        partes = candidatos[0].get("content", {}).get("parts") or []
        return "".join(str(p.get("text", "")) for p in partes)

    if proveedor == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": modelo,
            "temperature": temperatura,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
        }
        resp = _http_post_json(url, headers, payload)
        opciones = resp.get("choices") or []
        if not opciones:
            raise RuntimeError(f"OpenAI no devolvió opciones: {resp}")
        return str(opciones[0].get("message", {}).get("content", ""))

    if proveedor == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": modelo,
            "max_tokens": 300,
            "temperature": temperatura,
            "system": prompt_sistema,
            "messages": [{"role": "user", "content": prompt_usuario}],
        }
        resp = _http_post_json(url, headers, payload)
        bloques = resp.get("content") or []
        if not bloques:
            raise RuntimeError(f"Anthropic no devolvió contenido: {resp}")
        return "".join(str(b.get("text", "")) for b in bloques if b.get("type") == "text")

    raise ValueError(f"Proveedor no soportado: {proveedor!r}. Usa uno de {PROVEEDORES}.")


def ejecutar_modo(
    oraciones: Sequence[dict],
    modo: str,
    invocar_fn: Callable[[str, str], str],
    pausa_seg: float = 0.0,
    mapa_set: Optional[Dict[str, dict]] = None,
) -> List[dict]:
    """Ejecuta un modo (`zero-shot` o `few-shot`) sobre la lista de oraciones."""
    mapa_set = mapa_set or {}
    prompt_sistema = construir_prompt_sistema(modo)
    registros: List[dict] = []
    for idx, o in enumerate(oraciones):
        prompt_usuario = construir_prompt_usuario(o["oracion"])
        t0 = time.perf_counter()
        respuesta_cruda = invocar_fn(prompt_sistema, prompt_usuario)
        ms = round((time.perf_counter() - t0) * 1000, 3)
        parsed = parsear_respuesta_llm(respuesta_cruda)
        fenomeno = (mapa_set.get(str(o["id"])) or {}).get("fenomeno")
        registros.append(
            {
                "id": o["id"],
                "oracion": o["oracion"],
                "nivel": o["nivel"],
                "esperado": o["esperado"],
                "fenomeno": fenomeno,
                "modo": modo,
                "aceptada": parsed["aceptada"],
                "veredicto": parsed["veredicto"],
                "categoria_error": parsed["categoria_error"],
                "motivo": parsed["motivo"],
                "parse_ok": parsed["parse_ok"],
                "respuesta_cruda": respuesta_cruda,
                "tiempo_ms": ms,
            }
        )
        if pausa_seg > 0 and idx < len(oraciones) - 1:
            time.sleep(pausa_seg)
    return registros


def _clasificar_subgrupo_n3(fenomeno: Optional[str]) -> str:
    if fenomeno in _FENOMENOS_CONCORDANCIA:
        return "concordancia"
    if fenomeno in _FENOMENOS_VALIDO_ESPANOL_FUERA_V1:
        return "valido_espanol_fuera_v1"
    return "agramatical_sintactico"


def resumir_experimento(registros_por_modo: Dict[str, List[dict]]) -> dict:
    """Calcula métricas globales, por nivel y desglose de Nivel 3 para cada modo LLM."""
    resumen_modos: Dict[str, dict] = {}
    for modo, rs in registros_por_modo.items():
        por_nivel = {}
        for nivel in (1, 2, 3):
            rs_n = [r for r in rs if r["nivel"] == nivel]
            if rs_n:
                por_nivel[str(nivel)] = metricas.calcular_confusion(rs_n)

        desglose_n3 = {}
        rs_n3 = [r for r in rs if r["nivel"] == 3]
        for subgrupo in ("concordancia", "valido_espanol_fuera_v1", "agramatical_sintactico"):
            sub = [r for r in rs_n3 if _clasificar_subgrupo_n3(r.get("fenomeno")) == subgrupo]
            if sub:
                rechazadas_bien = sum(1 for r in sub if not r["aceptada"])
                desglose_n3[subgrupo] = {
                    "total": len(sub),
                    "rechazadas_correctamente": rechazadas_bien,
                    "falsos_positivos": len(sub) - rechazadas_bien,
                    "tasa_rechazo": metricas._div(rechazadas_bien, len(sub)),
                }

        resumen_modos[modo] = {
            "global": metricas.calcular_confusion(rs),
            "por_nivel": por_nivel,
            "desglose_nivel_3": desglose_n3,
            "respuestas_json_validas": sum(1 for r in rs if r.get("parse_ok")),
            "fallos": [
                {
                    "id": r["id"],
                    "nivel": r["nivel"],
                    "oracion": r["oracion"],
                    "esperado": r["esperado"],
                    "aceptada": r["aceptada"],
                    "tipo_error": "FP" if r["aceptada"] else "FN",
                    "fenomeno": r.get("fenomeno"),
                    "motivo": r.get("motivo", ""),
                }
                for r in rs
                if r["aceptada"] != r["esperado"]
            ],
        }
    return {"modos": resumen_modos}


def grafica_llm_svg(resumen: dict) -> str:
    """Genera una gráfica SVG comparando zero-shot vs few-shot."""
    colores = {"zero-shot": "#7c3aed", "few-shot": "#0d9488"}
    categorias = ["Precisión", "Cobertura (Recall)", "Rechazo correcto", "Exactitud"]
    claves = ("precision", "recall", "tasa_rechazo_correcto", "exactitud")
    series = []
    for modo, datos in resumen["modos"].items():
        g = datos["global"]
        vals = [round((g[c] or 0.0) * 100, 1) for c in claves]
        series.append((modo, vals, colores.get(modo, "#5b6b7f")))
    return metricas._barras_agrupadas_svg(
        "Experimento LLM: zero-shot vs few-shot (%)", categorias, series, "%", 100.0
    )


def formatear_reporte_markdown(resumen: dict, metadatos: dict, prompts: Dict[str, str]) -> str:
    """Construye un reporte Markdown con tablas, análisis de Nivel 3, fallos y prompts."""
    lineas = [
        "# Reporte del experimento con LLM (Zero-shot vs Few-shot)",
        "",
        f"- **Proveedor:** `{metadatos.get('proveedor')}`",
        f"- **Modelo:** `{metadatos.get('modelo')}`",
        f"- **Temperatura:** `{metadatos.get('temperatura')}`",
        f"- **Fecha UTC:** `{metadatos.get('fecha_utc')}`",
        f"- **Set evaluado:** `{metadatos.get('entrada')}` ({metadatos.get('total_oraciones')} oraciones)",
        "",
        "## Resumen global (`zero-shot` vs `few-shot`)",
        "",
        "| Modo | TP | FP | FN | TN | Precisión | Cobertura (Recall) | F1 | Rechazo correcto | Exactitud | Mediana (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for modo, datos in resumen["modos"].items():
        g = datos["global"]
        lineas.append(
            f"| {modo} | {g['tp']} | {g['fp']} | {g['fn']} | {g['tn']} | "
            f"{metricas._fmt_pct(g['precision'])} | {metricas._fmt_pct(g['recall'])} | "
            f"{metricas._fmt_pct(g['f1'])} | {metricas._fmt_pct(g['tasa_rechazo_correcto'])} | "
            f"{metricas._fmt_pct(g['exactitud'])} | {g['tiempo_mediana_ms']:.1f} |"
        )

    lineas += [
        "",
        "## Exactitud por nivel lingüístico",
        "",
        "| Modo | Nivel 1 (Simples) | Nivel 2 (Modificadores) | Nivel 3 (Complejas / Fuera v1) |",
        "|---|---:|---:|---:|",
    ]
    for modo, datos in resumen["modos"].items():
        celdas = []
        for n in ("1", "2", "3"):
            m = datos["por_nivel"].get(n)
            celdas.append("N/A" if not m else f"{metricas._fmt_pct(m['exactitud'])} ({m['tp'] + m['tn']}/{m['total']})")
        lineas.append(f"| {modo} | {celdas[0]} | {celdas[1]} | {celdas[2]} |")

    lineas += [
        "",
        "## Desglose del Nivel 3 (adherencia a v1 vs conocimiento general del español)",
        "",
        "| Modo | Concordancia (8) | Válidas en español pero fuera de v1 (11) | Agramaticales sintácticas (3) |",
        "|---|---:|---:|---:|",
    ]
    for modo, datos in resumen["modos"].items():
        d3 = datos["desglose_nivel_3"]
        celdas = []
        for k in ("concordancia", "valido_espanol_fuera_v1", "agramatical_sintactico"):
            s = d3.get(k)
            if not s:
                celdas.append("N/A")
            else:
                celdas.append(
                    f"{metricas._fmt_pct(s['tasa_rechazo'])} ({s['rechazadas_correctamente']}/{s['total']})"
                )
        lineas.append(f"| {modo} | {celdas[0]} | {celdas[1]} | {celdas[2]} |")

    lineas += ["", "## Fallos registrados por modo", ""]
    for modo, datos in resumen["modos"].items():
        lineas.append(f"### Modo `{modo}` ({len(datos['fallos'])} fallos)")
        lineas.append("")
        if not datos["fallos"]:
            lineas.append("Sin fallos en este modo.")
        else:
            lineas.append("| ID | Nivel | Tipo | Fenómeno | Oración | Motivo del LLM |")
            lineas.append("|---:|---:|---|---|---|---|")
            for f in datos["fallos"]:
                motivo = f["motivo"].replace("|", "/").replace("\n", " ")
                lineas.append(
                    f"| {f['id']} | {f['nivel']} | {f['tipo_error']} | `{f['fenomeno']}` | "
                    f"{f['oracion']} | {motivo} |"
                )
        lineas.append("")

    lineas += ["## Prompts utilizados", ""]
    for modo, texto_prompt in prompts.items():
        lineas.append(f"### Prompt `{modo}`")
        lineas.append("")
        lineas.append("````text")
        lineas.append(texto_prompt)
        lineas.append("````")
        lineas.append("")

    return "\n".join(lineas)


def exportar_experimento(
    registros_por_modo: Dict[str, List[dict]],
    resumen: dict,
    metadatos: dict,
    prompts: Dict[str, str],
    outdir: str,
) -> List[str]:
    """Guarda logs JSON completos, reporte Markdown y gráfica SVG."""
    os.makedirs(outdir, exist_ok=True)
    log_completo = {
        "metadatos": metadatos,
        "prompts": prompts,
        "resumen": resumen,
        "respuestas": registros_por_modo,
    }
    archivos = []
    salidas = {
        "experimento_llm.json": json.dumps(log_completo, ensure_ascii=False, indent=2),
        "reporte_llm.md": formatear_reporte_markdown(resumen, metadatos, prompts),
        "grafica_llm_zero_vs_few.svg": grafica_llm_svg(resumen),
    }
    for nombre, contenido in salidas.items():
        ruta = os.path.join(outdir, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        archivos.append(ruta)
    return archivos


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser(description="Experimento con LLM vía API (zero-shot vs few-shot)")
    ap.add_argument("--proveedor", choices=PROVEEDORES, default="gemini", help="Proveedor de API LLM")
    ap.add_argument("--modelo", default=None, help="Nombre del modelo (opcional; usa el recomendado del proveedor)")
    ap.add_argument("--api-key", default=None, help="API key (si se omite, se lee de la variable de entorno)")
    ap.add_argument("--entrada", default="pruebas/set_p2.json", help="Set de oraciones en JSON")
    ap.add_argument("--modos", nargs="+", choices=MODOS, default=list(MODOS), help="Modos a evaluar")
    ap.add_argument("--outdir", default="comparacion/logs_llm", help="Carpeta para guardar logs y reporte")
    ap.add_argument("--temperatura", type=float, default=0.0, help="Temperatura de generación (default: 0.0)")
    ap.add_argument("--pausa", type=float, default=0.2, help="Pausa en segundos entre llamadas a la API")
    ap.add_argument("--limite", type=int, default=None, help="Evalúa solo las primeras N oraciones (para pruebas)")
    args = ap.parse_args(argv)

    modelo = args.modelo or MODELO_POR_DEFECTO[args.proveedor]
    env_var = ENV_API_KEY[args.proveedor]
    api_key = args.api_key or os.environ.get(env_var)
    if not api_key:
        print(
            f"Falta la API key para '{args.proveedor}'. Configura la variable de entorno {env_var} "
            f"o pásala con --api-key.",
            file=sys.stderr,
        )
        return 2

    oraciones = formato.cargar_oraciones(args.entrada)
    if args.limite is not None:
        oraciones = oraciones[: args.limite]
    mapa_set = metricas.cargar_mapa_set(args.entrada)

    prompts = {modo: construir_prompt_sistema(modo) for modo in args.modos}
    registros_por_modo: Dict[str, List[dict]] = {}

    def invocar(sistema_txt: str, usuario_txt: str) -> str:
        return llamar_api_llm(args.proveedor, modelo, api_key, sistema_txt, usuario_txt, args.temperatura)

    for modo in args.modos:
        print(f"Ejecutando modo '{modo}' con {args.proveedor}/{modelo} sobre {len(oraciones)} oraciones...")
        registros_por_modo[modo] = ejecutar_modo(
            oraciones, modo, invocar, pausa_seg=args.pausa, mapa_set=mapa_set
        )

    resumen = resumir_experimento(registros_por_modo)
    metadatos = {
        "proveedor": args.proveedor,
        "modelo": modelo,
        "temperatura": args.temperatura,
        "entrada": args.entrada,
        "total_oraciones": len(oraciones),
        "modos": list(args.modos),
        "fecha_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    archivos = exportar_experimento(registros_por_modo, resumen, metadatos, prompts, args.outdir)

    print(formatear_reporte_markdown(resumen, metadatos, prompts).split("## Prompts utilizados")[0])
    print("Archivos generados:")
    for a in archivos:
        print(" -", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
