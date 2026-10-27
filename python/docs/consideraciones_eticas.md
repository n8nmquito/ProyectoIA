# Consideraciones éticas y uso responsable

El sistema incluye el clasificador Python de 300 correos, consola/Streamlit,
una API en Docker y un flujo n8n con OpenAI y Redmine. Estas medidas describen
la versión entregada; las mejoras propuestas se distinguen de lo implementado.

## 1. Sesgos del dataset

Los 300 correos son simulados, en español y de un dominio limitado. Los 100
iniciales fueron aportados por el usuario y los 200 posteriores se elaboraron
como ejemplos ficticios para ampliar el corpus. El estilo puede repetirse por categoría y facilitar las
métricas sin representar la variedad de mensajes reales. Hay 70 accesos,
90 aplicaciones, 70 infraestructura y 70 otros.

Pueden perjudicarse usuarios con abreviaturas, redacción breve, variantes del
idioma o problemas poco representados. Los ejemplos ya inspeccionados orientaron
refuerzos posteriores: no son una prueba ciega de generalización. La asociación
del término «referencia omitida» con aplicaciones es una posible señal espuria;
no se ha demostrado su influencia causal. Se conservan los cuatro tamaños y los
errores para revisión; falta validación diversa con personas del área.

## 2. Equidad y fairness

No hay atributos demográficos ni una muestra suficiente para medir equidad
entre grupos de personas. F1 macro y métricas por categoría ayudan a observar
el desempeño entre tipos de ticket, pero no demuestran fairness demográfica.
Se exploró class_weight y el prompt indica no descartar soporte por faltas de
ortografía o mensajes incompletos. Son mitigaciones limitadas, no garantías.
No se debe denegar atención por una categoría o confianza automática.

## 3. Privacidad, servicios externos y redistribución

La autorización para redistribuir los 100 correos
iniciales no está confirmada. Se mantienen sin publicar. La licencia MIT del
código no autoriza por sí sola el corpus ni sus derivados. El .gitignore excluye
raw, processed, datasets de entrenamiento, hoja de revisión y modelos; también
resultados que contienen texto original. Antes de publicar notebooks, capturas,
informes o paquetes debe revisarse que no reproduzcan registros no autorizados.

| Destino | Información que puede recibir |
|---|---|
| API Python dentro de Docker | Título y cuerpo; no adjuntos ni remitente como campos separados |
| OpenAI, a través del agente n8n | Asunto, cuerpo, inventario/nombres de adjuntos y PNG/JPEG/WebP/PDF seleccionados |
| OpenAI mediante herramientas | Respuestas de Redmine sobre proyectos, miembros, nombres, roles y categorías |
| Redmine | Texto original conservado, análisis, remitente, asignación y adjuntos originales |
| Historial de n8n y backups | Entradas, salidas y respuestas de herramientas según la configuración de guardado |
| Resultados locales | Texto y predicciones de consola; evitar compartir información sensible |

Python reemplaza ciertos emails, enlaces, IP, archivos y números largos al
clasificar. **Esa limpieza no anonimiza el correo original que n8n envía a OpenAI.**
No existe un filtro general previo al agente que elimine nombres, contraseñas,
secretos o documentos sensibles. Seleccionar adjuntos por tamaño/formato no
constituye anonimización. La API minimiza campos, pero el cuerpo puede contener
datos personales escritos dentro del texto.

La API requiere X-API-Key, no tiene puerto publicado y se comunica dentro de la
red Docker. Las credenciales permanecen fuera del código y de las exportaciones.
Los accesos públicos actualmente documentados para n8n y Redmine son HTTP; no
se afirma que exista cifrado TLS externo. No se debe introducir información real
confidencial hasta revisar transporte, permisos, retención, acceso a ejecuciones
y condiciones del proveedor. No se ha validado una política de eliminación ni
una auditoría de privacidad del sistema completo.

No se ha demostrado cumplimiento de GDPR, CCPA u otras regulaciones. No se
certifica cumplimiento por tener una API privada o utilizar datos simulados.
Deben determinarse las obligaciones aplicables antes de operar con datos reales.

## 4. Transparencia y explicabilidad

TF-IDF y SVM calibrada aprenden asociaciones de términos, no comprenden el
incidente como una persona. Se muestran probabilidades y términos asociados,
con límites explícitos. SHAP/LIME no están implementados. Los PDP S5 explican
el rendimiento estimado frente a hiperparámetros, no las palabras de un ticket.

OpenAI es un agente aparte que resume y propone categoría, prioridad y
responsable. La predicción Python se compara con esa propuesta; no decide la
categoría final del ticket. Coincidir entre ambos no demuestra exactitud.
El esquema valida formato y catálogos, no la veracidad completa del resumen.

## 5. Impacto social

El beneficio esperado es reducir tareas de lectura y clasificación de soporte.
No se han medido ahorros de tiempo ni satisfacción. Los errores pueden retrasar
la atención, asignar mal una solicitud o crear una falsa sensación de seguridad.
Las consultas de capacitación, planificación o permisos pueden ser ambiguas.
Debe conservarse una vía de atención humana y de corrección de tickets.

