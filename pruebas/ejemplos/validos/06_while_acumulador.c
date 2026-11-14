// ESPERADO: ok
// Caso: ciclo while que acumula una suma
int i = 1;
int suma = 0;
while (i <= 10) {
    suma = suma + i;
    i = i + 1;
}
printf("%d\n", suma);
