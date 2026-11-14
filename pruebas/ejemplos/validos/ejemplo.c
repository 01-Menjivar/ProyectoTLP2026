// ESPERADO: ok
// Programa de ejemplo
int manzanas = 3;
float precio = 2.50;
float total = manzanas * precio;

if (total > 5) {
    printf("Compra grande\n");
} else {
    printf("Compra pequeña\n");
}

while (manzanas > 0) {
    manzanas = manzanas - 1;
}
