"""Nodo del árbol de sintaxis (AST). Contrato en docs/contratos.md (propuesta de P2)."""
import json
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Nodo:
    tipo: str                                   # Programa, Declaracion, Si, OpBinario, ...
    hijos: List["Nodo"] = field(default_factory=list)
    valor: Any = None                           # nombre, operador o lexema, según el tipo
    linea: int = 0
    tipo_dato: Optional[str] = None             # lo llena el semántico (los literales, el parser)

    def a_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "valor": self.valor,
            "linea": self.linea,
            "tipo_dato": self.tipo_dato,
            "hijos": [h.a_dict() for h in self.hijos],
        }

    def a_json(self, indent: int = 2) -> str:
        return json.dumps(self.a_dict(), ensure_ascii=False, indent=indent)
