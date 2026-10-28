"""Discover trained classifier files in the active models directory."""

import re
from pathlib import Path

MODEL_NAME = re.compile(r"modelo_clasificador_([1-9][0-9]*)\.pkl\Z")


def available_model_sizes(directory):
    """List active model sizes without traversing backup subdirectories."""
    sizes = []
    for path in Path(directory).glob("modelo_clasificador_*.pkl"):
        match = MODEL_NAME.fullmatch(path.name)
        if match:
            try:
                if path.is_file():
                    sizes.append(int(match.group(1)))
            except FileNotFoundError:
                # A model can be removed between listing and checking it.
                continue
    return sorted(sizes)
