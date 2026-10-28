"""Interactive ticket classifier with bilingual session tools."""

import json
import logging
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

from app.presentation import apply_style, heading  # noqa: E402
from app.session_results import (  # noqa: E402
    HISTORY_LIMIT, csv_bytes, remember_prediction,
)
from src.data_processing import combine_text  # noqa: E402
from src.model import load_model, predict_ticket  # noqa: E402
from src.utils import file_hash, load_config  # noqa: E402

LOGGER = logging.getLogger(__name__)
MODEL_SIZES = (10, 100, 200, 300)
EXAMPLES = (
    (
        "Cuenta bloqueada al iniciar sesión en el sistema de gestión",
        "Buenos días, equipo de soporte:\n\n"
        "Desde el inicio de mi jornada no puedo ingresar al sistema de gestión "
        "con mi usuario habitual. Después de varios intentos aparece el mensaje "
        "«La cuenta se encuentra bloqueada. Comuníquese con el administrador». "
        "Ayer podía acceder con normalidad y no solicité cambios de permisos.\n\n"
        "Verifiqué la distribución del teclado, desactivé el bloqueo de "
        "mayúsculas y probé desde otro navegador. También intenté el proceso "
        "de recuperación, pero informa que la cuenta debe ser desbloqueada "
        "por un administrador. Mis compañeros pueden iniciar sesión, por lo "
        "que el inconveniente parece limitado a mi cuenta.\n\n"
        "Necesito registrar las solicitudes pendientes del área. Por favor, "
        "revisen el bloqueo y ayúdenme a recuperar el acceso mediante el "
        "procedimiento de validación de identidad correspondiente. No adjunto "
        "contraseñas ni códigos de verificación. Muchas gracias.",
    ),
    (
        "JDE muestra un error y no guarda las modificaciones de una orden",
        "Hola, equipo de aplicaciones:\n\n"
        "Al editar una orden de compra en JDE, modifico la fecha de entrega "
        "y agrego una observación. Cuando presiono Guardar, la pantalla muestra "
        "«Error al actualizar el registro» y vuelve al listado. Al abrir "
        "nuevamente la orden, ambos campos conservan los valores anteriores.\n\n"
        "Repetí el procedimiento después de cerrar sesión y desde otro "
        "navegador, con el mismo resultado. Una compañera autorizada también "
        "reprodujo el error con otra orden en el ambiente de pruebas. Podemos "
        "consultar registros y acceder a las demás pantallas; el problema "
        "aparece específicamente al guardar estas modificaciones.\n\n"
        "Esto impide actualizar los compromisos con los proveedores. "
        "Solicitamos revisar la validación y el proceso de actualización "
        "de la aplicación. Evitaremos crear órdenes duplicadas o modificar "
        "datos directamente en la base mientras se investiga. Podemos "
        "compartir los pasos de reproducción por el canal de soporte.",
    ),
    (
        "Varios equipos de la oficina perdieron la conexión de red",
        "Buen día, mesa de ayuda:\n\n"
        "Desde hace aproximadamente media hora, varios equipos del mismo "
        "sector no tienen conexión a la red corporativa ni acceso a internet. "
        "No podemos abrir las carpetas compartidas ni comunicarnos con el "
        "servidor de archivos. Las aplicaciones instaladas localmente "
        "continúan funcionando, pero sus conexiones al servidor fallan.\n\n"
        "Comprobamos que los cables de red estén conectados y reiniciamos "
        "uno de los equipos de prueba, sin recuperar la conectividad. "
        "Desde otra oficina sí es posible acceder a esos mismos recursos. "
        "El inconveniente afecta a varios usuarios y no cambia al iniciar "
        "sesión con otra cuenta autorizada.\n\n"
        "Solicitamos revisar el switch del sector, el enlace de red y la "
        "asignación de direcciones. El área tiene detenida la consulta de "
        "documentos compartidos. No modificamos la configuración de los "
        "equipos de comunicaciones ni conectamos dispositivos externos. "
        "Quedamos disponibles para realizar las comprobaciones que indiquen.",
    ),
    (
        "Solicitud de capacitación sobre el circuito de compras en JDE",
        "Hola, equipo de soporte:\n\n"
        "La próxima semana se incorporarán personas al área de compras y "
        "queremos coordinar una capacitación sobre el uso habitual de JDE. "
        "Necesitamos repasar la consulta de órdenes, la interpretación de "
        "sus estados, el registro de observaciones y los canales para "
        "solicitar ayuda cuando una operación no pueda completarse.\n\n"
        "No estamos reportando un error de la aplicación ni una caída del "
        "servicio. Las cuentas actuales funcionan y no solicitamos altas, "
        "cambios de permisos o modificaciones técnicas mediante este correo. "
        "Buscamos orientación y material de referencia para que las nuevas "
        "personas conozcan el procedimiento antes de comenzar a operar.\n\n"
        "¿Podrían indicarnos si existe un manual actualizado y proponer "
        "una fecha para una sesión de aproximadamente una hora? Podemos "
        "utilizar ejemplos ficticios en el ambiente de capacitación y "
        "reunir previamente las consultas del equipo. Gracias por ayudarnos "
        "a organizar la actividad.",
    ),
)
CATEGORIES_EN = {
    "accesos": "Access", "aplicaciones": "Applications",
    "infraestructura": "Infrastructure", "otros": "Other",
}


