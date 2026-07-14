from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from build123d import export_stl, import_step, import_stl

from cad_workspace.exporter import export_png_from_stl


STEP_SUFFIXES = (".step", ".stp")
STL_SUFFIXES = (".stl",)
SUPPORTED_IMPORT_SUFFIXES = STEP_SUFFIXES + STL_SUFFIXES


@dataclass(frozen=True)
class ImportInspection:
    path: Path
    file_format: str
    size_x_mm: float
    size_y_mm: float
    size_z_mm: float
    volume_mm3: float | None
    solid_count: int | None


def inspect_file(path: Path) -> ImportInspection:
    suffix = path.suffix.lower()

    if suffix in STEP_SUFFIXES:
        shape = import_step(path)
        solids = shape.solids()
        return ImportInspection(
            path=path,
            file_format="step",
            size_x_mm=shape.bounding_box().size.X,
            size_y_mm=shape.bounding_box().size.Y,
            size_z_mm=shape.bounding_box().size.Z,
            volume_mm3=shape.volume if solids else None,
            solid_count=len(solids),
        )

    if suffix in STL_SUFFIXES:
        shape = import_stl(path)
        return ImportInspection(
            path=path,
            file_format="stl",
            size_x_mm=shape.bounding_box().size.X,
            size_y_mm=shape.bounding_box().size.Y,
            size_z_mm=shape.bounding_box().size.Z,
            volume_mm3=None,
            solid_count=None,
        )

    raise ValueError(
        f"Unsupported file format {suffix!r}. Supported formats: "
        f"{', '.join(SUPPORTED_IMPORT_SUFFIXES)}"
    )


def format_inspection(inspection: ImportInspection) -> str:
    lines = [
        str(inspection.path),
        f"  format: {inspection.file_format}",
        "  bounding box (mm): "
        f"{inspection.size_x_mm:.2f} x {inspection.size_y_mm:.2f} x {inspection.size_z_mm:.2f}",
    ]

    if inspection.file_format == "step":
        if inspection.solid_count:
            lines.append(
                f"  volume: {inspection.volume_mm3:.1f} mm^3 "
                f"({inspection.volume_mm3 / 1000:.2f} cm^3)"
            )
            lines.append(f"  solids: {inspection.solid_count}")
        else:
            lines.append("  solids: 0 (surfaces only, not a closed solid)")
    else:
        lines.append("  volume: n/a (STL is a mesh reference, not an editable solid)")

    return "\n".join(lines)


def import_reference_file(path: Path, project_id: str, projects_root: Path) -> Path:
    project_dir = projects_root / project_id
    if not project_dir.exists():
        raise ValueError(
            f"Unknown project {project_id!r}. Create {project_dir}/project.toml first, "
            "or create the project directory before importing a reference file."
        )

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_IMPORT_SUFFIXES:
        raise ValueError(
            f"Unsupported file format {suffix!r}. Supported formats: "
            f"{', '.join(SUPPORTED_IMPORT_SUFFIXES)}"
        )

    reference_dir = project_dir / "reference"
    reference_dir.mkdir(exist_ok=True)
    destination = reference_dir / path.name
    shutil.copy2(path, destination)
    return destination


def render_preview(path: Path, output: Path) -> None:
    suffix = path.suffix.lower()

    if suffix in STL_SUFFIXES:
        export_png_from_stl(path, output)
        return

    if suffix in STEP_SUFFIXES:
        shape = import_step(path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            stl_path = Path(tmp_dir) / "preview.stl"
            export_stl(shape, stl_path)
            export_png_from_stl(stl_path, output)
        return

    raise ValueError(
        f"Unsupported file format {suffix!r}. Supported formats: "
        f"{', '.join(SUPPORTED_IMPORT_SUFFIXES)}"
    )
