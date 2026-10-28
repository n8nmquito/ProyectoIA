"""Shared TF-IDF pipelines and probability-based ticket predictions."""

from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.data_processing import CLASSES, combine_text
from src.utils import load_config


def refit_pipeline(pipeline, texts, labels):
    """Fit a fresh selected pipeline on every supplied training record."""
    final = clone(pipeline)
    final.fit(texts, labels)
    final.training_sample_count_ = len(texts)
    final.training_class_counts_ = dict(Counter(labels))
    return final


def build_pipeline(kind="logistic", seed=None, config=None):
    """Build a pipeline using configurable text features and model settings."""
    config = load_config() if config is None else config
    seed = config["seed"] if seed is None else seed
    model = config["model"]
    tfidf = config["tfidf"]
    estimators = {
        "baseline": DummyClassifier(strategy="most_frequent"),
        "logistic": LogisticRegression(
            max_iter=model["logistic_max_iter"], random_state=seed
        ),
        "svm": CalibratedClassifierCV(
            LinearSVC(random_state=seed, dual="auto"),
            cv=model["calibration_folds"],
        ),
    }
    if kind not in estimators:
        raise ValueError(f"Modelo desconocido: {kind}.")
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=tuple(tfidf["ngram_range"]),
                    sublinear_tf=tfidf["sublinear_tf"],
                    strip_accents=tfidf["strip_accents"],
                ),
            ),
            ("classifier", estimators[kind]),
        ]
    )


def load_model(path):
    """Load a trusted local pipeline and validate its prediction interface."""
    path = Path(path)
    try:
        pipeline = joblib.load(path)
    except Exception as exc:
        raise ValueError(
            f"No se pudo cargar el modelo {path}. Entrena de nuevo."
        ) from exc
    if not isinstance(pipeline, Pipeline) or not hasattr(
        pipeline, "predict_proba"
    ):
        raise ValueError(
            "El archivo no contiene un pipeline con probabilidades."
        )
    if set(pipeline.classes_) != set(CLASSES):
        raise ValueError(
            "El modelo no representa las cuatro categorías esperadas."
        )
    return pipeline


def predict_ticket(pipeline, title, body, threshold=None):
    """Return all class probabilities and flag low-confidence or OOV input."""
    threshold = (
        load_config()["confidence_threshold"]
        if threshold is None
        else threshold
    )
    text = combine_text(title, body)
    try:
        vector = pipeline.named_steps["tfidf"].transform([text])
        probabilities = pipeline.predict_proba([text])[0]
    except Exception as exc:
        raise ValueError(
            "No se pudo clasificar el ticket con este modelo."
        ) from exc
    best = int(np.argmax(probabilities))
    confidence = float(probabilities[best])
    oov = vector.nnz == 0
    return {
        "categoria": str(pipeline.classes_[best]),
        "confianza": confidence,
        "probabilidades": dict(
            zip(pipeline.classes_, map(float, probabilities))
        ),
        "requiere_revision": confidence < threshold or oov,
        "sin_vocabulario": bool(oov),
    }


def top_terms(pipeline, count=12):
    """Expose linear coefficients, averaging calibrated SVM estimators."""
    classifier = pipeline.named_steps["classifier"]
    if hasattr(classifier, "coef_"):
        coefficients = classifier.coef_
    elif hasattr(classifier, "calibrated_classifiers_"):
        coefficients = np.mean(
            [
                item.estimator.coef_
                for item in classifier.calibrated_classifiers_
            ],
            axis=0,
        )
    else:
        return {}
    names = pipeline.named_steps["tfidf"].get_feature_names_out()
    return {
        str(label): names[np.argsort(row)[-count:][::-1]].tolist()
        for label, row in zip(classifier.classes_, coefficients)
    }