def tr(spanish, english):
    """Translate interface copy without changing labels learned by the model."""
    return english if st.session_state.get("language") == "English" else spanish


def category_label(category):
    """Display translated labels while keeping exported categories stable."""
    return tr(category.capitalize(), CATEGORIES_EN.get(category, category))


def clear_prediction():
    """Prevent a displayed/exported result from describing edited inputs."""
    for key in ("last_result", "result_model_size", "last_entry"):
        st.session_state.pop(key, None)


def load_example():
    """Cycle through the four Spanish-domain examples before rendering inputs."""
    index = st.session_state.get("example_index", 0)
    title, body = EXAMPLES[index % len(EXAMPLES)]
    st.session_state.update(example_index=index + 1, title=title, body=body)
    clear_prediction()


def clear_history():
    """Remove session history without affecting the currently displayed result."""
    st.session_state.pop("prediction_history", None)
    st.session_state.pop("comparison_ids", None)


@st.cache_resource
def cached_model(path, modified_ns):
    """Reload a model when the selected file changes."""
    return load_model(path)


def read_metrics():
    """Read the separately identified historical diagnostic metrics."""
    try:
        return json.loads((ROOT / "results/metrics/test_metrics.json").read_text(
            encoding="utf-8"))
    except (OSError, ValueError) as exc:
        LOGGER.warning("Métricas no disponibles: %s", exc)
        return None


def read_version_metrics(size):
    """Only show metrics whose model fingerprint matches the selected file."""
    try:
        results = json.loads(
            (ROOT / "results/metrics/version_evaluation.json").read_text(
                encoding="utf-8"))
        path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
        return next((row for row in results["versions"]
                     if row["correos"] == size
                     and row["model_sha256"] == file_hash(path)), None)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        LOGGER.warning("Evaluación no disponible: %s", exc)
        return None


def probability_chart(entries, compare=False):
    """Show actual probability distributions with interactive hover tooltips."""
    rows = [
        {"category": category_label(category), "probability": probability,
         "prediction": f"#{entry.get('id', 1)} · {entry['modelo_correos']} "
                       + tr("correos", "emails")}
        for entry in entries
        for category, probability in entry["probabilidades"].items()
    ]
    chart = alt.Chart(pd.DataFrame(rows)).mark_bar(orient="horizontal").encode(
        x=alt.X("probability:Q", scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%"), title=tr("Probabilidad", "Probability")),
        y=alt.Y("category:N", title=None),
        x2=alt.X2(datum=0),
        color=alt.Color("prediction:N", title=tr("Predicción", "Prediction"),
                        legend=alt.Legend(orient="bottom")),
        tooltip=[alt.Tooltip("category:N", title=tr("Categoría", "Category")),
                 alt.Tooltip("probability:Q", format=".2%",
                             title=tr("Probabilidad", "Probability")),
                 alt.Tooltip("prediction:N", title=tr("Predicción", "Prediction"))],
    )
    if compare:
        chart = chart.encode(yOffset="prediction:N")
    light = st.session_state.get("theme") == "light"
    text_color = "#172b43" if light else "#e1ebf8"
    chart = (
        chart.properties(height=240 if not compare else 330,
                         background="#ffffff" if light else "#0d1218")
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor=text_color, titleColor=text_color,
                        gridColor="#cbd8e8" if light else "#34404e")
        .configure_legend(labelColor=text_color, titleColor=text_color)
        .add_params(alt.selection_interval(bind="scales", encodings=["x"]))
    )
    st.altair_chart(chart, use_container_width=True, theme=None)


