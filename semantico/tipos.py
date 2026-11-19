"""Reglas de tipos de mini-C: S3 a S7 y S10."""
from typing import List, Optional

from parser.nodo import Nodo


TIPOS_NUMERICOS = {"char", "int", "float"}
JERARQUIA_NUMERICA = {"char": 0, "int": 1, "float": 2}


def asignable(tipo_destino: str, tipo_valor: str) -> bool:
    """Indica si un valor cabe en el destino sin estrechar su tipo."""
    return (tipo_destino in JERARQUIA_NUMERICA and tipo_valor in JERARQUIA_NUMERICA
            and JERARQUIA_NUMERICA[tipo_valor] <= JERARQUIA_NUMERICA[tipo_destino])


def es_numerico(tipo: Optional[str]) -> bool:
    """Indica si el tipo puede participar en operaciones numéricas."""
    return tipo in TIPOS_NUMERICOS


def _error(nodo: Nodo, errores: List[dict], mensaje: str) -> None:
    errores.append({"fase": "semantico", "linea": nodo.linea,
                    "columna": 1, "mensaje": mensaje})


def _tipo_variable(nodo: Nodo, tabla) -> Optional[str]:
    """Obtiene el tipo visible sin repetir el diagnóstico S1."""
    if nodo.tipo_dato is not None:
        return nodo.tipo_dato
    simbolo = tabla.buscar(nodo.valor)
    if simbolo is not None:
        nodo.tipo_dato = simbolo["tipo"]
    return nodo.tipo_dato


def tipo_expresion(nodo: Nodo, tabla, errores: List[dict]) -> Optional[str]:
    """Calcula y anota el tipo de una expresión, o ``None`` si esta es inválida."""
    if nodo.tipo == "Literal":
        return nodo.tipo_dato
    if nodo.tipo == "Variable":
        return _tipo_variable(nodo, tabla)
    if nodo.tipo == "OpUnario":
        tipo_operando = tipo_expresion(nodo.hijos[0], tabla, errores)
        if tipo_operando is None:
            return None
        if nodo.valor == "-":
            if not es_numerico(tipo_operando):
                _error(nodo, errores, "El operador '-' solo acepta operandos numéricos")
                return None
            nodo.tipo_dato = "float" if tipo_operando == "float" else "int"
            return nodo.tipo_dato
        if nodo.valor == "!":
            if not es_numerico(tipo_operando):
                _error(nodo, errores, "El operador '!' solo acepta operandos numéricos")
                return None
            nodo.tipo_dato = "int"
            return nodo.tipo_dato
        raise ValueError(f"Operador unario no soportado: {nodo.valor}")
    if nodo.tipo != "OpBinario":
        raise ValueError(f"Expresión no soportada: {nodo.tipo}")

    tipo_izquierdo = tipo_expresion(nodo.hijos[0], tabla, errores)
    tipo_derecho = tipo_expresion(nodo.hijos[1], tabla, errores)
    if tipo_izquierdo is None or tipo_derecho is None:
        return None

    if nodo.valor in {"+", "-", "*", "/"}:
        if not (es_numerico(tipo_izquierdo) and es_numerico(tipo_derecho)):
            _error(nodo, errores,
                   f"El operador '{nodo.valor}' solo acepta operandos numéricos")
            return None
        nodo.tipo_dato = "float" if "float" in (tipo_izquierdo, tipo_derecho) else "int"
        return nodo.tipo_dato
    if nodo.valor == "%":
        if tipo_izquierdo not in {"char", "int"} or tipo_derecho not in {"char", "int"}:
            _error(nodo, errores, "El operador '%' solo acepta operandos int o char")
            return None
        nodo.tipo_dato = "int"
        return nodo.tipo_dato
    if nodo.valor in {"&&", "||"}:
        if not (es_numerico(tipo_izquierdo) and es_numerico(tipo_derecho)):
            _error(nodo, errores,
                   f"El operador '{nodo.valor}' solo acepta operandos numéricos")
            return None
        nodo.tipo_dato = "int"
        return nodo.tipo_dato
    if nodo.valor in {"==", "!=", "<", ">", "<=", ">="}:
        if not (es_numerico(tipo_izquierdo) and es_numerico(tipo_derecho)):
            _error(nodo, errores,
                   f"La comparación '{nodo.valor}' solo acepta operandos numéricos")
            return None
        nodo.tipo_dato = "int"
        return nodo.tipo_dato
    raise ValueError(f"Operador binario no soportado: {nodo.valor}")
