"""Verifica un árbol de la gramática española v1 (docs/gramatica_espanol.md)."""
from parser.nodo import Nodo
from semantico.tabla_simbolos import TablaSimbolos


def verificar_concordancia(oracion: Nodo, tabla: TablaSimbolos) -> list[dict]:
    """Comprueba un árbol sintácticamente válido usando el léxico de la oración."""
    errores = []

    def rasgos(hoja, requeridos):
        clave = f"{hoja.tipo}:{hoja.valor['lexema'].casefold()}"
        simbolo = tabla.buscar(clave)
        if simbolo is None:
            raise ValueError(f"Falta la entrada léxica {clave}")
        if any(campo not in simbolo for campo in requeridos):
            raise ValueError(f"Rasgos incompletos para {clave}: se requieren {requeridos}")
        return simbolo

    def comparar(nucleo, dependiente, campos):
        origen = rasgos(nucleo, campos)
        destino = rasgos(dependiente, campos)
        for campo in campos:
            if origen[campo] != destino[campo]:
                errores.append({
                    "fase": "semantico",
                    "linea": dependiente.linea,
                    "columna": dependiente.valor["columna"],
                    "mensaje": (f"'{dependiente.valor['lexema']}' discrepa en {campo} "
                                f"con '{nucleo.valor['lexema']}': se esperaba "
                                f"{origen[campo]} y se obtuvo {destino[campo]}"),
                })

    def verificar_sn(sn):
        nucleo = sn.hijos[1]
        for hijo in sn.hijos:
            if hijo.tipo in ("DET", "ADJ"):
                comparar(nucleo, hijo, ("genero", "numero"))
            elif hijo.tipo == "SP":
                verificar_sn(hijo.hijos[1])
        return nucleo

    sujeto, predicado = oracion.hijos
    nucleo = sujeto if sujeto.tipo == "PRON" else verificar_sn(sujeto)
    for hijo in predicado.hijos:
        if hijo.tipo in ("V_PRES", "V_PRET"):
            comparar(nucleo, hijo, ("numero", "persona"))
        elif hijo.tipo == "SN":
            verificar_sn(hijo)
    return errores