def render_history():
    """Compare explicit predictions in the current session and download CSV."""
    st.subheader(tr("Historial de la sesión", "Session history"))
    st.caption(tr(
        f"Se conservan las últimas {HISTORY_LIMIT} predicciones solo en esta sesión. "
        "No se guardan en archivos. El historial se pierde al terminar o reiniciar "
        "la sesión del servidor; una reconexión puede conservarlo temporalmente.",
        f"The latest {HISTORY_LIMIT} predictions are kept only in this session. "
        "They are not written to files. History is lost when the server session "
        "ends or restarts; a reconnection may temporarily retain it."))
    history = st.session_state.get("prediction_history", [])
    if not history:
        st.info(tr("Clasifica un ticket para iniciar el historial.",
                   "Classify a ticket to start the history."))
        return
    records = [{
        "ID": entry["id"], tr("Fecha UTC", "UTC time"): entry["fecha_utc"],
        tr("Título", "Title"): entry["titulo"],
        tr("Correos del modelo", "Training emails"): entry["modelo_correos"],
        tr("Categoría", "Category"): category_label(entry["categoria"]),
        tr("Confianza", "Confidence"): f"{entry['confianza']:.2%}",
        tr("Revisión", "Review"): tr("Sí", "Yes") if entry["requiere_revision"]
        else tr("No", "No"),
    } for entry in history]
    st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
    st.download_button(tr("Descargar historial CSV", "Download history CSV"),
                       csv_bytes(history), "historial_clasificador.csv", "text/csv",
                       key="download_history")
    lookup = {entry["id"]: entry for entry in history}
    ids = st.multiselect(
        tr("Predicciones para comparar", "Predictions to compare"),
        list(lookup), default=list(lookup)[-2:], key="comparison_ids",
        format_func=lambda value: f"#{value} · {lookup[value]['modelo_correos']} · "
                                  f"{lookup[value]['titulo'][:55]}",
    )
    if len(ids) >= 2:
        selected = [lookup[value] for value in ids]
        st.subheader(tr("Comparación de probabilidades", "Probability comparison"))
        probability_chart(selected, compare=True)
        st.caption(tr(
            "Para comparar modelos sobre el mismo ticket, conserva el texto y "
            "vuelve a clasificar con otra versión. Coincidencia y confianza no miden aciertos.",
            "To compare models on the same ticket, keep the text and classify it "
            "again with another version. Agreement and confidence do not measure accuracy."))
    else:
        st.info(tr("Selecciona al menos dos predicciones para compararlas.",
                   "Select at least two predictions to compare them."))
    st.button(tr("Borrar historial", "Clear history"), key="clear_history",
              on_click=clear_history)


