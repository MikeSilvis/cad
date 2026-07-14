from __future__ import annotations

import argparse
import re
from pathlib import Path

from cad_workspace.cost import CostSettings
from cad_workspace.exporter import SUPPORTED_FORMATS, export_model
from cad_workspace.imports import (
    format_inspection,
    import_reference_file,
    inspect_file,
    render_preview,
)
from cad_workspace.model import SpecError
from cad_workspace.projects import (
    DEFAULT_PROJECTS_ROOT,
    discover_projects,
    load_project,
    package_project,
)
from cad_workspace.render import render_project
from cad_workspace.registry import discover_models


def main() -> None:
    parser = argparse.ArgumentParser(prog="cad")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available CAD models")

    new_parser = subparsers.add_parser("new", help="Create a new design from the template")
    new_parser.add_argument("name", help="Snake-case design name, like phone_stand")
    new_parser.add_argument(
        "--description",
        default="Short human description of what this part is for.",
        help="Description shown by cad list.",
    )

    build_parser = subparsers.add_parser("build", help="Export one model or all models")
    build_parser.add_argument("model", help="Model name, or 'all'")
    build_parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=SUPPORTED_FORMATS,
        default=None,
        help="Export format. Repeat for multiple formats. Defaults to stl, step, and png.",
    )
    build_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Override a model parameter. Only valid when building one model.",
    )
    build_parser.add_argument(
        "--out",
        type=Path,
        default=Path("exports"),
        help="Output directory. Defaults to ./exports.",
    )
    add_cost_arguments(build_parser)

    project_parser = subparsers.add_parser(
        "projects",
        help="List configured projects under projects/<project-id>/.",
    )
    project_parser.add_argument(
        "--projects-root",
        type=Path,
        default=DEFAULT_PROJECTS_ROOT,
        help="Directory that contains project folders. Defaults to ./projects.",
    )

    package_parser = subparsers.add_parser(
        "package",
        help="Build committed artifacts for a configured project.",
    )
    package_parser.add_argument("project", help="Project id, like my-project")
    package_parser.add_argument(
        "--projects-root",
        type=Path,
        default=DEFAULT_PROJECTS_ROOT,
        help="Directory that contains project folders. Defaults to ./projects.",
    )
    add_cost_arguments(package_parser)

    render_parser = subparsers.add_parser(
        "render",
        help="Build the standard final PNG render for a configured project.",
    )
    render_parser.add_argument("project", help="Project id, like my-project")
    render_parser.add_argument(
        "--projects-root",
        type=Path,
        default=DEFAULT_PROJECTS_ROOT,
        help="Directory that contains project folders. Defaults to ./projects.",
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a downloaded STL or STEP file: bounding box, volume, solid count.",
    )
    inspect_parser.add_argument("file", type=Path, help="Path to an STL or STEP file.")
    inspect_parser.add_argument(
        "--preview",
        type=Path,
        default=None,
        help="Write a quick PNG preview of the file to this path.",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Copy a downloaded STL/STEP file into a project as a reference and inspect it.",
    )
    import_parser.add_argument("file", type=Path, help="Path to an STL or STEP file to import.")
    import_parser.add_argument("project", help="Project id, like my-project")
    import_parser.add_argument(
        "--projects-root",
        type=Path,
        default=DEFAULT_PROJECTS_ROOT,
        help="Directory that contains project folders. Defaults to ./projects.",
    )
    import_parser.add_argument(
        "--as-design",
        dest="as_design",
        default=None,
        metavar="NAME",
        help=(
            "Scaffold a starter design file (snake_case name) that imports this STEP "
            "file for further modification. STEP files only."
        ),
    )
    import_parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Skip writing a PNG preview of the imported file.",
    )

    args = parser.parse_args()

    if args.command == "list":
        list_models()
        return

    if args.command == "new":
        create_design(args.name, args.description)
        return

    if args.command == "build":
        build_models(
            args.model,
            args.formats or SUPPORTED_FORMATS,
            args.overrides,
            args.out,
            cost_settings_from_args(args),
        )
        return

    if args.command == "projects":
        list_projects(args.projects_root)
        return

    if args.command == "package":
        package_selected_project(args.project, args.projects_root, cost_settings_from_args(args))
        return

    if args.command == "render":
        render_selected_project(args.project, args.projects_root)
        return

    if args.command == "inspect":
        inspect_selected_file(args.file, args.preview)
        return

    if args.command == "import":
        import_reference(
            args.file, args.project, args.projects_root, args.as_design, args.no_preview
        )
        return


def add_cost_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--filament-density",
        type=float,
        default=CostSettings.filament_density_g_cm3,
        help="Filament density in g/cm^3 for cost estimates. Defaults to PETG-like 1.27.",
    )
    parser.add_argument(
        "--filament-cost-per-kg",
        type=float,
        default=CostSettings.filament_cost_per_kg,
        help="Filament cost in dollars per kilogram. Defaults to 24.",
    )
    parser.add_argument(
        "--material-multiplier",
        type=float,
        default=CostSettings.material_multiplier,
        help="Multiplier for purge, brim, supports, and print waste. Defaults to 1.12.",
    )
    parser.add_argument(
        "--no-cost",
        action="store_true",
        help="Skip writing cost_estimate.json and cost_estimate.txt.",
    )


def cost_settings_from_args(args: argparse.Namespace) -> CostSettings | None:
    if args.no_cost:
        return None

    return CostSettings(
        filament_density_g_cm3=args.filament_density,
        filament_cost_per_kg=args.filament_cost_per_kg,
        material_multiplier=args.material_multiplier,
    )


