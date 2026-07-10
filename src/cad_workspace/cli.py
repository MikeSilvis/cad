from __future__ import annotations

import argparse
import re
from pathlib import Path

from cad_workspace.cost import CostSettings
from cad_workspace.exporter import SUPPORTED_FORMATS, export_model
from cad_workspace.model import SpecError
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
    build_parser.add_argument(
        "--filament-density",
        type=float,
        default=CostSettings.filament_density_g_cm3,
        help="Filament density in g/cm^3 for cost estimates. Defaults to PETG-like 1.27.",
    )
    build_parser.add_argument(
        "--filament-cost-per-kg",
        type=float,
        default=CostSettings.filament_cost_per_kg,
        help="Filament cost in dollars per kilogram. Defaults to 24.",
    )
    build_parser.add_argument(
        "--material-multiplier",
        type=float,
        default=CostSettings.material_multiplier,
        help="Multiplier for purge, brim, supports, and print waste. Defaults to 1.12.",
    )
    build_parser.add_argument(
        "--no-cost",
        action="store_true",
        help="Skip writing cost_estimate.json and cost_estimate.txt.",
    )

    args = parser.parse_args()

    if args.command == "list":
        list_models()
        return

    if args.command == "new":
        create_design(args.name, args.description)
        return

    if args.command == "build":
        cost_settings = None
        if not args.no_cost:
            cost_settings = CostSettings(
                filament_density_g_cm3=args.filament_density,
                filament_cost_per_kg=args.filament_cost_per_kg,
                material_multiplier=args.material_multiplier,
            )

        build_models(
            args.model,
            args.formats or SUPPORTED_FORMATS,
            args.overrides,
            args.out,
            cost_settings,
        )


def list_models() -> None:
    models = discover_models()

    for model in models.values():
        print(f"{model.name}: {model.description}")
        for name, field_type, default in model.spec_fields():
            print(f"  {name} ({type_name(field_type)}): {default}")


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

    root = Path.cwd()
    template_path = root / "templates" / "new_design.py"
    destination = root / "designs" / f"{name}.py"

    if destination.exists():
        raise SystemExit(f"{destination} already exists")
    if not template_path.exists():
        raise SystemExit(f"Could not find template at {template_path}")

    class_prefix = to_pascal_case(name)
    source = template_path.read_text()
    source = source.replace("NewDesign", class_prefix)
    source = source.replace("new_design", name)
    source = source.replace("Short human description of what this part is for.", description)

    destination.parent.mkdir(exist_ok=True)
    destination.write_text(source)
    print(f"Created {destination}")


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