def render_about(size, threshold):
    """Explain the actual model, performance evidence and known limitations."""
    st.subheader(tr(f"Modelo seleccionado: {size} correos",
                    f"Selected model: {size} emails"))
    st.code(f"modelo_clasificador_{size}.pkl", language=None)
    st.write(tr(
        "Clasificación supervisada de texto con TF-IDF de palabras y pares de "
        "palabras, seguida de una SVM lineal calibrada. Título y descripción se "
        "validan, limpian y concatenan antes de predecir una de cuatro categorías.",
        "Supervised text classification using word and bigram TF-IDF followed "
        "by a calibrated linear SVM. Title and description are validated, cleaned "
        "and combined before predicting one of four categories."))
    st.caption(tr(
        "El modelo final elegido usa 300 correos. Las versiones de 10, 100 y 200 "
        "permiten comparar predicciones; no son una prueba independiente.",
        "The chosen final model uses 300 emails. The 10, 100 and 200 versions "
        "allow prediction comparisons; they are not an independent test."))
    st.subheader(tr("Variables de entrada y salida", "Input and output variables"))
    st.dataframe(pd.DataFrame([
        {tr("Variable", "Variable"): "titulo", tr("Uso", "Purpose"):
         tr("Texto obligatorio, hasta 255 caracteres.", "Required text, up to 255 characters.")},
        {tr("Variable", "Variable"): "cuerpo", tr("Uso", "Purpose"):
         tr("Texto obligatorio, hasta 16.000 caracteres.", "Required text, up to 16,000 characters.")},
        {tr("Variable", "Variable"): "clasificacion", tr("Uso", "Purpose"):
         tr("Etiqueta de entrenamiento; no se solicita al usuario.",
            "Training label; users do not enter it.")},
    ]), hide_index=True, use_container_width=True)
    try:
        path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
        model = cached_model(str(path), path.stat().st_mtime_ns)
        vectorizer = model.named_steps["tfidf"]
        calibrated = model.named_steps["classifier"]
        svm = calibrated.estimator
        first, second, third = st.columns(3)
        first.metric(tr("Correos usados", "Training emails"), model.training_sample_count_)
        second.metric(tr("Términos TF-IDF", "TF-IDF terms"), len(vectorizer.vocabulary_))
        third.metric(tr("Categorías", "Categories"), len(model.classes_))
        with st.expander(tr("Parámetros y distribución de clases", "Parameters and class distribution")):
            params = {f"TF-IDF: {key}": str(getattr(vectorizer, key))
                      for key in ("ngram_range", "min_df", "max_df", "sublinear_tf",
                                  "norm", "strip_accents")}
            params.update({f"SVM: {key}": str(getattr(svm, key)) for key in
                           ("C", "class_weight", "penalty", "loss", "max_iter", "random_state")})
            params.update({"calibration": f"{calibrated.method} / {calibrated.cv}",
                           tr("Umbral de revisión", "Review threshold"): f"{threshold:.0%}"})
            st.dataframe(pd.DataFrame(params.items(), columns=[tr("Parámetro", "Parameter"),
                                                               tr("Valor", "Value")]),
                         hide_index=True, use_container_width=True)
            st.dataframe(pd.DataFrame([
                {tr("Categoría", "Category"): category_label(key),
                 tr("Correos", "Emails"): int(value)}
                for key, value in model.training_class_counts_.items()
            ]), hide_index=True, use_container_width=True)
    except (OSError, ValueError, AttributeError, KeyError):
        st.info(tr("No se pudieron leer los parámetros del archivo seleccionado.",
                   "Parameters for the selected file could not be read."))
    st.subheader(tr("Métricas de rendimiento", "Performance metrics"))
    metrics = read_version_metrics(size)
    if metrics:
        if metrics["cv_f1_macro"] is not None:
            first, second, third = st.columns(3)
            first.metric("F1 macro CV", f"{metrics['cv_f1_macro']:.4f}")
            second.metric("Accuracy CV", f"{metrics['cv_accuracy']:.1%}")
            third.metric("F1 macro baseline CV", f"{metrics['baseline_cv_f1_macro']:.4f}")
            st.caption(tr(
                "CV exploratoria de cuatro particiones con ajustes ya seleccionados "
                "sobre datos relacionados. No es una evaluación externa ni anidada.",
                "Exploratory four-fold CV with settings already selected on related "
                "data. This is not an external or nested evaluation."))
        else:
            st.info(tr(
                "Con 10 correos no quedan suficientes ejemplos por clase para "
                "la calibración interna de CV; no se inventa una cifra.",
                "With 10 emails there are too few samples per class for internal "
                "CV calibration; no CV score is reported."))
        st.caption(tr(
            f"F1 de entrenamiento: {metrics['train_f1_macro']:.4f}. Mide ajuste "
            "sobre ejemplos conocidos, no generalización.",
            f"Training F1: {metrics['train_f1_macro']:.4f}. It measures fit on "
            "known examples, not generalization."))
        st.write(tr(
            f"De 25 correos sin etiquetas, {metrics['test_25_review_count']} "
            "requieren revisión. Esa prueba no produce accuracy ni F1.",
            f"Of 25 unlabeled emails, {metrics['test_25_review_count']} need "
            "review. This test does not produce accuracy or F1."))
    else:
        st.info(tr("Métricas no disponibles para la huella del modelo actual.",
                   "Metrics are unavailable for the current model fingerprint."))
    historical = read_metrics()
    if historical:
        with st.expander(tr("Métricas del diagnóstico de desarrollo", "Historical development diagnostic")):
            st.metric("F1 macro", f"{historical['f1_macro']:.3f}")
            st.metric("Accuracy", f"{historical['accuracy']:.1%}")
            st.caption(tr(
                "Diagnóstico de 20 casos con modelo entrenado con 280. No "
                "atribuible al archivo final de 300 ni a otros tamaños.",
                "Diagnostic on 20 cases with a model trained on 280. These "
                "results do not apply to the final 300 model or other sizes."))
    st.subheader(tr("Limitaciones y advertencias", "Limitations and warnings"))
    st.warning(tr(
        "La confianza no garantiza acierto. El corpus es pequeño y sintético, "
        "en español y concentrado en soporte TI/JDE/BSSV. No se ha demostrado "
        "generalización a otras empresas ni equidad demográfica. No usar para "
        "conceder accesos, sancionar personas o cerrar incidentes críticos.",
        "Confidence does not guarantee correctness. The dataset is small, "
        "synthetic, in Spanish, and focused on IT/JDE/BSSV support. Generalization "
        "to other organizations and demographic fairness have not been demonstrated. "
        "Do not use it to grant access, penalize people or close critical incidents."))
    st.write(tr(
        "El formulario no envía textos a proveedores de IA ni escribe un "
        "historial en disco. En el portal remoto, los textos sí viajan al VPS y "
        "el historial reside en la memoria de la sesión. Una descarga CSV contiene "
        "los textos ingresados. No introduzcas contraseñas ni información sensible. "
        "El portal usa HTTP y no tiene autenticación.",
        "The form does not send text to AI providers or write history to disk. "
        "On the remote portal, text is sent to the VPS and history is held in "
        "session memory. CSV downloads contain the entered text. Do not enter "
        "passwords or sensitive information. The portal uses HTTP without authentication."))


