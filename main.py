"""Punto de entrada del compilador Manzana (lo completa P5).

Uso:  python main.py programa.mz [--salida carpeta]
"""
import argparse
import os
import sys


def hay_errores(lista: list) -> bool:
    """Los avisos (mensaje que empieza con 'Aviso:') no cuentan como errores."""
    return any(not e["mensaje"].startswith("Aviso:") for e in lista)


def compilar(ruta_fuente: str, carpeta_salida: str = "salida") -> bool:
    from lexer.lexer import analizar as lexico
    from parser.parser import analizar as sintactico
    from semantico.semantico import analizar as semantico
    from generador.generador import generar
    from generador import reportes

    os.makedirs(carpeta_salida, exist_ok=True)
    salida = lambda nombre: os.path.join(carpeta_salida, nombre)

    with open(ruta_fuente, encoding="utf-8") as f:
        codigo = f.read()

    errores, tabla, ast = [], [], None

    tokens, errs = lexico(codigo)
    errores += errs
    reportes.escribir_tokens(tokens, salida("tokens.txt"))

    if not hay_errores(errores):          # cada fase corre solo si la anterior salió limpia
        ast, errs = sintactico(tokens)
        errores += errs
    if not hay_errores(errores):
        ast, tabla, errs = semantico(ast)
        errores += errs

    reportes.escribir_tabla_simbolos(tabla, salida("tabla_simbolos.txt"))
    reportes.escribir_errores(errores, salida("errores.txt"))

    if hay_errores(errores):
        return False
    with open(salida("programa.py"), "w", encoding="utf-8") as f:
        f.write(generar(ast))
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compilador de Manzana a Python")
    ap.add_argument("archivo", help="programa .mz")
    ap.add_argument("--salida", default="salida", help="carpeta de salida (por defecto: salida)")
    args = ap.parse_args()
    sys.exit(0 if compilar(args.archivo, args.salida) else 1)
