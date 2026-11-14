// ESPERADO: ok
// Caso: if / else anidados
int nota = 85;
if (nota >= 90) {
    printf("Excelente\n");
} else {
    if (nota >= 60) {
        printf("Aprobado\n");
    } else {
        printf("Reprobado\n");
    }
}