def main():
    """Render validated inputs, prediction tools and a model information section."""
    st.set_page_config(page_title="Tickets TI | Clasificador", page_icon="🎫", layout="wide")
    st.session_state.setdefault("model_size", 300)
    # Keep user values when translated widget labels produce new widget IDs.
    for key in ("title", "body", "model_size", "theme"):
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    language_column, theme_column = st.columns(2)
    with language_column:
        st.selectbox("Idioma / Language", ("Español", "English"), key="language")
    with theme_column:
        theme_labels = {"dark": tr("Oscuro", "Dark"),
                        "light": tr("Claro", "Light")}
        st.selectbox(tr("Tema", "Theme"), ("dark", "light"), key="theme",
                     format_func=lambda mode: theme_labels[mode])
    apply_style(st.session_state.theme)
    classify_tab, about_tab, history_tab = st.tabs([
        tr("Clasificar", "Classify"), tr("Acerca de", "About"),
        tr("Historial y comparación", "History and comparison"),
    ])
    try:
        config = load_config()
    except ValueError:
        st.error(tr("No se pudo leer la configuración. Consulta al responsable.",
                    "Configuration could not be loaded. Contact the project owner."))
        return
    with classify_tab:
        if st.session_state.language == "English":
            st.info("The interface is available in English. The model was trained "
                    "on Spanish tickets: enter Spanish text or use a built-in example.")
        left, right = st.columns([1.6, 1], gap="medium")
        with left, st.container(border=True, key="ticket-panel"):
            heading(tr("Datos del ticket", "Ticket details"), "document")
            st.button(tr("Prueba con ejemplo", "Try an example"), key="load_example",
                      on_click=load_example, use_container_width=True,
                      icon=":material/description:")
            st.divider()
            email_label = tr("correos", "emails")
            size = st.selectbox(tr("Modelo de clasificación", "Classification model"),
                                MODEL_SIZES, key="model_size",
                                format_func=lambda value: f"{value} {email_label}",
                                on_change=clear_prediction)
            st.text_input(tr("Título", "Title"), key="title", max_chars=255,
                          placeholder=tr("Ej.: Cuenta bloqueada", "E.g.: Cuenta bloqueada"),
                          on_change=clear_prediction)
            st.text_area(tr("Descripción", "Description"), key="body", height=190,
                         max_chars=16000, on_change=clear_prediction,
                         placeholder=tr("Describe el problema o la solicitud.",
                                        "Describe the issue in Spanish."))
            submitted = st.button(tr("Clasificar", "Classify"), key="classify",
                                  type="primary", use_container_width=True,
                                  icon=":material/arrow_forward:")
        with right, st.container(border=True, key="result-panel"):
            heading(tr("Resultado", "Result"), "chart")
            st.divider()
            if submitted:
                clear_prediction()
                try:
                    combine_text(st.session_state.title, st.session_state.body)
                    path = ROOT / "models" / f"modelo_clasificador_{size}.pkl"
                    with st.spinner(tr("Analizando el ticket…", "Analyzing the ticket…")):
                        model = cached_model(str(path), path.stat().st_mtime_ns)
                        result = predict_ticket(model, st.session_state.title,
                                                st.session_state.body,
                                                config["confidence_threshold"])
                    st.session_state.update(last_result=result, result_model_size=size)
                    remember_prediction(st.session_state, st.session_state.title,
                                        st.session_state.body, size, result)
                except FileNotFoundError:
                    st.error(tr(f"Falta el modelo de {size} correos. Consulta al responsable.",
                                f"The {size}-email model is missing. Contact the project owner."))
                except ValueError as exc:
                    st.error(tr(str(exc), "Invalid input or model. Title and description "
                                "must contain letters, within the displayed length limits. "
                                "If the issue persists, contact the project owner."))
                except Exception:
                    LOGGER.exception("Error durante la clasificación")
                    st.error(tr("No pudimos procesar el ticket. Intenta nuevamente o consulta al responsable.",
                                "The ticket could not be processed. Try again or contact the project owner."))
            result = st.session_state.get("last_result")
            if result:
                st.caption(tr(f"Modelo de {st.session_state.result_model_size} correos",
                              f"Model trained on {st.session_state.result_model_size} emails"))
                st.caption(tr("Categoría sugerida", "Suggested category"))
                st.subheader(category_label(result["categoria"]), anchor=False)
                st.metric(tr("Confianza estimada", "Estimated confidence"), f"{result['confianza']:.2%}")
                if result["requiere_revision"]:
                    st.warning(tr("Revisión recomendada: confianza baja o vocabulario desconocido.",
                                  "Review recommended: low confidence or unknown vocabulary."))
                probability_chart([st.session_state.last_entry])
                st.caption(tr("La confianza no garantiza acierto.", "Confidence does not guarantee correctness."))
                st.download_button(tr("Descargar predicción CSV", "Download prediction CSV"),
                                   csv_bytes([st.session_state.last_entry]),
                                   "prediccion.csv", "text/csv", key="download_prediction")
            elif not submitted:
                st.info(tr("Completa los campos y pulsa Clasificar, o usa Prueba con ejemplo.",
                           "Fill in the fields and click Classify, or try an example."))
    with about_tab:
        render_about(size, config["confidence_threshold"])
    with history_tab:
        render_history()


if __name__ == "__main__":
    main()
