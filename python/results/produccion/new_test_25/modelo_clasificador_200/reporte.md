# Prueba de correos nuevos

25 entradas con solo título y cuerpo. Modelo entrenado previamente con 200 correos.
El script predice; no reentrena ni añade estos correos al corpus.
Se muestran categorías predichas y confianza. Sin respuestas esperadas no se calculan accuracy ni F1 en esta prueba.

## Alcance

Estos 25 correos son sintéticos del mismo generador que parte del entrenamiento. No tener duplicados exactos no garantiza independencia semántica. Esta prueba pequeña no demuestra ausencia de sobreajuste; se necesita evidencia adicional con tickets reales y etiquetas revisadas por otras personas.