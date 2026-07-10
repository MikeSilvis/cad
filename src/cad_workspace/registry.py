from __future__ import annotations

import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path

import designs

from cad_workspace.model import CadModel


PROJECTS_ROOT = Path("projects")


def discover_models() -> dict[str, CadModel]:
    models: dict[str, CadModel] = {}

    for module_info in pkgutil.iter_modules(designs.__path__):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"designs.{module_info.name}")
        model = getattr(module, "MODEL", None)
        if model is None:
            continue
        if not isinstance(model, CadModel):
            raise TypeError(f"designs.{module_info.name}.MODEL must be a CadModel")
        if model.name in models:
            raise ValueError(f"Duplicate CAD model name: {model.name}")
        models[model.name] = model

    for project_design in sorted(PROJECTS_ROOT.glob("*/designs/*.py")):
        if project_design.name.startswith("_"):
            continue

        module_name = module_name_for_project_design(project_design)
        module = import_module_from_path(module_name, project_design)
        model = getattr(module, "MODEL", None)
        if model is None:
            continue
        if not isinstance(model, CadModel):
            raise TypeError(f"{project_design}.MODEL must be a CadModel")
        if model.name in models:
            raise ValueError(f"Duplicate CAD model name: {model.name}")
        models[model.name] = model

    return dict(sorted(models.items()))


def import_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def module_name_for_project_design(path: Path) -> str:
    project_id = path.parent.parent.name.replace("-", "_")
    return f"cad_project_{project_id}_{path.stem}"
