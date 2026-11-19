"""Nodo del árbol de sintaxis (AST). Contrato en docs/contratos.md, sección 3."""
import json
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Nodo:
    tipo: str                                   # Programa, Declaracion, Si, OpBinario, ...
    hijos: List["Nodo"] = field(default_factory=list)
    valor: Any = None                           # nombre, operador o lexema, según el tipo
    linea: int = 0
    tipo_dato: Optional[str] = None             # lo llena el semántico (los literales ya lo traen)

    def a_dict(self) -> dict:
        """Convierte el nodo (y todos sus hijos) a un diccionario listo para JSON."""
        return {
            "tipo": self.tipo,
            "valor": self.valor,
            "linea": self.linea,
            "tipo_dato": self.tipo_dato,
            "hijos": [h.a_dict() for h in self.hijos],
        }

    def a_json(self, indent: int = 2) -> str:
        """Devuelve el árbol como texto JSON."""
        return json.dumps(self.a_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def desde_dict(cls, d: dict) -> "Nodo":
        """Construye un Nodo (con sus hijos) desde un dict como el que produce a_dict().

        Solo "tipo" es obligatorio; las demás claves toman su valor por defecto.
        """
        return cls(
            tipo=d["tipo"],
            hijos=[cls.desde_dict(h) for h in d.get("hijos", [])],
            valor=d.get("valor"),
            linea=d.get("linea", 0),
            tipo_dato=d.get("tipo_dato"),
        )

    @classmethod
    def desde_json(cls, texto: str) -> "Nodo":
        """Construye un Nodo desde un texto JSON (por ejemplo, un archivo de pruebas/ejemplos/ast/)."""
        return cls.desde_dict(json.loads(texto))
