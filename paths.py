"""Project path roots for a standalone clone (or legacy parent-layout data)."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
_PARENT = REPO_ROOT.parent


def _resolve_root(name: str) -> Path:
    """Prefer repo-local dirs; fall back to sibling dirs under the parent project."""
    local = REPO_ROOT / name
    parent = _PARENT / name
    if local.exists():
        return local
    if parent.exists():
        return parent
    return local


DATA_ROOT = _resolve_root("data")
DATASETS_ROOT = _resolve_root("datasets")
# Artifacts default to this repo (created on demand)
RESULTS_ROOT = REPO_ROOT / "results"
CHECKPOINTS_ROOT = REPO_ROOT / "checkpoints"
IMAGES_ROOT = REPO_ROOT / "images"
MODELS_ROOT = REPO_ROOT / "models"

# String forms for f-strings / os.path.join
DATA = str(DATA_ROOT)
DATASETS = str(DATASETS_ROOT)
RESULTS = str(RESULTS_ROOT)
CHECKPOINTS = str(CHECKPOINTS_ROOT)
IMAGES = str(IMAGES_ROOT)
MODELS = str(MODELS_ROOT)


def ensure_output_dirs() -> None:
    for path in (RESULTS_ROOT, CHECKPOINTS_ROOT, IMAGES_ROOT, MODELS_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    for years in (1, 3, 5):
        (DATASETS_ROOT / f"{years}YEAR").mkdir(parents=True, exist_ok=True)
        (RESULTS_ROOT / f"{years}YEAR").mkdir(parents=True, exist_ok=True)
        (CHECKPOINTS_ROOT / f"{years}YEAR").mkdir(parents=True, exist_ok=True)
