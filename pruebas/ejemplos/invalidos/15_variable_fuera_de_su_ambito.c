// ESPERADO: error semantico linea 6
// Caso (S8): una variable declarada dentro de un bloque no existe afuera
if (1) {
    int dentro = 1;
}
printf("%d\n", dentro);
