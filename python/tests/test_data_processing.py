"""Data validation tests with isolated JSON fixtures."""

import json

import pytest

from src.data_processing import (
    CLASSES,
    clean_text,
    combine_text,
    load_data,
    split_data,
    ticket_fingerprint,
)
from src.utils import ROOT, file_hash, load_config, project_path


def write_records(tmp_path, rows):
    """Create a temporary dataset for a single test."""
    path = tmp_path / "tickets.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def records():
    """Generate distinct, balanced unit-test records."""
    return [
        {
            "titulo": f"Ticket {label} {i}",
            "cuerpo": f"Problema número {i}",
            "clasificacion": label,
        }
        for label in CLASSES
        for i in range(10)
    ]


def test_clean_text_removes_identifiers():
    """Cleaning must remove email addresses and attachment filenames."""
    text = clean_text("<b>ACCESO</b> test@example.org mensaje_acceso.txt")
    assert text == "acceso correo adjunto"


@pytest.mark.parametrize(
    "title,body",
    [("", "Ayuda"), ("***", "Ayuda"), ("Ayuda", "1234"), (None, "Ayuda")],
)
def test_invalid_input(title, body):
    """Blank, numeric and symbol-only text must fail before prediction."""
    with pytest.raises(ValueError):
        combine_text(title, body)


def test_load_and_deduplicate(tmp_path):
    """Exact normalized duplicates must be removed before splitting."""
    rows = records()
    result = load_data(write_records(tmp_path, rows + [rows[0]]))
    assert len(result) == 40
    assert "texto" in result


def test_missing_and_unknown_labels(tmp_path):
    """Missing fields and unsupported labels must fail explicitly."""
    with pytest.raises(ValueError, match="Faltan columnas"):
        load_data(write_records(tmp_path, [{"titulo": "Ayuda"}]))
    rows = records()
    rows[0]["clasificacion"] = "inventada"
    with pytest.raises(ValueError, match="permitidas"):
        load_data(write_records(tmp_path, rows))


def test_split_is_disjoint_and_reproducible(tmp_path):
    """No duplicate text or row may cross train and test partitions."""
    frame = load_data(write_records(tmp_path, records()))
    train, test = split_data(frame)
    assert set(train.index).isdisjoint(test.index)
    assert set(train.texto).isdisjoint(test.texto)
    assert set(test.clasificacion) == set(CLASSES)
    assert train.index.tolist() == split_data(frame)[0].index.tolist()


def test_conflicting_labels_rejected(tmp_path):
    """The same normalized ticket cannot carry contradictory targets."""
    rows = records()
    duplicate = dict(rows[0], clasificacion="otros")
    with pytest.raises(ValueError, match="contradictorias"):
        load_data(write_records(tmp_path, rows + [duplicate]))


def test_frozen_holdout_survives_new_training_data(tmp_path):
    """Appending data must not move reserved tickets into training."""
    frame = load_data(write_records(tmp_path, records()))
    _, test = split_data(frame)
    manifest = {
        "test_tickets": [
            {
                "fingerprint": ticket_fingerprint(row.texto),
                "clasificacion": row.clasificacion,
            }
            for row in test.itertuples()
        ]
    }
    path = tmp_path / "holdout.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    rows = records() + [
        {
            "titulo": "Nueva solicitud",
            "cuerpo": "Ayuda con mi cuenta",
            "clasificacion": "accesos",
        }
    ]
    expanded = load_data(write_records(tmp_path, rows))
    train, frozen = split_data(expanded, holdout_manifest=path)
    assert frozen.texto.tolist() == test.texto.tolist()
    assert len(train) == 33
    assert "Nueva solicitud" in train.titulo.values
    assert set(train.texto).isdisjoint(frozen.texto)


def test_frozen_holdout_rejects_changed_label(tmp_path):
    """Reserved labels must never be silently changed for evaluation."""
    frame = load_data(write_records(tmp_path, records()))
    _, test = split_data(frame)
    entries = [
        {
            "fingerprint": ticket_fingerprint(row.texto),
            "clasificacion": row.clasificacion,
        }
        for row in test.itertuples()
    ]
    entries[0]["clasificacion"] = (
        "otros" if entries[0]["clasificacion"] != "otros" else "accesos"
    )
    path = tmp_path / "holdout.json"
    path.write_text(json.dumps({"test_tickets": entries}), encoding="utf-8")
    with pytest.raises(ValueError, match="modificadas"):
        split_data(frame, holdout_manifest=path)


def test_frozen_holdout_rejects_missing_ticket(tmp_path):
    """Missing holdout records must fail rather than trigger a fresh split."""
    frame = load_data(write_records(tmp_path, records()))
    path = tmp_path / "holdout.json"
    path.write_text(
        json.dumps(
            {
                "test_tickets": [
                    {"fingerprint": "missing", "clasificacion": "accesos"}
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Faltan tickets"):
        split_data(frame, holdout_manifest=path)


def test_delivered_holdout_reproduces_recorded_diagnostic_split():
    """Require the shipped manifest to recover the historical 280/20 split."""
    config = load_config()
    manifest_path = project_path(config["holdout_manifest"])
    summary = json.loads(
        (ROOT / "results/metrics/training_summary.json").read_text(
            encoding="utf-8"
        )
    )
    before = file_hash(manifest_path)
    assert before == summary["holdout_manifest_sha256"]
    frame = load_data(project_path(config["data_path"]))
    training, diagnostic = split_data(
        frame,
        config["test_size"],
        config["seed"],
        config["cv_folds"],
        holdout_manifest=manifest_path,
    )
    assert len(training) == summary["n_evaluation_train"] == 280
    assert len(diagnostic) == summary["n_test"] == 20
    assert diagnostic.index.tolist() == summary["test_indices"]
    assert training.index.tolist() == summary["evaluation_train_indices"]
    assert set(training.texto).isdisjoint(diagnostic.texto)
    assert set(diagnostic.clasificacion) == set(CLASSES)
    assert file_hash(manifest_path) == before