Se beneficiarían operadores de mesa de ayuda, personal TI y solicitantes si la
clasificación facilita la derivación. Podrían verse perjudicados solicitantes
con problemas poco representados o mensajes ambiguos, así como personas cuyos
datos aparezcan en correos o adjuntos enviados a servicios externos. Estos
beneficios y perjuicios son potenciales; no se midió su magnitud.

## 6. Responsabilidad, revisión y seguimiento

El equipo de soporte responde por la atención y corrección del ticket. El
responsable funcional define categorías; el equipo técnico mantiene datos,
modelos y flujo. María Quito Castillo es la líder del proyecto y desarrolladora
full stack, correspondiente a los roles Líder del Proyecto y Desarrollador TI
del cronograma. Los demás responsables nominales siguen por completar.

| Rol del cronograma | Responsabilidad ante fallos | Integrante |
|---|---|---|
| Líder del Proyecto | Coordinar revisión, correcciones y decisión de continuidad | María Quito Castillo |
| Desarrollador TI | Revisar integración, errores y versiones del código | María Quito Castillo |
| Data Scientist y Equipo IA | Revisar etiquetas, métricas y propuestas de actualización | &nbsp; |
| Experto Soporte TI y Soporte TI | Validar categorías y revisar derivaciones incorrectas | &nbsp; |
| TI y Mesa de Ayuda | Observar la operación y corregir la atención de tickets | &nbsp; |

Python marca revisión bajo 60 % o sin vocabulario conocido. **En n8n esa señal
no bloquea el alta ni obliga a una revisión humana.** Si el agente marca revisión,
el título lleva [REVISAR] y se aplica prioridad normal. La validación de un
responsable puede dejar el ticket sin asignar. No existe una aprobación humana
obligatoria antes de crear cada ticket ni un aprendizaje automático en línea.

Se conservan hashes, versiones, datasets y ejecuciones. No hay monitoreo
automático de deriva ni una política de auditoría y retención validada. Se
propone revisar semanalmente errores, bloqueos, discrepancias y casos de baja
confianza; la frecuencia y responsables deben confirmarse según el servicio.
Las correcciones deben revisarse antes de incorporarlas a futuros entrenamientos.

### Plan de monitoreo y actualización propuesto

1. Revisar semanalmente una muestra de tickets y los bloqueos, discrepancias
   y avisos de revisión; registrar fecha, versión y corrección humana.
2. Separar problemas de clasificación de fallos de integración y de asignación;
   escalar los incidentes al rol correspondiente de la tabla anterior.
3. Crear un conjunto nuevo autorizado y etiquetado por personas para evaluar
   cambios. Mantener los casos conocidos como regresión, separados del nuevo test.
4. Comparar F1 macro, métricas por clase y baseline antes de promover una versión.
   Conservar modelo, datos, hashes y configuración anteriores para poder revertir.
5. La líder del proyecto coordina la revisión con soporte y desarrollo antes de
   actualizar. La frecuencia y asignación al resto del equipo deben confirmarse.

Este plan no es un monitor automático implementado ni una actividad cuya
ejecución periódica se haya demostrado.

## 7. Uso dual y controles implementados

El sistema podría usarse para ocultar reclamos, vigilar trabajadores o automatizar
decisiones sin revisión. Esos usos no están justificados. El contenido de correos
y adjuntos se trata como entrada no confiable; el prompt prohíbe seguir órdenes
que cambien reglas o permisos. Esto reduce el riesgo, pero no prueba inmunidad
a prompt injection ni evita todas las filtraciones por el agente.

Las herramientas del agente consultan Redmine por GET. El código verifica
proyecto activo, categoría real, membresía y rol asignable. El tipo de ticket se
resuelve por nombre contra el catálogo habilitado; el agente no impone un ID.
El flujo sí crea y asigna tickets y puede enviar avisos; no concede permisos,
revoca cuentas, borra documentos ni resuelve automáticamente el incidente.
Los archivos pickle deben provenir de fuentes confiables.

## 8. Casos en los que no debe usarse

No usar como único criterio para seguridad, incidentes críticos, sanciones,
concesión/revocación de acceso o cierre automático de solicitudes. No asumir
fiabilidad en otros idiomas, dominios, mensajes incompletos o múltiples problemas.
No enviar secretos, datos personales innecesarios o adjuntos confidenciales al
agente sin controles adicionales y autorización.

La evaluación 280/20 no mide de forma independiente el modelo final de 300.
Los mismos 25 casos se utilizan para regresión;
sus etiquetas requieren revisión humana. No permiten afirmar ausencia de
sobreajuste ni generalización a producción. Una confianza alta puede ser errónea.

## Privacidad de la interfaz principal local

Streamlit carga el modelo en esta computadora y se inicia ligado a 127.0.0.1.
El título y cuerpo no se envían a OpenAI, n8n ni a la API del servidor desde
esta aplicación. No se escriben como historial de predicciones. La limpieza no
es anonimización y deben evitarse datos personales y secretos. Las advertencias
son recomendaciones: no garantizan supervisión humana ni una categoría correcta.

El flujo separado de correo/n8n sí puede enviar texto
y adjuntos seleccionados al agente externo y crear tickets. Sus riesgos y
responsabilidades siguen siendo los descritos en las secciones anteriores.
