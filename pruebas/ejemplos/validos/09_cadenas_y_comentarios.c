// ESPERADO: ok
// Caso: cadenas con escapes y comentarios de línea y de bloque (de varias líneas)
/* Este comentario
   ocupa varias líneas */
int x = 5; // comentario al final de una línea
printf("Valor: %d\n", x);
printf("Comilla: \" y tabulador: \t\n");
char salto = '\n';
