"""Analyze saved hyperparameter trials with the Workshop S5 surrogate."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict

from src.utils import ROOT, file_hash, save_json


def analyze_saved_search(path, family="svm", output_dir=None, figure_dir=None):
    """Fit a surrogate of CV scores, without training a ticket classifier."""
    output_dir = output_dir or ROOT / "results/metrics"
    figure_dir = figure_dir or ROOT / "documentacion/imagenes"
    output_dir, figure_dir = Path(output_dir), Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    try:
        trials = pd.read_csv(path)
        trials = trials.loc[trials["family"] == family].copy()
        if len(trials) < 6:
            raise ValueError(
                "Se requieren al menos seis configuraciones de la familia."
            )
        features = pd.DataFrame(
            {
                "log10_C": np.log10(
                    pd.to_numeric(trials["param_classifier__C"])
                ),
                "class_weight_balanced": (
                    trials["param_classifier__class_weight"].fillna("none")
                    == "balanced"
                ).astype(int),
                "min_df": pd.to_numeric(trials["param_tfidf__min_df"]),
            }
        )
        scores = pd.to_numeric(trials["mean_test_score"])
        if (
            not np.isfinite(features.to_numpy()).all()
            or not np.isfinite(scores).all()
        ):
            raise ValueError("La grilla contiene valores no finitos.")
    except (OSError, KeyError, TypeError) as exc:
        raise ValueError(
            "No se pudo leer una grilla válida de hiperparámetros."
        ) from exc
    surrogate = RandomForestRegressor(
        n_estimators=300, max_depth=3, random_state=42, n_jobs=1
    )
    loo_predictions = cross_val_predict(
        surrogate, features, scores, cv=LeaveOneOut(), n_jobs=1
    )
    surrogate.fit(features, scores)
    importance = permutation_importance(
        surrogate,
        features,
        scores,
        scoring="neg_mean_absolute_error",
        n_repeats=40,
        random_state=42,
        n_jobs=1,
    )
    ranking = sorted(
        [
            {
                "parameter": name,
                "mdi": float(surrogate.feature_importances_[i]),
                "permutation_mae_increase": float(
                    importance.importances_mean[i]
                ),
                "permutation_std": float(importance.importances_std[i]),
            }
            for i, name in enumerate(features.columns)
        ],
        key=lambda row: row["permutation_mae_increase"],
        reverse=True,
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    PartialDependenceDisplay.from_estimator(
        surrogate,
        features,
        [0, 1, 2],
        ax=axes,
        grid_resolution=3,
        percentiles=(0, 1),
    )
    axes[0].set_xticks([-1, 0, 1], ["0.1", "1", "10"])
    axes[0].set_xlabel("C (escala logarítmica)")
    axes[1].set_xticks([0, 1], ["None", "balanced"])
    axes[1].set_xlabel("class_weight")
    axes[2].set_xticks([1, 2])
    for ax in axes:
        ax.set_ylabel("F1 macro CV estimado")
    fig.suptitle("S5: dependencia parcial del F1 CV estimado por el sustituto")
    fig.tight_layout()
    fig.savefig(figure_dir / "s5_pdp_hiperparametros.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 5))
    PartialDependenceDisplay.from_estimator(
        surrogate,
        features,
        [(0, 2)],
        ax=ax,
        grid_resolution=3,
        percentiles=(0, 1),
    )
    fig.suptitle("S5: interacción log10(C) y min_df en el sustituto")
    fig.tight_layout()
    fig.savefig(figure_dir / "s5_pdp_interaccion.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(
        [r["parameter"] for r in ranking][::-1],
        [r["permutation_mae_increase"] for r in ranking][::-1],
    )
    ax.set(
        xlabel="Aumento de MAE al permutar (sobre las 12 configuraciones)",
        title="S5: importancia de hiperparámetros en el sustituto",
    )
    fig.tight_layout()
    fig.savefig(figure_dir / "s5_importancia_hiperparametros.png", dpi=160)
    plt.close(fig)
    report = {
        "source_sha256": file_hash(path),
        "family": family,
        "n_trials": len(trials),
        "surrogate": "RandomForestRegressor",
        "surrogate_parameters": {
            "n_estimators": 300,
            "max_depth": 3,
            "random_state": 42,
        },
        "target": "mean_test_score: F1 macro de validación cruzada",
        "encoding": {
            "C": "log10(C)",
            "class_weight": "None=0, balanced=1",
            "min_df": "1 o 2",
        },
        "loo_mae": float(mean_absolute_error(scores, loo_predictions)),
        "loo_r2": float(r2_score(scores, loo_predictions)),
        "observed_score_min": float(scores.min()),
        "observed_score_max": float(scores.max()),
        "ranking": ranking,
        "limitations": [
            "Solo 12 configuraciones; el sustituto es una aproximación exploratoria.",
            "La importancia por permutación se calcula sobre las configuraciones ajustadas, no en una muestra independiente.",
            "Los PDP explican el rendimiento estimado frente a hiperparámetros, no palabras ni causas de un ticket.",
            "No se reentrenó ni se modificó ninguno de los cuatro clasificadores.",
        ],
    }
    save_json(output_dir / "s5_surrogate_analysis.json", report)
    pd.DataFrame(ranking).to_csv(
        output_dir / "s5_hyperparameter_importance.csv", index=False
    )
    return report


def main():
    """Generate Workshop S5 figures from the saved GridSearchCV results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--grid", default=str(ROOT / "results/metrics/grid_search.csv")
    )
    parser.add_argument("--family", choices=["svm", "logistic"], default="svm")
    args = parser.parse_args()
    try:
        report = analyze_saved_search(args.grid, args.family)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error en el análisis S5: {exc}\n")
    print(
        f"S5: {report['n_trials']} configuraciones; MAE LOO {report['loo_mae']:.6f}."
    )


if __name__ == "__main__":
    main()
