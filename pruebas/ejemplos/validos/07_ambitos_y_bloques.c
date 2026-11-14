// ESPERADO: ok
// Caso: un bloque abre un ámbito nuevo; se puede reusar un nombre adentro
int x = 1;
{
    int x = 2;
    printf("%d\n", x);
}
printf("%d\n", x);

while (x < 3) {
    int paso = 1;
    x = x + paso;
}
