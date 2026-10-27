"""Train, compare and optimize pipelines without fitting on held-out test."""

import argparse
import json
import logging
import platform
from datetime import datetime, timezone

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sklearn
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_validate,
)

from src.data_processing import CLASSES, load_data, split_data
from src.evaluate import evaluate_model
from src.model import build_pipeline, refit_pipeline, top_terms
from src.optimization_analysis import analyze_saved_search
from src.utils import ROOT, file_hash, load_config, project_path, save_json

LOGGER = logging.getLogger(__name__)


def save_figure(fig, name):
    """Export a consistently sized plot and release its resources."""
    fig.tight_layout()
    fig.savefig(ROOT / "documentacion/imagenes" / name, dpi=160)
    plt.close(fig)


def export_eda(frame):
    """Produce six descriptive plots without fitting predictive transforms."""
    lengths = frame["texto"].str.len()
    words = frame["texto"].str.split().str.len()
    labels = frame["clasificacion"]
    summary = {
        "rows": len(frame),
        "class_counts": labels.value_counts().to_dict(),
        "missing": frame.isna().sum().to_dict(),
        "length_characters": lengths.describe().to_dict(),
        "length_words": words.describe().to_dict(),
        "length_outliers_iqr": int(
            (
                lengths
                > lengths.quantile(0.75)
                + 1.5 * (lengths.quantile(0.75) - lengths.quantile(0.25))
            ).sum()
        ),
        "length_correlation": float(lengths.corr(words)),
    }
    save_json(ROOT / "results/metrics/eda.json", summary)
    fig, ax = plt.subplots(figsize=(8, 5))
    labels.value_counts().reindex(CLASSES).plot.bar(
        ax=ax, rot=15, color="#3484b8"
    )
    ax.set(title="Distribución de clases", ylabel="Tickets")
    save_figure(fig, "01_class_distribution.png")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(lengths, bins=14, color="#3484b8")
    ax.set(
        title="Longitud del texto limpio",
        xlabel="Caracteres",
        ylabel="Tickets",
    )
    save_figure(fig, "02_text_lengths.png")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(x=labels, y=words, order=CLASSES, ax=ax)
    ax.set(
        title="Longitud por categoría", ylabel="Palabras", xlabel="Categoría"
    )
    save_figure(fig, "03_words_by_class.png")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(frame["titulo"].str.len(), frame["cuerpo"].str.len(), alpha=0.7)
    ax.set(
        title="Título y cuerpo",
        xlabel="Caracteres del título",
        ylabel="Caracteres del cuerpo",
    )
    save_figure(fig, "04_title_body.png")
    counts = pd.Series(" ".join(frame["texto"]).split()).value_counts()
    fig, ax = plt.subplots(figsize=(8, 6))
    counts.head(18).sort_values().plot.barh(ax=ax, color="#3484b8")
    ax.set(
        title="Términos más frecuentes (incluye palabras funcionales)",
        xlabel="Ocurrencias",
    )
    save_figure(fig, "05_common_terms.png")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        pd.DataFrame(
            {
                "caracteres": lengths,
                "palabras": words,
                "titulo": frame["titulo"].str.len(),
            }
        ).corr(),
        annot=True,
        vmin=-1,
        vmax=1,
        cmap="vlag",
        ax=ax,
    )
    ax.set(title="Correlación de longitudes; no implica causalidad")
    save_figure(fig, "06_length_correlations.png")
    return summary


