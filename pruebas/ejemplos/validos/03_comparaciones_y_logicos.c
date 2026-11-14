// ESPERADO: ok
// Caso: comparaciones y operadores lógicos && || !  (en C el resultado es un int)
int p = 7;
int q = 3;
int mayor = p > q;
int igual = p == q;
int distinto = p != q;
int rango = p >= 5 && q <= 5;
int alguno = p < 0 || q > 0;
int negado = !mayor;
int compuesto = !(p == q) && (q < p || p < 0);

printf("%d\n", rango);
printf("%d\n", alguno);
printf("%d\n", negado);
printf("%d\n", compuesto);
