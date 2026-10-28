# Modelos entrenados

Los modelos ya están incluidos en Git. **No necesitas entrenarlos para probar el proyecto.** Se entregan dos series: la referencia evaluada y una copia de los modelos reentrenados del portal de producción.

## Modelo final y versiones de referencia

Estos cuatro archivos coinciden con los hashes de [version_evaluation.json](../results/metrics/version_evaluation.json). El **modelo final de 300** es también el utilizado por NexpAPI en producción.

| Modelo descargable | Correos | Dataset |
|---|---:|---|
| [modelo_clasificador_10.pkl](modelo_clasificador_10.pkl) | 10 | [correos_10.json](../data/train/correos_10.json) |
| [modelo_clasificador_100.pkl](modelo_clasificador_100.pkl) | 100 | [correos_100.json](../data/train/correos_100.json) |
| [modelo_clasificador_200.pkl](modelo_clasificador_200.pkl) | 200 | [correos_200.json](../data/train/correos_200.json) |
| **[modelo_clasificador_300.pkl](modelo_clasificador_300.pkl)** | **300** | [correos_300.json](../data/train/correos_300.json) |

Son pipelines TF-IDF con palabras y pares de palabras y SVM lineal calibrada. Reciben título y cuerpo y devuelven accesos, aplicaciones, infraestructura u otros, con probabilidades. Comparten `C=10`, `class_weight=None`, `min_df=1` y calibración sigmoide de dos particiones. El modelo de 10 es demostrativo y no dispone de CV viable con esta calibración.

## Copias reentrenadas del portal de producción

La carpeta [reentrenados_produccion/](reentrenados_produccion/) conserva los cuatro archivos recogidos del servidor el **28/10/2026**:

- [Modelo reentrenado de 10](reentrenados_produccion/modelo_clasificador_10.pkl).
- [Modelo reentrenado de 100](reentrenados_produccion/modelo_clasificador_100.pkl).
- [Modelo reentrenado de 200](reentrenados_produccion/modelo_clasificador_200.pkl).
- [Modelo reentrenado de 300](reentrenados_produccion/modelo_clasificador_300.pkl).

Sus hashes son distintos de los del reporte de referencia; **sus métricas siguen pendientes de evaluación**. Se guardan aparte para no reemplazar los modelos evaluados. El selector Streamlit no recorre subcarpetas, por lo que estas copias no se mezclan con las opciones principales.

## Cómo obtenerlos y usarlos

Descarga el repositorio completo con Git o con **Code → Download ZIP** en GitHub. Los archivos están en `python/models/`, sin Git LFS ni descargas adicionales:

```bash
git clone https://github.com/n8nmquito/ProyectoIA.git
cd ProyectoIA/python
python -m pip install -r requirements.txt
python -m streamlit run app/app.py
```

Si ya tienes el repositorio, `git pull origin main` obtiene los modelos nuevos; conserva antes cualquier modelo propio que quieras mantener. Para crear y activar un entorno virtual, consulta [Instalación y uso](../README.md#7-instalación-y-uso).

Desde `python/`, prueba una versión de referencia con los 25 correos incluidos:

```bash
python evaluar_nuevos.py --model 10
python evaluar_nuevos.py --model 100
python evaluar_nuevos.py --model 200
python evaluar_nuevos.py --model 300
```

Para probar una copia de producción sin sustituir los modelos principales:

```bash
python evaluar_nuevos.py --model models/reentrenados_produccion/modelo_clasificador_300.pkl --output results/prueba_produccion_300
```

Estos comandos realizan predicciones, no entrenan. Los 25 casos permiten revisión manual; no proporcionan accuracy o F1 sin categorías esperadas validadas. El [manual](../docs/manual_usuario.md) explica la interfaz.

## Integridad y comprobaciones

[manifest.json](manifest.json) identifica la serie, cantidad de correos, dataset, tamaño, hash SHA-256 y estado de evaluación de cada archivo. [SHA256SUMS](SHA256SUMS) permite comprobar las ocho descargas.

En Linux, desde `python/models/`:

```bash
sha256sum -c SHA256SUMS
```

En PowerShell, calcula el hash de un archivo y compáralo con el manifiesto:

```powershell
Get-FileHash .\modelo_clasificador_300.pkl -Algorithm SHA256
```

Se verificaron **los ocho archivos**, su correspondencia con los datasets y **25 predicciones por modelo**: 200 predicciones con cuatro probabilidades válidas, sin reentrenar ni modificar los artefactos. Son comprobaciones de funcionamiento, no nuevas métricas de precisión. Usa las versiones fijadas en `requirements.txt` y carga únicamente modelos de una fuente confiable: pickle puede ejecutar código.

## Volver a entrenar

Los modelos entregados pueden usarse directamente. Si quieres crear una nueva versión, guarda una copia y ejecuta desde `python/`:

```bash
python -m src.train_versions --size 300
```

Cambia `300` por `10`, `100` o `200`; sin `--size` se entrenan los cuatro. Se reemplaza el archivo del tamaño indicado. Después debes actualizar la evaluación y los hashes antes de atribuirle métricas del modelo anterior. Estos pasos no despliegan ni cambian por sí solos NexpAPI o el portal del servidor.
