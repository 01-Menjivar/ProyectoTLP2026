"""Tabla de símbolos de mini-C: una pila de ámbitos y su historial."""
from typing import List, Optional


class TablaSimbolos:
    """Busca desde el bloque más cercano y conserva las declaraciones al cerrarlo."""

    def __init__(self):
        self._ambitos = [{}]
        self._identificadores = [0]
        self._siguiente_ambito = 1
        self._historial = []

    def abrir_ambito(self) -> None:
        """Abre un bloque con identificador único, incluso entre bloques hermanos."""
        self._ambitos.append({})
        self._identificadores.append(self._siguiente_ambito)
        self._siguiente_ambito += 1

    def cerrar_ambito(self) -> None:
        """Cierra el bloque actual; el ámbito global nunca se elimina."""
        if len(self._ambitos) == 1:
            raise ValueError("No se puede cerrar el ámbito global")
        self._ambitos.pop()
        self._identificadores.pop()

    def declarar(self, nombre: str, tipo: str, linea: int, *,
                 genero: Optional[str] = None, numero: Optional[str] = None,
                 persona: Optional[int] = None) -> bool:
        """Registra un nombre; devuelve False si ya existe en el ámbito actual."""
        if nombre in self._ambitos[-1]:
            return False
        simbolo = {"nombre": nombre, "tipo": tipo,
                   "ambito": self._identificadores[-1], "linea": linea}
        rasgos = {"genero": genero, "numero": numero, "persona": persona}
        simbolo.update((k, v) for k, v in rasgos.items() if v is not None)
        self._ambitos[-1][nombre] = simbolo
        self._historial.append(simbolo)
        return True

    def buscar(self, nombre: str) -> Optional[dict]:
        """Devuelve el símbolo visible más cercano o None si no está declarado."""
        for ambito in reversed(self._ambitos):
            if nombre in ambito:
                return dict(ambito[nombre])
        return None

    def a_lista(self) -> List[dict]:
        """Devuelve copias de todas las declaraciones válidas, en orden de aparición."""
        return [dict(simbolo) for simbolo in self._historial]
