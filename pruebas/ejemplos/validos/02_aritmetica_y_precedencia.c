// ESPERADO: ok
// Caso: operadores aritméticos, precedencia, paréntesis y signo negativo
int a = 10;
int b = 3;
int suma = a + b;
int resta = a - b;
int producto = a * b;
int cociente = a / b;
int resto = a % b;
int mezcla = 2 + 3 * 4;
int agrupado = (2 + 3) * 4;
int negativo = -a;
float promedio = (a + b) / 2.0;

printf("%d\n", mezcla);
printf("%d\n", agrupado);
printf("%f\n", promedio);