def list_models() -> None:
    models = discover_models()

    for model in models.values():
        print(f"{model.name}: {model.description}")
        for name, field_type, default in model.spec_fields():
            print(f"  {name} ({type_name(field_type)}): {default}")


def list_projects(projects_root: Path) -> None:
    projects = discover_projects(projects_root)

    for project in projects.values():
        print(f"{project.project_id}: {project.title}")
        if project.description:
            print(f"  {project.description}")
        for artifact in project.artifacts:
            formats = ", ".join(artifact.formats)
            print(f"  {artifact.slug}: {artifact.model} ({formats})")


def package_selected_project(
    project_id: str,
    projects_root: Path,
    cost_settings: CostSettings | None,
) -> None:
    try:
        project = load_project(project_id, projects_root)
        written = package_project(project, cost_settings=cost_settings)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    for path in written:
        print(f"Exported {path}")


def render_selected_project(project_id: str, projects_root: Path) -> None:
    try:
        project = load_project(project_id, projects_root)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    render_path = render_project(project)
    if render_path is None:
        raise SystemExit(f"{project_id} has no artifact PNGs to render")

    print(f"Rendered {render_path}")


def build_models(
    selected_model: str,
    formats: list[str] | tuple[str, ...],
    raw_overrides: list[str],
    output_root: Path,
    cost_settings: CostSettings | None,
) -> None:
    models = discover_models()
    overrides = parse_overrides(raw_overrides)

    if selected_model == "all":
        if overrides:
            raise SystemExit("--set overrides can only be used when building one model")
        selected = models.values()
    else:
        if selected_model not in models:
            available = ", ".join(models)
            raise SystemExit(f"Unknown model {selected_model!r}. Available models: {available}")
        selected = [models[selected_model]]

    for model in selected:
        try:
            spec = model.spec_with_overrides(overrides if selected_model != "all" else {})
        except SpecError as error:
            raise SystemExit(str(error)) from error

        written = export_model(model, spec, output_root, formats, cost_settings)
        for path in written:
            print(f"Exported {path}")


def create_design(name: str, description: str) -> None:
    validate_design_name(name)

    destination = Path.cwd() / "designs" / f"{name}.py"
    write_from_template(
        Path.cwd() / "templates" / "new_design.py",
        destination,
        {
            "NewDesign": to_pascal_case(name),
            "new_design": name,
            "Short human description of what this part is for.": description,
        },
    )
    print(f"Created {destination}")


def write_from_template(
    template_path: Path, destination: Path, replacements: dict[str, str]
) -> None:
    if destination.exists():
        raise SystemExit(f"{destination} already exists")
    if not template_path.exists():
        raise SystemExit(f"Could not find template at {template_path}")

    source = template_path.read_text()
    for old, new in replacements.items():
        source = source.replace(old, new)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source)


def inspect_selected_file(path: Path, preview: Path | None) -> None:
    if not path.exists():
        raise SystemExit(f"{path} does not exist")

    try:
        inspection = inspect_file(path)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    print(format_inspection(inspection))

    if preview is not None:
        write_preview(path, preview)


def import_reference(
    path: Path,
    project_id: str,
    projects_root: Path,
    as_design: str | None,
    no_preview: bool,
) -> None:
    if not path.exists():
        raise SystemExit(f"{path} does not exist")

    try:
        destination = import_reference_file(path, project_id, projects_root)
        inspection = inspect_file(destination)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    print(f"Copied {path} -> {destination}")
    print(format_inspection(inspection))
    if not no_preview:
        write_preview(destination, destination.with_suffix(".png"))

    if as_design is not None:
        if inspection.file_format != "step":
            raise SystemExit(
                "--as-design only supports STEP files. STL files are meshes with no "
                "parametric data; use them as a dimensional reference and hand-build a "
                "new parametric design instead."
            )
        design_path = scaffold_imported_design(as_design, project_id, projects_root, destination)
        print(f"Created {design_path}")
    elif inspection.file_format == "stl":
        print(
            "STL is a mesh with no parametric data. Either commit it as-is under "
            f"projects/{project_id}/outputs/<artifact-slug>/, or use it as a "
            "dimensional reference to hand-build a new parametric design in "
            f"projects/{project_id}/designs/."
        )


def scaffold_imported_design(
    name: str, project_id: str, projects_root: Path, reference_path: Path
) -> Path:
    validate_design_name(name)

    destination = projects_root / project_id / "designs" / f"{name}.py"
    write_from_template(
        Path.cwd() / "templates" / "imported_step_design.py",
        destination,
        {
            "NewDesign": to_pascal_case(name),
            "new_design": name,
            "REFERENCE_FILENAME": reference_path.name,
        },
    )
    return destination


def write_preview(path: Path, preview: Path) -> None:
    try:
        render_preview(path, preview)
    except RuntimeError as error:
        print(f"Skipped preview: {error}")
        return

    print(f"Wrote preview {preview}")


def parse_overrides(raw_overrides: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for override in raw_overrides:
        if "=" not in override:
            raise SystemExit(f"Expected NAME=VALUE, got {override!r}")
        name, value = override.split("=", 1)
        overrides[name.strip()] = value.strip()
    return overrides


def type_name(field_type: object) -> str:
    return getattr(field_type, "__name__", str(field_type))


def validate_design_name(name: str) -> None:
    if re.fullmatch(r"[a-z][a-z0-9_]*", name) is None:
        raise SystemExit("Design name must be snake_case, like phone_stand or wall_mount")


def to_pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


if __name__ == "__main__":
    main()
