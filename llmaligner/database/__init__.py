from __future__ import annotations

from pathlib import Path

from .database_retriv import DatabaseRetriv


_DATABASE_CLASSES: tuple[type, ...] = (DatabaseRetriv,)


def build_database(
    yaml_path: Path,
    output_path: Path,
):
    return DatabaseRetriv.build(yaml_path, output_path)


def load_database(
    path: Path | str,
):
    errors: list[tuple[str, Exception]] = []
    for db_cls in _DATABASE_CLASSES:
        try:
            return db_cls(path)
        except Exception as exc:
            errors.append((db_cls.__name__, exc))
            continue
    error_lines = "; ".join(f"{name}: {exc}" for name, exc in errors)
    raise RuntimeError(f"Unable to load database from {path}. Errors: {error_lines}")
