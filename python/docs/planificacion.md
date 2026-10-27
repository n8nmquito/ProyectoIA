# Planificación del sistema de clasificación de tickets TI

El proyecto prueba versiones de 10, 100, 200 y 300 correos y adopta
**modelo_clasificador_300.pkl como modelo final**. Las tres versiones menores
se conservan para comparación; las métricas por versión se detallan en la evaluación actual.

Versión: 27 de octubre de 2026.

## Problema y propósito

Los correos de soporte mezclan consultas sobre cuentas, errores de aplicaciones,
equipos, redes y dudas generales. El operador debe leerlos y decidir quién los
atiende. El proyecto propone una categoría inicial para apoyar esa tarea y
facilitar su supervisión. En la automatización actual, el agente propone la decisión
y el código crea el ticket después de validar los datos de Redmine.

El objetivo general es entregar una capa Python reproducible que permita
entrenar, guardar y probar un clasificador de texto. Los objetivos específicos
son validar el formato de los correos, comparar algoritmos, optimizar ajustes,
conservar versiones por cantidad de datos y mostrar resultados comprensibles.

La relevancia está en reducir trabajo repetitivo y hacer visible cuándo hace
falta revisión manual. No se midieron ahorros de tiempo ni beneficios económicos;
son objetivos de uso futuro, no resultados comprobados.

## Alcance acordado

Incluye cuatro categorías; un JSON maestro de 300 correos simulados; datasets
de 10/100/200/300; cuatro modelos guardados; pruebas por consola con selección
de modelo; entrenamiento y evaluación; gráficos, notebooks y documentación.
También incluye Streamlit, una API Python en Docker y la integración con n8n,
OpenAI y Redmine para registrar solicitudes y comprobar asignaciones.

El flujo desplegado lee el buzón, envía texto y adjuntos seleccionados al agente,
crea tickets y puede enviar avisos. Quedan fuera la resolución automática de
incidentes y la modificación real de permisos/cuentas. La publicación del
repositorio y los videos académicos siguen pendientes. Streamlit continúa local;
la API está desplegada en una red Docker interna.

## Criterios de aceptación y estado real

| Criterio | Evidencia actual |
|---|---|
| Cargar y validar correos | src/data_processing.py y pruebas asociadas |
| Combinar título y cuerpo | combine_text aplicado antes de entrenar o predecir |
| Comparar baseline, LR y SVM | results/metrics/model_comparison.csv |
| Buscar hiperparámetros | grid_search.csv y sensitivity.json |
| Guardar cuatro tamaños exactos | models/ y data/train/; cantidades verificadas |
| Elegir modelo desde CMD | evaluar_nuevos.py --model 10/100/200/300 |
| Mostrar dudas y texto del ticket | requiere_revision y detalle en consola |
| Probar funciones críticas | 51 pruebas automatizadas aprobadas |
| Explicar resultados y límites | seis documentos requeridos y evaluación complementaria |

## Etapas previstas frente al estado realizado

No se conserva un cronograma inicial con fechas aprobadas. La siguiente tabla
organiza el plan por etapas y registra lo comprobado al cierre; no atribuye
duraciones ni fechas de ejecución que no puedan verificarse.

| Etapa prevista | Trabajo | Estado al 26 de octubre de 2026 |
|---|---|---|
| 1. Definición | Categorías, usuarios, alcance y datos | Implementado y documentado |
| 2. Preparación | Validación, limpieza, EDA y particiones | Implementado; corpus actual de 300 |
| 3. Modelado | Referencia, LR y SVM | Comparación disponible |
| 4. Optimización | Búsqueda y sensibilidad | Grilla actual de 24 combinaciones |
| 5. Versiones | 10/100/200/300, guardado y selección | Cuatro modelos y datasets exactos |
| 6. Verificación | Pruebas, errores e interfaz real | 51 pruebas y capturas disponibles |
| 7. Entrega | Revisión del equipo, repositorio y videos | Documentación local lista; datos de entrega pendientes |

## Recursos

Para entrenar se necesita CPU, Python 3.10/3.11 y las dependencias de
requirements.txt. No se usa GPU. La operación integrada necesita servidor Docker,
n8n, Redmine, buzón y credencial OpenAI; puede generar costes de servicio. Las
dependencias principales son pandas, scikit-learn, joblib, Streamlit, pytest,
matplotlib y seaborn. El corpus y los modelos están guardados localmente.

Se requiere que una persona del área revise la definición de categorías y que
los integrantes del equipo validen los resultados y expliquen las decisiones.
No se registró una evaluación con usuarios finales externos.

## Riesgos y tratamiento

| Riesgo | Medida aplicada o pendiente |
|---|---|
| Confundir permisos con fallos de aplicación | Ejemplos contrastados y revisión manual; el riesgo continúa |
| Pocos datos o estilo sintético repetido | Procedencia declarada; se requiere validación real futura |
| Mezclar entrenamiento y prueba | Los 25 permanecen fuera de fit; se comprueban coincidencias exactas |
| Presentar confianza como certeza | Avisos en consola, interfaz y documentación |
| Exponer información sensible | Ejemplos ficticios y limpieza parcial; revisar antes de usar datos reales |
| Perder correspondencia modelo/dataset | Índices, etiquetas, huellas y hashes verificables |
| Cambiar archivos al volver a entrenar | Nombres estables y trazabilidad; conservar versiones antes de cambios importantes |
| Entrega académica incompleta | Lista explícita de autores, repositorio, soporte y videos pendientes |

## Próximo trabajo recomendado

Recoger un conjunto realmente nuevo y autorizado, etiquetado por una persona
que no use las predicciones como respuesta esperada. Mantenerlo separado mientras
se evalúan cambios. Antes de usar el sistema en una organización, acordar
responsables, retención de datos y un proceso de revisión de errores.

## Interfaz de usuario

La interfaz usa Streamlit, opción A de la rúbrica. Permite seleccionar modelos
de 10, 100, 200 o 300 correos, ingresar título y descripción, cargar ejemplos
y mostrar categoría, confianza y cuatro probabilidades. Incluye validación,
indicador de procesamiento, manejo de errores e información del modelo.
La navegación utiliza un selector centrado con Clasificar y Modelo y métricas.
La automatización de correo en n8n funciona como componente separado.
