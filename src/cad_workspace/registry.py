from __future__ import annotations

import importlib
import pkgutil

import designs

from cad_workspace.model import CadModel


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

    return dict(sorted(models.items()))

