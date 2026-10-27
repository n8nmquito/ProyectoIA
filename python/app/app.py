"""Streamlit UI for local, advisory ticket classification."""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

from app.presentation import (  # noqa: E402
    apply_style, empty_result, heading,
)
from src.model import load_model, predict_ticket  # noqa: E402
from src.utils import file_hash, load_config  # noqa: E402

LOGGER = logging.getLogger(__name__)
MODEL_SIZES = (10, 100, 200, 300)
EXAMPLES = {
    "Accesos": (
        "Mi usuario está bloqueado",
        "No puedo iniciar sesión con mi cuenta. Necesito restablecer el "
        "acceso.",
    ),
    "Aplicaciones": (
        "Error al guardar una orden",
        "JDE devuelve un error al confirmar la orden de compra y no guarda "
        "los cambios.",
    ),
    "Infraestructura": (
        "Sin conexión de red",
        "Todos los equipos de la oficina perdieron conexión al servidor y "
        "a internet.",
    ),
    "Otros": (
        "Solicitud de capacitación",
        "Necesitamos coordinar una capacitación para aprender a utilizar "
        "el sistema.",
    ),
}


def load_example():
    """Populate widget state before the next Streamlit render."""
    index = st.session_state.get("example_index", 0)
    title, body = list(EXAMPLES.values())[index % len(EXAMPLES)]
    st.session_state["example_index"] = index + 1
    st.session_state["title"] = title
    st.session_state["body"] = body
    st.session_state.pop("last_result", None)


def clear_prediction():
    """Clear the previous prediction when the selected model changes."""
    st.session_state.pop("last_result", None)
    st.session_state.pop("result_model_size", None)


@st.cache_resource
def cached_model(path, modified_ns):
    """Reload a model whenever the underlying file is replaced."""
    return load_model(path)