def analyze_search(results):
    """Estimate grid marginal sensitivity and two-factor interactions."""
    factors = [
        "param_classifier__C",
        "param_classifier__class_weight",
        "param_tfidf__min_df",
    ]
    ranked = []
    for factor in factors:
        data = results.assign(level=results[factor].fillna("none").astype(str))
        marginal = data.groupby("level")["mean_test_score"].mean()
        ranked.append(
            {
                "hyperparameter": factor,
                "range_f1": float(marginal.max() - marginal.min()),
                "marginal_means": marginal.to_dict(),
            }
        )
        fig, ax = plt.subplots(figsize=(7, 5))
        marginal.plot(marker="o", ax=ax)
        ax.set(
            title=f"Dependencia parcial en la grilla: {factor}",
            ylabel="F1 macro CV medio",
            xlabel="Valor del hiperparámetro",
        )
        save_figure(fig, factor.replace("param_", "sensitivity_") + ".png")
    ranked.sort(key=lambda item: item["range_f1"], reverse=True)
    matrix = results.pivot_table(
        index="param_classifier__C",
        columns="param_tfidf__min_df",
        values="mean_test_score",
        aggfunc="mean",
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(matrix, annot=True, fmt=".3f", cmap="Blues", ax=ax)
    ax.set(title="Interacción C × min_df (media sobre pesos de clase)")
    save_figure(fig, "hyperparameter_interaction.png")
    save_json(ROOT / "results/metrics/sensitivity.json", ranked)
    return ranked


def train(config):
    """Run the complete reproducible experiment and save a fitted pipeline."""
    for folder in (
        "data/processed",
        "models",
        "results/metrics",
        "documentacion/imagenes",
        "results/reports",
    ):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    seed = config["seed"]
    source = project_path(config["data_path"])
    frame = load_data(source)
    eda = export_eda(frame)
    manifest = config.get("holdout_manifest")
    train_frame, test_frame = split_data(
        frame,
        config["test_size"],
        seed,
        config["cv_folds"],
        holdout_manifest=project_path(manifest) if manifest else None,
    )
    LOGGER.info(
        "Datos: %d; entrenamiento: %d; prueba: %d",
        len(frame),
        len(train_frame),
        len(test_frame),
    )
    if manifest:
        LOGGER.info(
            "Se conserva el test original como referencia diagnóstica."
        )
    train_frame.to_csv(ROOT / "data/processed/train.csv", index_label="row_id")
    test_frame.to_csv(ROOT / "data/processed/test.csv", index_label="row_id")
    cv = StratifiedKFold(
        n_splits=config["cv_folds"], shuffle=True, random_state=seed
    )
    comparisons = []
    for kind in ("baseline", "logistic", "svm"):
        LOGGER.info("Comparando %s con CV estratificada", kind)
        scores = cross_validate(
            build_pipeline(kind, seed),
            train_frame["texto"],
            train_frame["clasificacion"],
            cv=cv,
            scoring={"f1_macro": "f1_macro", "accuracy": "accuracy"},
            return_train_score=True,
            n_jobs=config["n_jobs"],
            error_score="raise",
        )
        comparisons.append(
            {
                "modelo": kind,
                "f1_macro_cv": float(scores["test_f1_macro"].mean()),
                "f1_std_cv": float(scores["test_f1_macro"].std()),
                "f1_train_cv": float(scores["train_f1_macro"].mean()),
                "accuracy_cv": float(scores["test_accuracy"].mean()),
            }
        )
    searches = {}
    tables = []
    for family in ("logistic", "svm"):
        prefix = (
            "classifier__"
            if family == "logistic"
            else "classifier__estimator__"
        )
        grid = {
            prefix + "C": config["search"]["C"],
            prefix + "class_weight": config["search"]["class_weight"],
            "tfidf__min_df": config["search"]["min_df"],
        }
        candidate = GridSearchCV(
            build_pipeline(family, seed),
            grid,
            scoring="f1_macro",
            cv=cv,
            refit=True,
            n_jobs=config["n_jobs"],
            return_train_score=True,
            error_score="raise",
        )
        LOGGER.info("Optimizando %s", family)
        candidate.fit(train_frame["texto"], train_frame["clasificacion"])
        searches[family] = candidate
        table = pd.DataFrame(candidate.cv_results_)
        table["family"] = family
        if family == "svm":
            table["param_classifier__C"] = table[
                "param_classifier__estimator__C"
            ]
            table["param_classifier__class_weight"] = table[
                "param_classifier__estimator__class_weight"
            ]
        tables.append(table)
        best_row = table.iloc[candidate.best_index_]
        comparisons.append(
            {
                "modelo": family + "_optimized",
                "f1_macro_cv": float(candidate.best_score_),
                "f1_std_cv": float(best_row["std_test_score"]),
                "f1_train_cv": float(best_row["mean_train_score"]),
                "accuracy_cv": None,
            }
        )
    selected_family = max(
        searches, key=lambda name: searches[name].best_score_
    )
    search = searches[selected_family]
    results = pd.concat(tables, ignore_index=True)
    results.to_csv(ROOT / "results/metrics/grid_search.csv", index=False)
    # Calcular la sensibilidad por algoritmo evita mezclar estimadores.
    sensitivity = analyze_search(results[results["family"] == selected_family])
    analyze_saved_search(
        ROOT / "results/metrics/grid_search.csv", selected_family
    )
    best = search.best_estimator_
    before_score = next(
        row["f1_macro_cv"]
        for row in comparisons
        if row["modelo"] == selected_family
    )
    model_path = project_path(config["model_path"])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best, model_path)
    pd.DataFrame(comparisons).to_csv(
        ROOT / "results/metrics/model_comparison.csv", index=False
    )
    final = evaluate_model(
        best, test_frame, ROOT / "results/metrics", ROOT / "documentacion/imagenes"
    )
    # Seleccionar con validación cruzada; reservar el test para evaluar.
    baseline = build_pipeline("baseline", seed).fit(
        train_frame["texto"], train_frame["clasificacion"]
    )
    baseline_test = evaluate_model(baseline, test_frame)
    from sklearn.metrics import f1_score

    train_f1 = float(
        f1_score(
            train_frame["clasificacion"],
            best.predict(train_frame["texto"]),
            average="macro",
        )
    )
    fit_all = config.get("fit_all", False)
    evaluation_path = model_path
    final_frame = train_frame
    if fit_all:
        evaluation_path = None
        train_frame.to_csv(
            ROOT / "data/processed/evaluation_train.csv", index_label="row_id"
        )
        LOGGER.info("Reentrenando el modelo final con %d correos", len(frame))
        best = refit_pipeline(best, frame["texto"], frame["clasificacion"])
        final_frame = frame
        joblib.dump(best, model_path)
        frame.to_csv(ROOT / "data/processed/train.csv", index_label="row_id")
    final["evaluation_model_path"] = (
        str(evaluation_path.relative_to(ROOT)) if evaluation_path else None
    )
    final["evaluation_training_rows"] = len(train_frame)
    final["final_model_training_rows"] = len(final_frame)
    final["applies_to_final_model"] = not fit_all
    save_json(ROOT / "results/metrics/test_metrics.json", final)
    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "source_sha256": file_hash(source),
        "model_sha256": file_hash(model_path),
        "test_sha256": file_hash(ROOT / "data/processed/test.csv"),
        "n_train": len(final_frame),
        "n_evaluation_train": len(train_frame),
        "training_data_path": "data/processed/train.csv",
        "train_sha256": file_hash(ROOT / "data/processed/train.csv"),
        "fit_policy": "full_corpus_refit" if fit_all else "holdout",
        "evaluation_model_path": (
            str(evaluation_path.relative_to(ROOT)) if evaluation_path else None
        ),
        "evaluation_model_sha256": (
            file_hash(evaluation_path) if evaluation_path else None
        ),
        "evaluation_train_sha256": (
            file_hash(ROOT / "data/processed/evaluation_train.csv")
            if fit_all
            else None
        ),
        "n_test": len(test_frame),
        "train_indices": final_frame.index.tolist(),
        "evaluation_train_indices": train_frame.index.tolist(),
        "test_indices": test_frame.index.tolist(),
        "split_policy": "frozen_holdout" if manifest else "stratified",
        "evaluation_scope": (
            "previously_inspected_diagnostic_holdout"
            if manifest
            else "stratified_holdout"
        ),
        "holdout_manifest_sha256": (
            file_hash(project_path(manifest)) if manifest else None
        ),
        "best_params": search.best_params_,
        "best_cv_f1_macro": float(search.best_score_),
        "selected_family": selected_family,
        "before_cv_f1_macro": before_score,
        "cv_improvement": float(search.best_score_ - before_score),
        "evaluation_train_f1_macro": train_f1,
        "train_f1_macro": float(
            f1_score(
                final_frame["clasificacion"],
                best.predict(final_frame["texto"]),
                average="macro",
            )
        ),
        "test_f1_macro": final["f1_macro"],
        "baseline_test_f1_macro": baseline_test["f1_macro"],
        "baseline_test_accuracy": baseline_test["accuracy"],
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
        "config": config,
        "top_terms": top_terms(best),
    }
    save_json(ROOT / "results/metrics/training_summary.json", summary)
    save_json(
        ROOT / "results/metrics/baseline_test_metrics.json", baseline_test
    )
    save_json(
        ROOT / "results/metrics/versions.json",
        {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
    )
    report = [
        "# Informe de ejecución",
        "",
        "Resultados medidos; no estimaciones de producción.",
        "",
        f"Train: {len(train_frame)}; test: {len(test_frame)}; clases: "
        f"{eda['class_counts']}.",
        f"Modelo final: {len(final_frame)} correos. "
        f"Modelo de evaluación: {len(train_frame)} correos.",
        "Las métricas de test corresponden al modelo de evaluación. "
        "Si el modelo final usa todo el corpus, no tiene test independiente.",
        f"F1 macro CV antes: {summary['before_cv_f1_macro']:.4f}; después: "
        f"{search.best_score_:.4f}.",
        f"Cambio absoluto de F1 CV: {summary['cv_improvement']:.4f}.",
        f"Accuracy test: {final['accuracy']:.4f}; F1 macro test: "
        f"{final['f1_macro']:.4f}.",
        f"Baseline test F1 macro: {baseline_test['f1_macro']:.4f}.",
        f"F1 train: {train_f1:.4f}. Una brecha train/CV/test sugiere "
        f"sobreajuste.",
        f"Parámetros: `{json.dumps(search.best_params_)}`.",
        "",
        "## Sensibilidad (amplitud de medias marginales; no causal)",
        "",
    ]
    report.extend(
        f"- {row['hyperparameter']}: {row['range_f1']:.4f}"
        for row in sensitivity
    )
    if manifest:
        report.extend(
            [
                "",
                "## Alcance de evaluación",
                "",
                "El test original ya se examinó durante el desarrollo. "
                "Se conserva fuera de entrenamiento como referencia "
                "diagnóstica; "
                "no es una validación nueva independiente de la ampliación.",
            ]
        )
    errors = pd.read_csv(
        ROOT / "results/metrics" / final["artifact_files"]["errors"]
    )
    report.extend(["", "## Errores de test", ""])
    if errors.empty:
        report.append(
            "No hubo errores en este test pequeño. No demuestra "
            "perfección; ampliar evaluación externa."
        )
    for row in errors.itertuples():
        report.append(
            f"- Fila {row.row_id}: real {row.real}; predicha "
            f"{row.predicha}; confianza {row.confianza:.3f}. "
            "Consultar el texto local en test.csv; revisar ambigüedad y "
            "vocabulario."
        )
    (ROOT / "results/reports/evaluation.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    LOGGER.info(
        "Modelo final guardado: %s; entrenado con %d correos",
        model_path,
        len(final_frame),
    )
    LOGGER.info(
        "Evaluación del modelo de %d correos: F1 macro %.3f",
        len(train_frame),
        final["f1_macro"],
    )
    return summary


def main():
    """Parse an optional YAML configuration and report actionable failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None)
    parser.add_argument(
        "--fit-all",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Reentrenar el modelo final con todo el corpus tras evaluar.",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    try:
        config = load_config(args.config)
        if args.fit_all is not None:
            config["fit_all"] = args.fit_all
        train(config)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Error de entrenamiento: {exc}\n")


if __name__ == "__main__":
    main()
