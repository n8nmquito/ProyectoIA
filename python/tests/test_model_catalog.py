"""Verify filesystem discovery and exclusion of archived model files."""

from app.model_catalog import available_model_sizes


def test_catalog_reads_available_sizes_and_excludes_backups(tmp_path):
    for name in (
        "modelo_clasificador_200.pkl", "modelo_clasificador_10.pkl",
        "modelo_clasificador_500.pkl", "modelo_clasificador_0.pkl",
        "modelo_clasificador_abc.pkl", "archivo.txt",
    ):
        (tmp_path / name).write_bytes(b"fixture")
    backup = tmp_path / "Respaldo"
    backup.mkdir()
    (backup / "modelo_clasificador_300.pkl").write_bytes(b"fixture")
    (tmp_path / "modelo_clasificador_100.pkl").mkdir()
    assert available_model_sizes(tmp_path) == [10, 200, 500]
    (tmp_path / "modelo_clasificador_200.pkl").unlink()
    assert available_model_sizes(tmp_path) == [10, 500]


def test_missing_directory_has_no_available_models(tmp_path):
    assert available_model_sizes(tmp_path / "missing") == []