def read_metrics():
    """Read measured test metrics, or explain why they are unavailable."""
    try:
        return json.loads(
            (ROOT / "results/metrics/test_metrics.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Métricas no disponibles: %s", exc)
        return None


def read_version_metrics(size):
    """Read version-specific measurements only for the current model hash."""
    try:
        path = ROOT / "results/metrics/version_evaluation.json"
        results = json.loads(path.read_text(encoding="utf-8"))
        model_path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
        for row in results["versions"]:
            if row["correos"] == size:
                if row["model_sha256"] == file_hash(model_path):
                    return row
    except (OSError, ValueError, KeyError) as exc:
        LOGGER.warning("Evaluación por versión no disponible: %s", exc)
    return None


def render_model_details(size, threshold):
    """Explain variables and read actual parameters from the selected artifact."""
    st.subheader("Variables de entrada y salida", anchor=False)
    st.dataframe(
        pd.DataFrame([
            {"Variable": "titulo", "Tipo": "Entrada: texto",
             "Uso": "Resumen del problema; obligatorio, hasta 255 caracteres."},
            {"Variable": "cuerpo / descripción", "Tipo": "Entrada: texto",
             "Uso": "Detalle del ticket; obligatorio, hasta 16.000 caracteres."},
            {"Variable": "clasificacion", "Tipo": "Etiqueta de entrenamiento",
             "Uso": "Accesos, aplicaciones, infraestructura u otros. "
                    "No se solicita al clasificar."},
        ]), hide_index=True, use_container_width=True,
    )
    st.write(
        "Título y descripción se unen en un texto. Se normalizan mayúsculas, "
        "espacios y caracteres, se retira HTML y se sustituyen enlaces, "
        "correos, direcciones IP, ciertos nombres de adjuntos y números largos. "
        "Esta limpieza no garantiza anonimización. TF-IDF transforma el texto "
        "en variables numéricas: palabras y pares de palabras del vocabulario."
    )
    st.subheader("Parámetros del modelo seleccionado", anchor=False)
    try:
        path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
        model = cached_model(str(path), path.stat().st_mtime_ns)
        vectorizer = model.named_steps["tfidf"]
        calibrated = model.named_steps["classifier"]
        svm = calibrated.estimator
        first, second, third = st.columns(3)
        first.metric("Correos usados", model.training_sample_count_)
        second.metric("Términos TF-IDF", len(vectorizer.vocabulary_))
        third.metric("Categorías", len(model.classes_))
        rows = [
            ("TF-IDF: ngram_range", str(vectorizer.ngram_range),
             "Incluye palabras individuales y pares consecutivos."),
            ("TF-IDF: min_df", str(vectorizer.min_df),
             "Mínimo de documentos para conservar un término."),
            ("TF-IDF: max_df", str(vectorizer.max_df),
             "Proporción máxima de documentos que contienen el término."),
            ("TF-IDF: sublinear_tf", str(vectorizer.sublinear_tf),
             "Escala logarítmica para reducir el peso de repeticiones."),
            ("TF-IDF: norm", vectorizer.norm,
             "Normalización de la longitud de cada vector."),
            ("TF-IDF: strip_accents", str(vectorizer.strip_accents),
             "Normaliza los acentos al construir el vocabulario."),
            ("SVM: C", str(svm.C),
             "Controla la regularización; mayor C penaliza más los errores."),
            ("SVM: class_weight", str(svm.class_weight),
             "None: sin ponderación automática por clase."),
            ("SVM: penalty / loss", f"{svm.penalty} / {svm.loss}",
             "Penalización de coeficientes y función de pérdida."),
            ("SVM: max_iter", str(svm.max_iter),
             "Límite de iteraciones del ajuste."),
            ("SVM: random_state", str(svm.random_state),
             "Semilla utilizada para reproducibilidad."),
            ("Calibración: método / cv",
             f"{calibrated.method} / {calibrated.cv}",
             "Convierte las puntuaciones SVM en probabilidades estimadas."),
            ("Umbral de revisión", f"{threshold:.0%}",
             "Confianza inferior al umbral o texto sin vocabulario conocido "
             "requieren revisión."),
        ]
        st.dataframe(
            pd.DataFrame(rows, columns=["Parámetro", "Valor", "Qué significa"]),
            hide_index=True, use_container_width=True, height=360,
        )
        with st.expander("Distribución de clases del entrenamiento"):
            st.dataframe(
                pd.DataFrame([
                    {"Categoría": key.capitalize(), "Correos": int(value)}
                    for key, value in model.training_class_counts_.items()
                ]), hide_index=True, use_container_width=True,
            )
        st.caption(
            "Estos valores se leen del archivo seleccionado; el vocabulario "
            "y los coeficientes se aprenden por separado en cada versión. "
            "El umbral de revisión se lee de config.yaml."
        )
    except (OSError, ValueError, AttributeError, KeyError) as exc:
        LOGGER.warning("No se pudieron mostrar los parámetros: %s", exc)
        st.info("No se pudieron leer los parámetros del modelo seleccionado. "
                "Comprueba que su archivo esté disponible.")


def main():
    """Render ticket inputs, predictions and model information."""
    st.set_page_config(
        page_title="Tickets TI | Clasificador", page_icon="🎫", layout="wide"
    )
    apply_style()
    classify_tab, about_tab = st.tabs(
        ["Clasificar", "Modelo y métricas"]
    )
    try:
        config = load_config()
    except ValueError:
        st.error(
            "No se pudo leer la configuración. Revisa config.yaml y "
            "reinicia la aplicación."
        )
        return
    with classify_tab:
        left, right = st.columns([1.6, 1], gap="medium")
        with left, st.container(border=True, key="ticket-panel"):
            title_column, example_column = st.columns([1.4, 1])
            with title_column:
                heading("Datos del ticket", "document")
            with example_column:
                st.button(
                    "Cargar ejemplo", on_click=load_example,
                    use_container_width=True, icon=":material/description:",
                )
            st.divider()
            selected_size = st.selectbox(
                "Modelo de clasificación", MODEL_SIZES, index=3,
                format_func=lambda size: f"{size} correos",
                key="model_size", on_change=clear_prediction,
            )
            st.text_input(
                "Título", key="title", max_chars=255,
                placeholder="Ej.: Cuenta bloqueada",
            )
            st.text_area(
                "Descripción", key="body", height=190, max_chars=16000,
                placeholder="Describe el problema o la solicitud.",
            )
            submitted = st.button(
                "Clasificar", type="primary", use_container_width=True,
                icon=":material/arrow_forward:",
            )
        with right, st.container(border=True, key="result-panel"):
            heading("Resultado", "chart")
            st.divider()
            if submitted:
                st.session_state.pop("last_result", None)
                try:
                    from src.data_processing import combine_text

                    combine_text(st.session_state.title, st.session_state.body)
                    model_path = (ROOT / "models"
                                  / f"modelo_clasificador_{selected_size}.pkl")
                    with st.spinner("Analizando el ticket…"):
                        model = cached_model(
                            str(model_path), model_path.stat().st_mtime_ns
                        )
                        result = predict_ticket(
                            model,
                            st.session_state.title,
                            st.session_state.body,
                            config["confidence_threshold"],
                        )
                    st.session_state.last_result = result
                    st.session_state.result_model_size = selected_size
                except FileNotFoundError:
                    st.error(
                        f"Falta el modelo de {selected_size} correos. Ejecuta "
                        "python -m src.train_versions desde la carpeta "
                        "del proyecto."
                    )
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    LOGGER.exception("Error durante la clasificación")
                    st.error(
                        "No pudimos procesar el ticket. Intenta nuevamente "
                        "o consulta al responsable."
                    )
            result = st.session_state.get("last_result")
            if result:
                st.markdown(
                    '<div class="model-indicator">'
                    f'Modelo de {st.session_state.result_model_size} correos'
                    '</div>', unsafe_allow_html=True,
                )
                st.caption("Categoría sugerida")
                st.subheader(result["categoria"].capitalize(), anchor=False)
                st.metric("Confianza estimada", f"{result['confianza']:.2%}")
                if result["requiere_revision"]:
                    st.warning(
                        "Revisión recomendada: confianza baja o "
                        "vocabulario desconocido."
                    )
                for category, probability in result["probabilidades"].items():
                    st.progress(
                        probability,
                        text=f"{category.capitalize()}: {probability:.2%}",
                    )
                st.caption("La confianza no garantiza acierto.")
            elif not submitted:
                empty_result()
    with about_tab:
        st.subheader(f"Modelo seleccionado: {selected_size} correos")
        st.write(
            f"Este modelo fue entrenado con {selected_size} correos y se "
            "usa para clasificar el título y la descripción que ingreses. "
            "Puedes cambiarlo en el selector de la pestaña Clasificar."
        )
        st.code(f"modelo_clasificador_{selected_size}.pkl", language=None)
        st.caption(
            "Modelo final elegido para el proyecto: 300 correos. "
            "Las versiones de 10, 100 y 200 permiten comparar predicciones."
        )
        st.subheader("Modelos disponibles")
        st.dataframe(
            pd.DataFrame({
                "Correos de entrenamiento": MODEL_SIZES,
                "Archivo": [
                    f"modelo_clasificador_{size}.pkl" for size in MODEL_SIZES
                ],
                "Uso": ["Comparación", "Comparación", "Comparación",
                        "Modelo final del proyecto"],
            }),
            hide_index=True, use_container_width=True,
        )
        st.subheader("Cómo funciona")
        st.write(
            "Título y descripción → limpieza del texto → TF-IDF "
            "(palabras y pares de palabras) → SVM calibrada → categoría "
            "y probabilidades para las cuatro clases. Cada versión "
            "utiliza su propio archivo entrenado."
        )
        render_model_details(selected_size, config["confidence_threshold"])
        st.subheader("Rendimiento del modelo seleccionado")
        version_metrics = read_version_metrics(selected_size)
        if version_metrics:
            if version_metrics["cv_f1_macro"] is not None:
                first, second, third = st.columns(3)
                first.metric("F1 macro CV",
                             f"{version_metrics['cv_f1_macro']:.4f}")
                second.metric("Accuracy CV",
                              f"{version_metrics['cv_accuracy']:.1%}")
                third.metric("F1 macro baseline CV",
                             f"{version_metrics['baseline_cv_f1_macro']:.4f}")
                st.caption(
                    "Validación cruzada exploratoria de cuatro particiones "
                    "sobre el dataset de esta versión. Los ajustes ya habían "
                    "sido elegidos con datos relacionados; no es un test externo."
                )
            else:
                st.info(
                    "Con 10 correos hay clases con solo dos ejemplos. Al "
                    "dividirlos no quedan suficientes para la calibración "
                    "interna; no se presenta una cifra de CV para esta versión."
                )
            st.caption(
                f"F1 sobre sus propios datos de entrenamiento: "
                f"{version_metrics['train_f1_macro']:.4f}. Mide ajuste a "
                "ejemplos conocidos, no generalización."
            )
            st.write(
                f"Prueba de 25 correos: "
                f"{version_metrics['test_25_review_count']} requieren revisión. "
                "No se calcula F1 ni accuracy en esos 25 sin etiquetas humanas."
            )
        else:
            st.info(
                "Ejecuta python -m src.evaluate_versions para generar la "
                "evaluación correspondiente a los archivos actuales."
            )
        st.caption(
            "La confianza de un correo no es el porcentaje de aciertos del modelo."
        )
        metrics = read_metrics()
        if metrics:
            with st.expander("Métricas del diagnóstico de desarrollo"):
                st.caption(
                    "Resultado de una evaluación adicional del proceso de "
                    "desarrollo. No corresponde a una comparación de los "
                    "modelos de 10, 100, 200 y 300 correos ni cambia al "
                    "seleccionar otra versión."
                )
                left, right = st.columns(2)
                left.metric("F1 macro del diagnóstico",
                            f"{metrics['f1_macro']:.3f}")
                right.metric("Accuracy del diagnóstico",
                             f"{metrics['accuracy']:.1%}")
                st.caption(
                    f"Diagnóstico realizado sobre {metrics['n_test']} "
                    "tickets; no atribuir estos valores al modelo "
                    "seleccionado ni usarlos para afirmar generalización."
                )
        st.subheader("Uso responsable")
        st.write(
            "El corpus incluye datos sintéticos y se concentra en JDE/BSSV y "
            "español. "
            "No se ha demostrado equidad demográfica ni generalización a "
            "otras empresas. "
            "No usar para decisiones de seguridad, sanciones, prioridades "
            "automáticas ni cierre de tickets."
        )
        st.write(
            "El código no envía el texto a servicios de IA externos ni lo "
            "escribe en archivos. "
            "En un despliegue remoto, el navegador sí lo transmite al "
            "servidor de la aplicación. "
            "La limpieza básica no sustituye una anonimización revisada."
        )


if __name__ == "__main__":
    main()
