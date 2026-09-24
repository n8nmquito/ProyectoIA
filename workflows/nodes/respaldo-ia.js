const email = $('Normalizar correo').item.json;
return { json: {
  analisis_ia_fallido: true,
  output: {
    project_id: 1, tracker_id: 3, assigned_to_id: 0, membership_id: 0, role_id: 0, motivo_asignacion: 'Sin asignación automática por fallo de IA o herramientas; revisar en Intaco.',
    resumen: email.asunto || 'Solicitud con adjuntos para revisar',
    descripcion: 'No fue posible completar el análisis automático. Revisar el correo y los archivos adjuntos originales. No se afirma haber interpretado su contenido.',
    categoria: 'otros',
    prioridad: 'normal',
    requiere_revision: true,
    datos_faltantes: ['Revisión humana del correo y sus adjuntos; consultar el error de IA en la ejecución de n8n.'],
  },
} };
