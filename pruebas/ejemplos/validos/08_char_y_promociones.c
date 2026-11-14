// ESPERADO: ok
// Caso: un char cabe en un int y en un float; un int cabe en un float (promoción)
char letra = 'a';
int codigo = letra;
float real = codigo;
float suma = letra + 1.5;
real = codigo;
printf("%f\n", real);
