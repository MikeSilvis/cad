from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable

from build123d import export_step, export_stl

from cad_workspace.model import CadModel


SUPPORTED_FORMATS = ("stl", "step", "png")


def export_model(
    model: CadModel,
    spec: Any,
    output_root: Path,
    formats: Iterable[str],
) -> list[Path]:
    requested_formats = normalize_formats(formats)
    model_dir = output_root / model.name
    model_dir.mkdir(parents=True, exist_ok=True)

    part = model.build(spec)
    written: list[Path] = []
    stl_path: Path | None = None

    if "stl" in requested_formats or "png" in requested_formats:
        stl_path = model_dir / f"{model.name}.stl"
        export_stl(part, stl_path)
        if "stl" in requested_formats:
            written.append(stl_path)

    if "step" in requested_formats:
        step_path = model_dir / f"{model.name}.step"
        export_step(part, step_path)
        written.append(step_path)

    if "png" in requested_formats:
        if stl_path is None:
            raise RuntimeError("PNG export requires an STL intermediate")
        png_path = model_dir / f"{model.name}.png"
        export_png_from_stl(stl_path, png_path)
        written.append(png_path)

    return written


def normalize_formats(formats: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(format_name.lower() for format_name in formats))
    unsupported = sorted(set(normalized) - set(SUPPORTED_FORMATS))
    if unsupported:
        raise ValueError(f"Unsupported format(s): {', '.join(unsupported)}")
    return normalized


def export_png_from_stl(stl_path: Path, png_path: Path) -> None:
    openscad = shutil.which("openscad")
    if openscad is None:
        raise RuntimeError("PNG export requires the openscad command to be installed")

    with tempfile.TemporaryDirectory() as tmp_dir:
        scad_path = Path(tmp_dir) / "preview.scad"
        scad_path.write_text(f'import("{stl_path.resolve()}");\n')

        subprocess.run(
            [
                openscad,
                "-o",
                str(png_path),
                "--quiet",
                "--imgsize=1400,900",
                "--autocenter",
                "--viewall",
                "--camera=0,0,0,60,0,35,160",
                "--projection=ortho",
                "--colorscheme=Tomorrow",
                str(scad_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
